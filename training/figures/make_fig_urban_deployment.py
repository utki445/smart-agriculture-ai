"""Urban deployment concept figure for the smart-city framing of the project.

Shows the same node replicated across four kinds of urban green space, each
closing its own irrigation loop locally, with telemetry flowing upward to a
municipal dashboard that cannot actuate anything.

Usage:  python training/figures/make_fig_urban_deployment.py [outdir]
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fig_style as S

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EDGE = "#33415C"
GREEN = "#E3F1E6"
GREEN_E = "#4A7A5C"
NODE = "#CFE4F5"
CITY = "#FFF3D6"

SITES = [
    ("City park\nor urban forest", 0.30),
    ("Road median\nand green belt", 2.68),
    ("Green roof\nor terrace garden", 5.06),
    ("Community garden\nor urban farm", 7.44),
]


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "figures")
    os.makedirs(outdir, exist_ok=True)
    S.apply()

    fig, ax = plt.subplots(figsize=(S.FULL_W, 3.45))
    ax.set_xlim(0, 10.0)
    ax.set_ylim(-0.55, 6.6)
    ax.axis("off")

    # ---- municipal layer
    ax.add_patch(FancyBboxPatch((1.55, 5.40), 6.90, 0.80,
                                boxstyle="round,pad=0.02,rounding_size=0.08",
                                facecolor=CITY, edgecolor=EDGE, lw=0.8, zorder=3))
    ax.text(5.00, 5.80, "Municipal water-management dashboard",
            ha="center", va="center", fontsize=7.6, zorder=4)
    ax.text(5.00, 5.56, "fleet status  ·  consumption trends  ·  "
                        "maintenance alerts  ·  reporting",
            ha="center", va="center", fontsize=6.4, color="#4A5568", zorder=4)

    ax.text(5.00, 6.34, "City scale — monitoring and planning",
            ha="center", va="bottom", fontsize=7.0, color="#8A6D1F")

    # ---- the four sites
    for label, x in SITES:
        w = 2.10
        ax.add_patch(Rectangle((x, 0.45), w, 3.95, facecolor="none",
                               edgecolor=GREEN_E, lw=0.8,
                               linestyle=(0, (4, 2.6)), zorder=1))
        ax.text(x + w / 2, 4.10, label, ha="center", va="center",
                fontsize=7.2, zorder=4, linespacing=1.35)

        # node box
        ax.add_patch(FancyBboxPatch((x + 0.09, 2.52), w - 0.18, 1.04,
                                    boxstyle="round,pad=0.02,rounding_size=0.07",
                                    facecolor=NODE, edgecolor=EDGE, lw=0.7,
                                    zorder=3))
        ax.text(x + w / 2, 3.26, "Irrigation node", ha="center", va="center",
                fontsize=6.9, zorder=4)
        ax.text(x + w / 2, 2.98, "ESP32 · probe · relay",
                ha="center", va="center", fontsize=5.9, color="#4A5568", zorder=4)
        ax.text(x + w / 2, 2.74, "decides locally, 1 Hz",
                ha="center", va="center", fontsize=5.9, color="#2E6FAF", zorder=4)

        # local closed loop: soil -> node -> pump -> soil
        ax.add_patch(FancyBboxPatch((x + 0.09, 1.08), w - 0.18, 0.72,
                                    boxstyle="round,pad=0.02,rounding_size=0.06",
                                    facecolor=GREEN, edgecolor=GREEN_E, lw=0.7,
                                    zorder=3))
        ax.text(x + w / 2, 1.44, "Soil  →  pump  →  soil",
                ha="center", va="center", fontsize=6.6, zorder=4)

        ax.add_patch(FancyArrowPatch((x + 0.62, 2.52), (x + 0.62, 1.80),
                                     arrowstyle="-|>", mutation_scale=7,
                                     lw=0.9, color=GREEN_E, zorder=2,
                                     shrinkA=0, shrinkB=0))
        ax.add_patch(FancyArrowPatch((x + w - 0.62, 1.80), (x + w - 0.62, 2.52),
                                     arrowstyle="-|>", mutation_scale=7,
                                     lw=0.9, color=GREEN_E, zorder=2,
                                     shrinkA=0, shrinkB=0))

        # telemetry upward, dashed = non-critical
        ax.add_patch(FancyArrowPatch((x + w / 2, 4.46), (x + w / 2, 5.40),
                                     arrowstyle="-|>", mutation_scale=7,
                                     lw=0.8, color="#8A6D1F", zorder=2,
                                     linestyle=(0, (3, 2)),
                                     shrinkA=0, shrinkB=0))

    ax.text(5.00, 0.02,
            "Solid loop: the irrigation decision is taken on the node and "
            "never leaves it.     Dashed: telemetry upward only — the "
            "city layer reports, it cannot actuate.",
            ha="center", va="top", fontsize=6.4, color="#4A5568")

    ax.text(5.00, -0.30,
            "If the city network fails, every node keeps watering.",
            ha="center", va="top", fontsize=6.8, color="#2E6FAF")

    S.save(fig, os.path.join(outdir, "fig_urban_deployment.png"))


if __name__ == "__main__":
    main()
