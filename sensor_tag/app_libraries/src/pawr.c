/******************************************************************************/
/*                                                                            */
/*  Filename: pawr.c                                                          */
/*  Author: Markus Andersson                                                  */
/*  Date: January 11, 2025                                                    */
/*                                                                            */
/*  Description:                                                              */
/*  Functions used for creating the PAwR payload                              */
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

#include "pawr.h"
#include "sl_status.h"
#include "string.h"

#define PAWR_SENSOR_RESPONSE_LEN    17

/** Construct the PAwR response based on the measured values.  */
sl_status_t pawr_create_sensor_response(int32_t *temperature, uint32_t *humidity, 
                                        uint8_t *battery_level, uint8_t *data_buffer, 
                                        uint8_t *data_len)
{
    uint8_t advertising_data[] = {
        0x05, 0x16, 0x6E, 0x2A, 0x00, 0x00, // temperature
        0x05, 0x16, 0x6F, 0x2A, 0x00, 0x00, // humidity
        0x04, 0x16, 0x19, 0x2A, 0x00,       // battery level
    }; // 0x00 are placeholders

    // Initially the values are multiplied by 1000 in the sensor drive, so we have to divide by 10 to get two decimals.
    int16_t temp_val = (*temperature) / 10;
    uint32_t humidity_val = (*humidity) / 10;
    if (humidity_val > 10000) {
        humidity_val = 10000;
    }

    // Split the 16-bit values to bytes
    int8_t temp_val_msb = (temp_val >> 8) & 0xFF;
    int8_t temp_val_lsb = temp_val & 0xFF;
    uint8_t humidity_val_msb = (humidity_val >> 8) & 0xFF;
    uint8_t humidity_val_lsb = humidity_val & 0xFF;

    // Assign the bytes to the correct placeholders
    advertising_data[4] = temp_val_lsb;
    advertising_data[5] = temp_val_msb;
    advertising_data[10] = humidity_val_lsb;
    advertising_data[11] = humidity_val_msb;
    advertising_data[16] = *battery_level;

    memcpy((void *)data_buffer, (const void *)advertising_data, PAWR_SENSOR_RESPONSE_LEN);
    *data_len = PAWR_SENSOR_RESPONSE_LEN;

    return SL_STATUS_OK;
}