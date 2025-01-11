"""
Filename: PawrAdvertiser.py
Author: Markus Andersson
Date: January 11, 2025

Description:
Class for handling the BLE communation within the sensor network

License: MIT License

License:
This file is part of an open-source project and is distributed under the terms
of the MIT License. You may obtain a copy of the License at:
https://opensource.org/licenses/MIT

Copyright (c) 2025, Markus Andersson. All rights reserved.
"""

import logging
from common.util import BluetoothApp
import threading
import time
from utils.ble import *
from config import *
from SensorTag import SensorTag

# -------------------- Connection parameters -------------------- #
CONNECTION_PHY = 1
PERIPHERAL_NAME = "wsn"

# -------------------- PAWR parameters -------------------- #
PAWR_SENSOR_READ_PERIOD_M = 0.5
PAWR_SENSOR_READ_PERIOD_S = PAWR_SENSOR_READ_PERIOD_M * 60
PAWR_HEADER_SIZE = 2
PAWR_BROADCAST_ADDRESS = 255
PAWR_MAX_ALLOWED_MISSED_RESPONSES = 2

PAWR_ADVERTISING_SET = 0
PAWR_FLAGS = 0x2
PAWR_INTERVAL = 4000
PAWR_SUBEVENTS = 1
PAWR_SUBEVENT_INTERVAL = 65
PAWR_RESPONSE_SLOTS = 23 
PAWR_RESPONSE_SLOT_DELAY = 34  # 42.5ms. 15 * 1.25ms seems to be minimum
PAWR_RESPONSE_SLOT_SPACING = 12


