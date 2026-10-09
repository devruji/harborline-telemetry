"""Run ingestion twice and read the databases from the outside."""

import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.ingest import main

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _count(path: Path, table: str) -> int:
    conn = sqlite3.connect(path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


class IngestRunTest(unittest.TestCase):
    def test_samples_load_once_and_a_bad_speed_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / "data"
            output = root / "output"
            shutil.copytree(DATA, sample)
            poison_name = "source_a_gps_vendor_poison.json"
            poison = {
                "registration": "POISON",
                "event_th": "",
                "event_en": "LOCATION",
                "location_th": "",
                "location_en": "",
                "local_timestamp": "2025-01-01 00:00:00",
                "lat": 13.7,
                "lon": 100.5,
                "speed": -1,
                "course": 0,
                "type_of_fix": 0,
                "no_of_satellite": 4,
                "internal_power": 0,
                "external_power": 0,
                "mileage": None,
                "Temp1": "-",
                "Temp2": "-",
                "Temp3": "-",
                "fuel_sensor": 0,
                "fuel_canbus": 0,
                "driver_name": "-",
            }
            (sample / poison_name).write_text(json.dumps(poison))
            outside = dict(poison)
            outside["registration"] = "OUTSIDE"
            outside["lat"] = 0
            outside["speed"] = 10
            (sample / "source_a_gps_vendor_outside.json").write_text(json.dumps(outside))
            future = dict(poison)
            future["registration"] = "FUTURE"
            future["lat"] = 13.7
            future["speed"] = 10
            future["local_timestamp"] = "2099-01-01 00:00:00"
            (sample / "source_a_gps_vendor_future.json").write_text(json.dumps(future))

            from io import StringIO
            from contextlib import redirect_stdout

            first = StringIO()
            with redirect_stdout(first):
                code = main(["--data", str(sample), "--output", str(output)])
            self.assertEqual(code, 0)
            log = first.getvalue()
            self.assertIn(poison_name, log)
            self.assertIn("negative speed", log)
            self.assertIn("outside Thailand", log)
            self.assertIn("timestamp in the future", log)

            bronze = output / "bronze.sqlite"
            silver = output / "silver.sqlite"
            gold = output / "gold.sqlite"
            self.assertEqual(_count(bronze, "gps_vendor_report"), 1)
            self.assertEqual(_count(bronze, "logistics_report"), 32)
            self.assertEqual(_count(bronze, "connected_packet"), 2)
            self.assertEqual(_count(silver, "position_report"), 35)
            self.assertEqual(_count(silver, "b2b_event"), 2)
            self.assertEqual(_count(silver, "signal_row"), 100)
            self.assertEqual(_count(gold, "engine_session"), 0)
            self.assertEqual(_count(gold, "idle"), 0)
            self.assertEqual(_count(gold, "cross_source_pair"), 0)

            silver_conn = sqlite3.connect(silver)
            types = {
                row[0]
                for row in silver_conn.execute("SELECT event_type FROM b2b_event")
            }
            voltage = silver_conn.execute(
                "SELECT COUNT(*) FROM signal_row WHERE signal_name = ?",
                ("+B Voltage Value",),
            ).fetchone()[0]
            silver_conn.close()
            self.assertEqual(types, {30, 33})
            self.assertEqual(voltage, 2)

            second = StringIO()
            with redirect_stdout(second):
                code = main(["--data", str(sample), "--output", str(output)])
            self.assertEqual(code, 0)
            self.assertNotIn("inserted=1", second.getvalue())
            self.assertNotIn("inserted=2", second.getvalue())
            for line in second.getvalue().splitlines():
                self.assertIn("inserted=0", line)
            self.assertEqual(_count(bronze, "gps_vendor_report"), 1)
            self.assertEqual(_count(silver, "signal_row"), 100)


if __name__ == "__main__":
    unittest.main()
