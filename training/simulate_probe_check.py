"""Monte-Carlo logic check of the proposed transient-based probe-validity test.

NOT a physical validation. Narrow question: under a simple absorption model with
sensor noise measured from our own telemetry, do the decision rules separate
functional probe faults from healthy and merely-miscalibrated probes, and where
does that separation break down?

Honesty safeguards
  * Noise sigma drawn from the empirical range of our logs (median 0.50 pp,
    90th percentile 0.94 pp of 30-sample flat-window std); integer quantisation
    and [0,100] clamp as in firmware.
  * Thresholds CALIBRATED ON NORMAL BEHAVIOUR ONLY (healthy, offset drift, gain
    drift) from a separate draw, then frozen. Faults never seen at calibration.
  * 1-s smoothing uses mode='valid' (no zero-padding edge artefact).
  * A continuous sensitivity sweep over probe gain 0..1 shows where detection
    fails, instead of relying on a gap between hand-picked scenario ranges.
"""
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pathlib import Path
S = str(Path(__file__).resolve().parent.parent / "results"); Path(S).mkdir(exist_ok=True)
FS, PRE, POST, V = 10.0, 5.0, 90.0, 50.0
t = np.arange(-PRE, POST, 1 / FS)
K = np.ones(int(FS)) / FS

def response(rng, scen, gain_override=None):
    M0 = rng.uniform(15, 45)
    tau = rng.uniform(3, 15); Tr = rng.uniform(3, 10); Td = rng.uniform(60, 300)
    A = rng.uniform(0.30, 0.50) * V
    off, gain = 0.0, 1.0
    if scen == "offset_drift": off = rng.uniform(-20, 20)
    if scen == "gain_drift":   gain = rng.uniform(0.6, 0.9)
    if scen == "fouled":       gain = rng.uniform(0.05, 0.25); tau *= rng.uniform(1.5, 3)
    if scen == "dislodged":    gain = 0.0; M0 = rng.uniform(0, 10)   # near-air reading
    if scen == "free_water":   tau = rng.uniform(0, .3); Tr = rng.uniform(.2, .8); A = 100 - M0
    if gain_override is not None: gain = gain_override
    x = np.clip(t - tau, 0, None)
    shape = np.exp(-x / Td) - np.exp(-x / Tr); shape[t < tau] = 0
    m = M0 + off + gain * A * shape / max(shape.max(), 1e-9)
    m = m + rng.normal(0, rng.uniform(0.50, 0.94), len(t))
    if scen == "disconnected": m = np.zeros_like(t)   # ADC pinned -> clamp floor (TC-06)
    return np.clip(np.round(m), 0, 100)

def features(m):
    pre, post, tp = m[t < 0], m[t >= 0], t[t >= 0]
    b, s = pre.mean(), max(pre.std(), 0.5)
    pi = (post.max() - b) / V
    c = np.where(post > b + max(3 * s, 3))[0]
    tau = tp[c[0]] if len(c) else POST
    sm = np.convolve(post, K, mode="valid")
    g = np.max(np.diff(sm)) * FS
    return pi, tau, g

rng = np.random.default_rng(42)
NORMAL = ["healthy", "offset_drift", "gain_drift"]
FAULTS = ["fouled", "dislodged", "disconnected", "free_water"]

cal = np.array([features(response(rng, s)) for s in NORMAL for _ in range(1000)])
PI_MIN = np.percentile(cal[:, 0], 1.0)
TAU_MIN = np.percentile(cal[:, 1], 1.0)
G_MAX = np.percentile(cal[:, 2], 99.0)

def decide(pi, tau, g):
    return pi < PI_MIN or (tau < TAU_MIN and g > G_MAX)

def static_check(m):
    post = m[t >= 0]
    return bool(np.all(post <= 0) or np.all(post >= 100))

N = 2000
res, ex = {}, {}
for scen in NORMAL + FAULTS:
    a, b = [], []
    for i in range(N):
        m = response(rng, scen)
        a.append(decide(*features(m))); b.append(static_check(m))
        if i == 0: ex[scen] = m
    res[scen] = {"transient": float(np.mean(a)), "static": float(np.mean(b)), "n": N}

gains = np.round(np.linspace(0, 1, 21), 2)
sweep = []
for gv in gains:
    sweep.append(float(np.mean([decide(*features(response(rng, "healthy", gv)))
                                for _ in range(600)])))
g50 = float(np.interp(0.5, sweep[::-1], gains[::-1]))

