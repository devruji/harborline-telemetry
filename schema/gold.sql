-- Gold holds answer rows. Apply this file to the gold database.
-- These tables are filled by later SQL, not by this script.

CREATE TABLE engine_session (
    built_at_utc TEXT NOT NULL,
    vehicle_id TEXT NOT NULL,
    session_start_utc TEXT NOT NULL,
    session_end_utc TEXT,
    duration_seconds INTEGER,
    distance_km REAL,
    fuel_consumed REAL,
    missing_off_flag INTEGER NOT NULL,
    repeated_on_flag INTEGER NOT NULL,
    UNIQUE (vehicle_id, session_start_utc)
);

CREATE TABLE idle (
    built_at_utc TEXT NOT NULL,
    vehicle_id TEXT NOT NULL,
    idle_start_utc TEXT NOT NULL,
    duration_seconds INTEGER,
    fuel_consumed REAL,
    UNIQUE (vehicle_id, idle_start_utc)
);

CREATE TABLE cross_source_pair (
    built_at_utc TEXT NOT NULL,
    vehicle_id TEXT NOT NULL,
    source_system_left TEXT NOT NULL,
    source_system_right TEXT NOT NULL,
    event_time_left_utc TEXT NOT NULL,
    event_time_right_utc TEXT NOT NULL,
    latitude_left REAL NOT NULL,
    longitude_left REAL NOT NULL,
    latitude_right REAL NOT NULL,
    longitude_right REAL NOT NULL,
    distance_km REAL,
    disagree_flag INTEGER NOT NULL,
    UNIQUE (vehicle_id, event_time_left_utc, event_time_right_utc)
);
