from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


class TemplateManager:
    def __init__(self, default_template_path: str):
        self.default_template_path = Path(default_template_path)

    def load(self, path: str | None = None) -> dict[str, Any]:
        p = Path(path) if path else self.default_template_path
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, template: dict[str, Any], path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

    @staticmethod
    def clone(template: dict[str, Any]) -> dict[str, Any]:
        return deepcopy(template)
