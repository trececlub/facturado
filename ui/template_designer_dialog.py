from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class TemplateCanvas(QWidget):
    templateChanged = Signal(dict)

    def __init__(self, template: dict):
        super().__init__()
        self.template = template
        self.setMinimumSize(760, 420)
        self.selected = "header"
        self._drag_origin: QPointF | None = None

    def _scale(self) -> tuple[float, float, float, float, float]:
        tw = float(self.template.get("width_mm", 100))
        th = float(self.template.get("height_mm", 60))
        margin = 20
        scale = min((self.width() - margin * 2) / tw, (self.height() - margin * 2) / th)
        lw = tw * scale
        lh = th * scale
        x0 = (self.width() - lw) / 2
        y0 = (self.height() - lh) / 2
        return scale, x0, y0, lw, lh

    def _rects(self) -> dict[str, QRectF]:
        s, x0, y0, _, _ = self._scale()

        header = self.template["header"]
        lf = self.template["left_fields"]
        photo = self.template["photo"]
        bc = self.template["barcode"]
        qr = self.template["qr"]

        fields_h = lf["line_height_mm"] * len(lf.get("fields", []))
        qr_size = qr.get("size_mm", 8)

        return {
            "header": QRectF(x0 + header["x_mm"] * s, y0 + header["y_mm"] * s, header["w_mm"] * s, header["h_mm"] * s),
            "left_fields": QRectF(x0 + lf["x_mm"] * s, y0 + lf["y_mm"] * s, 56 * s, fields_h * s),
            "photo": QRectF(x0 + photo["x_mm"] * s, y0 + photo["y_mm"] * s, photo["w_mm"] * s, photo["h_mm"] * s),
            "barcode": QRectF(x0 + bc["x_mm"] * s, y0 + bc["y_mm"] * s, bc["w_mm"] * s, bc["h_mm"] * s),
            "qr": QRectF(x0 + qr["x_mm"] * s, y0 + qr["y_mm"] * s, qr_size * s, qr_size * s),
        }

    def _set_xy(self, key: str, x_mm: float, y_mm: float) -> None:
        sec = self.template[key]
        sec["x_mm"] = max(0.0, round(x_mm, 1))
        sec["y_mm"] = max(0.0, round(y_mm, 1))
        self.templateChanged.emit(self.template)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#131820"))

        s, x0, y0, lw, lh = self._scale()
        p.setPen(QPen(QColor("#2f3b4f"), 1))
        p.setBrush(QColor("#ffffff"))
        p.drawRoundedRect(QRectF(x0, y0, lw, lh), 12, 12)

        palette = {
            "header": QColor("#2b6ba9"),
            "left_fields": QColor("#2d8f6f"),
            "photo": QColor("#b87b2a"),
            "barcode": QColor("#7f5ab6"),
            "qr": QColor("#4f748f"),
        }

        for key, rect in self._rects().items():
            pen = QPen(QColor("#f6f8fb"), 3 if key == self.selected else 1)
            p.setPen(pen)
            p.setBrush(palette[key])
            p.drawRect(rect)
            p.drawText(rect, Qt.AlignCenter, key)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return

        for key, rect in self._rects().items():
            if rect.contains(event.position()):
                self.selected = key
                self._drag_origin = event.position()
                self.update()
                break

    def mouseMoveEvent(self, event) -> None:
        if self._drag_origin is None:
            return

        current = event.position()
        delta = current - self._drag_origin
        scale, _, _, _, _ = self._scale()
        dx_mm = delta.x() / scale
        dy_mm = delta.y() / scale

        sec = self.template[self.selected]
        x_mm = float(sec.get("x_mm", 0)) + dx_mm
        y_mm = float(sec.get("y_mm", 0)) + dy_mm

        self._set_xy(self.selected, x_mm, y_mm)
        self._drag_origin = current
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_origin = None


class TemplateDesignerDialog(QDialog):
    def __init__(self, template: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Disenador visual de plantilla")
        self.resize(1100, 560)
        self.template = deepcopy(template)

        root = QHBoxLayout(self)
        self.canvas = TemplateCanvas(self.template)
        self.canvas.templateChanged.connect(self._sync_from_canvas)
        root.addWidget(self.canvas, 2)

        side = QVBoxLayout()
        side.addWidget(QLabel("Arrastra elementos sobre el sticker."))

        self.target = QComboBox()
        self.target.addItems(["header", "left_fields", "photo", "barcode", "qr"])
        self.target.currentTextChanged.connect(self._load_controls)
        side.addWidget(self.target)

        form = QFormLayout()

        self.x = QDoubleSpinBox()
        self.x.setRange(0, 300)
        self.x.setDecimals(1)
        form.addRow("x_mm", self.x)

        self.y = QDoubleSpinBox()
        self.y.setRange(0, 300)
        self.y.setDecimals(1)
        form.addRow("y_mm", self.y)

        self.w = QDoubleSpinBox()
        self.w.setRange(1, 300)
        self.w.setDecimals(1)
        form.addRow("w_mm", self.w)

        self.h = QDoubleSpinBox()
        self.h.setRange(1, 300)
        self.h.setDecimals(1)
        form.addRow("h_mm", self.h)

        side.addLayout(form)

        apply_btn = QPushButton("Aplicar medida")
        apply_btn.clicked.connect(self._apply_controls)
        side.addWidget(apply_btn)

        actions = QGridLayout()
        cancel_btn = QPushButton("Cancelar")
        ok_btn = QPushButton("Aplicar")
        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self.accept)
        actions.addWidget(cancel_btn, 0, 0)
        actions.addWidget(ok_btn, 0, 1)
        side.addLayout(actions)

        side.addStretch(1)
        root.addLayout(side, 1)

        self._load_controls(self.target.currentText())

    def _sync_from_canvas(self, updated: dict) -> None:
        self.template = deepcopy(updated)
        self._load_controls(self.target.currentText())

    def _load_controls(self, key: str) -> None:
        sec = self.template[key]
        self.x.setValue(float(sec.get("x_mm", 0)))
        self.y.setValue(float(sec.get("y_mm", 0)))

        if key == "qr":
            s = float(sec.get("size_mm", 8))
            self.w.setValue(s)
            self.h.setValue(s)
        elif key == "left_fields":
            self.w.setValue(56)
            self.h.setValue(float(sec.get("line_height_mm", 5)) * len(sec.get("fields", [])))
        else:
            self.w.setValue(float(sec.get("w_mm", 10)))
            self.h.setValue(float(sec.get("h_mm", 10)))

    def _apply_controls(self) -> None:
        key = self.target.currentText()
        sec = self.template[key]

        sec["x_mm"] = round(self.x.value(), 1)
        sec["y_mm"] = round(self.y.value(), 1)

        if key == "qr":
            sec["size_mm"] = round(self.w.value(), 1)
        elif key == "left_fields":
            fields = max(1, len(sec.get("fields", [])))
            sec["line_height_mm"] = round(self.h.value() / fields, 1)
        else:
            sec["w_mm"] = round(self.w.value(), 1)
            sec["h_mm"] = round(self.h.value(), 1)

        self.canvas.template = self.template
        self.canvas.update()

    def result_template(self) -> dict:
        return deepcopy(self.template)
