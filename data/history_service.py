from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class HistoryService:
    def __init__(self, history_file: str):
        self.path = Path(history_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def add(self, action: str, record: dict[str, Any], status: str, message: str = "") -> None:
        data = self.list_all()
        data.append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "action": action,
                "record": record,
                "status": status,
                "message": message,
            }
        )
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def list_all(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []
