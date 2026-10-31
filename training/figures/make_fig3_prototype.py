"""Rebuild Figure 3 (the assembled prototype) with consistent labels.

The photograph itself is the 1800x1200 original kept in
Docs/old_docs/Research_paper.docx, which is 2.4x the resolution of the copy
that was in the manuscript. Its leader lines are part of the pixels, so they
are preserved and simply continued into the margin, where this script redraws
every label as crisp text with consistent wording ("5 V pump", "5 V relay",
"Green LED"), replacing the mixed "5v PUMP" / "5V Relay" / "Green Led" forms.

Note the photographic content is at its native 1138 px across; only the canvas
is larger. A genuinely higher-resolution figure needs the prototype to be
re-photographed.

Usage:  python training/figures/make_fig3_prototype.py [outdir]
"""

import io
import os
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont
import matplotlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DOCX = os.path.join(ROOT, "Docs", "old_docs", "Research_paper.docx")
SRC_MEMBER = "word/media/image4.jpg"

# Bounding box of the photograph inside the 1800x1200 composite.
CROP = (314, 143, 1452, 996)

PAD_L, PAD_R, PAD_T, PAD_B = 470, 470, 120, 260
STUB = 26                     # length of the connector stub in the margin
INK = (17, 24, 39)
LINE = (0, 0, 0)

# Where each baked-in leader line meets the edge of the photograph,
# in photograph-relative pixels, and the label that belongs to it.
RIGHT = [(114, "5 V relay module"),
         (288, "ESP32-WROOM-32"),
         (613, "5 V pump")]
LEFT = [(452, "5 V external supply\n(power bank)"),
        (736, "Red LED – system power")]
TOP = [(528, "Green LED – pump status")]
# The two bottom leaders leave the photograph only 231 px apart, so each is
# bent out to a well-separated label anchor (third item = anchor x).
BOTTOM = [(568, "DHT11 temperature\nand humidity sensor", 200),
          (799, "Capacitive soil moisture\nsensor v1.2", 1000)]


def _font(size):
    path = os.path.join(os.path.dirname(matplotlib.__file__),
                        "mpl-data", "fonts", "ttf", "DejaVuSans.ttf")
    return ImageFont.truetype(path, size)


def _multiline(draw, xy, text, font, anchor_x, line_h):
    """Draw possibly multi-line text; anchor_x is 'l', 'r' or 'c'."""
    lines = text.split("\n")
    x, y_mid = xy
    y = y_mid - (len(lines) - 1) * line_h / 2.0
    for ln in lines:
        w = draw.textbbox((0, 0), ln, font=font)[2]
        if anchor_x == "r":
            dx = -w
        elif anchor_x == "c":
            dx = -w / 2.0
        else:
            dx = 0
        draw.text((x + dx, y), ln, font=font, fill=INK, anchor="lm")
        y += line_h


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "figures")
    os.makedirs(outdir, exist_ok=True)

    with zipfile.ZipFile(SRC_DOCX) as z:
        photo = Image.open(io.BytesIO(z.read(SRC_MEMBER))).convert("RGB").crop(CROP)
    pw, ph = photo.size

    W, H = PAD_L + pw + PAD_R, PAD_T + ph + PAD_B
    canvas = Image.new("RGB", (W, H), "white")
    canvas.paste(photo, (PAD_L, PAD_T))
    d = ImageDraw.Draw(canvas)

    font = _font(30)
    line_h = 38
    lw = 3

    for y, text in RIGHT:
        yy = PAD_T + y
        d.line([(PAD_L + pw, yy), (PAD_L + pw + STUB, yy)], fill=LINE, width=lw)
        _multiline(d, (PAD_L + pw + STUB + 14, yy), text, font, "l", line_h)

    for y, text in LEFT:
        yy = PAD_T + y
        d.line([(PAD_L - STUB, yy), (PAD_L, yy)], fill=LINE, width=lw)
        _multiline(d, (PAD_L - STUB - 14, yy), text, font, "r", line_h)

    for x, text in TOP:
        xx = PAD_L + x
        d.line([(xx, PAD_T - STUB), (xx, PAD_T)], fill=LINE, width=lw)
        _multiline(d, (xx, PAD_T - STUB - 32), text, font, "c", line_h)

    for x, text, anchor in BOTTOM:
        xx, tx = PAD_L + x, PAD_L + anchor
        y0 = PAD_T + ph
        d.line([(xx, y0), (xx, y0 + STUB), (tx, y0 + STUB + 56),
                (tx, y0 + STUB + 76)], fill=LINE, width=lw, joint="curve")
        _multiline(d, (tx, y0 + STUB + 122), text, font, "c", line_h)

    out = os.path.join(outdir, "fig3_prototype.png")
    canvas.save(out, dpi=(400, 400))
    print("wrote %s  %dx%d (photograph %dx%d at native resolution)"
          % (out, W, H, pw, ph))


if __name__ == "__main__":
    main()
