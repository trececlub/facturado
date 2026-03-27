from __future__ import annotations

from datetime import datetime


def ensure_codes(record: dict) -> dict:
    out = dict(record)

    today = datetime.now().strftime("%Y%m%d")
    internal_id = out.get("id_interno", "").strip().replace(" ", "")

    if not out.get("barcode"):
        out["barcode"] = f"{internal_id}-{today}" if internal_id else today

    if not out.get("qr"):
        name = out.get("nombre", "").strip()
        site = out.get("sede", "").strip()
        out["qr"] = "|".join(x for x in [internal_id, name, site, today] if x)

    return out
