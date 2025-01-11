# Sensor Tag
This folder contains the source code for the wireless sensor tags. This project was generate using [SLC-CLI](https://docs.silabs.com/simplicity-studio-5-users-guide/latest/ss-5-users-guide-tools-slc-cli/), and can therefore be regenerated utilizing the [SLCP-file](sensor_tag.slcp)

## Folder structure
```
├── app.c   <- Main application source
├── app.h
├── app_libraries
│   ├── inc
│   └── src
│       ├── battery_level.c     <- Driver for reading battery level
│       ├── pawr.c      <- PAwR payload generator
│       └── tag_advertiser.c    <- Functions related to advertising
├── autogen
├── config
├── main.c
├── README.md
├── sensor_tag.Makefile
├── sensor_tag.slcp     <- Project configuration file
├── sensor_tag.slps
└── sl_gatt_service_device_information.c
```