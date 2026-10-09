# Runbook

Commands that work in this repo today. The objective and the deliverables stay in `README.md`.

## Python

pyenv selects 3.12.7 via `.python-version`. uv manages the virtualenv. `.venv/` stays untracked.

```bash
pyenv install 3.12.7
uv sync
uv run python --version
```

## Schema

The DDL creates empty databases. It does not load the samples.

```bash
mkdir -p output
sqlite3 output/bronze.sqlite < schema/bronze.sql
sqlite3 output/silver.sqlite < schema/silver.sql
sqlite3 output/gold.sqlite < schema/gold.sql
uv run python -m unittest tests.test_schema
```

What each file under `pipeline/` means is `docs/pipeline.md`.

## Ingest

```bash
uv run python -m pipeline.ingest --data data --output output
uv run python -m unittest tests.test_ingest
```

A second run of the same command inserts nothing.

## Gold

Run ingest first so silver exists. Each script deletes its gold rows, then inserts them again.

```bash
sqlite3 output/gold.sqlite "ATTACH 'output/silver.sqlite' AS silver;" ".read sql/query1_engine_sessions.sql" ".read sql/query2_idle_detection.sql" ".read sql/query3_cross_source.sql"
uv run python -m unittest tests.test_gold
```
