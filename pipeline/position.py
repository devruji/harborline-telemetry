"""Shared insert for silver.position_report."""

POSITION_SQL = """
INSERT INTO position_report (
    source_system, source_file, ingested_at_utc, vehicle_id,
    event_time_utc, event_time_bangkok, latitude, longitude, speed_kmh,
    heading_deg, fuel_sensor, fuel_canbus, altitude_m, mileage_km,
    gps_signal_flag, engine_on_flag, satellite_count, gps_fix_code,
    internal_power_mv, external_power_mv, driver_name
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def position_params(
    source_system: str,
    source_file: str,
    ingested: str,
    vehicle_id: str,
    event_time_utc: str,
    event_time_bangkok: str,
    latitude: float,
    longitude: float,
    speed,
    heading,
    fuel_sensor=None,
    fuel_canbus=None,
    altitude=None,
    mileage=None,
    gps_signal=None,
    engine_on=None,
    satellite_count=None,
    gps_fix=None,
    internal_power=None,
    external_power=None,
    driver_name=None,
) -> tuple:
    return (
        source_system,
        source_file,
        ingested,
        vehicle_id,
        event_time_utc,
        event_time_bangkok,
        latitude,
        longitude,
        speed,
        heading,
        fuel_sensor,
        fuel_canbus,
        altitude,
        mileage,
        gps_signal,
        engine_on,
        satellite_count,
        gps_fix,
        internal_power,
        external_power,
        driver_name,
    )
