"""Redraw Figure 1 (system architecture) as a flat, wide diagram.

Replaces the Mermaid render, which was tall and narrow and carried emoji
icons. The point the figure has to make is that the irrigation loop closes on
the ESP32: everything to the right of the serial link is logging, inference
and advice, and none of it can actuate the relay.

Emits both a 600 dpi PNG and an editable .drawio file.

Usage:  python training/figures/make_fig1_architecture.py [outdir]
"""

import os
import sys
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fig_style as S

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EDGE = "#33415C"
FILL_SENSE = "#E3F0FA"
FILL_MCU = "#CFE4F5"
FILL_ACT = "#FCE4D6"
FILL_HOST = "#E6F2E8"
FILL_UI = "#FFF3D6"

# (x, y, w, h, facecolor, text)
BOXES = [
    (0.06, 4.34, 1.76, 0.62, FILL_SENSE, "DHT11\nGPIO 4"),
    (0.06, 3.44, 1.76, 0.62, FILL_SENSE, "Capacitive probe\nGPIO 34"),
    (2.05, 3.44, 2.25, 1.52, FILL_MCU,
     "ESP32-WROOM-32\n\nhysteresis 30 / 60 %\n1 Hz control loop"),
    (4.62, 4.34, 1.62, 0.62, FILL_ACT, "BC547B driver\nGPIO 26"),
    (4.62, 3.44, 1.62, 0.62, FILL_ACT, "Status LEDs\nGPIO 13 / 14"),
    (6.56, 4.34, 1.30, 0.62, FILL_ACT, "5 V relay"),
    (8.18, 4.34, 1.30, 0.62, FILL_ACT, "DC pump"),
    (2.05, 1.32, 1.95, 0.78, FILL_HOST, "Python collector\n(pyserial)"),
    (4.32, 1.32, 1.80, 0.78, FILL_HOST, "CSV telemetry\nlog"),
    (6.44, 1.32, 2.00, 0.78, FILL_HOST, "Soil classifiers\nCNN features + SVM"),
    (4.14, 0.18, 4.48, 0.78, FILL_UI,
     "Streamlit dashboard (localhost:8501)\n"
     "live values · history · advisory schedule\n"
     "(soil condition + 48 h Open-Meteo forecast)"),
]

ARROWS = [
    ((1.82, 4.65), (2.05, 4.48)),
    ((1.82, 3.75), (2.05, 3.95)),
    ((4.30, 4.65), (4.62, 4.65)),
    ((4.30, 3.75), (4.62, 3.75)),
    ((6.24, 4.65), (6.56, 4.65)),
    ((7.86, 4.65), (8.18, 4.65)),
    ((3.02, 3.44), (3.02, 2.10)),          # serial link, down to the host
    ((4.00, 1.71), (4.32, 1.71)),
    ((6.12, 1.71), (6.44, 1.71)),
    ((7.44, 1.32), (6.96, 0.96)),
    ((5.10, 1.32), (5.10, 0.96)),
]


def png(outdir):
    S.apply()
    fig, ax = plt.subplots(figsize=(S.FULL_W, 3.30))
    ax.set_xlim(0, 10.0)
    ax.set_ylim(-0.30, 5.72)
    ax.axis("off")
    ax.set_aspect("auto")

    # Boundary of the part that keeps running with no network and no host.
    ax.add_patch(Rectangle((-0.06, 3.22), 9.70, 1.96, transform=ax.transData,
                           facecolor="none", edgecolor="#2E6FAF", lw=0.9,
                           linestyle=(0, (5, 3)), zorder=1))
    ax.text(-0.02, 5.26, "Irrigation control loop — runs on the ESP32 alone, "
                        "with no network and no host",
            fontsize=6.9, color="#2E6FAF", va="bottom", ha="left")

    ax.add_patch(Rectangle((1.92, 0.04), 6.84, 2.20, transform=ax.transData,
                           facecolor="none", edgecolor="#4A7A5C", lw=0.9,
                           linestyle=(0, (5, 3)), zorder=1))
    ax.text(1.96, 2.30, "Host — logging, classification and advice only",
            fontsize=6.9, color="#4A7A5C", va="bottom", ha="left")

    for x, y, w, h, fc, txt in BOXES:
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.015,rounding_size=0.07",
                                    facecolor=fc, edgecolor=EDGE, lw=0.7, zorder=3))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center",
                fontsize=6.4, zorder=4, linespacing=1.4)

    for a, b in ARROWS:
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=7,
                                     lw=0.8, color=EDGE, zorder=2,
                                     shrinkA=0, shrinkB=0))

    ax.text(3.14, 2.90, "USB serial, 115200 baud\nnewline-delimited JSON, 1 Hz",
            fontsize=6.6, ha="left", va="center", linespacing=1.4)

    S.save(fig, os.path.join(outdir, "fig1_architecture.png"))


def drawio(outdir):
    """Editable mxGraph source for the same diagram (1 unit = 100 px)."""
    K = 100.0
    HT = 5.72
    mx = ET.Element("mxfile", host="app.diagrams.net")
    dg = ET.SubElement(mx, "diagram", name="Fig 1 architecture")
    gm = ET.SubElement(dg, "mxGraphModel", dx="1100", dy="700", grid="1",
                       gridSize="10", page="1", pageWidth="1100",
                       pageHeight="620", math="0", shadow="0")
    root = ET.SubElement(gm, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    ids = {}
    for i, (x, y, w, h, fc, txt) in enumerate(BOXES, start=2):
        cid = "n%d" % i
        ids[(round(x, 2), round(y, 2))] = cid
        c = ET.SubElement(root, "mxCell", id=cid, value=txt.replace("\n", "&#10;"),
                          style=("rounded=1;whiteSpace=wrap;html=1;fillColor=%s;"
                                 "strokeColor=%s;fontSize=11;" % (fc, EDGE)),
                          vertex="1", parent="1")
        ET.SubElement(c, "mxGeometry", x=str(round(x * K)),
                      y=str(round((HT - y - h) * K)), width=str(round(w * K)),
                      height=str(round(h * K)), **{"as": "geometry"})

    for j, (a, b) in enumerate(ARROWS):
        e = ET.SubElement(root, "mxCell", id="e%d" % j, edge="1", parent="1",
                          style="endArrow=block;html=1;strokeColor=%s;" % EDGE)
        g = ET.SubElement(e, "mxGeometry", relative="1", **{"as": "geometry"})
        ET.SubElement(g, "mxPoint", x=str(round(a[0] * K)),
                      y=str(round((HT - a[1]) * K)), **{"as": "sourcePoint"})
        ET.SubElement(g, "mxPoint", x=str(round(b[0] * K)),
                      y=str(round((HT - b[1]) * K)), **{"as": "targetPoint"})

    out = os.path.join(outdir, "fig1_architecture.drawio")
    ET.ElementTree(mx).write(out, encoding="utf-8", xml_declaration=True)
    print("wrote", out)


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "figures")
    os.makedirs(outdir, exist_ok=True)
    png(outdir)
    drawio(outdir)


if __name__ == "__main__":
    main()
