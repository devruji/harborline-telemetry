# Harborline telemetry

Harborline turns vehicle telemetry from three different feeds into one local analytics model, then answers a few fleet questions in SQL.

## Objective

Ingest every sample file into a single position model that can be queried across fleets, while keeping each feed's extra fields and the connected-vehicle event history intact.

## What we will do

1. Design the tables and write down how each source field lands.
2. Build a local Python pipeline that reads the files, checks them, skips bad rows, and loads SQLite without creating duplicates on a rerun.
3. Write three SQL queries on top of that database: engine sessions, long idle, and positions that disagree across feeds.

## Goal

A teammate can run the pipeline twice on the same files, see the second run insert nothing, and use the SQL to explain a fleet question without knowing which feed a row came from.

## Challenge

The three feeds do not share a shape, a clock, or a vehicle id.

- The GPS vendor file is one JSON object. A second file repeats those same bytes under another name.
- The connected-vehicle feed sends two packet types. One packet is an engine-on snapshot. The other is a heartbeat plus about sixty per-second signals, and the battery voltage sits under a different key than the other signals.
- The logistics feed is a spreadsheet with its own column names and its own vehicle labels.
- Timestamps arrive in three formats. Some clocks sit in 2025 and one sits in 2026.
- Engine sessions have to survive a missing engine-off, two engine-on events in a row, and timestamps that arrive out of order.
- The sample set has no shared vehicle id, so a cross-feed position check may have nothing to flag. The query still has to be right.

## Deliver

```
README.md                          assumptions, decisions, limitations
schema/bronze.sql                  raw landing tables
schema/silver.sql                  typed position, event, and signal tables
schema/gold.sql                    answer tables, empty until the SQL exists
schema/field_mapping.md            source field to silver column, and what was left out
pipeline/                          Python ingestion, entry point ingest.py
sql/query1_engine_sessions.sql
sql/query2_idle_detection.sql
sql/query3_cross_source.sql
data/                              the sample extracts
```

The three databases are attached as `bronze`, `silver`, and `gold`. Files live under `output/` and stay untracked.

Done so far: the repo layout, the docs, the Python 3.12.7 environment, the medallion DDL, and the ingestion command. Gold is still empty. The SQL that fills it is not written.

## Python

Setup and run commands live in `docs/runbook.md`.

## Samples

| File | What it is |
|---|---|
| `data/source_a_gps_vendor.json` | Latest position from a GPS vendor |
| `data/source_a_gps_vendor_rerun.json` | Same payload as the file above, under another name |
| `data/source_b_toyota_0x51.json` | Periodic packet: one event snapshot plus a per-second signal stream |
| `data/source_b_toyota_0x52.json` | Engine-on packet: event snapshot only |
| `data/source_c_logistics.xlsx` | Flat GPS track from a logistics fleet |
