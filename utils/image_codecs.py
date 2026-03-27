from __future__ import annotations

import qrcode
from PIL.ImageQt import ImageQt
from PySide6.QtGui import QImage, QPixmap


def qr_to_pixmap(text: str, size_px: int = 96) -> QPixmap:
    qr = qrcode.QRCode(border=1, box_size=8)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = img.resize((size_px, size_px))
    return QPixmap.fromImage(QImage(ImageQt(img)))


def bytes_to_qpixmap(data: bytes) -> QPixmap:
    qimg = QImage.fromData(data)
    return QPixmap.fromImage(qimg)
