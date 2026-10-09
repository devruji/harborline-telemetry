"""Allow `python -m pipeline` to run the same command as `python -m pipeline.ingest`."""

from pipeline.ingest import main

raise SystemExit(main())
