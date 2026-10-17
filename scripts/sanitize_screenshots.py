"""Create public, sanitized copies of real TecnoHead Solar screenshots.

The source screenshots stay outside the repository in the local temporary
directory. This script only publishes layout/status evidence and deliberately
covers customer-specific network, serial, location and JSON payload values.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(tempfile.gettempdir())
OUTPUT_DIR = ROOT / "docs" / "screenshots"
VERSION = "0.1.13"


def font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def cover(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], label: str) -> None:
    draw.rounded_rectangle(box, radius=8, fill=(7, 39, 49), outline=(25, 196, 190), width=2)
    left, top, right, bottom = box
    draw.text((left + 12, top + max(4, (bottom - top - 16) // 2)), label, fill=(119, 230, 218), font=font(15))


def sanitize(source_name: str, output_name: str, boxes: list[tuple[int, int, int, int, str]]) -> None:
    source = SOURCE_DIR / source_name
    if not source.exists():
        raise FileNotFoundError(f"Missing real screenshot: {source}")
    image = Image.open(source).convert("RGB")
    draw = ImageDraw.Draw(image)
    for left, top, right, bottom, label in boxes:
        cover(draw, (left, top, right, bottom), label)
    draw.rectangle((0, 0, image.width, 32), fill=(4, 25, 33))
    draw.text((16, 8), f"Evidência real · publicação sanitizada · TecnoHead Solar {VERSION}", fill=(119, 230, 218), font=font(14))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_DIR / output_name, optimize=True)


def main() -> None:
    sanitize(
        "tecnohead-solar-overview-0.1.13.png",
        f"overview-{VERSION}.png",
        [],
    )
    sanitize(
        "tecnohead-solar-collectors-0.1.13.png",
        f"collectors-{VERSION}.png",
        [
            (640, 280, 1080, 304, "identidade local sanitizada"),
            (1260, 280, 1700, 304, "identidade local sanitizada"),
            (640, 539, 1080, 563, "identidade local sanitizada"),
            (1260, 539, 1700, 563, "identidade local sanitizada"),
            (640, 798, 1080, 822, "identidade local sanitizada"),
        ],
    )
    sanitize(
        "tecnohead-solar-map-0.1.13.png",
        f"map-{VERSION}.png",
        [],
    )
    sanitize(
        "tecnohead-solar-diagnostics-0.1.13.png",
        f"diagnostics-{VERSION}.png",
        [
            (590, 284, 1060, 316, "serial sanitizado"),
            (590, 360, 1060, 392, "serial sanitizado"),
            (590, 436, 1060, 468, "serial sanitizado"),
            (590, 512, 1060, 544, "serial sanitizado"),
            (590, 588, 1060, 620, "serial sanitizado"),
            (590, 660, 1815, 855, "evidência JSON sanitizada"),
        ],
    )
    sanitize(
        "tecnohead-solar-history-0.1.13.png",
        f"history-{VERSION}.png",
        [],
    )
    sanitize(
        "tecnohead-solar-settings-0.1.13.png",
        f"settings-{VERSION}.png",
        [
            (585, 255, 1420, 852, "dados da instalação sanitizados"),
            (1450, 250, 1850, 465, "endpoint e token sanitizados"),
        ],
    )
    sanitize(
        "tecnohead-solar-installation-0.1.13.png",
        f"installation-{VERSION}.png",
        [(1210, 530, 1675, 580, "identificador do host sanitizado")],
    )
    sanitize(
        "tecnohead-solar-installation-update-0.1.13.png",
        f"installation-update-{VERSION}.png",
        [],
    )


if __name__ == "__main__":
    main()
