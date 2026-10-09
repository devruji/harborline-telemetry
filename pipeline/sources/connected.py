"""Read a connected-vehicle packet as JSON. Field paths live in the feed map."""

import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text())
