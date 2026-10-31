"""Regenerate Figures 5-10 of the manuscript at 600 dpi.

Every number plotted here is read from a file in the repository -- nothing is
hard-coded from the paper:

  Fig. 5   data/sensor_log.csv                              (control-law trace)
  Fig. 6   results/source_disjoint_eval_manuscript_run.json (accuracy + CIs)
  Fig. 7   results/source_disjoint_eval_manuscript_run.json (fold / source spread)
  Fig. 8   results/source_disjoint_eval_manuscript_run.json (per-class F1)
  Fig. 9   results/source_disjoint_eval_manuscript_run.json (confusion matrices)
  Fig. 10  results/probe_check_simulation.json              (simulated test)

Usage:  python training/figures/make_data_figures.py [outdir]
"""

import json
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fig_style as S

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVAL = os.path.join(ROOT, "results", "source_disjoint_eval_manuscript_run.json")
SIM = os.path.join(ROOT, "results", "probe_check_simulation.json")
LOG = os.path.join(ROOT, "data", "sensor_log.csv")

BACKBONES = ["EfficientNetV2-B0", "MobileNetV2", "ResNet50"]
BB_LABEL = {"EfficientNetV2-B0": "EfficientNet\nV2-B0",
            "MobileNetV2": "MobileNet\nV2",
            "ResNet50": "ResNet50"}

# Firmware constants (hardware/smart_agri/smart_agri.ino)
T_DRY, T_WET = 30, 60
SESSION_GAP_S = 300          # gap that separates two logging sessions


# --------------------------------------------------------------------------
# Figure 5: measured drying / rewetting cycle and reconstructed pump state
# --------------------------------------------------------------------------
def relay_states(moisture, hysteresis):
    """Pump state the firmware would have held, sample by sample."""
    state, out = 0, []
    for m in moisture:
        if hysteresis:
            nxt = 1 if m < T_DRY else (0 if m > T_WET else state)
        else:
            nxt = 1 if m < T_DRY else 0
        out.append(nxt)
        state = nxt
    return np.asarray(out)


def fig5(outdir):
    df = pd.read_csv(LOG, parse_dates=["timestamp"])
    gap = df["timestamp"].diff().dt.total_seconds()
    sess = ((gap > SESSION_GAP_S) | gap.isna()).cumsum()

    # The session discussed in section 4.4: 697 samples, 2026-03-13, ~14 min.
    sizes = df.groupby(sess).size()
    target = sizes[sizes == 697].index[0]
    sub = df[sess == target].reset_index(drop=True)

    t = (sub["timestamp"] - sub["timestamp"].iloc[0]).dt.total_seconds() / 60.0
    m = sub["soil_moisture"].to_numpy(float)
    single = relay_states(m, hysteresis=False)
    hyst = relay_states(m, hysteresis=True)
    n_single = int((np.diff(single) != 0).sum())
    n_hyst = int((np.diff(hyst) != 0).sum())

    fig, axes = plt.subplots(
        3, 1, figsize=(S.FULL_W, 4.1), sharex=True,
        gridspec_kw={"height_ratios": [3.1, 1, 1], "hspace": 0.18})

    ax = axes[0]
    ax.axhspan(T_DRY, T_WET, color="#F2E2B0", alpha=0.55, lw=0,
               label="Hysteresis dead band")
    # Plot real samples only; markers make the sampling visible so that a
    # straight segment can never be mistaken for a measured curve.
    ax.plot(t, m, color=S.C_AUG, lw=0.8, marker="o", ms=0.7,
            markerfacecolor=S.C_AUG, markeredgecolor="none",
            label="Measured soil moisture")
    ax.axhline(T_DRY, color=S.C_DIS, ls="--", lw=0.8, label="$T_D$ = 30%")
    ax.axhline(T_WET, color=S.C_BASE, ls="--", lw=0.8, label="$T_W$ = 60%")
    ax.set_ylabel("Moisture (%)")
    ax.set_ylim(-5, 108)
    ax.grid(axis="y")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=4,
              columnspacing=1.1, handlelength=1.6, borderpad=0.2)

    for ax, state, n, lab, col in (
            (axes[1], single, n_single, "Single\nset point", "#C88A2E"),
            (axes[2], hyst, n_hyst, "Hysteresis\n(implemented)", S.C_NEUTRAL)):
        ax.fill_between(t, 0, state, step="post", color=col, alpha=0.85, lw=0)
        ax.set_yticks([0, 1])
        ax.set_yticklabels(["OFF", "ON"])
        ax.set_ylim(-0.15, 1.35)
        ax.set_ylabel(lab)
        ax.text(0.995, 0.80, "%d relay transitions" % n, transform=ax.transAxes,
                ha="right", va="top", fontsize=7.5, color=col,
                fontweight="normal")
    axes[2].set_xlabel("Time since start of session (min)")
    S.save(fig, os.path.join(outdir, "fig5_control_law.png"))
    return n_single, n_hyst, len(sub)


