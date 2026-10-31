"""Redraw Figure 2 (circuit schematic) from the wiring the firmware actually uses.

The schematic that was in the manuscript was a low-resolution screenshot of an
older build and showed DHT11 on GPIO 15, the probe on GPIO 32, the relay on
GPIO 23 and the LEDs on GPIO 2 and 18. Every pin here is taken from
hardware/smart_agri/smart_agri.ino and matches Table 2:

    DHT_PIN 4 | MOISTURE_PIN 34 | RELAY_PIN 26 | RED_LED 13 | GREEN_LED 14

Emits both a 600 dpi PNG and an editable .drawio file.

Usage:  python training/figures/make_fig2_circuit.py [outdir]
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, FancyArrow

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fig_style as S

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INO = os.path.join(ROOT, "hardware", "smart_agri", "smart_agri.ino")

INK = "#1A202C"
WIRE = "#1A202C"
RAIL33 = "#B03030"
RAIL5 = "#C2681F"
GNDC = "#2F4858"
BOX = "#F4F7FB"

LW = 0.85
FS = 6.4


# ---------------------------------------------------------------- primitives
def wire(ax, pts, color=WIRE, lw=LW, ls="-"):
    p = np.asarray(pts, float)
    ax.plot(p[:, 0], p[:, 1], color=color, lw=lw, ls=ls,
            solid_capstyle="round", solid_joinstyle="round", zorder=2)


def dot(ax, x, y, color=WIRE):
    ax.add_patch(Circle((x, y), 0.055, color=color, zorder=5))


def box(ax, x, y, w, h, label, sub=None):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=BOX, edgecolor=INK,
                           lw=LW, zorder=3))
    ax.text(x + w / 2, y + h / 2 + (0.15 if sub else 0), label, ha="center",
            va="center", fontsize=FS, zorder=4)
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.16, sub, ha="center", va="center",
                fontsize=FS - 1.7, color="#4A5568", zorder=4)


def resistor(ax, x, y, length, label, vertical=False, lab_side=1):
    """IEC rectangle resistor centred on (x, y)."""
    t = 0.17
    if vertical:
        ax.add_patch(Rectangle((x - t, y - length / 2), 2 * t, length,
                               facecolor="white", edgecolor=INK, lw=LW, zorder=4))
        ax.text(x + lab_side * (t + 0.10), y, label, ha="left" if lab_side > 0
                else "right", va="center", fontsize=FS - 0.5, zorder=5)
    else:
        ax.add_patch(Rectangle((x - length / 2, y - t), length, 2 * t,
                               facecolor="white", edgecolor=INK, lw=LW, zorder=4))
        ax.text(x, y + lab_side * (t + 0.16), label, ha="center",
                va="bottom" if lab_side > 0 else "top", fontsize=FS - 0.5, zorder=5)


def led(ax, x, y, label, colour):
    """LED pointing down: anode above, cathode below."""
    tri = [(x - 0.22, y + 0.18), (x + 0.22, y + 0.18), (x, y - 0.16)]
    ax.add_patch(Polygon(tri, closed=True, facecolor=colour, edgecolor=INK,
                         lw=LW, zorder=4))
    ax.plot([x - 0.24, x + 0.24], [y - 0.16, y - 0.16], color=INK, lw=LW, zorder=4)
    for k in (0, 1):
        ax.add_patch(FancyArrow(x + 0.26 + 0.14 * k, y + 0.10 + 0.14 * k,
                                0.17, 0.17, width=0.008, head_width=0.09,
                                head_length=0.09, color=INK, zorder=4,
                                length_includes_head=True))
    ax.text(x + 0.30, y - 0.16, label, ha="left", va="center",
            fontsize=FS - 0.5, zorder=5)


def npn(ax, x, y, label):
    """NPN transistor, base on the left, collector up, emitter down."""
    r = 0.42
    ax.add_patch(Circle((x, y), r, facecolor="white", edgecolor=INK,
                        lw=LW, zorder=4))
    ax.plot([x - 0.18, x - 0.18], [y - 0.26, y + 0.26], color=INK, lw=1.5, zorder=5)
    wire(ax, [(x - r - 0.30, y), (x - 0.18, y)])                 # base lead
    ax.plot([x - 0.18, x + 0.22], [y + 0.13, y + 0.34], color=INK, lw=LW, zorder=5)
    ax.plot([x - 0.18, x + 0.22], [y - 0.13, y - 0.34], color=INK, lw=LW, zorder=5)
    wire(ax, [(x + 0.22, y + 0.34), (x + 0.22, y + r + 0.30)])   # collector
    wire(ax, [(x + 0.22, y - 0.34), (x + 0.22, y - r - 0.30)])   # emitter
    ax.add_patch(FancyArrow(x + 0.02, y - 0.24, 0.13, -0.07, width=0.008,
                            head_width=0.11, head_length=0.11, color=INK,
                            zorder=6, length_includes_head=True))
    ax.text(x + 0.05, y + r + 0.16, label, ha="left", va="bottom",
            fontsize=FS - 0.5, zorder=5)


def ground(ax, x, y, label=None):
    wire(ax, [(x, y), (x, y - 0.16)], color=GNDC)
    for i, w in enumerate((0.30, 0.19, 0.09)):
        ax.plot([x - w, x + w], [y - 0.16 - 0.10 * i, y - 0.16 - 0.10 * i],
                color=GNDC, lw=LW, zorder=3)
    if label:
        ax.text(x, y - 0.56, label, ha="center", va="top", fontsize=FS - 0.8,
                color=GNDC, zorder=4)


def pin(ax, x, y, name, side):
    """Pin stub on the MCU body; the name is set just inside the outline."""
    dx = 0.30 if side == "r" else -0.30
    wire(ax, [(x, y), (x + dx, y)])
    ax.text(x - dx * 0.38, y, name, ha="left" if side == "l" else "right",
            va="center", fontsize=FS - 0.6, zorder=6)
    return x + dx


# ------------------------------------------------------------------ the figure
def check_pins():
    """Fail loudly if the firmware pins ever stop matching this drawing."""
    src = open(INO, encoding="utf-8", errors="ignore").read()
    want = {"DHT_PIN": "4", "MOISTURE_PIN": "34", "RELAY_PIN": "26",
            "RED_LED": "13", "GREEN_LED": "14",
            "MOISTURE_AIR": "2590", "MOISTURE_WATER": "1500",
            "MOISTURE_DRY": "30", "MOISTURE_WET": "60"}
    for k, v in want.items():
        m = re.search(r"#define\s+%s\s+(\S+)" % k, src)
        got = m.group(1) if m else None
        if got != v:
            raise SystemExit("firmware %s = %r, figure assumes %r" % (k, got, v))
    print("pin check OK against", os.path.relpath(INO, ROOT))


def png(outdir):
    S.apply()
    fig, ax = plt.subplots(figsize=(S.FULL_W, 3.28))
    ax.set_xlim(0, 14.4)
    ax.set_ylim(0, 7.4)
    ax.axis("off")
    ax.set_aspect("equal")

    y33, y5, ygnd = 6.85, 6.85, 0.55

    # ---- supply and ground rails
    wire(ax, [(0.38, y33), (6.40, y33)], color=RAIL33, lw=1.1)
    ax.text(0.33, y33, "+3.3 V", ha="right", va="center", fontsize=FS - 0.3,
            color=RAIL33)
    wire(ax, [(8.60, y5), (12.90, y5)], color=RAIL5, lw=1.1)
    ax.text(8.58, y5 + 0.20, "+5 V external supply", ha="left", va="bottom",
            fontsize=FS - 0.3, color=RAIL5)
    wire(ax, [(0.38, ygnd), (12.90, ygnd)], color=GNDC, lw=1.1)
    ground(ax, 5.78, ygnd, "common ground (ESP32 and pump supply)")

    # ---- MCU; the part name runs down the middle so that no pin label
    #      has to compete with it for width
    bx, by, bw, bh = 4.60, 1.55, 2.35, 4.55
    box(ax, bx, by, bw, bh, "")
    ax.text(bx + bw / 2, by + bh / 2, "ESP32-WROOM-32", rotation=90,
            ha="center", va="center", fontsize=FS + 0.5, zorder=5)

    p33 = pin(ax, bx, 5.60, "3V3", "l")
    p4 = pin(ax, bx, 4.55, "GPIO 4", "l")
    p34 = pin(ax, bx, 3.40, "GPIO 34", "l")
    pg = pin(ax, bx, 2.10, "GND", "l")
    p26 = pin(ax, bx + bw, 5.60, "GPIO 26", "r")
    p13 = pin(ax, bx + bw, 4.20, "GPIO 13", "r")
    p14 = pin(ax, bx + bw, 2.50, "GPIO 14", "r")

    wire(ax, [(p33, 5.60), (4.20, 5.60), (4.20, y33)]); dot(ax, 4.20, y33)
    wire(ax, [(pg, 2.10), (3.95, 2.10), (3.95, ygnd)]); dot(ax, 3.95, ygnd)

    # ---- DHT11 on GPIO 4, with its 10 k pull-up to 3V3
    box(ax, 0.72, 4.95, 2.40, 0.95, "DHT11", "temperature / humidity")
    wire(ax, [(1.25, 5.90), (1.25, y33)]); dot(ax, 1.25, y33)
    ax.text(1.19, 6.20, "VCC", ha="right", va="center", fontsize=FS - 1.3)
    wire(ax, [(2.60, 4.95), (2.60, ygnd)]); dot(ax, 2.60, ygnd)
    ax.text(2.66, 4.66, "GND", ha="left", va="center", fontsize=FS - 1.3)
    wire(ax, [(1.85, 4.95), (1.85, 4.55), (p4, 4.55)])
    ax.text(1.79, 4.66, "DATA", ha="right", va="center", fontsize=FS - 1.3)
    dot(ax, 3.50, 4.55)
    wire(ax, [(3.50, 4.55), (3.50, 5.10)])
    resistor(ax, 3.50, 5.55, 0.90, "10 kΩ", vertical=True, lab_side=1)
    wire(ax, [(3.50, 6.00), (3.50, y33)]); dot(ax, 3.50, y33)

    # ---- capacitive probe on GPIO 34 (ADC1_CH6)
    box(ax, 0.72, 2.85, 2.40, 0.95, "Capacitive soil", "moisture sensor v1.2")
    wire(ax, [(1.25, 3.80), (1.25, 4.40), (0.52, 4.40), (0.52, y33)])
    dot(ax, 0.52, y33)
    ax.text(0.58, 4.50, "VCC", ha="left", va="bottom", fontsize=FS - 1.3)
    wire(ax, [(2.60, 2.85), (2.60, ygnd)]); dot(ax, 2.60, ygnd)
    wire(ax, [(3.12, 3.40), (p34, 3.40)])
    ax.text(3.18, 3.56, "AOUT", ha="left", va="bottom", fontsize=FS - 1.3)
    ax.text(3.82, 3.24, "ADC1_CH6", ha="center", va="top", fontsize=FS - 1.4,
            color="#4A5568")

    # ---- status LEDs, each on its own lane down to ground
    wire(ax, [(p13, 4.20), (7.72, 4.20)])
    resistor(ax, 8.15, 4.20, 0.85, "220 Ω", lab_side=-1)
    wire(ax, [(8.58, 4.20), (8.95, 4.20)])
    led(ax, 8.95, 4.20, "", "#D64545")
    ax.text(8.95, 4.60, "Red LED", ha="center", va="bottom", fontsize=FS - 0.7)
    wire(ax, [(8.95, 4.04), (8.95, ygnd)]); dot(ax, 8.95, ygnd)

    wire(ax, [(p14, 2.50), (7.40, 2.50)])
    resistor(ax, 7.80, 2.50, 0.80, "220 Ω", lab_side=-1)
    wire(ax, [(8.20, 2.50), (8.35, 2.50)])
    led(ax, 8.35, 2.50, "", "#3E9B54")
    ax.text(8.35, 2.90, "Green LED", ha="center", va="bottom", fontsize=FS - 0.7)
    wire(ax, [(8.35, 2.34), (8.35, ygnd)]); dot(ax, 8.35, ygnd)

    # ---- relay driver on GPIO 26
    wire(ax, [(p26, 5.60), (7.57, 5.60)])
    resistor(ax, 8.00, 5.60, 0.85, "1 kΩ", lab_side=1)
    wire(ax, [(8.43, 5.60), (8.83, 5.60)])
    npn(ax, 9.30, 5.60, "")
    ax.text(9.00, 4.98, "BC547B", ha="right", va="center", fontsize=FS - 0.7)
    wire(ax, [(9.52, 6.32), (9.52, 6.40), (10.30, 6.40)])
    wire(ax, [(9.52, 4.88), (9.52, ygnd)]); dot(ax, 9.52, ygnd)

    # ---- relay module and the pump it switches
    box(ax, 10.30, 6.05, 1.80, 0.70, "5 V relay", None)
    ax.text(10.08, 6.46, "IN", ha="center", va="bottom", fontsize=FS - 1.3)
    wire(ax, [(11.20, 6.75), (11.20, y5)]); dot(ax, 11.20, y5)

    wire(ax, [(12.60, y5), (12.60, 5.45)]); dot(ax, 12.60, y5)
    dot(ax, 12.60, 5.45)
    ax.plot([12.60, 13.06], [5.45, 4.94], color=INK, lw=LW, zorder=4)
    dot(ax, 12.60, 4.80)
    ax.text(13.16, 5.20, "COM / NO", ha="left", va="center", fontsize=FS - 1.3,
            color="#4A5568")
    wire(ax, [(12.60, 4.80), (12.60, 4.10)])
    box(ax, 11.75, 3.15, 1.70, 0.95, "DC pump", "3–6 V")
    wire(ax, [(12.60, 3.15), (12.60, ygnd)]); dot(ax, 12.60, ygnd)
    wire(ax, [(11.20, 6.05), (11.20, 5.72), (12.35, 5.72), (12.35, 5.12)],
         ls=(0, (2, 2)), lw=0.6, color="#6B7280")

    S.save(fig, os.path.join(outdir, "fig2_circuit.png"))


def drawio(outdir):
    """Editable block-level version of the same wiring."""
    nodes = [
        ("dht", 40, 60, 190, 70, "DHT11&#10;GPIO 4 (data, 10 k&#937; pull-up to 3V3)"),
        ("probe", 40, 190, 190, 70, "Capacitive soil moisture sensor v1.2&#10;"
                                    "AOUT &#8594; GPIO 34 (ADC1_CH6)"),
        ("mcu", 300, 110, 200, 160, "ESP32-WROOM-32&#10;&#10;3V3 / GND&#10;"
                                    "hysteresis 30 / 60 %"),
        ("drv", 570, 40, 190, 70, "BC547B + 1 k&#937;&#10;base from GPIO 26"),
        ("relay", 830, 40, 170, 70, "5 V relay module&#10;coil from +5 V ext."),
        ("pump", 830, 170, 170, 70, "DC pump 3&#8211;6 V&#10;via COM / NO"),
        ("led1", 570, 170, 190, 60, "Red LED + 220 &#937;&#10;GPIO 13"),
        ("led2", 570, 250, 190, 60, "Green LED + 220 &#937;&#10;GPIO 14"),
        ("gnd", 300, 330, 200, 50, "Common ground&#10;(ESP32 and pump supply)"),
    ]
    edges = [("dht", "mcu"), ("probe", "mcu"), ("mcu", "drv"), ("drv", "relay"),
             ("relay", "pump"), ("mcu", "led1"), ("mcu", "led2"),
             ("mcu", "gnd"), ("pump", "gnd")]

    mx = ET.Element("mxfile", host="app.diagrams.net")
    dg = ET.SubElement(mx, "diagram", name="Fig 2 circuit")
    gm = ET.SubElement(dg, "mxGraphModel", dx="1100", dy="700", grid="1",
                       gridSize="10", page="1", pageWidth="1100",
                       pageHeight="450", math="0", shadow="0")
    root = ET.SubElement(gm, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    for nid, x, y, w, h, label in nodes:
        c = ET.SubElement(root, "mxCell", id=nid, value=label,
                          style=("rounded=1;whiteSpace=wrap;html=1;fillColor=%s;"
                                 "strokeColor=%s;fontSize=11;" % (BOX, INK)),
                          vertex="1", parent="1")
        ET.SubElement(c, "mxGeometry", x=str(x), y=str(y), width=str(w),
                      height=str(h), **{"as": "geometry"})
    for i, (a, b) in enumerate(edges):
        e = ET.SubElement(root, "mxCell", id="e%d" % i, edge="1", parent="1",
                          source=a, target=b,
                          style="endArrow=none;html=1;strokeColor=%s;" % INK)
        ET.SubElement(e, "mxGeometry", relative="1", **{"as": "geometry"})

    out = os.path.join(outdir, "fig2_circuit.drawio")
    ET.ElementTree(mx).write(out, encoding="utf-8", xml_declaration=True)
    print("wrote", out)


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "figures")
    os.makedirs(outdir, exist_ok=True)
    check_pins()
    png(outdir)
    drawio(outdir)


if __name__ == "__main__":
    main()
