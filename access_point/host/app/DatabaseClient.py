"""
Filename: DatabaseClient.py
Author: Markus Andersson
Date: January 11, 2025

Description:
Class for subscribing to sensor data over MQTT and pushing to database..

License: MIT License

License:
This file is part of an open-source project and is distributed under the terms
of the MIT License. You may obtain a copy of the License at:
https://opensource.org/licenses/MIT

Copyright (c) 2025, Markus Andersson. All rights reserved.
"""

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
import json
import logging
import threading
from utils.timescale import *
from queue import Queue
from config import * 
import traceback


# Timescaledb connection address
TIMESCALE_CONNECTION = f"postgres://{TIMESCALE_USER}:{TIMESCALE_PASS}@{TIMESCALE_HOST}:{TIMESCALE_PORT}/{TIMESCALE_DATABASE}"

class DatabaseClient():
    def __init__(self, mqtt_host, mqtt_port):
        self.logger = logging.getLogger(__name__)
        self.host = mqtt_host
        self.port = mqtt_port
        self.connected = False
        self.ready_to_loop = False
        self.topic_queue = Queue()
        
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Connect to MQTT broker and start loop
        self.client.connect(self.host, self.port)
        self.client.loop_start()

    def subscribe(self, mqtt_topic):
        """ Check if client is connected. If not, add the topic to a queue so we can subscribe to it later. """
        if self.connected:
            self.client.subscribe(mqtt_topic)
            self.logger.info(f"Database client subscribed to topic {mqtt_topic}")
        else:
            self.logger.warning("Database client is not connected. Adding topic to queue, and subscribing when the connection is established.")
            self.topic_queue.put(mqtt_topic)

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        """ Check the code and subscribe to the required topics"""
        if reason_code:
            self.logger.error(f"Database client failed to connect: {reason_code}")
        else:
            self.logger.info(f"Database client connected to {self.host}:{self.port}")
            self.connected = True
            while self.topic_queue.empty() == False:
                topic = self.topic_queue.get()
                self.client.subscribe(topic)
                self.logger.info(f"Database client successfully subscribed to topic {topic}.")

    def on_message(self, client, userdata, message):
        self.write_sensor_data_to_db(message)

    def write_sensor_data_to_db(self, mqtt_message):
        """ Unpack the MQTT message, construct the SQL-query, and write the data to database"""
        sensor_data = json.loads(mqtt_message.payload.decode("utf-8"))
        address = sensor_data.get("address").lower()
        timestamp = sensor_data.get("timestamp")
        temperature = sensor_data.get("temperature")
        humidity = sensor_data.get("humidity")
        battery_level = sensor_data.get("battery_level")

        sensor_id_query = f"SELECT sensor_id FROM sensors WHERE ble_addr = '{address}';" 
        try:
            with psycopg2.connect(TIMESCALE_CONNECTION) as conn:
                self.logger.debug(f"Connected to database at {TIMESCALE_HOST}:{TIMESCALE_PORT}")
                cursor = conn.cursor()
                sensor_id = timescale_read(cursor, sensor_id_query)[0][0]  # Get the sensor id corresponding to the BLE addr
            
                # Update the sensors battery level and last seen values
                sensor_bat_and_last_seen_query = f"UPDATE sensors SET battery_level = {battery_level}, last_seen = '{timestamp}' WHERE sensor_id = '{sensor_id}'"
                timescale_write(cursor, sensor_bat_and_last_seen_query)
                
                # Add the sensor data to the sensor_data table
                sensor_data_query = f"INSERT INTO sensor_data (time, sensor_id, temperature, humidity) values ('{timestamp}', '{sensor_id}', {temperature}, {humidity});"
                timescale_write(cursor, sensor_data_query)
                self.logger.info(f"Data written to database: {sensor_data}")
                
        except Exception as e:
            tb_str = traceback.format_exc()
            self.logger.error(f"Writing to database failed with exception: {tb_str}")
