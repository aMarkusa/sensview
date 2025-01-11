/******************************************************************************/
/*                                                                            */
/*  Filename: battery_level.c                                                 */
/*  Author: Markus Andersson                                                  */
/*  Date: January 11, 2025                                                    */
/*                                                                            */
/*  Description:                                                              */
/*  Driver for reading the tags battery level.                                */
/*  Modified version of vendor sample code.                                   */
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

#include "battery_level.h"
#include "em_chip.h"
#include "em_cmu.h"
#include "em_device.h"
#include "em_gpio.h"
#include "em_iadc.h"

// Set CLK_ADC to 10MHz
#define CLK_SRC_ADC_FREQ 20000000 // CLK_SRC_ADC
#define CLK_ADC_FREQ 10000000     // CLK_ADC - 10MHz max in normal mode

#define IADC_INPUT_0_PORT_PIN iadcPosInputAvdd
#define IADC_INPUT_1_PORT_PIN iadcNegInputGnd;

#define IADC_INPUT_0_BUS BBUSALLOC
#define IADC_INPUT_0_BUSALLOC GPIO_BBUSALLOC_BEVEN0_ADC0
#define IADC_INPUT_1_BUS BBUSALLOC
#define IADC_INPUT_1_BUSALLOC GPIO_BBUSALLOC_BODD0_ADC0

#define IADC_REF_VOLTAGE_MV 1210.0
#define IADC_RESOLUTION 4096.0

#define BATTERY_LEVEL_FULL 3.0
#define BATTERY_LEVEL_EMPTY 2.0    // Si7021 min voltage is 1.9V
#define BATTERY_LEVEL_SCALE 100 // 0-100%

static volatile int32_t sample;
static volatile double singleResult; // Volts

void init_IADC(void)
{
    IADC_Init_t init = IADC_INIT_DEFAULT;
    IADC_AllConfigs_t initAllConfigs = IADC_ALLCONFIGS_DEFAULT;
    IADC_InitSingle_t initSingle = IADC_INITSINGLE_DEFAULT;
    IADC_SingleInput_t initSingleInput = IADC_SINGLEINPUT_DEFAULT;

    // Enable IADC0 and GPIO clock branches
    CMU_ClockEnable(cmuClock_IADC0, true);
    CMU_ClockEnable(cmuClock_GPIO, true);

    // Select clock for IADC
    CMU_ClockSelectSet(cmuClock_IADCCLK, cmuSelect_FSRCO); // FSRCO - 20MHz

    // Modify init structs and initialize
    init.warmup = iadcWarmupNormal;

    // Set the HFSCLK prescale value
    init.srcClkPrescale = IADC_calcSrcClkPrescale(IADC0, CLK_SRC_ADC_FREQ, 0);

    // Use internal bandgap voltage as reference
    initAllConfigs.configs[0].reference = iadcCfgReferenceInt1V2;
    initAllConfigs.configs[0].analogGain = iadcCfgAnalogGain1x;
    initAllConfigs.configs[0].vRef = IADC_REF_VOLTAGE_MV;

    // Divides CLK_SRC_ADC to set the CLK_ADC frequency
    initAllConfigs.configs[0].adcClkPrescale = IADC_calcAdcClkPrescale(IADC0, CLK_ADC_FREQ, 0, iadcCfgModeNormal, init.srcClkPrescale);

    // Assign pins to positive and negative inputs in differential mode
    initSingleInput.posInput = IADC_INPUT_0_PORT_PIN;
    initSingleInput.negInput = IADC_INPUT_1_PORT_PIN;

    // Initialize the IADC
    IADC_init(IADC0, &init, &initAllConfigs);

    // Initialize the Single conversion inputs
    IADC_initSingle(IADC0, &initSingle, &initSingleInput);

    // Allocate the analog bus for ADC0 inputs
    GPIO->IADC_INPUT_0_BUS |= IADC_INPUT_0_BUSALLOC;
    GPIO->IADC_INPUT_1_BUS |= IADC_INPUT_1_BUSALLOC;
}

/** Read the battery voltage using IADC */
float read_battery_voltage(void)
{
    init_IADC();
    IADC_command(IADC0, iadcCmdStartSingle);
    while ((IADC0->STATUS & (_IADC_STATUS_CONVERTING_MASK | _IADC_STATUS_SINGLEFIFODV_MASK)) != IADC_STATUS_SINGLEFIFODV)
        ; // while combined status bits 8 & 6 don't equal 1 and 0 respectively

    // Get ADC result
    sample = IADC_pullSingleFifoResult(IADC0).data;

    // Calculate supply voltage:
    float battery_voltage = (sample * (IADC_REF_VOLTAGE_MV / IADC_RESOLUTION)) / 250; // The input voltage is divided by 4 and the measurement is done in mV (1000/4=250)
    if (battery_voltage > BATTERY_LEVEL_FULL) {
        battery_voltage = BATTERY_LEVEL_FULL;
    }

    deinit_IADC();

    return battery_voltage;
}

/** Read the battery voltage and convert to battery level */
sl_status_t get_battery_level(uint8_t *battery_level)
{
    float battery_voltage = read_battery_voltage();
    // Convert voltage to percentage
    *battery_level = (battery_voltage - BATTERY_LEVEL_EMPTY) / (BATTERY_LEVEL_FULL - BATTERY_LEVEL_EMPTY) * BATTERY_LEVEL_SCALE;

    return SL_STATUS_OK;
}

void deinit_IADC(void) {
    // Reset IADC
    IADC_reset(IADC0);
}