# -------------------- Main class -------------------- #
class PawrAdvertiser(BluetoothApp):
    def __init__(self, connector, data_processing_thread):
        super().__init__(connector)
        self.logger = logging.getLogger(__name__)
        self.pawr_advertising_set_handle = None     
        self.advertising_tags = []
        self.subevent_count = 0
        self.response_slot_count = 0
        self.connection_info = None
        self.data_processing_thread = data_processing_thread
        self.tags = [[]]
        self.tag_waiting_list = []  # Tags that we are expecting a response from 
        self.read_sensor_values = False
        self.synced_tags = 0

    def bt_evt_system_boot(self, evt):
        """ Immediately start the scanner and PAwR train. """
        _, self.pawr_advertising_set_handle = self.lib.bt.advertiser.create_set()
        self.lib.bt.pawr_advertiser.start(
            self.pawr_advertising_set_handle,
            PAWR_INTERVAL,
            PAWR_INTERVAL,
            PAWR_FLAGS,
            PAWR_SUBEVENTS,
            PAWR_SUBEVENT_INTERVAL,
            PAWR_RESPONSE_SLOT_DELAY,
            PAWR_RESPONSE_SLOT_SPACING,
            PAWR_RESPONSE_SLOTS
        ) 
        self.logger.info("PAwR advertiser started.")
        self.lib.bt.scanner.start(
            self.lib.bt.scanner.SCAN_PHY_SCAN_PHY_1M,
            self.lib.bt.scanner.DISCOVER_MODE_DISCOVER_OBSERVATION)
        self.logger.info("Scanning started.")
        self.scanner_sensor_read_timer = threading.Thread(target=self.sensor_data_period_handler)  # TODO: Improve naming of this thread
        self.scanner_sensor_read_timer.start()
    
    def bt_evt_scanner_legacy_advertisement_report(self, evt):
        """ Check if device is of wanted type, and open connection if true. Currently only supporting one connection at a time. """
        if self.connection_info == None:
            if self.is_sensor(evt.data) and evt.address not in self.advertising_tags:
                self.lib.bt.scanner.stop()
                self.advertising_tags.append(evt.address)
                self.logger.info(f"Sensor Peripheral found with address {evt.address}. Opening Connection...")
                self.lib.bt.connection.open(evt.address, evt.address_type, CONNECTION_PHY)
            
    def bt_evt_connection_opened(self, evt):
        """ Connection is open. Init the connection info, and start service discovery. """
        del self.advertising_tags[self.advertising_tags.index(evt.address)]
        self.connection_info = ConnectionInfo(evt.address, evt.connection)
        
        self.logger.info(f"Connection opened to {evt.address}.")
        
        pawr_addr = self.get_advertising_tag_pawr_addr(evt.address)
        if pawr_addr != None:
            self.connection_info.pawr_addr = pawr_addr
            self.logger.info(f"Device is known. It will be reassigned to {pawr_addr}.")
            
        self.logger.info("Dicovering services...")
        self.lib.bt.gatt.discover_primary_services_by_uuid(self.connection_info.conn_handle, BLE_SENSOR_PAWR_SERVICE_UUID)
        self.connection_info.state = ConnectionStates.DISCOVER_SERVICES
    
    def bt_evt_gatt_service(self, evt):
        """ Once the PAwR Sensor service is discovered, start the char discovery. """
        if evt.uuid == BLE_SENSOR_PAWR_SERVICE_UUID:
            self.logger.info("PAwR sensor service discovered.")
            self.connection_info.service_handle = evt.service
            self.connection_info.state = ConnectionStates.DISCOVER_CHARACTERISTICS
            self.logger.info("Discovering characteristics...")
            
    def bt_evt_gatt_characteristic(self, evt):
        """ Once the subevent and response_slot chars are discovered, write the values to GATT. """
        char_uuid = evt.uuid
        if char_uuid == BLE_PAWR_SUBEVENT_CHAR_UUID or char_uuid == BLE_PAWR_RESPONSE_SLOT_CHAR_UUID:
            self.connection_info.char_handles.append(evt.characteristic)
            if len(self.connection_info.char_handles) == 2:
                self.connection_info.state = ConnectionStates.WRITE_SUBEVENT
        
    def bt_evt_gatt_procedure_completed(self, evt):
        """ This function takes care of setting the new application states when one is finished. """
        if evt.result != 0:
            self.log.error(f"GATT procedure completed with status {evt.result:#x}: {evt.result}")
            return
        
        match self.connection_info.state:
            case ConnectionStates.DISCOVER_CHARACTERISTICS:
                if len(self.connection_info.char_handles) == 0:
                    self.lib.bt.gatt.discover_characteristics_by_uuid(self.connection_info.conn_handle, self.connection_info.service_handle, BLE_PAWR_SUBEVENT_CHAR_UUID)
                else:
                    self.lib.bt.gatt.discover_characteristics_by_uuid(self.connection_info.conn_handle, self.connection_info.service_handle, BLE_PAWR_RESPONSE_SLOT_CHAR_UUID)
            
            case ConnectionStates.WRITE_SUBEVENT:
                self.log.info("Characteristics discovered.")
                if self.connection_info.pawr_addr != None:
                    subevent = self.connection_info.pawr_addr[0]
                else:
                    subevent = self.subevent_count
                self.lib.bt.gatt.write_characteristic_value(self.connection_info.conn_handle, self.connection_info.char_handles[0], subevent.to_bytes(1, byteorder='big'))
                self.connection_info.state = ConnectionStates.WRITE_RESPONSE_SLOT
            
            case ConnectionStates.WRITE_RESPONSE_SLOT:
                self.log.info("Subevent written to peripheral.")
                if self.connection_info.pawr_addr != None:
                    response_slot = self.connection_info.pawr_addr[1]
                else:
                    response_slot = self.response_slot_count
                self.lib.bt.gatt.write_characteristic_value(self.connection_info.conn_handle, self.connection_info.char_handles[1], response_slot.to_bytes(1, byteorder='big'))
                self.connection_info.state = ConnectionStates.PAST_TRANSFER
                
            case ConnectionStates.PAST_TRANSFER:
                self.log.info("Response slot written to peripheral.")
                self.lib.bt.advertiser_past.transfer(self.connection_info.conn_handle, 0, self.pawr_advertising_set_handle)
                self.log.info("Initiating PAST transfer.")
            case _:
                pass
        
    def bt_evt_pawr_advertiser_subevent_data_request(self, evt):
        """ Handler for subevent data requests. Only sets data when we want to read the sensors. """                
        if self.read_sensor_values == True:
            subevent = evt.subevent_start
            subevents_left = evt.subevent_data_count
            resend = False
            while subevents_left > 0:
                response_slot_start = 0
                response_slot_count = len(self.tags[subevent])
                payload = []
                if len(self.tag_waiting_list) > 0:  # There were missing responses
                    resend = True
                    for i, (target_subevent, target_response_slot) in enumerate(self.tag_waiting_list):
                        if target_subevent == subevent:
                            address = target_response_slot  
                            payload.append(address)
                            self.logger.info(f"Reading sensor at ({subevent}, {target_response_slot}).")
                    
                elif resend == False:
                    payload.append(PAWR_BROADCAST_ADDRESS)
                    self.logger.info(f"Reading all sensors in subevent {subevent}.")
                    self.add_tags_to_waiting_list(subevent, response_slot_start, response_slot_count)
 

                payload[:0] = [len(payload)]  # Add the header len to the payload start
                payload.append(PawrOpCodes.READ_SENSOR_VALUES.value)    
                self.lib.bt.pawr_advertiser.set_subevent_data(self.pawr_advertising_set_handle, subevent, response_slot_start, response_slot_count, 
                                                              bytes(payload))
                                
                # Check if subevent roll-over is required
                if subevent == PAWR_SUBEVENTS - 1:
                    subevent = 0
                else:
                    subevent = subevent + 1
                subevents_left = subevents_left - 1
            
            self.read_sensor_values = False
            threading.Timer(PAWR_INTERVAL * 1.25 / 1000 * 1.5, self.check_for_missing_responses).start()  # Check for missing responses in ~1.5x PAwR interval
            
    def bt_evt_pawr_advertiser_response_report(self, evt):
        """ Receives the response data and pushes it to the DataProcessor queue. """
        tag_pawr_addr = (evt.subevent, evt.response_slot)
        if evt.data_status == 0:
            self.logger.info(f"Response receiveved in slot: {evt.response_slot}, data: {evt.data}, data_status: {evt.data_status}")
            if evt.data[1] == PawrOpCodes.READ_SENSOR_VALUES.value:
                del self.tag_waiting_list[self.tag_waiting_list.index(tag_pawr_addr)]  # Response received -> delete tag from waiting list
                sensor_data = evt.data[2:]
                sensor_address = self.tags[evt.subevent][evt.response_slot].ble_address 
                self.data_processing_thread.queue.put((sensor_data, sensor_address))
        else:
            if tag_pawr_addr in self.tag_waiting_list:
                self.logger.error(f"Failed response receiveved in slot: {evt.response_slot}, data: {evt.data}, data_status: {evt.data_status}")
    
    def bt_evt_connection_closed(self, evt):
        """ Handles closed connections """
        self.logger.info(f"Connection {evt.connection} closed with reason {evt.reason:#x}: {evt.reason}")
        
        # We assume that the tag is synced if it closes the connection while we are in the PAST transfer. We will only know for sure once we try to read the sensor data.
        if evt.reason == 0x1013 and self.connection_info.state == ConnectionStates.PAST_TRANSFER:
            if self.connection_info.pawr_addr != None:
                subevent = self.connection_info.pawr_addr[0]
                response_slot = self.connection_info.pawr_addr[1]
                self.tags[subevent][response_slot].synced = True
            else:
                subevent = self.subevent_count
                response_slot = self.response_slot_count
                synced_tag = SensorTag(self.connection_info.ble_address, subevent, response_slot)
                synced_tag.synced = True
                self.tags[subevent].append(synced_tag)
            
                # Check if the subevent is full, and move on to the next one if needed
                if self.response_slot_count >= (PAWR_RESPONSE_SLOTS - 1) and self.subevent_count < (PAWR_SUBEVENTS - 1):
                    self.response_slot_count = 0
                    self.subevent_count = self.subevent_count + 1
                    self.tags.append([])  # Append empty list for the next subevent
                else:
                    self.response_slot_count = self.response_slot_count + 1

            self.synced_tags += 1
                
        self.connection_info = None
        self.lib.bt.scanner.start(
            self.lib.bt.scanner.SCAN_PHY_SCAN_PHY_1M,
            self.lib.bt.scanner.DISCOVER_MODE_DISCOVER_OBSERVATION)
        
    def sensor_data_period_handler(self):
        """ This function runs in a loop and lets the main application know when we want to read the sensor values through the read_sensor_values boolean. """
        self.logger.info(f"Sensor reading period is set to {PAWR_SENSOR_READ_PERIOD_M} minutes.") 
        while True:
            time.sleep(PAWR_SENSOR_READ_PERIOD_S)
            if self.synced_tags > 0:
                self.read_sensor_values = True
            else:
                self.logger.info("No synced tags. Skipping reading!")
                
    def is_sensor(self, adv_data):
        """ Check if the advertising device is one of our sensors. """
        #self.logger.debug(f"Raw adv data: {adv_data}") TODO: Add TRACE level to logger
        adv_data = list(adv_data)
        if get_from_adv_data(adv_data, BLE_ADV_TYPE_NAME) == PERIPHERAL_NAME:
            return True
        else:
            return False

    def add_tags_to_waiting_list(self, subevent, response_slot_start, response_slot_count):
        """ Add the tags from which we are expecting responses to the waiting list. """
        for rs in range(response_slot_count):
            tag_pawr_addr = (subevent, response_slot_start + rs)
            if tag_pawr_addr not in self.tag_waiting_list and self.tags[tag_pawr_addr[0]][tag_pawr_addr[1]].synced == True:
                self.tag_waiting_list.append(tag_pawr_addr)
            
    def check_for_missing_responses(self):
        """ Schedule a resend ff there are tags in the waiting list after we have received the response events. """
        if len(self.tag_waiting_list) > 0:
            self.read_sensor_values = True
            for tag_pawr_addr in self.tag_waiting_list:
                self.logger.error(f"Tag at PAwR address {tag_pawr_addr} did not respond to the previous PAwR command. Resend scheduled!")
                self.tags[tag_pawr_addr[0]][tag_pawr_addr[1]].missed_responses += 1
                
                if self.tags[tag_pawr_addr[0]][tag_pawr_addr[1]].missed_responses >= PAWR_MAX_ALLOWED_MISSED_RESPONSES:
                    self.tags[tag_pawr_addr[0]][tag_pawr_addr[1]].synced = False
                    self.synced_tags -= 1
                    del self.tag_waiting_list[self.tag_waiting_list.index(tag_pawr_addr)]
                    
    def get_advertising_tag_pawr_addr(self, ble_address):
        """ Find the assigned subevent and response slot for a specific BLE address """
        for i in range(len(self.tags)):
            for j in range(len(self.tags[i])):
                if self.tags[i][j].ble_address == ble_address:
                    return (i, j)
                
        return None