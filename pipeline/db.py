"""Open the three databases and insert rows. A unique clash is a skip."""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema"
SENTINEL = {
    "bronze": "gps_vendor_report",
    "silver": "position_report",
    "gold": "engine_session",
}


class Databases:
    def __init__(self, output: Path):
        output.mkdir(parents=True, exist_ok=True)
        self._connections = {}
        for layer, table in SENTINEL.items():
            path = output / f"{layer}.sqlite"
            conn = sqlite3.connect(path)
            conn.execute("PRAGMA foreign_keys = ON")
            present = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table,),
            ).fetchone()
            if present is None:
                conn.executescript((SCHEMA / f"{layer}.sql").read_text())
                conn.commit()
            self._connections[layer] = conn

    def commit(self):
        for conn in self._connections.values():
            conn.commit()

    def close(self):
        for conn in self._connections.values():
            conn.close()

    def insert(self, layer: str, sql: str, params: tuple) -> int | None:
        conn = self._connections[layer]
        try:
            cursor = conn.execute(sql, params)
        except sqlite3.IntegrityError:
            return None
        return cursor.lastrowid
