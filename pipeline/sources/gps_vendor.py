"""GPS vendor parser. One object or an array."""

import json
from pathlib import Path


def records(path: Path) -> list[dict]:
    payload = json.loads(path.read_text())
    if isinstance(payload, list):
        return payload
    return [payload]
