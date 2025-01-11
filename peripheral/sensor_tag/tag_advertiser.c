/******************************************************************************/
/*                                                                            */
/*  Filename: tag_advertiser.c                                                */
/*  Author: Markus Andersson                                                  */
/*  Date: January 11, 2025                                                    */
/*                                                                            */
/*  Description:                                                              */
/*  Functions used for managing the tag advertising                           */
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

#include "tag_advertiser.h"
#include "app_assert.h"
#include "sl_bluetooth.h"

#define ADVERTISING_INTERVAL_MS     500
#define ADVERTISING_INTERVAL        ADVERTISING_INTERVAL_MS * 1.6

/* Start the advertiser with the given data */
sl_status_t tag_advertiser_start(uint8_t *adv_handle)
{
    sl_status_t sc;

    sc = sl_bt_advertiser_create_set(adv_handle);
    app_assert_status(sc);

    sc = sl_bt_legacy_advertiser_generate_data(*adv_handle, sl_bt_advertiser_general_discoverable);
    app_assert_status(sc);

    // Set advertising interval to 100ms.
    sc = sl_bt_advertiser_set_timing(*adv_handle,
                                     ADVERTISING_INTERVAL, // min. adv. interval (milliseconds * 1.6)
                                     ADVERTISING_INTERVAL, // max. adv. interval (milliseconds * 1.6)
                                     0,                    // adv. duration
                                     0);                   // max. num. adv. events
    app_assert_status(sc);
    // Start advertising and enable connections.
    sc = sl_bt_legacy_advertiser_start(*adv_handle, sl_bt_advertiser_connectable_scannable);
    return sc;
}

/* Stop the advertiser */
sl_status_t tag_advertiser_stop(uint8_t* adv_handle)
{
    sl_status_t sc = sl_bt_advertiser_stop(*adv_handle);
    app_assert_status(sc);
    sc = sl_bt_advertiser_delete_set(*adv_handle);
    *adv_handle = 255;

    return sc;
}
