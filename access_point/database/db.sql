CREATE DATABASE sensor_monitoring;

\c sensor_monitoring;

CREATE TABLE sites (
    site_id TEXT NOT NULL,
    site_m2 INT NOT NULL,
    number_of_sensors INT NOT NULL,
    PRIMARY KEY (site_id)
);

INSERT INTO sites(site_id, site_m2, number_of_sensors) VALUES ('apartment', 28, 6);

CREATE TABLE sensors (
    sensor_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    sensor_model TEXT NOT NULL,
    location_north INT,
    location_east INT,
    ble_addr TEXT NOT NULL,
    battery_level INT,
    last_seen TIMESTAMPTZ,
    PRIMARY KEY (sensor_id),
    FOREIGN KEY (site_id) REFERENCES sites(site_id)
);

INSERT INTO sensors (sensor_id, site_id, sensor_model, location_north, location_east, ble_addr)
VALUES
    ('S1', 'apartment', 'TRH', 0, 1, '8c:f6:81:b8:82:cd'),
    ('S2', 'apartment', 'TRH', 0, -1, '70:54:64:ea:95:c1'),
    ('S3', 'apartment', 'TRH', -1, -1, '70:54:64:ea:95:bf'),
    ('S4', 'apartment', 'TRH', -1, 1, 'cc:86:ec:12:db:5f'),
    ('S5', 'apartment', 'TRH', 1, 1, '68:0a:e2:28:89:f4'),
    ('S6', 'apartment', 'TRH', 1, -1, '8c:f6:81:b8:82:ff');


CREATE TABLE sensor_data (
    time TIMESTAMPTZ NOT NULL,
    sensor_id TEXT NOT NULL,
    temperature FLOAT,
    humidity FLOAT,
    FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id)
);

SELECT create_hypertable('sensor_data', 'time');
SELECT add_retention_policy('sensor_data', INTERVAL '30 days');
