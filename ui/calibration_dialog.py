from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from printer.printer_service import PrinterService


class CalibrationDialog(QDialog):
    def __init__(
        self,
        printer_config: dict,
        on_test_print: Callable[[dict], tuple[bool, str]],
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Calibracion de impresora")
        self.resize(560, 430)
        self._on_test_print = on_test_print

        root = QVBoxLayout(self)
        form = QFormLayout()

        self.interface = QComboBox()
        self.interface.addItems(["usb", "network"])
        self.interface.setCurrentText(printer_config.get("interface", "usb"))
        form.addRow("Interface", self.interface)

        printer_row = QHBoxLayout()
        self.printer_name = QComboBox()
        self.printer_name.setEditable(True)
        self._load_printers(printer_config.get("default_name", ""))
        refresh = QPushButton("Refrescar")
        refresh.clicked.connect(lambda: self._load_printers(self.printer_name.currentText()))
        printer_row.addWidget(self.printer_name)
        printer_row.addWidget(refresh)
        form.addRow("Impresora USB", printer_row)

        self.host = QLineEdit(printer_config.get("network_host", ""))
        form.addRow("Host red", self.host)

        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(int(printer_config.get("network_port", 9100)))
        form.addRow("Puerto", self.port)

        self.darkness = QSpinBox()
        self.darkness.setRange(-30, 30)
        self.darkness.setValue(int(printer_config.get("darkness", 15)))
        form.addRow("Darkness", self.darkness)

        self.speed = QSpinBox()
        self.speed.setRange(1, 14)
        self.speed.setValue(int(printer_config.get("speed", 3)))
        form.addRow("Velocidad", self.speed)

        self.offset_x = QDoubleSpinBox()
        self.offset_x.setRange(-20, 20)
        self.offset_x.setDecimals(1)
        self.offset_x.setValue(float(printer_config.get("offset_x_mm", 0)))
        form.addRow("Offset X (mm)", self.offset_x)

        self.offset_y = QDoubleSpinBox()
        self.offset_y.setRange(-20, 20)
        self.offset_y.setDecimals(1)
        self.offset_y.setValue(float(printer_config.get("offset_y_mm", 0)))
        form.addRow("Offset Y (mm)", self.offset_y)

        self.retries = QSpinBox()
        self.retries.setRange(0, 10)
        self.retries.setValue(int(printer_config.get("retries", 2)))
        form.addRow("Reintentos", self.retries)

        self.retry_delay = QDoubleSpinBox()
        self.retry_delay.setRange(0, 15)
        self.retry_delay.setDecimals(1)
        self.retry_delay.setValue(float(printer_config.get("retry_delay_sec", 1.0)))
        form.addRow("Delay reintento (s)", self.retry_delay)

        self.simulate = QCheckBox("Solo simulacion (guardar ZPL sin enviar)")
        self.simulate.setChecked(bool(printer_config.get("simulate_only", False)))
        form.addRow("Modo", self.simulate)

        root.addLayout(form)

        root.addWidget(
            QLabel(
                "Tip: usa 'Test de calibracion' para ajustar offsets y oscuridad antes de produccion."
            )
        )

        actions = QGridLayout()
        cancel_btn = QPushButton("Cancelar")
        test_btn = QPushButton("Test de calibracion")
        save_btn = QPushButton("Guardar")

        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        test_btn.clicked.connect(self._test)

        actions.addWidget(cancel_btn, 0, 0)
        actions.addWidget(test_btn, 0, 1)
        actions.addWidget(save_btn, 0, 2)
        root.addLayout(actions)

    def _load_printers(self, preferred: str) -> None:
        names = PrinterService.list_printers_windows()
        self.printer_name.clear()
        self.printer_name.addItems(names)

        if preferred:
            if preferred not in names:
                self.printer_name.addItem(preferred)
            self.printer_name.setCurrentText(preferred)

    def _test(self) -> None:
        cfg = self.result_config()
        ok, message = self._on_test_print(cfg)
        if ok:
            QMessageBox.information(self, "Calibracion", message)
        else:
            QMessageBox.warning(self, "Calibracion", message)

    def result_config(self) -> dict:
        return {
            "interface": self.interface.currentText(),
            "default_name": self.printer_name.currentText().strip(),
            "network_host": self.host.text().strip(),
            "network_port": int(self.port.value()),
            "darkness": int(self.darkness.value()),
            "speed": int(self.speed.value()),
            "offset_x_mm": float(self.offset_x.value()),
            "offset_y_mm": float(self.offset_y.value()),
            "retries": int(self.retries.value()),
            "retry_delay_sec": float(self.retry_delay.value()),
            "simulate_only": self.simulate.isChecked(),
        }
