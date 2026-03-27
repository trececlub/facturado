from __future__ import annotations

from io import BytesIO

import barcode
from barcode.writer import ImageWriter
from PIL.ImageQt import ImageQt
from PySide6.QtGui import QImage, QPixmap


def code128_to_pixmap(data: str, width_px: int = 380, height_px: int = 70) -> QPixmap:
    value = data.strip() or "000000"

    code = barcode.get("code128", value, writer=ImageWriter())
    output = BytesIO()
    code.write(
        output,
        options={
            "module_width": 0.2,
            "module_height": 12,
            "quiet_zone": 1,
            "font_size": 9,
            "text_distance": 1,
            "dpi": 300,
            "write_text": True,
            "background": "white",
            "foreground": "black"
        },
    )
    output.seek(0)

    from PIL import Image

    img = Image.open(output).convert("RGB")
    img = img.resize((width_px, height_px))
    return QPixmap.fromImage(QImage(ImageQt(img)))
