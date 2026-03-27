from __future__ import annotations


def validate_record(record: dict) -> list[str]:
    errors: list[str] = []

    if not record.get("nombre", "").strip():
        errors.append("El campo 'Nombre' es obligatorio.")

    if not record.get("id_interno", "").strip():
        errors.append("El campo 'ID interno' es obligatorio.")

    return errors
