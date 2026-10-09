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

The pipeline and the three analytical queries are not runnable yet. Add those commands in the same change that creates them.