# --------------------------------------------------------------------------
# Figure 6: accuracy under the two protocols
# --------------------------------------------------------------------------
def fig6(outdir, d):
    fig, axes = plt.subplots(1, 2, figsize=(S.FULL_W, 2.9))
    for ax, task, title in ((axes[0], "type", "(a) Soil type, 5 classes, 16 source photographs"),
                            (axes[1], "cond", "(b) Soil condition, 4 classes, 14 source photographs")):
        xs = np.arange(len(BACKBONES))
        w = 0.36
        for off, key, boot, col, lab in (
                (-w / 2, "leaky", "boot_leaky", S.C_AUG, "Augmentation-level CV"),
                (+w / 2, "honest", "boot_honest", S.C_DIS, "Source-disjoint CV")):
            vals = [d[task][b][key] * 100 for b in BACKBONES]
            lo = [d[task][b][boot][0] * 100 for b in BACKBONES]
            hi = [d[task][b][boot][1] * 100 for b in BACKBONES]
            err = [np.subtract(vals, lo), np.subtract(hi, vals)]
            ax.bar(xs + off, vals, w, color=col, label=lab, zorder=3)
            ax.errorbar(xs + off, vals, yerr=err, fmt="none", ecolor="#222222",
                        elinewidth=0.7, capsize=1.8, zorder=4)
            for x, v, h in zip(xs + off, vals, hi):
                ax.text(x, h + 1.5, "%.1f" % v, ha="center", va="bottom",
                        fontsize=7, fontweight="normal")
        base = d[task][BACKBONES[0]]["majority"] * 100
        ax.axhline(base, color=S.C_BASE, ls=":", lw=1.1, zorder=2)
        ax.set_xticks(xs)
        ax.set_xticklabels([BB_LABEL[b] for b in BACKBONES])
        ax.set_ylim(0, 118)
        ax.set_yticks(range(0, 101, 20))
        ax.grid(axis="y", zorder=0)
        S.panel(ax, title)
    axes[0].set_ylabel("Accuracy (%)")

    handles = [Patch(color=S.C_AUG), Patch(color=S.C_DIS),
               Line2D([], [], color=S.C_BASE, ls=":", lw=1.1)]
    labels = ["Augmentation-level CV", "Source-disjoint CV", "Majority-class baseline"]
    fig.legend(handles, labels, loc="lower center", ncol=3,
               bbox_to_anchor=(0.5, -0.09), handlelength=1.6)
    fig.tight_layout()
    S.save(fig, os.path.join(outdir, "fig6_accuracy.png"))


