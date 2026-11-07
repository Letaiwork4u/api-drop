"""
Generate the app icons from logo_icon_mint.svg.

    pip install PyQt6 pillow
    python tools/make_icons.py

Writes assets/icons/ApiDrop.icns (macOS), ApiDrop.ico (Windows) and
apidrop_512.png (Linux / window icon). The generated files are committed,
so the CI build only needs them, not this script.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402
from PyQt6.QtCore import QRectF, Qt  # noqa: E402
from PyQt6.QtGui import QBrush, QColor, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath, QPen  # noqa: E402
from PyQt6.QtSvg import QSvgRenderer  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "icons"
SIZE = 1024


def render_master() -> QImage:
    img = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # macOS Big Sur style: 824 px rounded square centred on a 1024 canvas
    inset = (SIZE - 824) / 2
    tile = QRectF(inset, inset, 824, 824)
    path = QPainterPath()
    path.addRoundedRect(tile, 185, 185)
    grad = QLinearGradient(tile.topLeft(), tile.bottomLeft())
    grad.setColorAt(0.0, QColor("#f6fafb"))
    grad.setColorAt(1.0, QColor("#d9e5e8"))
    p.fillPath(path, QBrush(grad))
    p.setPen(QPen(QColor("#c5d5d9"), 4))
    p.drawPath(path)

    # logo (380x200 viewBox) scaled to ~88 % of the tile width
    svg = QSvgRenderer(str(ROOT / "logo_icon_mint.svg"))
    w = 824 * 0.88
    h = w * 200 / 380
    svg.render(p, QRectF((SIZE - w) / 2, (SIZE - h) / 2, w, h))
    p.end()
    return img


def main() -> int:
    app = QGuiApplication(sys.argv)  # noqa: F841 (must stay alive while rendering)
    OUT.mkdir(parents=True, exist_ok=True)
    master_png = OUT / "apidrop_1024.png"
    render_master().save(str(master_png))
    im = Image.open(master_png).convert("RGBA")
    im.resize((512, 512), Image.LANCZOS).save(OUT / "apidrop_512.png")
    im.save(OUT / "ApiDrop.icns")
    im.save(OUT / "ApiDrop.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    master_png.unlink()
    print("icons written to", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
