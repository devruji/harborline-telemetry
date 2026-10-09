"""Apply the medallion DDL and check the external shape."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema"

BRONZE_TABLES = ("gps_vendor_report", "logistics_report", "connected_packet")
SILVER_TABLES = ("position_report", "b2b_event", "signal_row")
GOLD_TABLES = ("engine_session", "idle", "cross_source_pair")

UNIQUE = {
    ("bronze", "gps_vendor_report"): (
        "registration", "event_th", "event_en", "location_th", "location_en",
        "local_timestamp", "lat", "lon", "speed", "course", "type_of_fix",
        "no_of_satellite", "internal_power", "external_power", "mileage",
        "temp1", "temp2", "temp3", "fuel_sensor", "fuel_canbus", "driver_name",
    ),
    ("bronze", "logistics_report"): (
        "imei", "tkno", "latitude", "longitude", "speed", "direction",
        "gps_status", "engine_status", "gps_time", "altitude",
    ),
    ("bronze", "connected_packet"): ("packet_type", "payload"),
    ("silver", "position_report"): (
        "source_system", "vehicle_id", "event_time_utc", "latitude", "longitude",
    ),
    ("silver", "b2b_event"): (
        "event_type", "event_time_utc", "latitude", "longitude",
    ),
    ("silver", "signal_row"): ("b2b_event_id", "signal_name", "signal_timestamp"),
    ("gold", "engine_session"): ("vehicle_id", "session_start_utc"),
    ("gold", "idle"): ("vehicle_id", "idle_start_utc"),
    ("gold", "cross_source_pair"): (
        "vehicle_id", "event_time_left_utc", "event_time_right_utc",
    ),
}


def _columns(conn, schema, table):
    rows = conn.execute(f"PRAGMA {schema}.table_info('{table}')").fetchall()
    return {row[1]: row[2] for row in rows}


def _unique_sets(conn, schema, table):
    found = []
    for index in conn.execute(f"PRAGMA {schema}.index_list('{table}')"):
        if index[2] != 1:
            continue
        info = conn.execute(f"PRAGMA {schema}.index_info('{index[1]}')").fetchall()
        found.append(tuple(column[2] for column in info))
    return found


class SchemaShapeTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.conn = sqlite3.connect(":memory:")
        for layer in ("bronze", "silver", "gold"):
            path = root / f"{layer}.sqlite"
            layer_conn = sqlite3.connect(path)
            layer_conn.executescript((SCHEMA / f"{layer}.sql").read_text())
            layer_conn.close()
            self.conn.execute(f"ATTACH DATABASE ? AS {layer}", (str(path),))

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_tables_sit_in_their_schema(self):
        for schema, tables in (
            ("bronze", BRONZE_TABLES),
            ("silver", SILVER_TABLES),
            ("gold", GOLD_TABLES),
        ):
            names = {
                row[0]
                for row in self.conn.execute(
                    f"SELECT name FROM {schema}.sqlite_master WHERE type = 'table'"
                )
            }
            self.assertTrue(set(tables) <= names)

    def test_silver_types_and_metadata(self):
        position = _columns(self.conn, "silver", "position_report")
        self.assertEqual(position["source_system"], "TEXT")
        self.assertEqual(position["vehicle_id"], "TEXT")
        self.assertEqual(position["event_time_utc"], "TEXT")
        self.assertEqual(position["event_time_bangkok"], "TEXT")
        self.assertEqual(position["latitude"], "REAL")
        self.assertEqual(position["speed_kmh"], "REAL")
        self.assertEqual(position["heading_deg"], "INTEGER")
        self.assertEqual(position["gps_signal_flag"], "INTEGER")
        for table in ("position_report", "b2b_event", "signal_row"):
            columns = _columns(self.conn, "silver", table)
            self.assertIn("source_file", columns)
            self.assertIn("ingested_at_utc", columns)
            self.assertNotIn("record_hash", columns)
        signal = _columns(self.conn, "silver", "signal_row")
        self.assertEqual(
            list(signal),
            [
                "source_system",
                "source_file",
                "ingested_at_utc",
                "b2b_event_id",
                "signal_name",
                "signal_value",
                "signal_timestamp",
            ],
        )

    def test_gold_has_no_source_file(self):
        for table in GOLD_TABLES:
            columns = _columns(self.conn, "gold", table)
            self.assertIn("built_at_utc", columns)
            self.assertNotIn("source_file", columns)
            self.assertNotIn("record_hash", columns)

    def test_unique_business_keys(self):
        for (schema, table), expected in UNIQUE.items():
            self.assertIn(expected, _unique_sets(self.conn, schema, table))


if __name__ == "__main__":
    unittest.main()
