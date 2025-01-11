#ifndef APP
#define APP

#include "stdint.h"
#include "stdbool.h"
#include "sl_sleeptimer.h"

/** Application init */
void app_init(void);

/** Application task handler */
void app_process_action(void);

typedef enum { 
    IDLE,
    READING_SENSOR,
    SENSOR_VALUES_READ,
    ADVERTISING,
    PREPARING_FOR_SLEEP,
    UNSYNCED, 
    SYNCED, 
    CLOSE_SYNC
} app_state_t;

typedef enum { 
    PING, 
    READ_SENSOR_VALUES 
} pawr_opcodes_t;

typedef struct {
  app_state_t current_state;
  app_state_t previous_state;
} fsm_t;

typedef struct {
  int32_t temperature;
  uint32_t humidity;
  uint8_t battery_level;
} sensor_values_t;

/** Setting the new fsm state */
void app_set_new_state(app_state_t new_state);

void pawr_set_new_state(app_state_t new_state);

/* Checking if app is ok to enter sleep. This overwrites the function in sl_power_manager_handler.c */
bool app_is_ok_to_sleep(void);

/* Callback for stopping advertiser */
void advertising_cb(sl_sleeptimer_timer_handle_t *sleeptimer_handle, void* data);

/* Handle the incoming PAwR data */
void pawr_data_handler(pawr_opcodes_t subevent_opcode, uint8_t data_len, uint8_t* response_data, uint8_t* response_data_len);

/* Check if the tag address (response slot) is in the header of the PAwR message. If address is found, return the data */
uint8_t find_addr_in_payload(uint8_t* message);

/* Callback for when we detect out of sync */
void out_of_sync_callback(sl_sleeptimer_timer_handle_t *handle, void *data);

#endif /* APP */
