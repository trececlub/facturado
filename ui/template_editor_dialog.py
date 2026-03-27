from __future__ import annotations

from copy import deepcopy

from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QPushButton,
    QVBoxLayout,
)


class TemplateEditorDialog(QDialog):
    def __init__(self, template: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor de plantilla")
        self.resize(480, 420)
        self.template = deepcopy(template)

        root = QVBoxLayout(self)

        self.controls: dict[str, QDoubleSpinBox] = {}

        root.addWidget(self._build_group(
            "Header",
            [
                ("header_x", "header.x_mm", self.template["header"]["x_mm"]),
                ("header_y", "header.y_mm", self.template["header"]["y_mm"]),
            ],
        ))

        root.addWidget(self._build_group(
            "Campos",
            [
                ("fields_x", "left_fields.x_mm", self.template["left_fields"]["x_mm"]),
                ("fields_y", "left_fields.y_mm", self.template["left_fields"]["y_mm"]),
                (
                    "fields_font",
                    "left_fields.value_font_size",
                    self.template["left_fields"]["value_font_size"],
                ),
            ],
        ))

        root.addWidget(self._build_group(
            "Imagen",
            [
                ("photo_x", "photo.x_mm", self.template["photo"]["x_mm"]),
                ("photo_y", "photo.y_mm", self.template["photo"]["y_mm"]),
                ("photo_w", "photo.w_mm", self.template["photo"]["w_mm"]),
                ("photo_h", "photo.h_mm", self.template["photo"]["h_mm"]),
            ],
        ))

        root.addWidget(self._build_group(
            "Barcode + QR",
            [
                ("barcode_x", "barcode.x_mm", self.template["barcode"]["x_mm"]),
                ("barcode_y", "barcode.y_mm", self.template["barcode"]["y_mm"]),
                ("barcode_h", "barcode.h_mm", self.template["barcode"]["h_mm"]),
                ("qr_x", "qr.x_mm", self.template["qr"]["x_mm"]),
                ("qr_y", "qr.y_mm", self.template["qr"]["y_mm"]),
                ("qr_s", "qr.size_mm", self.template["qr"]["size_mm"]),
            ],
        ))

        buttons = QGridLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_ok = QPushButton("Aplicar")
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.accept)
        buttons.addWidget(btn_cancel, 0, 0)
        buttons.addWidget(btn_ok, 0, 1)
        root.addLayout(buttons)

    def _build_group(self, title: str, rows: list[tuple[str, str, float]]) -> QGroupBox:
        g = QGroupBox(title)
        f = QFormLayout(g)

        for key, label, value in rows:
            sb = QDoubleSpinBox()
            sb.setDecimals(1)
            sb.setRange(0, 300)
            sb.setValue(float(value))
            sb.setSingleStep(0.5)
            self.controls[key] = sb
            f.addRow(label, sb)

        return g

    def result_template(self) -> dict:
        t = deepcopy(self.template)

        t["header"]["x_mm"] = self.controls["header_x"].value()
        t["header"]["y_mm"] = self.controls["header_y"].value()

        t["left_fields"]["x_mm"] = self.controls["fields_x"].value()
        t["left_fields"]["y_mm"] = self.controls["fields_y"].value()
        t["left_fields"]["value_font_size"] = self.controls["fields_font"].value()

        t["photo"]["x_mm"] = self.controls["photo_x"].value()
        t["photo"]["y_mm"] = self.controls["photo_y"].value()
        t["photo"]["w_mm"] = self.controls["photo_w"].value()
        t["photo"]["h_mm"] = self.controls["photo_h"].value()

        t["barcode"]["x_mm"] = self.controls["barcode_x"].value()
        t["barcode"]["y_mm"] = self.controls["barcode_y"].value()
        t["barcode"]["h_mm"] = self.controls["barcode_h"].value()

        t["qr"]["x_mm"] = self.controls["qr_x"].value()
        t["qr"]["y_mm"] = self.controls["qr_y"].value()
        t["qr"]["size_mm"] = self.controls["qr_s"].value()

        return t
