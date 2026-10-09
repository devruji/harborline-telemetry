"""Dispatch a file to the loader named by its feed format."""

from datetime import datetime
from pathlib import Path

from pipeline.db import Databases
from pipeline.formats.flat import load_flat
from pipeline.formats.packet import load_packet
from pipeline.mapping import Feed, FeedMap
from pipeline.tally import FileTally


def load_feed(
    feed_map: FeedMap,
    databases: Databases,
    path: Path,
    now: datetime,
    ingested: str,
    feed: Feed,
) -> FileTally:
    if feed.format == "packet":
        return load_packet(feed, feed_map.bounds, databases, path, now, ingested)
    return load_flat(feed, feed_map.bounds, databases, path, now, ingested)
