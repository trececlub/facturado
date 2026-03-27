from pathlib import Path

from PIL import Image

from printer.print_engine import PrintEngine
from templates.template_manager import TemplateManager


def test_generate_zpl_basic():
    template = TemplateManager("templates/corporate_100x60.json").load()
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

    zpl = PrintEngine(dpi=203, printer_profile={"darkness": 15, "speed": 3}).generate_zpl(record, template)
    assert zpl.startswith("^XA")
    assert zpl.endswith("^XZ")
    assert "^BCN" in zpl
    assert "^BQN" in zpl


def test_generate_zpl_with_photo_gfa(tmp_path):
    image_path = tmp_path / "photo.png"
    img = Image.new("RGB", (80, 80), color=(10, 10, 10))
    img.save(image_path)

    template = TemplateManager("templates/corporate_100x60.json").load()
    template["photo"]["print_real_image"] = True
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
        "foto_path": str(image_path),
    }

    zpl = PrintEngine(dpi=203, printer_profile={}).generate_zpl(record, template)
    assert "^GFA" in zpl
