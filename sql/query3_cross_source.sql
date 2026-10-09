-- Latest position per vehicle and source, compared across sources.
-- Run against the gold database with silver attached as silver.
--
-- Empty vehicle_id is ignored. The connected-vehicle sample has none,
-- so it cannot match another feed by accident.
-- A pair is kept when the two latest times are within 5 minutes.
-- disagree_flag is 1 when the haversine distance is over 1 km.

DELETE FROM cross_source_pair;

WITH latest AS (
    SELECT *
    FROM (
        SELECT
            vehicle_id,
            source_system,
            event_time_utc,
            latitude,
            longitude,
            substr(replace(event_time_utc, 'T', ' '), 1, 19) AS ts,
            ROW_NUMBER() OVER (
                PARTITION BY vehicle_id, source_system
                ORDER BY event_time_utc DESC
            ) AS rn
        FROM silver.position_report
        WHERE vehicle_id != ''
    )
    WHERE rn = 1
),
pairs AS (
    SELECT
        a.vehicle_id,
        a.source_system AS source_system_left,
        b.source_system AS source_system_right,
        a.event_time_utc AS event_time_left_utc,
        b.event_time_utc AS event_time_right_utc,
        a.latitude AS latitude_left,
        a.longitude AS longitude_left,
        b.latitude AS latitude_right,
        b.longitude AS longitude_right,
        2 * 6371 * ASIN(MIN(1.0, SQRT(
            POW(SIN(RADIANS(b.latitude - a.latitude) / 2), 2)
            + COS(RADIANS(a.latitude)) * COS(RADIANS(b.latitude))
            * POW(SIN(RADIANS(b.longitude - a.longitude) / 2), 2)
        ))) AS distance_km
    FROM latest AS a
    JOIN latest AS b
      ON a.vehicle_id = b.vehicle_id
     AND a.source_system < b.source_system
     AND ABS(julianday(a.ts) - julianday(b.ts)) * 86400 <= 300
)
INSERT INTO cross_source_pair (
    built_at_utc,
    vehicle_id,
    source_system_left,
    source_system_right,
    event_time_left_utc,
    event_time_right_utc,
    latitude_left,
    longitude_left,
    latitude_right,
    longitude_right,
    distance_km,
    disagree_flag
)
SELECT
    strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
    vehicle_id,
    source_system_left,
    source_system_right,
    event_time_left_utc,
    event_time_right_utc,
    latitude_left,
    longitude_left,
    latitude_right,
    longitude_right,
    distance_km,
    CASE WHEN distance_km > 1 THEN 1 ELSE 0 END
FROM pairs;
