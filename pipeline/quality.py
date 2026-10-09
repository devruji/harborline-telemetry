"""Parse source clocks and reject rows that fail the silver rules."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BANGKOK = ZoneInfo("Asia/Bangkok")
LAT_MIN, LAT_MAX = 5.6, 20.5
LON_MIN, LON_MAX = 97.3, 105.7


def iso(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


def parse_local(text: str, fmt: str) -> datetime:
    return datetime.strptime(text, fmt).replace(tzinfo=BANGKOK)


def event_times(text: str, fmt: str) -> tuple[str, str, datetime]:
    local = parse_local(text, fmt)
    utc = local.astimezone(timezone.utc)
    return iso(utc), iso(local), utc


def blank(value) -> str:
    if value is None:
        return ""
    return str(value)


def number(value):
    if value is None or value == "" or value == "-":
        return None
    return float(value)


def whole(value):
    parsed = number(value)
    if parsed is None:
        return None
    return int(parsed)


def flag(value):
    if value is None or value == "":
        return None
    token = str(value).strip().upper()
    if token == "Y":
        return 1
    if token == "N":
        return 0
    return whole(value)


def reject(
    latitude,
    longitude,
    speed,
    event_utc: datetime,
    now: datetime,
    lat_min: float = LAT_MIN,
    lat_max: float = LAT_MAX,
    lon_min: float = LON_MIN,
    lon_max: float = LON_MAX,
) -> str | None:
    if latitude is None or longitude is None:
        return "missing coordinates"
    if not (lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max):
        return "outside Thailand"
    if speed is not None and speed < 0:
        return "negative speed"
    if event_utc > now:
        return "timestamp in the future"
    return None
