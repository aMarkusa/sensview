
"""
Filename: SensorTag.py
Author: Markus Andersson
Date: January 11, 2025

Description:
Class that represents a tag. Used when configuring tags and keeping track of synce/unsynced tags.

License: MIT License

License:
This file is part of an open-source project and is distributed under the terms
of the MIT License. You may obtain a copy of the License at:
https://opensource.org/licenses/MIT

Copyright (c) 2025, Markus Andersson. All rights reserved.
"""

import logging

class SensorTag():
    def __init__(self, ble_address, subevent, response_slot):
        self.ble_address = ble_address
        self.subevent = subevent
        self.response_slot = response_slot
        self.missed_responses = None
        self._synced = False
        self.logger = logging.getLogger(__name__)
        
    @property
    def synced(self):
        return self._synced
    
    @synced.setter
    def synced(self, bool_val):
        self._synced = bool_val
        if bool_val == True:
            self.logger.info(f"Sensor tag with address {self.ble_address} synced to subevent: {self.subevent}, response slot: {self.response_slot}.")
            self.missed_responses = 0
        else:
            self.logger.error(f"Sensor tag with address {self.ble_address} dropped from sync!")


