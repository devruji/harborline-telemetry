-- Silver is the typed model. Apply this file to the silver database.
-- Event time is ISO-8601 TEXT with an offset.

CREATE TABLE position_report (
    source_system TEXT NOT NULL,
    source_file TEXT NOT NULL,
    ingested_at_utc TEXT NOT NULL,
    vehicle_id TEXT NOT NULL,
    event_time_utc TEXT NOT NULL,
    event_time_bangkok TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    speed_kmh REAL,
    heading_deg INTEGER,
    fuel_sensor REAL,
    fuel_canbus REAL,
    altitude_m REAL,
    mileage_km REAL,
    gps_signal_flag INTEGER,
    engine_on_flag INTEGER,
    satellite_count INTEGER,
    gps_fix_code INTEGER,
    internal_power_mv REAL,
    external_power_mv REAL,
    driver_name TEXT,
    UNIQUE (source_system, vehicle_id, event_time_utc, latitude, longitude)
);

CREATE TABLE b2b_event (
    b2b_event_id INTEGER PRIMARY KEY,
    source_system TEXT NOT NULL,
    source_file TEXT NOT NULL,
    ingested_at_utc TEXT NOT NULL,
    event_type INTEGER NOT NULL,
    event_time_utc TEXT NOT NULL,
    event_time_bangkok TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    speed_kmh REAL,
    heading_deg INTEGER,
    engine_rpm REAL,
    UNIQUE (event_type, event_time_utc, latitude, longitude)
);

CREATE TABLE signal_row (
    source_system TEXT NOT NULL,
    source_file TEXT NOT NULL,
    ingested_at_utc TEXT NOT NULL,
    b2b_event_id INTEGER NOT NULL REFERENCES b2b_event (b2b_event_id),
    signal_name TEXT NOT NULL,
    signal_value REAL,
    signal_timestamp TEXT NOT NULL,
    UNIQUE (b2b_event_id, signal_name, signal_timestamp)
);