json.dump({"thresholds": {"PI_MIN_pp_per_mL": float(PI_MIN), "TAU_MIN_s": float(TAU_MIN),
                          "G_MAX_pp_per_s": float(G_MAX)},
           "settings": {"fs_hz": FS, "dose_mL": V, "noise_sigma_pp": [.50, .94],
                        "calibration_draws": 3000, "test_draws": N},
           "results": res, "sweep": {"gain": gains.tolist(), "flag_rate": sweep,
                                     "gain_at_50pct_detection": g50}},
          open(S + "/probe_check_simulation.json", "w"), indent=2)

print(f"Thresholds (normal-only calibration): PI_MIN={PI_MIN:.3f} pp/mL  "
      f"TAU_MIN={TAU_MIN:.2f} s  G_MAX={G_MAX:.2f} pp/s")
print(f"{'scenario':<14}{'transient':>12}{'static':>10}")
for k, v in res.items():
    print(f"{k:<14}{v['transient']*100:>11.1f}%{v['static']*100:>9.1f}%")
print("gain sweep:", " ".join(f"{g:.2f}:{r*100:.0f}" for g, r in zip(gains, sweep)))
print(f"50% detection at probe gain {g50:.2f} of nominal")

lab = {"healthy": "Healthy", "offset_drift": "Offset drift (\u00B120 pp)",
       "gain_drift": "Gain drift (0.6\u20130.9\u00D7)", "fouled": "Fouled (0.05\u20130.25\u00D7)",
       "dislodged": "Dislodged", "disconnected": "Disconnected",
       "free_water": "In free water"}
fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.8, 3.2), dpi=200,
                              gridspec_kw={"width_ratios": [1.15, 1.05, 1]})
cols = {"healthy": "#2b6cb0", "offset_drift": "#4299e1", "gain_drift": "#90cdf4",
        "fouled": "#c05621", "dislodged": "#c53030", "free_water": "#6b46c1"}
for s in ["healthy", "offset_drift", "gain_drift", "fouled", "dislodged", "free_water"]:
    a.plot(t, ex[s], color=cols[s], lw=1, ls="-" if s in NORMAL else "--", label=lab[s])
a.axvline(0, color="#4a5568", lw=.8, ls=":")
a.set_xlim(-PRE, 60); a.set_ylim(-3, 138); a.set_yticks(range(0, 101, 20))
a.set_xlabel("Time from pulse (s)", fontsize=8); a.set_ylabel("Reported moisture (%)", fontsize=8)
a.tick_params(labelsize=7); a.legend(fontsize=5.4, loc="upper center", ncol=2, framealpha=.95, columnspacing=.8, handlelength=1.6)
a.set_title("(a) Example responses", fontsize=8.5, fontweight="bold")
a.grid(alpha=.25); a.spines[["top", "right"]].set_visible(False)

names = NORMAL + FAULTS; y = np.arange(len(names)); h = .38
b.barh(y - h / 2, [res[s]["transient"] * 100 for s in names], h, color="#2b6cb0",
       label="Transient test")
b.barh(y + h / 2, [res[s]["static"] * 100 for s in names], h, color="#a0aec0",
       label="Static clamp check")
b.set_yticks(y); b.set_yticklabels([lab[s] for s in names], fontsize=6.3)
b.invert_yaxis(); b.set_xlim(0, 100); b.axhline(2.5, color="#4a5568", lw=.8, ls=":")
b.set_xlabel("Flagged as fault (%)", fontsize=8); b.tick_params(axis="x", labelsize=7)
b.legend(fontsize=5.8, loc="lower right"); b.grid(axis="x", alpha=.25)
b.spines[["top", "right"]].set_visible(False)
b.set_title("(b) Flag rate, n=%d each" % N, fontsize=8.5, fontweight="bold")

c.plot(gains, np.array(sweep) * 100, "o-", color="#2b6cb0", ms=3, lw=1.2)
c.axhline(50, color="#a0aec0", lw=.8, ls=":")
c.axvspan(0.6, 0.9, color="#90cdf4", alpha=.25, lw=0)
c.text(0.75, 88, "normal\ndrift", ha="center", fontsize=6.5, color="#2c5282")
c.set_xlabel("Probe sensitivity (× nominal)", fontsize=8)
c.set_ylabel("Flagged as fault (%)", fontsize=8); c.tick_params(labelsize=7)
c.set_xlim(0, 1); c.set_ylim(-3, 103)
c.set_title("(c) Sensitivity sweep", fontsize=8.5, fontweight="bold")
c.grid(alpha=.25); c.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(S + "/probe_check_simulation.png"); plt.close(fig)
print("figure written")
