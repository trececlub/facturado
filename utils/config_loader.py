from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent


def _resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return ROOT


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return ROOT


def _ensure_runtime_copy(relative_path: str) -> Path:
    src = (_resource_root() / relative_path).resolve()
    dst = (_runtime_root() / relative_path).resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists() and not dst.exists():
        shutil.copy2(src, dst)
    return dst


def load_config() -> dict[str, Any]:
    config_path = _ensure_runtime_copy("config/app_config.json")
    with config_path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Keep template editable near executable in packaged mode.
    template_rel = cfg.get("default_template", "templates/corporate_100x60.json")
    _ensure_runtime_copy(template_rel)

    runtime = _runtime_root()
    cfg["default_template"] = str((runtime / template_rel).resolve())
    cfg["history_file"] = str((runtime / cfg["history_file"]).resolve())
    cfg["records_file"] = str((runtime / cfg["records_file"]).resolve())
    cfg["zpl_output_dir"] = str((runtime / cfg["zpl_output_dir"]).resolve())

    return cfg
