from flask import Flask, render_template, jsonify
from utils.timescale import get_sensors, get_sensor_data
import datetime
from config import *

SENSOR_DATA_INTERVAL_H = 200

app = Flask(__name__)

@app.route("/")
def home():
    return sensors()  # No home view, just display the sensors

@app.route("/sites/")
def sites():
    return render_template("sites.html")

@app.route("/sensors/")
def sensors():
    sensor_list = get_sensors()
    return render_template("sensors.html", sensor_list=sensor_list)

@app.route('/sensors/<string:sensor_id>', methods=['GET'])
def sensor_data(sensor_id):
    sensor_data_list = get_sensor_data(str(sensor_id), int(SENSOR_DATA_INTERVAL_H)) 
    timestamps = [measurement[0] for measurement in sensor_data_list]
    temp_measurements = [measurement[2] for measurement in sensor_data_list]
    hum_measurements = [measurement[3] for measurement in sensor_data_list]

    ret_json = jsonify( {
        "timestamps": timestamps,
        "temp_measurements": temp_measurements,
        "hum_measurements": hum_measurements
    })

    return ret_json

if __name__ == "__main__":
    app.run(debug=True, host=WEB_APP_HOST, port=WEB_APP_PORT)
