from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from data.history_service import HistoryService
from data.record_store import RecordStore
from printer.print_engine import PrintEngine
from printer.printer_service import PrinterService
from templates.template_manager import TemplateManager
from ui.form_panel import FormPanel
from ui.preview_widget import StickerPreviewWidget
from ui.template_editor_dialog import TemplateEditorDialog
from utils.code_generator import ensure_codes
from utils.config_loader import load_config
from utils.importer import import_records
from utils.validators import validate_record


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()

        self.setWindowTitle(self.config["app_name"])
        self.resize(1220, 760)

        self.template_manager = TemplateManager(self.config["default_template"])
        self.template = self.template_manager.load()
        self.print_engine = PrintEngine(self.template.get("dpi", 203))

        self.history = HistoryService(self.config["history_file"])
        self.record_store = RecordStore(self.config["records_file"])
        self.imported_records: list[dict] = []

        self.form_panel = FormPanel()
        self.preview = StickerPreviewWidget()

        self._build_ui()

        initial = {
            "fecha": datetime.now().strftime("%Y-%m-%d"),
        }
        self.form_panel.set_data(initial)
        self._update_preview(self.form_panel.data())

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        toolbar = QHBoxLayout()
        buttons = [
            ("Nuevo", self.new_record),
            ("Guardar", self.save_record),
            ("Cargar plantilla", self.load_template),
            ("Editar plantilla", self.edit_template),
            ("Importar CSV/Excel", self.import_file),
            ("Generar codigo", self.generate_codes),
            ("Imprimir", self.print_single),
            ("Impresion por lote", self.print_batch),
            ("Ver historial", self.show_history),
        ]

        for text, callback in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            toolbar.addWidget(btn)

        self.status = QLabel("Listo")
        self.status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        toolbar.addWidget(self.status, 1)
        layout.addLayout(toolbar)

        splitter = QSplitter()
        splitter.addWidget(self.form_panel)
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)

        self.form_panel.changed.connect(self._update_preview)

    def _update_preview(self, data: dict) -> None:
        self.preview.update_payload(self.template, data)

    def _current_record(self) -> dict:
        return self.form_panel.data()

    def new_record(self) -> None:
        self.form_panel.set_data({"fecha": datetime.now().strftime("%Y-%m-%d")})
        self.status.setText("Nuevo registro")

    def save_record(self) -> None:
        record = self._current_record()
        errors = validate_record(record)
        if errors:
            QMessageBox.warning(self, "Validacion", "\n".join(errors))
            return

        self.record_store.save(record)
        self.status.setText("Registro guardado en data/records.json")

    def load_template(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Cargar plantilla", "templates", "JSON (*.json)")
        if not path:
            return

        self.template = self.template_manager.load(path)
        self._update_preview(self._current_record())
        self.status.setText(f"Plantilla cargada: {Path(path).name}")

    def edit_template(self) -> None:
        dlg = TemplateEditorDialog(self.template, self)
        if dlg.exec() != dlg.Accepted:
            return

        self.template = dlg.result_template()
        self._update_preview(self._current_record())

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar plantilla",
            "templates/corporate_custom.json",
            "JSON (*.json)",
        )
        if path:
            self.template_manager.save(self.template, path)
            self.status.setText(f"Plantilla guardada: {Path(path).name}")

    def import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar CSV/Excel",
            "",
            "Datos (*.csv *.xlsx)",
        )
        if not path:
            return

        try:
            self.imported_records = import_records(path)
        except Exception as e:
            QMessageBox.critical(self, "Importacion", str(e))
            return

        if self.imported_records:
            self.form_panel.set_data(self.imported_records[0])
        self.status.setText(f"Importados {len(self.imported_records)} registros")

    def generate_codes(self) -> None:
        record = ensure_codes(self._current_record())
        self.form_panel.set_data(record)
        self.status.setText("Codigo de barras y QR generados")

    def _build_zpl(self, record: dict) -> str:
        return self.print_engine.generate_zpl(record, self.template)

    def print_single(self) -> None:
        record = ensure_codes(self._current_record())
        self.form_panel.set_data(record)

        errors = validate_record(record)
        if errors:
            QMessageBox.warning(self, "Validacion", "\n".join(errors))
            return

        zpl = self._build_zpl(record)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zpl_file = PrinterService.save_zpl_copy(
            self.config["zpl_output_dir"], f"single_{timestamp}.zpl", zpl
        )

        try:
            printer_cfg = self.config.get("printer", {})
            interface = printer_cfg.get("interface", "usb")
            if interface == "network" and printer_cfg.get("network_host"):
                PrinterService.send_raw_network(
                    printer_cfg["network_host"], int(printer_cfg.get("network_port", 9100)), zpl
                )
            elif printer_cfg.get("default_name"):
                PrinterService.send_raw_windows(printer_cfg["default_name"], zpl)
            else:
                raise RuntimeError(
                    "No hay impresora configurada. Ajusta config/app_config.json (printer.default_name)."
                )

            self.history.add("print_single", record, "ok", zpl_file)
            self.status.setText("Etiqueta enviada a impresora")
        except Exception as e:
            self.history.add("print_single", record, "error", str(e))
            QMessageBox.warning(
                self,
                "Impresion",
                f"No se pudo imprimir en RAW.\nDetalle: {e}\n\nSe guardo copia ZPL en:\n{zpl_file}",
            )
            self.status.setText("Error al imprimir (se guardo ZPL)")

    def print_batch(self) -> None:
        if not self.imported_records:
            QMessageBox.information(self, "Lote", "Primero importa un CSV o Excel para lote.")
            return

        ok = 0
        failed = 0
        printer_cfg = self.config.get("printer", {})

        for i, raw_record in enumerate(self.imported_records, start=1):
            record = ensure_codes(raw_record)
            errors = validate_record(record)
            if errors:
                failed += 1
                self.history.add("print_batch", record, "error", "; ".join(errors))
                continue

            zpl = self._build_zpl(record)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            PrinterService.save_zpl_copy(
                self.config["zpl_output_dir"], f"batch_{i}_{ts}.zpl", zpl
            )

            try:
                interface = printer_cfg.get("interface", "usb")
                if interface == "network" and printer_cfg.get("network_host"):
                    PrinterService.send_raw_network(
                        printer_cfg["network_host"], int(printer_cfg.get("network_port", 9100)), zpl
                    )
                elif printer_cfg.get("default_name"):
                    PrinterService.send_raw_windows(printer_cfg["default_name"], zpl)
                else:
                    raise RuntimeError("Impresora no configurada")

                ok += 1
                self.history.add("print_batch", record, "ok", "printed")
            except Exception as e:
                failed += 1
                self.history.add("print_batch", record, "error", str(e))

        self.status.setText(f"Lote terminado. OK={ok}, Error={failed}")
        QMessageBox.information(self, "Lote", f"Impresion por lote finalizada.\nOK: {ok}\nError: {failed}")

    def show_history(self) -> None:
        rows = self.history.list_all()
        if not rows:
            QMessageBox.information(self, "Historial", "No hay historial aun.")
            return

        text = "\n".join(
            f"[{r['timestamp']}] {r['action']} -> {r['status']} ({r.get('message', '')})"
            for r in rows[-20:]
        )
        QMessageBox.information(self, "Historial (ultimos 20)", text)


def _load_stylesheet() -> str:
    return """
    QWidget {
        background-color: #131820;
        color: #dce6f2;
        font-family: Segoe UI;
        font-size: 12px;
    }
    QGroupBox {
        border: 1px solid #2a3342;
        border-radius: 8px;
        margin-top: 8px;
        padding-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px;
        color: #92abc8;
    }
    QLineEdit, QTextEdit {
        background: #0d1117;
        border: 1px solid #2a3342;
        border-radius: 5px;
        padding: 6px;
        color: #e5edf8;
    }
    QPushButton {
        background: #215a93;
        border: none;
        border-radius: 6px;
        padding: 8px 10px;
        color: white;
    }
    QPushButton:hover {
        background: #2b6ba9;
    }
    QPushButton:pressed {
        background: #1c4e80;
    }
    QLabel {
        color: #9eb3cc;
    }
    """


def run_app() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(_load_stylesheet())
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
