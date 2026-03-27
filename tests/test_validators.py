from utils.validators import validate_record


def test_validate_record_ok():
    record = {
        "nombre": "Laura",
        "apellido": "Diaz",
        "cargo": "Operaciones",
        "id_interno": "EMP-001",
        "fecha": "2026-03-27",
        "sede": "Bogota",
        "observaciones": "Turno A",
        "barcode": "EMP-001-20260327",
        "qr": "EMP-001|Bogota",
        "foto_path": "",
    }
    assert validate_record(record) == []


def test_validate_record_invalid_fields():
    record = {
        "nombre": "",
        "cargo": "",
        "id_interno": "@@@",
        "fecha": "27-03-2026",
        "sede": "",
        "barcode": "*",
        "foto_path": "/tmp/not_exists.png",
    }
    errors = validate_record(record)
    assert len(errors) >= 5
