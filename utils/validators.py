from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,32}$")
BARCODE_PATTERN = re.compile(r"^[A-Za-z0-9._\-/:+ ]{3,64}$")


MAX_LENGTHS = {
    "nombre": 40,
    "apellido": 40,
    "cargo": 40,
    "id_interno": 32,
    "fecha": 10,
    "sede": 60,
    "observaciones": 120,
    "barcode": 64,
    "qr": 300,
}


def _validate_date_iso(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_record(record: dict) -> list[str]:
    errors: list[str] = []

    for field in ["nombre", "cargo", "id_interno", "fecha", "sede"]:
        if not record.get(field, "").strip():
            errors.append(f"El campo '{field}' es obligatorio.")

    for field, max_len in MAX_LENGTHS.items():
        value = record.get(field, "")
        if value and len(str(value)) > max_len:
            errors.append(f"El campo '{field}' supera el maximo ({max_len}).")

    internal_id = record.get("id_interno", "").strip()
    if internal_id and not ID_PATTERN.match(internal_id):
        errors.append("ID interno invalido. Usa solo letras, numeros, ., _, - (3 a 32).")

    date_val = record.get("fecha", "").strip()
    if date_val and not _validate_date_iso(date_val):
        errors.append("Fecha invalida. Usa formato YYYY-MM-DD.")

    barcode_val = record.get("barcode", "").strip()
    if barcode_val and not BARCODE_PATTERN.match(barcode_val):
        errors.append("Codigo de barras invalido. Revisa caracteres permitidos.")

    qr_val = record.get("qr", "")
    if qr_val and len(qr_val.encode("utf-8")) > 600:
        errors.append("QR demasiado largo para impresion estable.")

    photo_path = record.get("foto_path", "").strip()
    if photo_path:
        p = Path(photo_path)
        if not p.exists():
            errors.append("La ruta de foto/imagen no existe.")
        elif p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
            errors.append("La imagen debe ser PNG/JPG/JPEG/BMP.")

    return errors
