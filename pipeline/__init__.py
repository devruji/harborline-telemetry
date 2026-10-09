"""Harborline ingestion.

mappings/feeds.toml declares each feed. formats/ has one loader per file shape.
apply.py only chooses the loader. sources/ reads a file. quality.py holds the rules.
db.py opens the three databases and commits once per file. ingest.py is the command.
"""
