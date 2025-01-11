"""
Filename: DataProcessor.py
Author: Markus Andersson
Date: January 11, 2025

Description:
Class for parsing and publishing (MQTT) the data received by the access point.

License: MIT License

License:
This file is part of an open-source project and is distributed under the terms
of the MIT License. You may obtain a copy of the License at:
https://opensource.org/licenses/MIT

Copyright (c) 2025, Markus Andersson. All rights reserved.
"""

from utils.ble import *
import threading
import paho.mqtt.client as mqtt
import time
import json
import queue
import datetime
import logging

PUBLISH_TO_MQTT = True

class DataProcessor(threading.Thread):
    def __init__(self, queue, mqtt_host, mqtt_port, mqtt_topic, args=(), kwargs=None):
        self.logger = logging.getLogger(__name__)
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.queue = queue
        self.daemon = True
        self.receive_messages = True
        self.host = mqtt_host
        self.port = mqtt_port
        self.topic = mqtt_topic
        self.client = None

        self.init_mqtt()

    def run(self):
        while 1:
            # Check if there is any data in the queue
            try:
                adv_info = self.queue.get()
            except queue.Empty:
                continue
            
            # Deconstruct the advertisement data into chunks of characteristic data
            adv_data = adv_info[0]
            adv_address = adv_info[1].upper()
            temperature = get_from_adv_data(adv_data, BLE_ADV_TYPE_CHAR, BLE_TEMP_CHAR_UUID)
            humidity = get_from_adv_data(adv_data, BLE_ADV_TYPE_CHAR, BLE_HUM_CHAR_UUID)
            battery_level = int.from_bytes(get_from_adv_data(adv_data, BLE_ADV_TYPE_CHAR, BLE_BATTERY_LEVEL_CHAR_UUID), "big")

            # Parse the characteristic data into the required datatype
            temperature = parse_char_data(temperature, float)
            humidity = parse_char_data(humidity, float)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

            mqtt_data = {
                "address": adv_address,
                "timestamp": timestamp,
                "temperature": temperature,
                "humidity": humidity,
                "battery_level": battery_level,
            }

            if PUBLISH_TO_MQTT == True:
                self.publish_mqtt_data(mqtt_data)

    def init_mqtt(self):
        self.client = mqtt.Client()
        self.client.connect(self.host, self.port, keepalive=300)
        self.logger.info(f"Dataprocessor connected to {self.host}:{self.port}")

    def publish_mqtt_data(self, mqtt_data):
        self.client.publish(self.topic, json.dumps(mqtt_data))
        self.logger.info(f"Published data to {self.host}:{self.port}: {mqtt_data}")
    