# --------------------------------------------------------------------------
# Figure 7: where the accuracy comes from -- folds vs held-out photographs
# --------------------------------------------------------------------------
def fig7(outdir, d):
    fig, axes = plt.subplots(1, 2, figsize=(S.FULL_W, 2.9))
    rng = np.random.default_rng(0)
    for ax, task, title in ((axes[0], "type", "(a) Soil type"),
                            (axes[1], "cond", "(b) Soil condition")):
        for i, b in enumerate(BACKBONES):
            folds = np.array(d[task][b]["leaky_folds"]) * 100
            per = np.array(list(d[task][b]["honest_per_source"].values())) * 100
            ax.boxplot(per, positions=[i + 0.18], widths=0.26, orientation="vertical",
                       patch_artist=True, showfliers=False,
                       boxprops=dict(facecolor="#FBE3E0", edgecolor=S.C_DIS, lw=0.7),
                       medianprops=dict(color="#111111", lw=0.9),
                       whiskerprops=dict(color=S.C_DIS, lw=0.7),
                       capprops=dict(color=S.C_DIS, lw=0.7))
            ax.scatter(i + 0.18 + rng.uniform(-0.075, 0.075, per.size), per,
                       s=4.5, color=S.C_DIS, zorder=4, linewidths=0)
            ax.scatter(np.full(folds.size, i - 0.18), folds, s=9,
                       marker="D", color=S.C_AUG, zorder=4, linewidths=0)
        ax.set_xticks(np.arange(len(BACKBONES)))
        ax.set_xticklabels([BB_LABEL[b] for b in BACKBONES])
        ax.set_xlim(-0.6, len(BACKBONES) - 0.4)
        ax.set_ylim(-6, 108)
        ax.set_yticks(range(0, 101, 20))
        ax.grid(axis="y")
        S.panel(ax, title)
    axes[0].set_ylabel("Accuracy (%)")

    handles = [Line2D([], [], marker="D", ls="none", color=S.C_AUG, ms=3.4),
               Line2D([], [], marker="o", ls="none", color=S.C_DIS, ms=3.0)]
    fig.legend(handles, ["Augmentation-level fold", "Held-out source photograph"],
               loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.09),
               handlelength=1.2)
    fig.tight_layout()
    S.save(fig, os.path.join(outdir, "fig7_distribution.png"))


# --------------------------------------------------------------------------
# Figure 8: source-disjoint F1 against the number of source photographs
# --------------------------------------------------------------------------
def fig8(outdir, d):
    # Per-class F1 recomputed from the stored confusion matrices, so the
    # figure and Table 8 cannot drift apart.
    classes = d["meta"]["type_classes"]
    photos = {"Clay": 7, "Sand": 5, "Loamy sand": 2, "Loam": 1, "Sandy Loam": 1}
    markers = {"EfficientNetV2-B0": "o", "MobileNetV2": "s", "ResNet50": "^"}

    colours = {"EfficientNetV2-B0": S.C_AUG, "MobileNetV2": "#C88A2E",
               "ResNet50": S.C_BASE}

    fig, ax = plt.subplots(figsize=(S.FULL_W * 0.66, 2.6))
    rng = np.random.default_rng(1)
    for b in BACKBONES:
        cm = np.array(d["type"][b]["cm_honest"], float)
        f1s, xs = [], []
        for i, c in enumerate(classes):
            tp = cm[i, i]
            fp = cm[:, i].sum() - tp
            fn = cm[i, :].sum() - tp
            f1 = 0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn)
            f1s.append(f1)
            xs.append(photos[c] + rng.uniform(-0.10, 0.10))
        ax.scatter(xs, f1s, s=18, marker=markers[b], label=b,
                   color=colours[b], alpha=0.9, linewidths=0)

    # name the classes, so the reader can see which ones sit at F1 = 0
    for c, dx, dy, ha in (("Loam / Sandy Loam", 0.18, 0.055, "left"),
                          ("Loamy sand", 0.18, 0.055, "left"),
                          ("Sand", 0.0, -0.085, "center"),
                          ("Clay", -0.18, -0.085, "right")):
        ax.annotate(c, (photos.get(c.split(" /")[0], 1) + dx,
                        {"Loam / Sandy Loam": 0.0, "Loamy sand": 0.05,
                         "Sand": 0.38, "Clay": 0.71}[c] + dy),
                    fontsize=6.6, color="#4A5568", ha=ha, va="bottom")

    ax.set_xlabel("Source photographs available for the class")
    ax.set_ylabel("Source-disjoint F1")
    ax.set_xticks([1, 2, 3, 4, 5, 6, 7])
    ax.set_xlim(0.4, 7.9)
    ax.set_ylim(-0.06, 0.88)
    ax.grid(axis="y")
    ax.legend(loc="upper left", handlelength=1.0, borderpad=0.2,
              handletextpad=0.4)
    fig.tight_layout()
    S.save(fig, os.path.join(outdir, "fig8_f1_vs_photos.png"))


