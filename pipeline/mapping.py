"""Load the declarative feed map."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEEDS_PATH = ROOT / "mappings" / "feeds.toml"


@dataclass(frozen=True)
class Field:
    column: str
    source: str
    cast: str


@dataclass(frozen=True)
class Bounds:
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float


@dataclass(frozen=True)
class Feed:
    id: str
    pattern: str
    format: str
    clock: str
    bronze_table: str
    time_from: str
    bronze_fields: tuple[Field, ...]
    silver_fields: tuple[Field, ...]
    packet_types: tuple[str, ...]
    event_keys: tuple[str, ...]
    contained_path: tuple[str, ...]
    value_buckets: tuple[str, ...]
    warning_bucket: str
    header: dict
    event: dict


@dataclass(frozen=True)
class FeedMap:
    bounds: Bounds
    feeds: tuple[Feed, ...]


def _fields(rows: list[dict] | None) -> tuple[Field, ...]:
    return tuple(
        Field(column=row["column"], source=row["from"], cast=row.get("cast", "text"))
        for row in (rows or [])
    )


def load(path: Path = FEEDS_PATH) -> FeedMap:
    raw = tomllib.loads(path.read_text())
    box = raw["bounds"]
    feeds = []
    for item in raw["feed"]:
        feeds.append(
            Feed(
                id=item["id"],
                pattern=item["pattern"],
                format=item["format"],
                clock=item["clock"],
                bronze_table=item["bronze_table"],
                time_from=item.get("time_from", ""),
                bronze_fields=_fields(item.get("bronze_field")),
                silver_fields=_fields(item.get("silver_field")),
                packet_types=tuple(item.get("packet_types", ())),
                event_keys=tuple(item.get("event_keys", ())),
                contained_path=tuple(item.get("contained_path", ())),
                value_buckets=tuple(item.get("value_buckets", ())),
                warning_bucket=item.get("warning_bucket", ""),
                header=item.get("header", {}),
                event=item.get("event", {}),
            )
        )
    return FeedMap(
        bounds=Bounds(box["lat_min"], box["lat_max"], box["lon_min"], box["lon_max"]),
        feeds=tuple(feeds),
    )
