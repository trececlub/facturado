from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from utils.barcode_tools import code128_to_pixmap
from utils.image_codecs import qr_to_pixmap


class StickerPreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.template: dict = {}
        self.record: dict = {}
        self.setMinimumSize(700, 420)

    @staticmethod
    def _mm_to_px(mm: float, scale: float) -> float:
        return mm * scale

    def update_payload(self, template: dict, record: dict) -> None:
        self.template = template
        self.record = record
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor("#111419"))

        if not self.template:
            return

        tw = float(self.template.get("width_mm", 100))
        th = float(self.template.get("height_mm", 60))

        margin = 24
        available_w = self.width() - margin * 2
        available_h = self.height() - margin * 2
        scale = min(available_w / tw, available_h / th)

        label_w = tw * scale
        label_h = th * scale
        x0 = (self.width() - label_w) / 2
        y0 = (self.height() - label_h) / 2

        radius = self.template.get("preview", {}).get("corner_radius_px", 12)
        rect = QRectF(x0, y0, label_w, label_h)
        painter.setPen(QPen(QColor("#2d333f"), 1))
        painter.setBrush(QColor(self.template.get("preview", {}).get("background", "#ffffff")))
        painter.drawRoundedRect(rect, radius, radius)

        self._draw_header(painter, x0, y0, scale)
        self._draw_fields(painter, x0, y0, scale)
        self._draw_photo(painter, x0, y0, scale)
        self._draw_barcode(painter, x0, y0, scale)
        self._draw_qr(painter, x0, y0, scale)

    def _draw_header(self, p: QPainter, x0: float, y0: float, scale: float) -> None:
        h = self.template["header"]
        x = x0 + self._mm_to_px(h["x_mm"], scale)
        y = y0 + self._mm_to_px(h["y_mm"], scale)
        w = self._mm_to_px(h["w_mm"], scale)
        hgt = self._mm_to_px(h["h_mm"], scale)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(h["bg_color"]))
        p.drawRoundedRect(QRectF(x, y, w, hgt), 5, 5)

        p.setPen(QColor(h["text_color"]))
        title_font = QFont("Segoe UI", max(8, int(h["font_size_title"] * scale * 0.38)), QFont.Bold)
        p.setFont(title_font)
        p.drawText(QRectF(x + 8, y + 2, w - 10, hgt / 2), Qt.AlignLeft | Qt.AlignVCenter, h["company_name"])

        sub_font = QFont("Segoe UI", max(7, int(h["font_size_subtitle"] * scale * 0.36)))
        p.setFont(sub_font)
        p.setPen(QColor(h["subtitle_color"]))
        p.drawText(QRectF(x + 8, y + hgt / 2 - 1, w - 10, hgt / 2), Qt.AlignLeft | Qt.AlignVCenter, h["subtitle"])

    def _draw_fields(self, p: QPainter, x0: float, y0: float, scale: float) -> None:
        lf = self.template["left_fields"]
        x = x0 + self._mm_to_px(lf["x_mm"], scale)
        y = y0 + self._mm_to_px(lf["y_mm"], scale)
        step = self._mm_to_px(lf["line_height_mm"], scale)

        fields = [
            ("Nombre", self.record.get("nombre", "")),
            ("Apellido", self.record.get("apellido", "")),
            ("Cargo", self.record.get("cargo", "")),
            ("ID", self.record.get("id_interno", "")),
            ("Fecha", self.record.get("fecha", "")),
            ("Sede", self.record.get("sede", "")),
            ("Obs", self.record.get("observaciones", "")),
        ]

        font = QFont("Segoe UI", max(8, int(lf["value_font_size"] * scale * 0.35)))
        p.setFont(font)
        p.setPen(QColor("#223042"))

        for idx, (label, value) in enumerate(fields):
            text = f"{label}: {value}"
            p.drawText(QRectF(x, y + idx * step, self.width(), step), Qt.AlignLeft | Qt.AlignVCenter, text)

    def _draw_photo(self, p: QPainter, x0: float, y0: float, scale: float) -> None:
        photo = self.template["photo"]
        if not photo.get("enabled", True):
            return

        x = x0 + self._mm_to_px(photo["x_mm"], scale)
        y = y0 + self._mm_to_px(photo["y_mm"], scale)
        w = self._mm_to_px(photo["w_mm"], scale)
        h = self._mm_to_px(photo["h_mm"], scale)

        p.setPen(QPen(QColor(photo.get("border_color", "#8ea0b8")), 1))
        p.setBrush(QColor("#f5f7fa"))
        p.drawRect(QRectF(x, y, w, h))

        image_path = self.record.get("foto_path", "")
        if image_path and Path(image_path).exists():
            pix = QPixmap(image_path)
            if not pix.isNull():
                scaled = pix.scaled(int(w - 4), int(h - 4), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                p.drawPixmap(int(x + 2), int(y + 2), scaled)
                return

        p.setPen(QColor("#6a7485"))
        p.drawText(QRectF(x, y, w, h), Qt.AlignCenter, "IMAGEN")

    def _draw_barcode(self, p: QPainter, x0: float, y0: float, scale: float) -> None:
        bc = self.template["barcode"]
        if not bc.get("enabled", True):
            return

        x = x0 + self._mm_to_px(bc["x_mm"], scale)
        y = y0 + self._mm_to_px(bc["y_mm"], scale)
        w = self._mm_to_px(bc["w_mm"], scale)
        h = self._mm_to_px(bc["h_mm"], scale)

        barcode_data = self.record.get("barcode", "")
        try:
            barcode_pix = code128_to_pixmap(barcode_data, int(w), int(h + 20))
            p.drawPixmap(int(x), int(y), barcode_pix)
        except Exception:
            p.setPen(QColor("#222"))
            p.drawRect(QRectF(x, y, w, h))
            p.drawText(QRectF(x, y, w, h), Qt.AlignCenter, "Barcode")

    def _draw_qr(self, p: QPainter, x0: float, y0: float, scale: float) -> None:
        qr = self.template.get("qr", {})
        if not qr.get("enabled", False):
            return

        val = self.record.get("qr", "")
        if not val:
            return

        x = x0 + self._mm_to_px(qr["x_mm"], scale)
        y = y0 + self._mm_to_px(qr["y_mm"], scale)
        size = self._mm_to_px(qr["size_mm"], scale)

        try:
            pix = qr_to_pixmap(val, int(size))
            p.drawPixmap(int(x), int(y), pix)
        except Exception:
            p.setPen(QColor("#444"))
            p.drawRect(QRectF(x, y, size, size))
            p.drawText(QRectF(x, y, size, size), Qt.AlignCenter, "QR")
