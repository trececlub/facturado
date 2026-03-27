from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Any


class PrintQueueService:
    def __init__(self, queue_file: str):
        self.path = Path(queue_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _load(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self, rows: list[dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    def enqueue(self, record: dict, zpl: str, source: str = "single") -> str:
        rows = self._load()
        job_id = str(uuid.uuid4())
        rows.append(
            {
                "job_id": job_id,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "source": source,
                "record": record,
                "zpl": zpl,
                "status": "queued",
                "attempts": 0,
                "last_error": "",
            }
        )
        self._save(rows)
        return job_id

    def list_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._load()
        return rows[-limit:]

    def process(
        self,
        sender: Callable[[str], None],
        retries: int = 2,
        retry_delay_sec: float = 1.0,
    ) -> tuple[int, int]:
        rows = self._load()
        sent = 0
        failed = 0

        for job in rows:
            if job.get("status") not in {"queued", "retry"}:
                continue

            max_attempts = retries + 1
            while job["attempts"] < max_attempts:
                job["attempts"] += 1
                job["updated_at"] = datetime.now().isoformat(timespec="seconds")
                try:
                    sender(job["zpl"])
                    job["status"] = "sent"
                    job["last_error"] = ""
                    sent += 1
                    break
                except Exception as e:
                    job["last_error"] = str(e)
                    if job["attempts"] < max_attempts:
                        job["status"] = "retry"
                        time.sleep(max(0.0, retry_delay_sec))
                    else:
                        job["status"] = "failed"
                        failed += 1

        self._save(rows)
        return sent, failed
