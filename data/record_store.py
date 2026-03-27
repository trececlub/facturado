from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class RecordStore:
    def __init__(self, records_file: str):
        self.path = Path(records_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def save(self, record: dict[str, Any]) -> None:
        rows = self.load_all()
        row = dict(record)
        row["saved_at"] = datetime.now().isoformat(timespec="seconds")
        rows.append(row)
        self.path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_all(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []
