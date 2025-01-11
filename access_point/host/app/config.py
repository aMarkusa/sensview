from datetime import datetime

LOGFILE = datetime.now().strftime("app_%Y-%m-%d_%H-%M-%S.log")
LOGFOLDER = "logs/"

TIMESCALE_USER = "secret"
TIMESCALE_PASS = "secret"
TIMESCALE_HOST = "192.168.0.102"
TIMESCALE_PORT = "5432"
TIMESCALE_DATABASE = "sensor_monitoring"

MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor_data"