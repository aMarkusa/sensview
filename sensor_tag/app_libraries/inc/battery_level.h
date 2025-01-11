#ifndef __BATTERY_VOLTAGE_H__
#define __BATTERY_VOLTAGE_H__

#include "sl_status.h"

void init_IADC(void);

void deinit_IADC(void);

/** Read the battery voltage using IADC */
float read_battery_voltage(void);

/** Read the battery voltage and convert to battery level */
sl_status_t get_battery_level(uint8_t* battery_level);

#endif // __BATTERY_VOLTAGE_H__;
