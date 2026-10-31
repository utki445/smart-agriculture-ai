"""Shared Matplotlib styling for the manuscript figures.

Every figure in the paper is produced at the width it occupies on the page, so
that Word never has to rescale it (rescaling is what shrinks the text). The
page is A4 with 25.4 mm margins, giving a 6.27 in text column; FULL_W leaves a
little slack inside that.

House rules applied here, from the faculty formatting requirements:
  * 600 dpi on save;
  * no title inside the axes (the caption does that job);
  * no bold anywhere inside a plot;
  * fonts never smaller than 8 pt at the final printed size.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DPI = 600
FULL_W = 6.1          # inches, full text column
HALF_W = 3.0          # inches, one of a side-by-side pair

# Colour-blind-safe pair used throughout for the two evaluation protocols.
C_AUG = "#2E6FAF"     # augmentation-level
C_DIS = "#C23B22"     # source-disjoint
C_BASE = "#2F7A4D"    # majority-class baseline
C_NEUTRAL = "#4A5568"


def apply():
    plt.rcParams.update({
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.5,
        "axes.titleweight": "normal",
        "axes.labelweight": "normal",
        "font.weight": "normal",
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "lines.linewidth": 1.0,
        "grid.linewidth": 0.4,
        "grid.alpha": 0.35,
        "legend.frameon": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def panel(ax, text):
    """Non-bold panel identifier, e.g. '(a) Soil type'."""
    ax.set_title(text, fontweight="normal", fontsize=8, pad=4)


def save(fig, path):
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    print("wrote", path)
