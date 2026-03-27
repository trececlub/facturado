from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class FormPanel(QWidget):
    changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.inputs: dict[str, object] = {}
        root = QVBoxLayout(self)

        group = QGroupBox("Datos del sticker")
        form = QFormLayout(group)

        self._add_line(form, "nombre", "Nombre")
        self._add_line(form, "apellido", "Apellido/Segundo nombre")
        self._add_line(form, "cargo", "Cargo/Categoria")
        self._add_line(form, "id_interno", "ID interno")
        self._add_line(form, "fecha", "Fecha")
        self._add_line(form, "sede", "Sede/Direccion")

        obs = QTextEdit()
        obs.setMaximumHeight(75)
        obs.textChanged.connect(self._emit)
        self.inputs["observaciones"] = obs
        form.addRow("Observaciones", obs)

        self._add_line(form, "barcode", "Codigo de barras")
        self._add_line(form, "qr", "QR (texto)")

        foto = QLineEdit()
        foto.textChanged.connect(self._emit)
        btn = QPushButton("Buscar")
        btn.clicked.connect(self._browse_image)
        row = QHBoxLayout()
        row.addWidget(foto)
        row.addWidget(btn)
        self.inputs["foto_path"] = foto
        form.addRow("Foto/Imagen", row)

        root.addWidget(group)
        root.addStretch(1)

    def _add_line(self, form: QFormLayout, key: str, label: str) -> None:
        w = QLineEdit()
        w.textChanged.connect(self._emit)
        self.inputs[key] = w
        form.addRow(label, w)

    def _browse_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen",
            "",
            "Imagenes (*.png *.jpg *.jpeg *.bmp)",
        )
        if path:
            casted = self.inputs["foto_path"]
            assert isinstance(casted, QLineEdit)
            casted.setText(path)

    def set_data(self, values: dict) -> None:
        for key, widget in self.inputs.items():
            val = str(values.get(key, ""))
            if isinstance(widget, QTextEdit):
                widget.blockSignals(True)
                widget.setPlainText(val)
                widget.blockSignals(False)
            else:
                widget.blockSignals(True)
                widget.setText(val)
                widget.blockSignals(False)
        self._emit()

    def data(self) -> dict:
        out = {}
        for key, widget in self.inputs.items():
            if isinstance(widget, QTextEdit):
                out[key] = widget.toPlainText().strip()
            else:
                out[key] = widget.text().strip()
        return out

    def _emit(self) -> None:
        self.changed.emit(self.data())
