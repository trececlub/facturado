from __future__ import annotations

from dataclasses import dataclass, field

from utils.zpl_image import photo_to_gfa_for_template


@dataclass
class PrintEngine:
    dpi: int = 203
    printer_profile: dict = field(default_factory=dict)

    @staticmethod
    def _escape(value: str) -> str:
        return value.replace("^", " ").replace("~", " ")

    def mm_to_dots(self, mm: float) -> int:
        return int((mm / 25.4) * self.dpi)

    def _printer_setup_lines(self) -> list[str]:
        profile = self.printer_profile or {}

        offset_x_mm = float(profile.get("offset_x_mm", 0))
        offset_y_mm = float(profile.get("offset_y_mm", 0))
        darkness = int(profile.get("darkness", 15))
        speed = int(profile.get("speed", 3))

        darkness = max(-30, min(30, darkness))
        speed = max(1, min(14, speed))

        offset_x = self.mm_to_dots(offset_x_mm)
        offset_y = self.mm_to_dots(offset_y_mm)

        return [f"^LH{offset_x},{offset_y}", f"^MD{darkness}", f"^PR{speed}"]

    def generate_calibration_zpl(self, template: dict, note: str = "CALIBRACION") -> str:
        width = self.mm_to_dots(template.get("width_mm", 100))
        height = self.mm_to_dots(template.get("height_mm", 60))

        lines = ["^XA", "^CI28", f"^PW{width}", f"^LL{height}"]
        lines.extend(self._printer_setup_lines())

        lines.extend(
            [
                f"^FO0,0^GB{width},{height},2^FS",
                f"^FO20,20^A0N,38,30^FD{self._escape(note)}^FS",
                f"^FO20,70^A0N,26,22^FDSIZE: {template.get('width_mm')}x{template.get('height_mm')}mm^FS",
                "^FO20,110^A0N,24,20^FDCruces de referencia:^FS",
                f"^FO10,10^GB20,2,2^FS",
                f"^FO10,10^GB2,20,2^FS",
                f"^FO{width-30},10^GB20,2,2^FS",
                f"^FO{width-10},10^GB2,20,2^FS",
                f"^FO10,{height-10}^GB20,2,2^FS",
                f"^FO10,{height-30}^GB2,20,2^FS",
                f"^FO{width-30},{height-10}^GB20,2,2^FS",
                f"^FO{width-10},{height-30}^GB2,20,2^FS",
                "^XZ",
            ]
        )
        return "\n".join(lines)

    def generate_zpl(self, record: dict, template: dict) -> str:
        width = self.mm_to_dots(template.get("width_mm", 100))
        height = self.mm_to_dots(template.get("height_mm", 60))

        h = template["header"]
        lf = template["left_fields"]
        photo = template["photo"]
        bc = template["barcode"]
        qr = template.get("qr", {"enabled": False})

        lines = ["^XA", "^CI28", f"^PW{width}", f"^LL{height}"]
        lines.extend(self._printer_setup_lines())

        hx, hy = self.mm_to_dots(h["x_mm"]), self.mm_to_dots(h["y_mm"])
        hw, hh = self.mm_to_dots(h["w_mm"]), self.mm_to_dots(h["h_mm"])
        lines += [
            f"^FO{hx},{hy}^GB{hw},{hh},{hh},B,0^FS",
            f"^FO{hx + 8},{hy + 6}^A0N,34,28^FR^FD{self._escape(h.get('company_name', ''))}^FS",
            f"^FO{hx + 8},{hy + 40}^A0N,24,20^FR^FD{self._escape(h.get('subtitle', ''))}^FS",
        ]

        fields = [
            ("Nombre", record.get("nombre", "")),
            ("Apellido", record.get("apellido", "")),
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

        if photo.get("enabled", True):
            px, py = self.mm_to_dots(photo["x_mm"]), self.mm_to_dots(photo["y_mm"])
            pw, ph = self.mm_to_dots(photo["w_mm"]), self.mm_to_dots(photo["h_mm"])
            lines.append(f"^FO{px},{py}^GB{pw},{ph},2^FS")

            image_path = record.get("foto_path", "").strip()
            print_photo = bool(photo.get("print_real_image", True))
            if image_path and print_photo:
                try:
                    gfa = photo_to_gfa_for_template(image_path, photo, self.dpi)
                    lines.append(f"^FO{px},{py}{gfa}^FS")
                except Exception:
                    lines.append(f"^FO{px + 10},{py + int(ph/2)}^A0N,22,20^FDIMG ERR^FS")
            else:
                lines.append(f"^FO{px + 10},{py + int(ph/2)}^A0N,22,20^FDIMAGEN^FS")

        if bc.get("enabled", True):
            bcx, bcy = self.mm_to_dots(bc["x_mm"]), self.mm_to_dots(bc["y_mm"])
            bch = self.mm_to_dots(bc["h_mm"])
            barcode_val = self._escape(record.get("barcode", "000000"))
            show_text = "Y" if bc.get("show_human_readable", True) else "N"
            lines += [
                "^BY2,2,70",
                f"^FO{bcx},{bcy}^BCN,{bch},{show_text},N,N^FD{barcode_val}^FS",
            ]

        if qr.get("enabled", False) and record.get("qr"):
            qx, qy = self.mm_to_dots(qr["x_mm"]), self.mm_to_dots(qr["y_mm"])
            qd = self._escape(record.get("qr", ""))
            qr_scale = int(max(1, min(10, qr.get("scale", 4))))
            lines.append(f"^FO{qx},{qy}^BQN,2,{qr_scale}^FDLA,{qd}^FS")

        lines.append("^XZ")
        return "\n".join(lines)
