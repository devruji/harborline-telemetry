# Runbook

Commands that work in this repo today. The objective and the deliverables stay in `README.md`.

## Python

pyenv selects 3.12.7 via `.python-version`. uv manages the virtualenv. `.venv/` stays untracked.

```bash
pyenv install 3.12.7
uv sync
uv run python --version
```

Schema, pipeline, and SQL are not runnable yet. Add the ingest command and the three SQL commands here in the same change that creates those files.
