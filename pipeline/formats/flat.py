"""Load a flat JSON or spreadsheet feed from the declared columns."""

from datetime import datetime
from pathlib import Path

from pipeline.db import Databases
from pipeline.formats.cast import cast
from pipeline.mapping import Bounds, Feed
from pipeline.position import POSITION_SQL, position_params
from pipeline.quality import blank, event_times, reject
from pipeline.sources import gps_vendor, logistics
from pipeline.sqlident import ident
from pipeline.tally import FileTally

_READERS = {
    "json": gps_vendor.records,
    "xlsx": logistics.records,
}


def _bronze_sql(feed: Feed) -> str:
    columns = ["source_system", "source_file", "ingested_at_utc"]
    columns.extend(ident(field.column) for field in feed.bronze_fields)
    placeholders = ", ".join("?" for _ in columns)
    names = ", ".join(columns)
    return f"INSERT INTO {ident(feed.bronze_table)} ({names}) VALUES ({placeholders})"


def load_flat(
    feed: Feed,
    bounds: Bounds,
    databases: Databases,
    path: Path,
    now: datetime,
    ingested: str,
) -> FileTally:
    tally = FileTally(path.name)
    reader = _READERS.get(feed.format)
    if reader is None:
        raise ValueError(f"unsupported flat format: {feed.format}")
    try:
        rows = reader(path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        tally.errors.append(str(exc))
        return tally
    sql = _bronze_sql(feed)
    silver_by_column = {field.column: field for field in feed.silver_fields}
    for row in rows:
        try:
            latitude = cast(row.get(silver_by_column["latitude"].source), "real")
            longitude = cast(row.get(silver_by_column["longitude"].source), "real")
            speed_field = silver_by_column.get("speed_kmh")
            speed = cast(row.get(speed_field.source), "real") if speed_field else None
            event_time_utc, event_time_bangkok, event_utc = event_times(
                str(row.get(feed.time_from)), feed.clock
            )
        except (ValueError, KeyError, TypeError) as exc:
            tally.skipped += 1
            tally.errors.append(str(exc))
            continue
        reason = reject(
            latitude,
            longitude,
            speed,
            event_utc,
            now,
            bounds.lat_min,
            bounds.lat_max,
            bounds.lon_min,
            bounds.lon_max,
        )
        if reason:
            tally.skipped += 1
            tally.errors.append(reason)
            continue
        bronze_values = [feed.id, path.name, ingested]
        bronze_values.extend(blank(row.get(field.source)) for field in feed.bronze_fields)
        bronze_id = databases.insert("bronze", sql, tuple(bronze_values))
        values = {
            field.column: cast(row.get(field.source), field.cast) for field in feed.silver_fields
        }
        silver_id = databases.insert(
            "silver",
            POSITION_SQL,
            position_params(
                feed.id,
                path.name,
                ingested,
                values.get("vehicle_id", ""),
                event_time_utc,
                event_time_bangkok,
                latitude,
                longitude,
                values.get("speed_kmh"),
                values.get("heading_deg"),
                values.get("fuel_sensor"),
                values.get("fuel_canbus"),
                values.get("altitude_m"),
                values.get("mileage_km"),
                values.get("gps_signal_flag"),
                values.get("engine_on_flag"),
                values.get("satellite_count"),
                values.get("gps_fix_code"),
                values.get("internal_power_mv"),
                values.get("external_power_mv"),
                values.get("driver_name"),
            ),
        )
        tally.note_inserts([bronze_id, silver_id])
    return tally
