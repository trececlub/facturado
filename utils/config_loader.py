from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "app_config.json"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Normalize relative paths against project root
    for key in ["default_template", "history_file", "records_file", "zpl_output_dir"]:
        cfg[key] = str((ROOT / cfg[key]).resolve())

    return cfg