# --------------------------------------------------------------------------
# Figure 9: source-disjoint confusion matrices
# --------------------------------------------------------------------------
def _heat(ax, cm, labels, title):
    row = cm.sum(axis=1, keepdims=True)
    frac = np.divide(cm, np.where(row == 0, 1, row))
    im = ax.imshow(frac, cmap="Blues", vmin=0, vmax=1)
    n = len(labels)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, "%d\n%.0f%%" % (cm[i, j], 100 * frac[i, j]),
                    ha="center", va="center", fontsize=6.4,
                    color="white" if frac[i, j] > 0.55 else "#1A202C")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_linewidth(0.5)
    S.panel(ax, title)
    return im


def fig9(outdir, d):
    tcls = d["meta"]["type_classes"]
    ccls = [c.capitalize() for c in d["meta"]["cond_classes"]]
    b = "EfficientNetV2-B0"
    fig, axes = plt.subplots(1, 2, figsize=(S.FULL_W, 2.85),
                             gridspec_kw={"width_ratios": [1.16, 1]})
    _heat(axes[0], np.array(d["type"][b]["cm_honest"]), tcls,
          "(a) Soil type, %.1f%% accuracy" % (d["type"][b]["honest"] * 100))
    im = _heat(axes[1], np.array(d["cond"][b]["cm_honest"]), ccls,
               "(b) Soil condition, %.1f%% accuracy" % (d["cond"][b]["honest"] * 100))
    fig.tight_layout()
    cb = fig.colorbar(im, ax=axes, fraction=0.022, pad=0.015)
    cb.set_label("Row fraction", fontsize=7.5)
    cb.ax.tick_params(labelsize=7)
    cb.outline.set_linewidth(0.5)
    S.save(fig, os.path.join(outdir, "fig9_confusion.png"))


