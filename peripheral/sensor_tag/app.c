/******************************************************************************/
/*                                                                            */
/*  Filename: app.c                                                           */
/*  Author: Markus Andersson                                                  */
/*  Date: January 11, 2025                                                    */
/*                                                                            */
/*  Description:                                                              */
/*  Main application for the sensor tag.                                      */
/*                                                                            */
/*                                                                            */
/*  License: MIT License                                                      */
/*                                                                            */
/*  This file is part of an open-source project and is distributed under      */
/*  the terms of the MIT License. You may obtain a copy of the License at:    */
/*  https://opensource.org/licenses/MIT                                       */
/*                                                                            */
/*  Copyright (c) <Year>, <Your Name/Organization>. All rights reserved.      */
/*                                                                            */
/******************************************************************************/

#include "app.h"
#include "app_assert.h"
#include "battery_level.h"
#include "em_common.h"
#include "gatt_db.h"
#include "pawr.h"
#include "tag_advertiser.h"
#include "sl_bluetooth.h"
#include "sl_clock_manager.h"
#include "sl_i2cspm_instances.h"
#include "sl_power_manager.h"
#include "sl_sensor_rht.h"
#include "sl_sleeptimer.h"

#define PAWR_SKIP                   0
#define PAWR_TIMEOUT                0x4000
#define PAWR_HEADER_LEN             2
#define PAWR_BROADCAST_ADDR         255
#define IGNORE_MESSAGE              255
#define PAWR_OUT_OF_SYNC_LIMIT      20  // Number of subevents that can be missed before starting advertising to resync

/* Static global variables */
static uint8_t advertising_set_handle = 0xff;
static uint8_t connection_handle = 0xff;
static uint8_t pawr_response_slot = 0xff;
static sl_sleeptimer_timer_handle_t out_of_sync_timer_handle;
static uint32_t timer_limit = 0;
static uint16_t sync_handle;

static sensor_values_t sensor_values;

static fsm_t app_fsm;
static fsm_t pawr_fsm;

/* Application init */
SL_WEAK void app_init(void)
{
    sl_status_t sc = sl_sensor_rht_init();
    app_assert_status(sc);
    pawr_set_new_state(UNSYNCED);
    sensor_values.temperature = 0;
    sensor_values.humidity = 0;
}

/* Application task handler */
SL_WEAK void app_process_action(void)
{
    sl_status_t sc;

    switch (app_fsm.current_state) {
        case CLOSE_SYNC:
            sc = sl_bt_sync_close(sync_handle);
            app_assert_status(sc);
            app_set_new_state(IDLE);
            break;

        default:
            break;
    }
}

/* BLE stack event handler */
void sl_bt_on_event(sl_bt_msg_t *evt)
{
    sl_status_t sc;

    switch (SL_BT_MSG_ID(evt->header)) {
        case sl_bt_evt_system_boot_id:
            sc = sl_bt_past_receiver_set_default_sync_receive_parameters(sl_bt_past_receiver_mode_synchronize, PAWR_SKIP, PAWR_TIMEOUT, sl_bt_sync_report_all);
            app_assert_status(sc);
            sc = tag_advertiser_start(&advertising_set_handle);
            break;

        case sl_bt_evt_connection_opened_id:
            connection_handle = evt->data.evt_connection_opened.connection;
            sc = tag_advertiser_stop(&advertising_set_handle);
            app_assert_status(sc);
            app_set_new_state(IDLE);
            break;

        case sl_bt_evt_gatt_server_attribute_value_id:
            if (evt->data.evt_gatt_server_attribute_value.attribute == gattdb_pawr_response_slot) {
                pawr_response_slot = evt->data.evt_gatt_server_attribute_value.value.data[0];
            }
            break;

        case sl_bt_evt_pawr_sync_transfer_received_id:
            // The tag is in sync -> Close the connection
            sc = sl_bt_connection_close(connection_handle);
            app_assert_status(sc);
            pawr_set_new_state(SYNCED);
            sync_handle = evt->data.evt_pawr_sync_transfer_received.sync;

            // Start the timer to detect sync timeout
            timer_limit = PAWR_OUT_OF_SYNC_LIMIT * evt->data.evt_pawr_sync_transfer_received.adv_interval * 1.25;
            sc = sl_sleeptimer_start_timer_ms(&out_of_sync_timer_handle, timer_limit, out_of_sync_callback, NULL, 5, 0);
            app_assert_status(sc);
            break;

        case sl_bt_evt_pawr_sync_subevent_report_id:
            // Handle the incoming subevent report
            pawr_opcodes_t subevent_opcode;
            uint8_t pawr_response_data[250];
            uint8_t pawr_response_data_len;
            uint8_t subevent_data_len = evt->data.evt_pawr_sync_subevent_report.data.len;

            if (subevent_data_len > 0) {
                // Check if the subevent data contains any message for the tag
                subevent_opcode = find_addr_in_payload(evt->data.evt_pawr_sync_subevent_report.data.data);

                if (subevent_opcode != IGNORE_MESSAGE) {
                    // Handle the messsage, and set the response
                    pawr_data_handler(subevent_opcode, subevent_data_len, pawr_response_data, &pawr_response_data_len);
                    sc = sl_bt_pawr_sync_set_response_data(evt->data.evt_pawr_sync_subevent_report.sync, evt->data.evt_pawr_sync_subevent_report.event_counter,
                                                        evt->data.evt_pawr_sync_subevent_report.subevent, evt->data.evt_pawr_sync_subevent_report.subevent, pawr_response_slot, pawr_response_data_len,
                                                        pawr_response_data);
                    app_assert_status(sc);
                }
            }
            // Restart the timer as the tag is in sync
            sc = sl_sleeptimer_restart_timer_ms(&out_of_sync_timer_handle, timer_limit, out_of_sync_callback, NULL, 5, 0);
            app_assert_status(sc);
            break;

        case sl_bt_evt_connection_closed_id:
            // Restart advertising if not synced
            if (pawr_fsm.current_state != SYNCED) {
                tag_advertiser_start(&advertising_set_handle);
            }
            break;

        case sl_bt_evt_sync_closed_id:
            // Restart advertising after sync is lost
            sc = tag_advertiser_start(&advertising_set_handle);
            app_assert_status(sc);
            break;

        default:
            break;
    }
}

