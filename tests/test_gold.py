"""Fill gold from silver and check the sample plus the edge-case fixture."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.ingest import main

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SQL = ROOT / "sql"


def _fill(gold: Path, silver: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(gold)
    conn.execute("ATTACH DATABASE ? AS silver", (str(silver),))
    for name in (
        "query1_engine_sessions.sql",
        "query2_idle_detection.sql",
        "query3_cross_source.sql",
    ):
        conn.executescript((SQL / name).read_text())
    return conn


def _event(conn, vehicle_id, event_type, when, latitude=14.0, longitude=100.0):
    conn.execute(
        """
        INSERT INTO b2b_event (
            source_system, source_file, ingested_at_utc, event_type,
            event_time_utc, event_time_bangkok, latitude, longitude, speed_kmh
        ) VALUES ('source_b', ?, '2024-01-01T00:00:00Z', ?, ?, ?, ?, ?, 0)
        """,
        (vehicle_id, event_type, when, when, latitude, longitude),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO position_report (
            source_system, source_file, ingested_at_utc, vehicle_id,
            event_time_utc, event_time_bangkok, latitude, longitude, speed_kmh
        )         VALUES ('source_b', ?, '2024-01-01T00:00:00Z', ?, '2019-01-01T00:00:00+00:00', '2019-01-01T00:00:00+00:00', 0, 0, 10)
        """,
        (vehicle_id, vehicle_id),
    )


def _position(conn, vehicle_id, source, when, latitude, longitude, speed):
    conn.execute(
        """
        INSERT INTO position_report (
            source_system, source_file, ingested_at_utc, vehicle_id,
            event_time_utc, event_time_bangkok, latitude, longitude, speed_kmh
        ) VALUES (?, 'fixture', '2024-01-01T00:00:00Z', ?, ?, ?, ?, ?, ?)
        """,
        (source, vehicle_id, when, when, latitude, longitude, speed),
    )


class GoldFillTest(unittest.TestCase):
    def test_sample_and_fixture_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "output"
            self.assertEqual(main(["--data", str(DATA), "--output", str(output)]), 0)
            gold = output / "gold.sqlite"
            silver = output / "silver.sqlite"

            conn = _fill(gold, silver)
            sessions = conn.execute(
                """
                SELECT vehicle_id, session_end_utc, missing_off_flag, repeated_on_flag
                FROM engine_session
                """
            ).fetchall()
            self.assertEqual(sessions, [("", None, 1, 0)])
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM idle").fetchone()[0], 0)
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM cross_source_pair").fetchone()[0], 0
            )

            silver_conn = sqlite3.connect(silver)
            _event(silver_conn, "fixture-dup", 33, "2024-06-01T00:00:00+00:00", 14.0, 100.0)
            _event(silver_conn, "fixture-dup", 33, "2024-06-01T00:01:00+00:00", 14.1, 100.1)
            _event(silver_conn, "fixture-dup", 34, "2024-06-01T00:10:00+00:00", 14.2, 100.2)
            _event(silver_conn, "fixture-open", 33, "2020-01-01T00:00:00+00:00", 14.3, 100.3)
            _event(silver_conn, "fixture-idle", 33, "2024-06-02T00:00:00+00:00", 14.4, 100.4)
            _event(silver_conn, "fixture-idle", 34, "2024-06-02T02:00:00+00:00", 14.5, 100.5)
            _position(
                silver_conn, "fixture-idle", "source_b",
                "2024-06-02T00:00:00+00:00", 14.4, 100.4, 0,
            )
            _position(
                silver_conn, "fixture-idle", "source_b",
                "2024-06-02T00:40:00+00:00", 14.4, 100.41, 0,
            )
            _position(
                silver_conn, "shared-1", "source_a",
                "2024-06-03T01:00:00+00:00", 13.7563, 100.5018, 10,
            )
            _position(
                silver_conn, "shared-1", "source_c",
                "2024-06-03T01:03:00+00:00", 13.7563, 100.5218, 10,
            )
            silver_conn.commit()
            silver_conn.close()

            conn.close()
            conn = _fill(gold, silver)
            dup = conn.execute(
                """
                SELECT session_end_utc IS NOT NULL, repeated_on_flag, missing_off_flag,
                       duration_seconds
                FROM engine_session
                WHERE vehicle_id = 'fixture-dup'
                """
            ).fetchone()
            self.assertEqual(dup[0], 1)
            self.assertEqual(dup[1], 1)
            self.assertEqual(dup[2], 0)
            self.assertEqual(dup[3], 9 * 60)
            open_row = conn.execute(
                """
                SELECT session_end_utc, missing_off_flag
                FROM engine_session
                WHERE vehicle_id = 'fixture-open'
                """
            ).fetchone()
            self.assertEqual(open_row, (None, 1))
            idle = conn.execute(
                """
                SELECT duration_seconds FROM idle WHERE vehicle_id = 'fixture-idle'
                """
            ).fetchone()
            self.assertEqual(idle[0], 40 * 60)
            pair = conn.execute(
                """
                SELECT source_system_left, source_system_right, disagree_flag
                FROM cross_source_pair
                WHERE vehicle_id = 'shared-1'
                """
            ).fetchone()
            self.assertEqual(pair, ("source_a", "source_c", 1))

            before = conn.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM engine_session),
                    (SELECT COUNT(*) FROM idle),
                    (SELECT COUNT(*) FROM cross_source_pair)
                """
            ).fetchone()
            conn.close()
            conn = _fill(gold, silver)
            after = conn.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM engine_session),
                    (SELECT COUNT(*) FROM idle),
                    (SELECT COUNT(*) FROM cross_source_pair)
                """
            ).fetchone()
            conn.close()
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
