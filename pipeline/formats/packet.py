"""Load a nested connected-vehicle packet from the declared paths."""

from datetime import datetime
from pathlib import Path

from pipeline.db import Databases
from pipeline.mapping import Bounds, Feed
from pipeline.position import POSITION_SQL, position_params
from pipeline.quality import event_times, number, reject, whole
from pipeline.sources import connected
from pipeline.sqlident import ident
from pipeline.tally import FileTally


def _dig(packet: dict, path: list[str]):
    cursor = packet
    for key in path:
        if not isinstance(cursor, dict) or key not in cursor:
            return None
        cursor = cursor[key]
    return cursor


def _event_block(packet: dict, keys: tuple[str, ...]) -> dict:
    for key in keys:
        if key not in packet:
            continue
        value = packet[key]
        if isinstance(value, list):
            if not value:
                break
            return value[0]
        return value
    raise KeyError("packet has no declared event block")


def _packet_type(path: Path, types: tuple[str, ...]) -> str:
    name = path.name.lower()
    for kind in types:
        if kind.lower() in name:
            return kind
    raise ValueError(f"packet type is not in the file name: {path.name}")


def _signals(feed: Feed, packet: dict, event: dict) -> list[tuple[str, object, str]]:
    found = []
    entries = _dig(packet, list(feed.contained_path)) if feed.contained_path else []
    for entry in entries or []:
        for item in entry.get("CAN List") or []:
            stamp = str(item.get("Timestamp") or "")
            for bucket in feed.value_buckets:
                for name, value in (item.get(bucket) or {}).items():
                    found.append((str(name), value, stamp))
    if feed.warning_bucket:
        for item in event.get("CAN List") or []:
            stamp = str(item.get("Timestamp") or "")
            for name, value in (item.get(feed.warning_bucket) or {}).items():
                found.append((str(name), value, stamp))
    return found


def load_packet(
    feed: Feed,
    bounds: Bounds,
    databases: Databases,
    path: Path,
    now: datetime,
    ingested: str,
) -> FileTally:
    tally = FileTally(path.name)
    try:
        kind = _packet_type(path, feed.packet_types)
        packet = connected.load(path)
        event = _event_block(packet, feed.event_keys)
        header_gps = _dig(packet, list(feed.header["parent"]))
        if not isinstance(header_gps, dict):
            raise KeyError("packet has no declared header GPS")
        event_gps = event[feed.event["gps"]]
        latitude = number(header_gps.get(feed.header["latitude"]))
        longitude = number(header_gps.get(feed.header["longitude"]))
        speed = number(event.get(feed.event["speed"]))
        event_time_utc, event_time_bangkok, event_utc = event_times(
            str(header_gps.get(feed.header["timestamp"])), feed.clock
        )
        b2b_utc, b2b_bangkok, _unused = event_times(
            str(event.get(feed.event["timestamp"])), feed.clock
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        tally.skipped += 1
        tally.errors.append(str(exc))
        return tally
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
        return tally
    table = ident(feed.bronze_table)
    bronze_id = databases.insert(
        "bronze",
        f"""
        INSERT INTO {table} (
            source_system, source_file, ingested_at_utc, packet_type, payload
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (feed.id, path.name, ingested, kind, path.read_text()),
    )
    position_id = databases.insert(
        "silver",
        POSITION_SQL,
        position_params(
            feed.id,
            path.name,
            ingested,
            "",
            event_time_utc,
            event_time_bangkok,
            latitude,
            longitude,
            speed,
            whole(header_gps.get(feed.header["heading"])),
        ),
    )
    event_id = databases.insert(
        "silver",
        """
        INSERT INTO b2b_event (
            source_system, source_file, ingested_at_utc, event_type,
            event_time_utc, event_time_bangkok, latitude, longitude,
            speed_kmh, heading_deg, engine_rpm
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            feed.id,
            path.name,
            ingested,
            whole(event.get(feed.event["event_type"])),
            b2b_utc,
            b2b_bangkok,
            number(event_gps.get(feed.event["latitude"])),
            number(event_gps.get(feed.event["longitude"])),
            speed,
            whole(event_gps.get(feed.event["heading"])),
            number(event.get(feed.event["engine_rpm"])),
        ),
    )
    tally.note_inserts([bronze_id, position_id, event_id])
    if event_id is None:
        return tally
    for name, value, stamp in _signals(feed, packet, event):
        try:
            signal_utc, _, signal_moment = event_times(stamp, feed.clock)
        except (ValueError, TypeError) as exc:
            tally.skipped += 1
            tally.errors.append(str(exc))
            continue
        if signal_moment > now:
            tally.skipped += 1
            tally.errors.append("timestamp in the future")
            continue
        signal_id = databases.insert(
            "silver",
            """
            INSERT INTO signal_row (
                source_system, source_file, ingested_at_utc, b2b_event_id,
                signal_name, signal_value, signal_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (feed.id, path.name, ingested, event_id, name, number(value), signal_utc),
        )
        if signal_id is None:
            tally.skipped += 1
        else:
            tally.inserted += 1
    return tally