/* Setting the new app fsm state */
void app_set_new_state(app_state_t new_state)
{
    app_fsm.previous_state = app_fsm.current_state;
    app_fsm.current_state = new_state;
}

/* Setting the new pawr fsm state */
void pawr_set_new_state(app_state_t new_state)
{
    pawr_fsm.previous_state = pawr_fsm.current_state;
    pawr_fsm.current_state = new_state;
}

/* Handle the incoming PAwR data */
void pawr_data_handler(pawr_opcodes_t subevent_opcode, uint8_t data_len, uint8_t *response_data, uint8_t *response_data_len)
{
    sl_status_t sc;
    (void)data_len;
    switch (subevent_opcode) {
        case PING:
            // When pinged, just reply with the tag address and ping opcode
            response_data[0] = pawr_response_slot;
            response_data[1] = PING;
            *response_data_len = 2;
            break;
        case READ_SENSOR_VALUES:
            // Read, format, and return the sensor values
            uint8_t pawr_sensor_data[30];
            uint8_t pawr_sensor_data_len;

            sc = sl_sensor_rht_get(&sensor_values.humidity, &sensor_values.temperature);
            app_assert_status(sc);
            sc = get_battery_level(&sensor_values.battery_level);
            app_assert_status(sc);
            sc = pawr_create_sensor_response(&sensor_values.temperature, &sensor_values.humidity, &sensor_values.battery_level,
                                             pawr_sensor_data, &pawr_sensor_data_len);
            app_assert_status(sc);

            // Set the response data
            response_data[0] = pawr_response_slot;
            response_data[1] = READ_SENSOR_VALUES;
            memcpy(&response_data[2], pawr_sensor_data, pawr_sensor_data_len);
            *response_data_len = pawr_sensor_data_len + PAWR_HEADER_LEN;
            break;
        default:
            break;
    }
}

/* Check if the tag address (response slot) is in the header of the PAwR message. If address is found, return the opcode */
uint8_t find_addr_in_payload(uint8_t* pawr_payload) {
    uint8_t header_len = pawr_payload[0];

    for (uint8_t i = 1; i <= header_len; i++) {
        uint8_t address = pawr_payload[i];
        if (address == pawr_response_slot || address == PAWR_BROADCAST_ADDR) {
            return pawr_payload[header_len + 1];  // return the opcode
        }
    }

    // Tag address was not found in the header
    return IGNORE_MESSAGE;
}

/* Callback for when we detect out of sync */
void out_of_sync_callback(sl_sleeptimer_timer_handle_t *handle, void *data) {
    (void)handle;
    (void)data;

    app_set_new_state(CLOSE_SYNC);
}
