from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps


def _mm_to_dots(mm: float, dpi: int) -> int:
    return max(1, int((mm / 25.4) * dpi))


def image_to_gfa_hex(
    image_path: str,
    width_dots: int,
    height_dots: int,
    threshold: int = 150,
    invert: bool = False,
) -> tuple[int, int, str]:
    img = Image.open(image_path).convert("L")
    img = ImageOps.fit(img, (width_dots, height_dots), Image.Resampling.LANCZOS)

    if invert:
        img = ImageOps.invert(img)

    img = img.point(lambda p: 255 if p > threshold else 0, mode="1")

    width, height = img.size
    bytes_per_row = (width + 7) // 8
    total_bytes = bytes_per_row * height

    pixels = img.load()
    hex_rows: list[str] = []

    for y in range(height):
        row_bytes = bytearray()
        for bx in range(bytes_per_row):
            byte = 0
            for bit in range(8):
                x = bx * 8 + bit
                if x < width:
                    pixel = pixels[x, y]
                    # In mode 1, 0 is black and 255 is white.
                    if pixel == 0:
                        byte |= 1 << (7 - bit)
            row_bytes.append(byte)
        hex_rows.append("".join(f"{b:02X}" for b in row_bytes))

    return total_bytes, bytes_per_row, "".join(hex_rows)


def image_to_gfa_command(
    image_path: str,
    width_dots: int,
    height_dots: int,
    threshold: int = 150,
    invert: bool = False,
) -> str:
    total, row_bytes, data_hex = image_to_gfa_hex(
        image_path=image_path,
        width_dots=width_dots,
        height_dots=height_dots,
        threshold=threshold,
        invert=invert,
    )
    return f"^GFA,{total},{total},{row_bytes},{data_hex}"


def photo_to_gfa_for_template(photo_path: str, photo_cfg: dict, dpi: int) -> str:
    if not photo_path or not Path(photo_path).exists():
        raise FileNotFoundError(f"Imagen no encontrada: {photo_path}")

    width = _mm_to_dots(float(photo_cfg["w_mm"]), dpi)
    height = _mm_to_dots(float(photo_cfg["h_mm"]), dpi)

    threshold = int(photo_cfg.get("threshold", 150))
    invert = bool(photo_cfg.get("invert", False))

    return image_to_gfa_command(photo_path, width, height, threshold=threshold, invert=invert)