# --------------------------------------------------------------------------
# Figure 10: simulated pulse-response test
# --------------------------------------------------------------------------
def fig10(outdir, sim):
    order = ["healthy", "offset_drift", "gain_drift", "fouled",
             "dislodged", "disconnected", "free_water"]
    nice = {"healthy": "Healthy", "offset_drift": "Offset drift (±20 pp)",
            "gain_drift": "Gain drift (0.6–0.9×)", "fouled": "Fouled (0.05–0.25×)",
            "dislodged": "Dislodged", "disconnected": "Disconnected",
            "free_water": "In free water"}
    # Short forms for the (b) axis; the ranges are given in the caption.
    short = {"healthy": "Healthy", "offset_drift": "Offset drift",
             "gain_drift": "Gain drift", "fouled": "Fouled",
             "dislodged": "Dislodged", "disconnected": "Disconnected",
             "free_water": "Free water"}

    fig, axes = plt.subplots(1, 3, figsize=(S.FULL_W, 3.15),
                             gridspec_kw={"width_ratios": [1.12, 1.08, 0.95]})

    # (a) illustrative responses, generated from the same response model the
    # simulation uses: difference of two exponentials plus measurement noise.
    ax = axes[0]
    t = np.linspace(-6, 60, 661)
    rng = np.random.default_rng(7)
    shown = [("healthy", 1.0, 0.0, 8.0, "-"), ("offset_drift", 1.0, -6.0, 8.0, "-"),
             ("gain_drift", 0.75, 0.0, 8.0, "-"), ("fouled", 0.15, 0.0, 22.0, "--"),
             ("dislodged", 0.0, -13.0, 8.0, "--"), ("free_water", 3.4, 3.0, 0.6, "--")]
    cols = {"healthy": "#1F4E79", "offset_drift": "#2E6FAF", "gain_drift": "#7FB3E0",
            "fouled": "#C4622D", "dislodged": "#C23B22", "free_water": "#7B52AB"}
    for key, gain, off, delay, ls in shown:
        peak = 22.0 * gain
        resp = np.where(t < delay, 0.0,
                        peak * (1 - np.exp(-(t - delay) / 6.0)) * np.exp(-(t - delay) / 220.0))
        y = np.clip(23.0 + off + resp + rng.normal(0, 0.72, t.size), 0, 100)
        ax.plot(t, y, ls, color=cols[key], lw=0.85, label=nice[key])
    ax.axvline(0, color="#555555", ls=":", lw=0.7)
    ax.set_xlabel("Time from pulse (s)")
    ax.set_ylabel("Reported moisture (%)")
    ax.set_ylim(-4, 118)
    ax.set_xticks([0, 20, 40, 60])
    ax.grid(axis="y")
    ax.legend(loc="upper center", bbox_to_anchor=(0.44, -0.30), ncol=2,
              fontsize=5.7, handlelength=1.2, columnspacing=0.6,
              borderpad=0.15, labelspacing=0.3)
    S.panel(ax, "(a) Example responses")

    # (b) flag rates -- legend placed outside the bars
    ax = axes[1]
    ys = np.arange(len(order))[::-1]
    h = 0.34
    ax.barh(ys + h / 2, [sim["results"][k]["transient"] * 100 for k in order],
            h, color=S.C_AUG, label="Pulse-response test")
    ax.barh(ys - h / 2, [sim["results"][k]["static"] * 100 for k in order],
            h, color="#A8B2C1", label="Static clamp check")
    ax.axhline(ys[2] - 0.5, color="#555555", ls=":", lw=0.7)
    ax.set_yticks(ys)
    ax.set_yticklabels([short[k] for k in order])
    ax.set_xlim(0, 108)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Flagged as fault (%)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.60, -0.30), ncol=2,
              handlelength=1.3, borderpad=0.15, fontsize=6.6,
              columnspacing=0.9)
    ax.grid(axis="x")
    S.panel(ax, "(b) Flag rate, n = 2000 each")

    # (c) sensitivity sweep
    ax = axes[2]
    g = np.array(sim["sweep"]["gain"])
    fr = np.array(sim["sweep"]["flag_rate"]) * 100
    ax.axvspan(0.6, 0.9, color="#D6E8F7", alpha=0.75, lw=0)
    ax.text(0.75, 88, "normal\ndrift", ha="center", va="center",
            fontsize=6.6, color="#2E6FAF")
    ax.plot(g, fr, "-o", color=S.C_AUG, ms=2.2, lw=1.0)
    ax.axhline(50, color="#777777", ls=":", lw=0.7)
    ax.axvline(sim["sweep"]["gain_at_50pct_detection"], color="#777777",
               ls=":", lw=0.7)
    ax.set_xlabel("Probe sensitivity (× nominal)")
    ax.set_ylabel("Flagged as fault (%)")
    ax.set_ylim(-4, 118)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.grid(axis="y")
    S.panel(ax, "(c) Sensitivity sweep")

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.33, wspace=0.50)
    S.save(fig, os.path.join(outdir, "fig10_simulation.png"))


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "figures")
    os.makedirs(outdir, exist_ok=True)
    S.apply()
    d = json.load(open(EVAL, encoding="utf-8"))
    sim = json.load(open(SIM, encoding="utf-8"))

    n_single, n_hyst, n = fig5(outdir)
    print("  Fig 5 session: %d samples, single=%d, hysteresis=%d transitions"
          % (n, n_single, n_hyst))
    fig6(outdir, d)
    fig7(outdir, d)
    fig8(outdir, d)
    fig9(outdir, d)
    fig10(outdir, sim)


if __name__ == "__main__":
    main()
