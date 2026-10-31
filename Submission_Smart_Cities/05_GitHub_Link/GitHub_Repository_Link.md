# GitHub Repository

## Link

**https://github.com/utki445/smart-agriculture-ai**

---

## Before submitting — verify

- [ ] The repository is set to **Public** (Settings → General → Danger Zone → Change visibility)
- [ ] The README renders correctly on the repository landing page
- [ ] The latest commit includes the corrected README and `hardware/WIRING.md`

> **Important:** the README was corrected on 31 October 2026. The previous version quoted
> soil-type accuracy as 94.4 %, soil condition as 100 %, and fusion accuracy as 98.7 % —
> all of which contradict the project report. It also listed the wrong sensor (DHT22) and
> the wrong LED pins. If these changes are not yet pushed, push them before submitting,
> or an evaluator comparing the repository against the report will find a direct conflict.

---

## What the repository contains

| Path | Contents |
|---|---|
| `hardware/` | ESP32 firmware (`smart_agri.ino`) and `WIRING.md` build guide |
| `edge/` | Serial telemetry collector |
| `app/` | Streamlit dashboard, soil predictors, irrigation scheduler |
| `planner/` | Crop suitability reasoning and reporting |
| `training/` | Model training and `source_disjoint_eval.py` — the main experiment |
| `training/figures/` | Scripts that regenerate every report figure at 600 dpi |
| `results/` | Evaluation outputs (JSON) and generated figures |
| `Docs/` | Project reports, proposal and slide deck |

## Reproducing the headline result

```bash
python training/source_disjoint_eval.py
```

Produces every accuracy, confidence interval and p-value quoted in Sections 5.4 and 6.3 of
the report. Nothing in the figures is hard-coded — they are regenerated from the files in
`results/` and `data/`.

## Note on trained models

Model weights (~128 MB) are not committed, as they exceed sensible repository limits.
Regenerate with `training/train_soil_model.py` and `training/train_condition_model.py`.
