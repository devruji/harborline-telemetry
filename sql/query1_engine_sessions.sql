-- Engine sessions from silver B2B events.
-- Run against the gold database with silver attached as silver.
--
-- Edge cases:
--   Missing OFF: an ON with no OFF within 24 hours stays open.
--     session_end_utc is null, missing_off_flag is 1, duration is null.
--   Duplicate ON: a later ON before any OFF moves the start to that ON
--     and sets repeated_on_flag to 1.
--   Out of order: events are sorted by event_time_utc before pairing.
-- Heartbeats (event type 30) do not open or close a session.
-- vehicle_id comes from the position report loaded from the same file.
-- A B2B event row does not store it.
-- Distance is max(Total Distance Traveled) - min(...) in the window.
--   One reading means 0. Fuel is Vehicle Fuel Rate (L/hr) times the gap
--   to the next rate reading. The last reading adds 0.

DELETE FROM engine_session;

WITH events AS (
    SELECT
        p.vehicle_id,
        e.event_type,
        e.event_time_utc,
        substr(replace(e.event_time_utc, 'T', ' '), 1, 19) AS ts
    FROM silver.b2b_event AS e
    JOIN silver.position_report AS p
      ON p.source_system = e.source_system
     AND p.source_file = e.source_file
    WHERE e.event_type IN (33, 34)
),
grouped AS (
    SELECT
        *,
        COALESCE(SUM(CASE WHEN event_type = 34 THEN 1 ELSE 0 END) OVER (
            PARTITION BY vehicle_id
            ORDER BY ts, event_time_utc
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ), 0) AS grp
    FROM events
),
sessions AS (
    SELECT
        vehicle_id,
        grp,
        MAX(CASE WHEN event_type = 33 THEN ts END) AS start_ts,
        MAX(CASE WHEN event_type = 33 THEN event_time_utc END) AS session_start_utc,
        MIN(CASE WHEN event_type = 34 THEN ts END) AS off_ts,
        MIN(CASE WHEN event_type = 34 THEN event_time_utc END) AS off_utc,
        SUM(CASE WHEN event_type = 33 THEN 1 ELSE 0 END) AS on_count
    FROM grouped
    GROUP BY vehicle_id, grp
    HAVING SUM(CASE WHEN event_type = 33 THEN 1 ELSE 0 END) > 0
),
bounded AS (
    SELECT
        vehicle_id,
        session_start_utc,
        start_ts,
        CASE
            WHEN off_ts IS NOT NULL
             AND (julianday(off_ts) - julianday(start_ts)) <= 1
            THEN off_utc
        END AS session_end_utc,
        CASE
            WHEN off_ts IS NOT NULL
             AND (julianday(off_ts) - julianday(start_ts)) <= 1
            THEN off_ts
            ELSE datetime(start_ts, '+1 day')
        END AS window_end_ts,
        CASE
            WHEN off_ts IS NOT NULL
             AND (julianday(off_ts) - julianday(start_ts)) <= 1
            THEN CAST(ROUND((julianday(off_ts) - julianday(start_ts)) * 86400) AS INTEGER)
        END AS duration_seconds,
        CASE WHEN on_count > 1 THEN 1 ELSE 0 END AS repeated_on_flag,
        CASE
            WHEN off_ts IS NOT NULL
             AND (julianday(off_ts) - julianday(start_ts)) <= 1
            THEN 0
            ELSE 1
        END AS missing_off_flag
    FROM sessions
)
INSERT INTO engine_session (
    built_at_utc,
    vehicle_id,
    session_start_utc,
    session_end_utc,
    duration_seconds,
    distance_km,
    fuel_consumed,
    missing_off_flag,
    repeated_on_flag
)
SELECT
    strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
    b.vehicle_id,
    b.session_start_utc,
    b.session_end_utc,
    b.duration_seconds,
    COALESCE((
        SELECT CASE
            WHEN COUNT(s.signal_value) <= 1 THEN 0
            ELSE MAX(s.signal_value) - MIN(s.signal_value)
        END
        FROM silver.signal_row AS s
        JOIN silver.b2b_event AS e ON e.b2b_event_id = s.b2b_event_id
        JOIN silver.position_report AS p
          ON p.source_system = e.source_system
         AND p.source_file = e.source_file
        WHERE p.vehicle_id = b.vehicle_id
          AND s.signal_name = 'Total Distance Traveled'
          AND substr(replace(s.signal_timestamp, 'T', ' '), 1, 19) >= b.start_ts
          AND substr(replace(s.signal_timestamp, 'T', ' '), 1, 19) < b.window_end_ts
    ), 0),
    COALESCE((
        SELECT SUM(
            r.signal_value * CASE
                WHEN r.next_ts IS NULL THEN 0
                ELSE (julianday(r.next_ts) - julianday(r.ts)) * 24
            END
        )
        FROM (
            SELECT
                s.signal_value,
                substr(replace(s.signal_timestamp, 'T', ' '), 1, 19) AS ts,
                LEAD(substr(replace(s.signal_timestamp, 'T', ' '), 1, 19))
                    OVER (ORDER BY s.signal_timestamp) AS next_ts
            FROM silver.signal_row AS s
            JOIN silver.b2b_event AS e ON e.b2b_event_id = s.b2b_event_id
            JOIN silver.position_report AS p
              ON p.source_system = e.source_system
             AND p.source_file = e.source_file
            WHERE p.vehicle_id = b.vehicle_id
              AND s.signal_name = 'Vehicle Fuel Rate'
              AND substr(replace(s.signal_timestamp, 'T', ' '), 1, 19) >= b.start_ts
              AND substr(replace(s.signal_timestamp, 'T', ' '), 1, 19) < b.window_end_ts
        ) AS r
    ), 0),
    b.missing_off_flag,
    b.repeated_on_flag
FROM bounded AS b;
