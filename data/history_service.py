from __future__ import annotations

import getpass
import hashlib
import json
import socket
from datetime import datetime
from pathlib import Path
from typing import Any


class HistoryService:
    def __init__(self, history_file: str):
        self.path = Path(history_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def add(
        self,
        action: str,
        record: dict[str, Any],
        status: str,
        message: str = "",
        *,
        printer_name: str = "",
        template_name: str = "",
        zpl_payload: str = "",
        queue_id: str = "",
        extra: dict[str, Any] | None = None,
    ) -> None:
        data = self.list_all()
        data.append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "action": action,
                "status": status,
                "message": message,
                "record": record,
                "audit": {
                    "user": getpass.getuser(),
                    "host": socket.gethostname(),
                    "printer": printer_name,
                    "template": template_name,
                    "queue_id": queue_id,
                    "zpl_sha256": hashlib.sha256(zpl_payload.encode("utf-8")).hexdigest()
                    if zpl_payload
                    else "",
                },
                "extra": extra or {},
            }
        )
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def list_all(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []
