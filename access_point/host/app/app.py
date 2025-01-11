"""
Filename: app.py
Author: Markus Andersson
Date: January 11, 2025

Description:
Main script that starts the application.

License: MIT License

License:
This file is part of an open-source project and is distributed under the terms
of the MIT License. You may obtain a copy of the License at:
https://opensource.org/licenses/MIT

Copyright (c) 2025, Markus Andersson. All rights reserved.
"""

from PawrAdvertiser import *
from DataProcessor import *
import os.path
import sys
from queue import Queue
from utils.ble import *
from DatabaseClient import *
from config import *

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from common.util import ArgumentParser, get_connector

def setup_logger():
    # Create a logger
    os.environ["PYTHONUNBUFFERED"] = "1"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO,
			format=format,
			handlers=[
				logging.FileHandler(LOGFOLDER + LOGFILE),
				logging.StreamHandler(sys.stdout)
			]
    )   

if __name__ == "__main__":
    setup_logger()
    logger = logging.getLogger(__name__)
    parser = ArgumentParser(description=__doc__)
    args = parser.parse_args()
    connector = get_connector(args)

    # Start the database client
    db_client = DatabaseClient(MQTT_HOST, MQTT_PORT)
    db_client.subscribe(MQTT_TOPIC)

    # Start the dataprocessor 
    q = Queue()
    data_processing_thread = DataProcessor(queue=q, 
                                           mqtt_host=MQTT_HOST,
                                           mqtt_port=MQTT_PORT,
                                           mqtt_topic=MQTT_TOPIC)
    data_processing_thread.start()

    # Start the BLE-app
    app = PawrAdvertiser(connector, data_processing_thread)
    
    # Running the application blocks execution until it terminates.
    app.run()
