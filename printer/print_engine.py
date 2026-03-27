from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PrintEngine:
    dpi: int = 203

    @staticmethod
    def _escape(value: str) -> str:
        return value.replace("^", " ").replace("~", " ")

    def mm_to_dots(self, mm: float) -> int:
        return int((mm / 25.4) * self.dpi)

    def generate_zpl(self, record: dict, template: dict) -> str:
        width = self.mm_to_dots(template.get("width_mm", 100))
        height = self.mm_to_dots(template.get("height_mm", 60))

        h = template["header"]
        lf = template["left_fields"]
        photo = template["photo"]
        bc = template["barcode"]
        qr = template.get("qr", {"enabled": False})

        lines = ["^XA", "^CI28", f"^PW{width}", f"^LL{height}", "^LH0,0"]

        # Header block
        hx, hy = self.mm_to_dots(h["x_mm"]), self.mm_to_dots(h["y_mm"])
        hw, hh = self.mm_to_dots(h["w_mm"]), self.mm_to_dots(h["h_mm"])
        lines += [
            f"^FO{hx},{hy}^GB{hw},{hh},{hh},B,0^FS",
            f"^FO{hx + 8},{hy + 6}^A0N,34,28^FR^FD{self._escape(h.get('company_name', ''))}^FS",
            f"^FO{hx + 8},{hy + 40}^A0N,24,20^FR^FD{self._escape(h.get('subtitle', ''))}^FS",
        ]

        # Left fields
        fields = [
            ("Nombre", record.get("nombre", "")),
            ("Segundo", record.get("apellido", "")),
            ("Cargo", record.get("cargo", "")),
            ("ID", record.get("id_interno", "")),
            ("Fecha", record.get("fecha", "")),
            ("Sede", record.get("sede", "")),
            ("Obs", record.get("observaciones", "")),
        ]
        base_x = self.mm_to_dots(lf["x_mm"])
        base_y = self.mm_to_dots(lf["y_mm"])
        step = self.mm_to_dots(lf["line_height_mm"])

        for idx, (label, value) in enumerate(fields):
            y = base_y + idx * step
            lines.append(
                f"^FO{base_x},{y}^A0N,24,20^FD{self._escape(label)}: {self._escape(str(value))}^FS"
            )

        # Photo placeholder (frame only)
        if photo.get("enabled", True):
            px, py = self.mm_to_dots(photo["x_mm"]), self.mm_to_dots(photo["y_mm"])
            pw, ph = self.mm_to_dots(photo["w_mm"]), self.mm_to_dots(photo["h_mm"])
            lines += [
                f"^FO{px},{py}^GB{pw},{ph},2^FS",
                f"^FO{px + 10},{py + int(ph/2)}^A0N,22,20^FDIMAGEN^FS",
            ]

        # Barcode
        if bc.get("enabled", True):
            bcx, bcy = self.mm_to_dots(bc["x_mm"]), self.mm_to_dots(bc["y_mm"])
            bch = self.mm_to_dots(bc["h_mm"])
            barcode_val = self._escape(record.get("barcode", "000000"))
            lines += [
                "^BY2,2,70",
                f"^FO{bcx},{bcy}^BCN,{bch},Y,N,N^FD{barcode_val}^FS",
            ]

        # QR
        if qr.get("enabled", False) and record.get("qr"):
            qx, qy = self.mm_to_dots(qr["x_mm"]), self.mm_to_dots(qr["y_mm"])
            qd = self._escape(record.get("qr", ""))
            lines.append(f"^FO{qx},{qy}^BQN,2,4^FDLA,{qd}^FS")

        lines.append("^XZ")
        return "\n".join(lines)
