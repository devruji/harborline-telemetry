# Glossary

Names for this repo. Use these words in schema, code, issues, and SQL. Add a term when a new name shows up in those places. One term, one meaning. If a new name is a synonym of a term below, use the term below.

The public project name is Harborline. Do not copy an organization name out of `private/`.

| Term | Meaning |
|---|---|
| Source system | One upstream feed. This repo has three: GPS vendor (`source_a`), connected vehicle (`source_b`), logistics fleet (`source_c`). |
| Position report | One row of where a vehicle was: coordinates, speed, heading, and event time. The unified table is this grain. |
| Source lineage | The `source_system` value that says which feed a row came from. |
| Vehicle id | The identifier used to group reports for one vehicle inside a source. GPS vendor uses the plate. Logistics uses `TKNO`. Connected-vehicle packets in the sample have none. |
| B2B event | The event snapshot inside a connected-vehicle packet. Event type 30 is a heartbeat, 33 is engine ON, 34 is engine OFF. Stored in its own table, not as a position report. |
| Signal row | One CAN or warning value from the per-second contained-data list, flattened to `b2b_event_id`, `signal_name`, `signal_value`, `signal_timestamp`. |
| Engine session | The interval from engine ON (event type 33) to the matching engine OFF (event type 34), after the edge cases in `sql/query1_engine_sessions.sql`. |
| Idle | Engine ON and speed 0, continuously, for the span measured by `sql/query2_idle_detection.sql`. |
| Cross-source pair | The same vehicle id seen in two source systems, compared by `sql/query3_cross_source.sql`. |
| Ingestion run | One execution of `pipeline/ingest.py` over the files in `data/`. |
| Idempotent ingestion | A second ingestion run of the same bytes inserts no new rows. |
| Local time | Timestamps as the source recorded them, before normalization. |
| Event time | A timestamp normalized to `Asia/Bangkok` and also stored in UTC. |
