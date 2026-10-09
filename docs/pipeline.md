# Pipeline files

What each file under `pipeline/` is for. Commands stay in `docs/runbook.md`. Column meanings stay in `schema/field_mapping.md`.

A run starts at `ingest.py`. It reads `mappings/feeds.toml`, asks `apply.py` which loader to use, and prints one tally line per file.

| File | Meaning |
|---|---|
| `ingest.py` | The command. Takes `--data` and `--output`, discovers files, commits once per file. |
| `__main__.py` | Lets `python -m pipeline` call the same command. |
| `mappings/feeds.toml` | The feed declaration: file pattern, clock, bronze columns, silver fields, and packet paths. |
| `mapping.py` | Loads that TOML into feed objects. It does not read sample files. |
| `apply.py` | Chooses the loader. `format = "packet"` goes to the packet loader. Anything else goes to the flat loader. |
| `formats/flat.py` | Loads a JSON object, a JSON array, or a spreadsheet from the declared columns. |
| `formats/packet.py` | Loads one nested connected-vehicle packet: bronze payload, position report, B2B event, signal rows. |
| `formats/cast.py` | Turns a source value into text, a real, an integer, a 0/1 flag, or a driver name. |
| `sources/gps_vendor.py` | Reads a GPS vendor JSON file. No column names. |
| `sources/logistics.py` | Reads a logistics workbook into rows. No column names. |
| `sources/connected.py` | Reads a connected-vehicle file as JSON. Paths live in the feed map. |
| `position.py` | The silver `position_report` insert used by every feed. |
| `quality.py` | Parses a local clock into UTC and `Asia/Bangkok`, and rejects a bad coordinate, a negative speed, or a future time. |
| `db.py` | Opens `bronze.sqlite`, `silver.sqlite`, and `gold.sqlite`. Applies DDL when a layer is missing. A unique clash is a skip. |
| `sqlident.py` | Checks that a table or column name from the feed map is a plain identifier before it is used in SQL. |
| `tally.py` | Counts rows inserted and skipped for one file, and formats the log line. |

`tests/test_schema.py` checks the empty DDL. `tests/test_ingest.py` runs the command and reads the databases. Neither test imports a loader.
