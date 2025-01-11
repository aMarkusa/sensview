#ifndef tag_advertiser
#define tag_advertiser

#include "sl_status.h"
#include "sl_sleeptimer.h"


/* Start the advertiser with the given data */
sl_status_t tag_advertiser_start(uint8_t* adv_handle);

/* Stop the advertiser. */
sl_status_t tag_advertiser_stop(uint8_t* adv_handle);

#endif /* tag_advertiser */
