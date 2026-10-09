-- Bronze keeps source values as TEXT. Apply this file to the bronze database.
-- JSON null and blank cells are stored as '' so the UNIQUE key can match a rerun.

CREATE TABLE gps_vendor_report (
    source_system TEXT NOT NULL,
    source_file TEXT NOT NULL,
    ingested_at_utc TEXT NOT NULL,
    registration TEXT NOT NULL,
    event_th TEXT NOT NULL,
    event_en TEXT NOT NULL,
    location_th TEXT NOT NULL,
    location_en TEXT NOT NULL,
    local_timestamp TEXT NOT NULL,
    lat TEXT NOT NULL,
    lon TEXT NOT NULL,
    speed TEXT NOT NULL,
    course TEXT NOT NULL,
    type_of_fix TEXT NOT NULL,
    no_of_satellite TEXT NOT NULL,
    internal_power TEXT NOT NULL,
    external_power TEXT NOT NULL,
    mileage TEXT NOT NULL,
    temp1 TEXT NOT NULL,
    temp2 TEXT NOT NULL,
    temp3 TEXT NOT NULL,
    fuel_sensor TEXT NOT NULL,
    fuel_canbus TEXT NOT NULL,
    driver_name TEXT NOT NULL,
    UNIQUE (
        registration, event_th, event_en, location_th, location_en,
        local_timestamp, lat, lon, speed, course, type_of_fix,
        no_of_satellite, internal_power, external_power, mileage,
        temp1, temp2, temp3, fuel_sensor, fuel_canbus, driver_name
    )
);

CREATE TABLE logistics_report (
    source_system TEXT NOT NULL,
    source_file TEXT NOT NULL,
    ingested_at_utc TEXT NOT NULL,
    imei TEXT NOT NULL,
    tkno TEXT NOT NULL,
    latitude TEXT NOT NULL,
    longitude TEXT NOT NULL,
    speed TEXT NOT NULL,
    direction TEXT NOT NULL,
    gps_status TEXT NOT NULL,
    engine_status TEXT NOT NULL,
    gps_time TEXT NOT NULL,
    altitude TEXT NOT NULL,
    UNIQUE (
        imei, tkno, latitude, longitude, speed, direction,
        gps_status, engine_status, gps_time, altitude
    )
);

CREATE TABLE connected_packet (
    source_system TEXT NOT NULL,
    source_file TEXT NOT NULL,
    ingested_at_utc TEXT NOT NULL,
    packet_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    UNIQUE (packet_type, payload)
);
