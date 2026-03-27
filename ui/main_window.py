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
from printer.queue_service import PrintQueueService
from templates.template_manager import TemplateManager
from ui.calibration_dialog import CalibrationDialog
from ui.form_panel import FormPanel
from ui.preview_widget import StickerPreviewWidget
from ui.template_designer_dialog import TemplateDesignerDialog
from ui.template_editor_dialog import TemplateEditorDialog
from utils.code_generator import ensure_codes
from utils.config_loader import load_config, load_raw_config, save_raw_config
from utils.importer import import_records
from utils.validators import validate_record


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()

        self.setWindowTitle(self.config["app_name"])
        self.resize(1300, 790)

        self.template_manager = TemplateManager(self.config["default_template"])
        self.template = self.template_manager.load()

        raw_cfg = load_raw_config()
        self.printer_cfg = dict(raw_cfg.get("printer", {}))
        self.print_engine = PrintEngine(
            dpi=int(self.template.get("dpi", 203)),
            printer_profile=self.printer_cfg,
        )

        self.history = HistoryService(self.config["history_file"])
        self.record_store = RecordStore(self.config["records_file"])
        self.queue = PrintQueueService(self.config["queue_file"])
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
            ("Editor plantilla", self.edit_template),
            ("Disenador visual", self.design_template),
            ("Importar CSV/Excel", self.import_file),
            ("Generar codigo", self.generate_codes),
            ("Calibrar impresora", self.calibrate_printer),
            ("Imprimir", self.print_single),
            ("Impresion por lote", self.print_batch),
            ("Procesar cola", self.process_queue),
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

    def _template_name(self) -> str:
        return str(self.template.get("name", Path(self.config["default_template"]).name))

    def _send_payload(self, payload: str, cfg: dict | None = None) -> None:
        profile = cfg or self.printer_cfg

        if bool(profile.get("simulate_only", False)):
            return

        interface = profile.get("interface", "usb")
        if interface == "network" and profile.get("network_host"):
            PrinterService.send_raw_network(
                profile["network_host"],
                int(profile.get("network_port", 9100)),
                payload,
            )
            return

        printer_name = profile.get("default_name", "")
        if not printer_name:
            raise RuntimeError("No hay impresora configurada. Define printer.default_name")

        PrinterService.send_raw_windows(printer_name, payload)

    def _enqueue(self, record: dict, source: str) -> tuple[str, str, str]:
        zpl = self.print_engine.generate_zpl(record, self.template)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zpl_file = PrinterService.save_zpl_copy(
            self.config["zpl_output_dir"],
            f"{source}_{timestamp}_{record.get('id_interno', 'NA')}.zpl",
            zpl,
        )
        job_id = self.queue.enqueue(record, zpl, source=source)
        return job_id, zpl_file, zpl

    def _job_by_id(self, job_id: str) -> dict | None:
        for job in self.queue.list_jobs(limit=1000):
            if job.get("job_id") == job_id:
                return job
        return None

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
        self.print_engine.dpi = int(self.template.get("dpi", 203))
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

    def design_template(self) -> None:
        dlg = TemplateDesignerDialog(self.template, self)
        if dlg.exec() != dlg.Accepted:
            return

        self.template = dlg.result_template()
        self._update_preview(self._current_record())

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar plantilla disenada",
            "templates/corporate_designed.json",
            "JSON (*.json)",
        )
        if path:
            self.template_manager.save(self.template, path)
            self.status.setText(f"Plantilla disenada guardada: {Path(path).name}")

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

    def _test_print(self, cfg: dict) -> tuple[bool, str]:
        try:
            test_engine = PrintEngine(dpi=int(self.template.get("dpi", 203)), printer_profile=cfg)
            zpl = test_engine.generate_calibration_zpl(self.template, note="TEST CALIBRACION")
            zpl_file = PrinterService.save_zpl_copy(
                self.config["zpl_output_dir"],
                f"calibration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zpl",
                zpl,
            )
            self._send_payload(zpl, cfg)
            return True, f"Test enviado correctamente. ZPL: {zpl_file}"
        except Exception as e:
            return False, f"No se pudo enviar test: {e}"

    def calibrate_printer(self) -> None:
        dlg = CalibrationDialog(self.printer_cfg, self._test_print, self)
        if dlg.exec() != dlg.Accepted:
            return

        self.printer_cfg = dlg.result_config()
        raw = load_raw_config()
        raw["printer"] = self.printer_cfg
        save_raw_config(raw)

        self.print_engine.printer_profile = self.printer_cfg
        self.status.setText("Configuracion de impresora guardada")

    def print_single(self) -> None:
        record = ensure_codes(self._current_record())
        self.form_panel.set_data(record)

        errors = validate_record(record)
        if errors:
            QMessageBox.warning(self, "Validacion", "\n".join(errors))
            return

        job_id, zpl_file, zpl_payload = self._enqueue(record, source="single")
        sent, failed = self.queue.process(
            sender=lambda payload: self._send_payload(payload),
            retries=int(self.printer_cfg.get("retries", 2)),
            retry_delay_sec=float(self.printer_cfg.get("retry_delay_sec", 1.0)),
        )

        job = self._job_by_id(job_id) or {}
        status = job.get("status", "unknown")
        printer_name = self.printer_cfg.get("default_name", self.printer_cfg.get("network_host", ""))

        self.history.add(
            "print_single",
            record,
            status,
            message=f"queue={job_id} zpl={zpl_file}",
            printer_name=printer_name,
            template_name=self._template_name(),
            zpl_payload=zpl_payload,
            queue_id=job_id,
            extra={"queue_sent": sent, "queue_failed": failed},
        )

        if status == "sent":
            self.status.setText("Etiqueta enviada a impresora")
        else:
            err = job.get("last_error", "Error desconocido")
            self.status.setText("Error en cola de impresion")
            QMessageBox.warning(
                self,
                "Impresion",
                f"No se pudo imprimir.\nEstado: {status}\nDetalle: {err}\n\nCopia ZPL: {zpl_file}",
            )

    def print_batch(self) -> None:
        if not self.imported_records:
            QMessageBox.information(self, "Lote", "Primero importa un CSV o Excel para lote.")
            return

        queued: list[tuple[str, dict, str]] = []
        invalid = 0

        for raw_record in self.imported_records:
            record = ensure_codes(raw_record)
            errors = validate_record(record)
            if errors:
                invalid += 1
                self.history.add(
                    "print_batch",
                    record,
                    "invalid",
                    message="; ".join(errors),
                    template_name=self._template_name(),
                )
                continue

            job_id, _, zpl_payload = self._enqueue(record, source="batch")
            queued.append((job_id, record, zpl_payload))

        sent, failed = self.queue.process(
            sender=lambda payload: self._send_payload(payload),
            retries=int(self.printer_cfg.get("retries", 2)),
            retry_delay_sec=float(self.printer_cfg.get("retry_delay_sec", 1.0)),
        )

        printer_name = self.printer_cfg.get("default_name", self.printer_cfg.get("network_host", ""))
        for job_id, record, zpl_payload in queued:
            job = self._job_by_id(job_id) or {}
            self.history.add(
                "print_batch",
                record,
                job.get("status", "unknown"),
                message=job.get("last_error", ""),
                printer_name=printer_name,
                template_name=self._template_name(),
                zpl_payload=zpl_payload,
                queue_id=job_id,
            )

        self.status.setText(f"Lote terminado. Enviadas={sent}, Fallidas={failed}, Invalidas={invalid}")
        QMessageBox.information(
            self,
            "Lote",
            f"Lote finalizado.\nEnviadas: {sent}\nFallidas: {failed}\nInvalidas: {invalid}",
        )

    def process_queue(self) -> None:
        sent, failed = self.queue.process(
            sender=lambda payload: self._send_payload(payload),
            retries=int(self.printer_cfg.get("retries", 2)),
            retry_delay_sec=float(self.printer_cfg.get("retry_delay_sec", 1.0)),
        )
        self.status.setText(f"Cola procesada. Enviadas={sent}, Fallidas={failed}")
        QMessageBox.information(self, "Cola", f"Cola procesada.\nEnviadas: {sent}\nFallidas: {failed}")

    def show_history(self) -> None:
        rows = self.history.list_all()
        if not rows:
            QMessageBox.information(self, "Historial", "No hay historial aun.")
            return

        lines = []
        for r in rows[-30:]:
            audit = r.get("audit", {})
            lines.append(
                f"[{r['timestamp']}] {r['action']} -> {r['status']} | "
                f"printer={audit.get('printer', '')} user={audit.get('user', '')} "
                f"queue={audit.get('queue_id', '')}"
            )

        QMessageBox.information(self, "Historial (ultimos 30)", "\n".join(lines))


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
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
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
