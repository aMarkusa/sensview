#ifndef PAWR
#define PAWR

#include <stdint.h>
#include "sl_status.h"

/** Construct the PAwR response based on the measured values.  */
sl_status_t pawr_create_sensor_response(int32_t *temperature, uint32_t *humidity, 
                                        uint8_t* battery_level, uint8_t *data_buffer, 
                                        uint8_t *data_len);

#endif /* PAWR */
