/***************************************************************************//**
 * @file
 * @brief Interrupt service routine for Bluetooth NCP Transport Layer over USART
 *******************************************************************************
 * # License
 * <b>Copyright 2024 Silicon Laboratories Inc. www.silabs.com</b>
 *******************************************************************************
 *
 * SPDX-License-Identifier: Zlib
 *
 * The licensor of this software is Silicon Laboratories Inc.
 *
 * This software is provided 'as-is', without any express or implied
 * warranty. In no event will the authors be held liable for any damages
 * arising from the use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose,
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 * 1. The origin of this software must not be misrepresented; you must not
 *    claim that you wrote the original software. If you use this software
 *    in a product, an acknowledgment in the product documentation would be
 *    appreciated but is not required.
 * 2. Altered source versions must be plainly marked as such, and must not be
 *    misrepresented as being the original software.
 * 3. This notice may not be removed or altered from any source distribution.
 *
 ******************************************************************************/
#include "sl_uartdrv_usart_vcom_config.h"

// ISR function, declared in sl_bt_ncp_transport_usart.c
extern void sli_bt_ncp_transport_usart_isr(void);

/*******************************************************************************
 * Concatenate preprocessor tokens A and B without expanding macro unless it is
 * invoked from a macro, already.
 ******************************************************************************/
#define PPCAT_NX(A, B)  A ## B

/*******************************************************************************
 * Concatenate preprocessor tokens A and B after macro-expanding them.
 ******************************************************************************/
#define PPCAT(A, B)     PPCAT_NX(A, B)

/*******************************************************************************
 * Actual USART instance number, generated upon project creation / modification.
 ******************************************************************************/
#define SL_UART_INST_NO SL_UARTDRV_USART_VCOM_PERIPHERAL_NO

/*******************************************************************************
 * Concatenate the actual value of SL_UARTDRV_USART_*_PERIPHERAL_NO and the
 * parameter to (partially) create the interrupt service routine name. This
 * will be the second part. Please note it can be created only this way: second
 * part of the name, first - otherwise recursive macro expansion would mess up
 * the whole effort.
 ******************************************************************************/
#define SLI_BT_NCP_TRANSPORT_USART_VNAME(A)  PPCAT(SL_UART_INST_NO, A)

/*******************************************************************************
 * Finally, construct the actual ISR vector name for USARTn
 * Currently, this macro has limited supports only for USARTn vectors.
 ******************************************************************************/
#define SLI_BT_NCP_TRANSPORT_USART_IRQ \
  PPCAT(USART, SLI_BT_NCP_TRANSPORT_USART_VNAME(_RX_IRQHandler))

/**************************************************************************//**
 * Override the default interrupt handler using the special macro in order to
 * place the vector in the appropriate place no matter which USART peripheral is
 * actually used.
 *****************************************************************************/
void SLI_BT_NCP_TRANSPORT_USART_IRQ()
{
  sli_bt_ncp_transport_usart_isr();
}
