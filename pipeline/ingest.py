"""Load sample files into bronze and silver. Gold is created and left empty."""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline.apply import load_feed
from pipeline.db import Databases
from pipeline.mapping import FeedMap, load

def discover(data: Path, feed_map: FeedMap) -> list[tuple]:
    found = []
    for feed in feed_map.feeds:
        found.extend((feed, path) for path in sorted(data.glob(feed.pattern)))
    return found


def run(data: Path, output: Path, now: datetime | None = None) -> list[str]:
    if not data.is_dir():
        raise FileNotFoundError(f"sample directory does not exist: {data}")
    feed_map = load()
    moment = now or datetime.now(timezone.utc)
    ingested = moment.astimezone(timezone.utc).isoformat(timespec="seconds")
    databases = Databases(output)
    lines = []
    try:
        for feed, path in discover(data, feed_map):
            tally = load_feed(feed_map, databases, path, moment, ingested, feed)
            databases.commit()
            lines.append(tally.line())
    finally:
        databases.close()
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load Harborline samples into SQLite")
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        lines = run(args.data, args.output)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
