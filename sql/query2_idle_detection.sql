-- Idle spans for connected-vehicle positions inside an engine-on window.
-- Run against the gold database with silver attached as silver.
--
-- A span is consecutive position reports with speed_kmh = 0.
-- A non-zero or missing speed ends the span.
-- Only spans longer than 30 minutes are kept.
-- Fuel uses Vehicle Fuel Rate (L/hr) times the gap to the next reading.

DELETE FROM idle;

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
      AND e.source_system = 'source_b'
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
        MAX(CASE WHEN event_type = 33 THEN ts END) AS start_ts,
        MAX(CASE WHEN event_type = 33 THEN event_time_utc END) AS session_start_utc,
        MIN(CASE WHEN event_type = 34 THEN ts END) AS off_ts,
        CASE
            WHEN MIN(CASE WHEN event_type = 34 THEN ts END) IS NOT NULL
             AND (
                julianday(MIN(CASE WHEN event_type = 34 THEN ts END))
                - julianday(MAX(CASE WHEN event_type = 33 THEN ts END))
             ) <= 1
            THEN MIN(CASE WHEN event_type = 34 THEN ts END)
            ELSE datetime(MAX(CASE WHEN event_type = 33 THEN ts END), '+1 day')
        END AS window_end_ts
    FROM grouped
    GROUP BY vehicle_id, grp
    HAVING SUM(CASE WHEN event_type = 33 THEN 1 ELSE 0 END) > 0
),
points AS (
    SELECT
        p.vehicle_id,
        s.session_start_utc,
        p.event_time_utc,
        substr(replace(p.event_time_utc, 'T', ' '), 1, 19) AS ts,
        CASE WHEN p.speed_kmh = 0 THEN 0 ELSE 1 END AS moving
    FROM silver.position_report AS p
    JOIN sessions AS s
      ON s.vehicle_id = p.vehicle_id
     AND p.source_system = 'source_b'
     AND substr(replace(p.event_time_utc, 'T', ' '), 1, 19) >= s.start_ts
     AND substr(replace(p.event_time_utc, 'T', ' '), 1, 19) < s.window_end_ts
),
islands AS (
    SELECT
        *,
        SUM(moving) OVER (
            PARTITION BY vehicle_id, session_start_utc
            ORDER BY ts
        ) AS island
    FROM points
),
spans AS (
    SELECT
        vehicle_id,
        MIN(event_time_utc) AS idle_start_utc,
        MIN(ts) AS start_ts,
        MAX(ts) AS end_ts,
        CAST(ROUND((julianday(MAX(ts)) - julianday(MIN(ts))) * 86400) AS INTEGER) AS duration_seconds
    FROM islands
    WHERE moving = 0
    GROUP BY vehicle_id, session_start_utc, island
    HAVING (julianday(MAX(ts)) - julianday(MIN(ts))) * 86400 > 1800
)
INSERT INTO idle (
    built_at_utc,
    vehicle_id,
    idle_start_utc,
    duration_seconds,
    fuel_consumed
)
SELECT
    strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
    span.vehicle_id,
    span.idle_start_utc,
    span.duration_seconds,
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
            WHERE p.vehicle_id = span.vehicle_id
              AND s.signal_name = 'Vehicle Fuel Rate'
              AND substr(replace(s.signal_timestamp, 'T', ' '), 1, 19) >= span.start_ts
              AND substr(replace(s.signal_timestamp, 'T', ' '), 1, 19) <= span.end_ts
        ) AS r
    ), 0)
FROM spans AS span;
