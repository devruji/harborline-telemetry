# Harborline telemetry

Local exercise: read three vehicle-telemetry extracts, land them in one analytics model, and answer a few fleet questions in SQL.

Harborline is a stand-in name. This repository does not use the organization that issued the exercise.

## Layout

```
data/       sample extracts
schema/     unified model and field mapping
pipeline/   Python ingestion
sql/        analytical queries
```

`schema/`, `pipeline/`, and `sql/` are placeholders. Nothing is implemented yet.

## Samples

| File | What it is |
|---|---|
| `data/source_a_gps_vendor.json` | Latest-position report from a GPS vendor |
| `data/source_a_gps_vendor_rerun.json` | Same payload as the file above, under another name |
| `data/source_b_toyota_0x51.json` | Periodic packet: one event snapshot plus a per-second signal stream |
| `data/source_b_toyota_0x52.json` | Engine-on packet: event snapshot only |
| `data/source_c_logistics.xlsx` | Flat GPS track from a logistics fleet |
