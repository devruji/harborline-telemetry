"""Per-file insert and skip counts printed by the ingestion command."""


class FileTally:
    def __init__(self, name: str):
        self.name = name
        self.inserted = 0
        self.skipped = 0
        self.errors: list[str] = []

    def line(self) -> str:
        errors = "; ".join(self.errors) if self.errors else "-"
        return (
            f"{self.name} inserted={self.inserted} "
            f"skipped={self.skipped} errors={errors}"
        )

    def note_inserts(self, row_ids: list) -> None:
        fresh = [row_id for row_id in row_ids if row_id is not None]
        if not fresh and row_ids:
            self.skipped += 1
            return
        self.inserted += len(fresh)
