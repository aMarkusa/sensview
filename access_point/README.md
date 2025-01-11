# Access point

## Folder structure

```
├── bt_ncp      <- NCP application for the target
├── database
│   ├── db.sql      <- SQL script used to create the database for sensor data
└── host
    ├── app
    │   ├── api
    │   ├── app.py      <- Main script that starts the application
    │   ├── common
    │   ├── config.py   <- Config for database and MQTT connections
    │   ├── DatabaseClient.py
    │   ├── DataProcessor.py
    │   ├── PawrAdvertiser.py   <- Class for managing the BLE communication
    │   ├── SensorTag.py
    │   └── utils
    ├── requirements.txt
```