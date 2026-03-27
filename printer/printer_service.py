from __future__ import annotations

import socket
from pathlib import Path


class PrinterService:
    @staticmethod
    def list_printers_windows() -> list[str]:
        try:
            import win32print  # type: ignore

            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            return [p[2] for p in win32print.EnumPrinters(flags)]
        except Exception:
            return []

    @staticmethod
    def send_raw_windows(printer_name: str, payload: str) -> None:
        import win32print  # type: ignore

        h = win32print.OpenPrinter(printer_name)
        try:
            job = win32print.StartDocPrinter(h, 1, ("Facturado Sticker Job", None, "RAW"))
            try:
                win32print.StartPagePrinter(h)
                win32print.WritePrinter(h, payload.encode("utf-8"))
                win32print.EndPagePrinter(h)
            finally:
                win32print.EndDocPrinter(h)
        finally:
            win32print.ClosePrinter(h)

    @staticmethod
    def send_raw_network(host: str, port: int, payload: str) -> None:
        with socket.create_connection((host, port), timeout=8) as s:
            s.sendall(payload.encode("utf-8"))

    @staticmethod
    def save_zpl_copy(directory: str, filename: str, payload: str) -> str:
        p = Path(directory)
        p.mkdir(parents=True, exist_ok=True)
        out = p / filename
        out.write_text(payload, encoding="utf-8")
        return str(out)
