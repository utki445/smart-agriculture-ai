"""
Source-disjoint vs augmentation-level evaluation of the soil classifiers
=========================================================================

Reproduces every accuracy figure in the Assessment-7 manuscript.

Why this script exists
----------------------
train_soil_model.py reports a stratified 5-fold score over *augmented* samples.
Because tiles and augmented copies of one source photograph then fall on both
sides of the split, that score measures how well the model recognises a
photograph, not how well it recognises soil. This script evaluates the same
features and the same classifier under two protocols:

  leaky            StratifiedKFold(5) over augmented samples
  source-disjoint  LeaveOneGroupOut, group = source photograph

Two further safeguards, both absent from train_soil_model.py:
  * StandardScaler is fitted inside each training fold (Pipeline), not on the
    full matrix before cross-validation.
  * SVM hyperparameters are fixed a priori (C=10, gamma='scale',
    class_weight='balanced'); nothing is tuned, so there is no selection leak.

Statistics reported
-------------------
  * bootstrap 95% CI resampling SOURCE PHOTOGRAPHS (the unit of independence)
  * naive sample-level Wilson CI, for comparison only (too narrow: samples
    from one photograph are not independent)
  * exact paired sign-flip permutation test over sources (2^n permutations)
  * sample-level McNemar, for comparison only (anti-conservative, same reason)
  * per-fold / per-source accuracy distributions
  * majority-class baseline
  * photograph-identification test (can features predict WHICH photo a tile
    came from?)

Backbones: EfficientNetV2-B0, MobileNetV2, ResNet50 (ImageNet, frozen, GAP).

Usage
-----
    python training/source_disjoint_eval.py            # writes results/source_disjoint_eval.json

Tiling and augmentation for the soil-type task are imported from
train_soil_model.py so the feature pipeline is identical to the deployed one.
"""

import os
import sys
import json
import random
import itertools
import warnings
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT_DIR = ROOT / "results"
OUT_DIR.mkdir(exist_ok=True)

import tensorflow as tf
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import LeaveOneGroupOut, StratifiedKFold, cross_val_predict
from sklearn.metrics import accuracy_score, confusion_matrix
from scipy.stats import chi2

import training.train_soil_model as T

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

BACKBONES = {
    "EfficientNetV2-B0": (tf.keras.applications.EfficientNetV2B0,
                          tf.keras.applications.efficientnet_v2.preprocess_input),
    "MobileNetV2": (tf.keras.applications.MobileNetV2,
                    tf.keras.applications.mobilenet_v2.preprocess_input),
    "ResNet50": (tf.keras.applications.ResNet50,
                 tf.keras.applications.resnet50.preprocess_input),
}
CONDITION_CLASSES = ["healthy", "cracked", "waterlogged", "compacted"]


def build_backbones():
    models = {}
    for name, (ctor, _) in BACKBONES.items():
        m = ctor(include_top=False, weights="imagenet", input_shape=(224, 224, 3), pooling="avg")
        m.trainable = False
        models[name] = m
    return models


def extract(models, name, batch):
    pre = BACKBONES[name][1]
    return models[name].predict(pre(batch.copy()), batch_size=32, verbose=0)


def soil_type_features(models):
    gt = T.load_ground_truth()
    samples, class_names, _ = T.load_all_images(gt)
    parts = {k: [] for k in BACKBONES}
    colour, y, g = [], [], []
    for s, data in samples.items():
        aug = T.augment_batch(data["images"], n_augmented=T.AUG_MULTIPLIER)
        for k in BACKBONES:
            parts[k].append(extract(models, k, aug))
        colour.append(T.extract_color_features(aug))
        y.extend([data["label"]] * len(aug))
        g.extend([s] * len(aug))
    feats = {k: np.vstack(v) for k, v in parts.items()}
    return feats, np.vstack(colour), np.array(y), np.array(g), class_names


def soil_condition_features(models):
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from PIL import Image
    root = ROOT / "IRSID_Dataset" / "soil_conditions"
    imgs, labels, groups = [], [], []
    gid = 0
    for idx, c in enumerate(CONDITION_CLASSES):
        for fn in sorted(os.listdir(root / c)):
            if not fn.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                continue
            imgs.append(np.array(Image.open(root / c / fn).convert("RGB").resize((224, 224))))
            labels.append(idx)
            groups.append(gid)
            gid += 1
    imgs = np.array(imgs)
    gen = ImageDataGenerator(rotation_range=30, width_shift_range=.2, height_shift_range=.2,
                             shear_range=.15, zoom_range=.25, horizontal_flip=True,
                             vertical_flip=True, brightness_range=[.7, 1.3],
                             channel_shift_range=30, fill_mode="reflect")
    X, y, g = [], [], []
    for i in range(len(imgs)):
        X.append(imgs[i]); y.append(labels[i]); g.append(groups[i])
        flow = gen.flow(imgs[i].reshape(1, 224, 224, 3), batch_size=1, seed=SEED + i)
        for _ in range(20):                       # 20 augmented + 1 original = 21 per source
            X.append(next(flow)[0].astype(np.uint8)); y.append(labels[i]); g.append(groups[i])
    X = np.array(X, dtype=np.float32)
    return {k: extract(models, k, X) for k in BACKBONES}, np.array(y), np.array(g)


def svm():
    return Pipeline([("scale", StandardScaler()),
                     ("svm", SVC(kernel="rbf", C=10, gamma="scale",
                                 class_weight="balanced", random_state=SEED))])


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [float(centre - half), float(centre + half)]


def source_bootstrap(y, pred, groups, n=4000):
    src = np.unique(groups)
    idx = {s: np.where(groups == s)[0] for s in src}
    rng = np.random.default_rng(SEED)
    acc = []
    for _ in range(n):
        sel = np.concatenate([idx[s] for s in rng.choice(src, len(src), replace=True)])
        acc.append(accuracy_score(y[sel], pred[sel]))
    return [float(np.percentile(acc, 2.5)), float(np.percentile(acc, 97.5))]


def sign_flip(y, p_leaky, p_honest, groups):
    """Exact two-sided paired permutation test over source photographs."""
    d = np.array([accuracy_score(y[groups == s], p_leaky[groups == s])
                  - accuracy_score(y[groups == s], p_honest[groups == s])
                  for s in np.unique(groups)])
    observed = abs(d.mean())
    hits = total = 0
    for signs in itertools.product((1, -1), repeat=len(d)):
        total += 1
        hits += abs((d * np.array(signs)).mean()) >= observed - 1e-12
    return {"p": hits / total, "permutations": total, "sources": int(len(d)),
            "sources_worse_under_disjoint": int((d > 0).sum())}


def mcnemar(y, a, b):
    ca, cb = a == y, b == y
    n01, n10 = int((ca & ~cb).sum()), int((~ca & cb).sum())
    if n01 + n10 == 0:
        return [n01, n10, 1.0]
    return [n01, n10, float(chi2.sf((abs(n01 - n10) - 1) ** 2 / (n01 + n10), 1))]


def evaluate(X, y, groups):
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    leaky = cross_val_predict(svm(), X, y, cv=skf)
    honest = cross_val_predict(svm(), X, y, groups=groups, cv=LeaveOneGroupOut())
    return {
        "leaky": float(accuracy_score(y, leaky)),
        "source_disjoint": float(accuracy_score(y, honest)),
        "leaky_fold_accuracies": [float(accuracy_score(y[te], leaky[te]))
                                  for _, te in skf.split(X, y)],
        "source_disjoint_per_source": {int(s): float(accuracy_score(y[groups == s],
                                                                    honest[groups == s]))
                                       for s in np.unique(groups)},
        "bootstrap_ci_leaky": source_bootstrap(y, leaky, groups),
        "bootstrap_ci_source_disjoint": source_bootstrap(y, honest, groups),
        "wilson_ci_leaky_naive": wilson(int((leaky == y).sum()), len(y)),
        "wilson_ci_source_disjoint_naive": wilson(int((honest == y).sum()), len(y)),
        "sign_flip_test": sign_flip(y, leaky, honest, groups),
        "mcnemar_naive": mcnemar(y, leaky, honest),
        "confusion_source_disjoint": confusion_matrix(y, honest).tolist(),
        "majority_baseline": float(np.bincount(y).max() / len(y)),
    }


def main():
    models = build_backbones()
    ft, colour, yt, gt_, type_classes = soil_type_features(models)
    fc, yc, gc = soil_condition_features(models)

    results = {"soil_type": {}, "soil_condition": {},
               "meta": {"soil_type_classes": type_classes,
                        "soil_condition_classes": CONDITION_CLASSES,
                        "soil_type_samples": int(len(yt)),
                        "soil_type_sources": int(len(np.unique(gt_))),
                        "soil_condition_samples": int(len(yc)),
                        "soil_condition_sources": int(len(np.unique(gc)))}}
    for name in BACKBONES:
        print(f"soil type      / {name}")
        results["soil_type"][name] = evaluate(np.hstack([ft[name], colour]), yt, gt_)
        print(f"soil condition / {name}")
        results["soil_condition"][name] = evaluate(fc[name], yc, gc)

    # Photograph identification: can the features name the SOURCE photograph of a tile?
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    pid = {}
    for label, X, groups in (("soil_type_cnn_plus_colour", np.hstack([ft["EfficientNetV2-B0"], colour]), gt_),
                             ("soil_type_colour_only", colour, gt_),
                             ("soil_condition_cnn", fc["EfficientNetV2-B0"], gc)):
        pred = cross_val_predict(svm(), X, groups, cv=skf)
        pid[label] = {"accuracy": float(accuracy_score(groups, pred)),
                      "chance": 1.0 / len(np.unique(groups))}
    results["photograph_identification"] = pid

    results["tiling_seed_study"] = tiling_seed_study(models)

    out = OUT_DIR / "source_disjoint_eval.json"
    json.dump(results, open(out, "w"), indent=2)
    print(f"wrote {out}")


def tiling_seed_study(models, seeds=(1, 2, 3, 4, 5)):
    """Repeat the EfficientNetV2-B0 evaluation with independent crop/augmentation seeds."""
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from PIL import Image
    name = "EfficientNetV2-B0"
    gt = T.load_ground_truth()
    root = ROOT / "IRSID_Dataset" / "soil_conditions"
    cimgs, clab = [], []
    for idx, c in enumerate(CONDITION_CLASSES):
        for fn in sorted(os.listdir(root / c)):
            if fn.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                cimgs.append(np.array(Image.open(root / c / fn).convert("RGB").resize((224, 224))))
                clab.append(idx)
    cimgs = np.array(cimgs)
    gen = ImageDataGenerator(rotation_range=30, width_shift_range=.2, height_shift_range=.2,
                             shear_range=.15, zoom_range=.25, horizontal_flip=True,
                             vertical_flip=True, brightness_range=[.7, 1.3],
                             channel_shift_range=30, fill_mode="reflect")
    runs = []
    for seed in seeds:
        random.seed(seed); np.random.seed(seed); tf.random.set_seed(seed)
        samples, _, _ = T.load_all_images(gt)
        X, y, g = [], [], []
        for s, d in samples.items():
            aug = T.augment_batch(d["images"], n_augmented=T.AUG_MULTIPLIER)
            X.append(np.hstack([extract(models, name, aug), T.extract_color_features(aug)]))
            y.extend([d["label"]] * len(aug)); g.extend([s] * len(aug))
        X, y, g = np.vstack(X), np.array(y), np.array(g)
        skf = StratifiedKFold(5, shuffle=True, random_state=seed)
        type_leaky = accuracy_score(y, cross_val_predict(svm(), X, y, cv=skf))
        type_disjoint = accuracy_score(y, cross_val_predict(svm(), X, y, groups=g, cv=LeaveOneGroupOut()))
        CI, CY, CG = [], [], []
        for i in range(len(cimgs)):
            CI.append(cimgs[i]); CY.append(clab[i]); CG.append(i)
            flow = gen.flow(cimgs[i].reshape(1, 224, 224, 3), batch_size=1, seed=seed * 1000 + i)
            for _ in range(20):
                CI.append(next(flow)[0].astype(np.uint8)); CY.append(clab[i]); CG.append(i)
        CX = extract(models, name, np.array(CI, dtype=np.float32))
        CY, CG = np.array(CY), np.array(CG)
        cond_leaky = accuracy_score(CY, cross_val_predict(svm(), CX, CY, cv=skf))
        cond_disjoint = accuracy_score(CY, cross_val_predict(svm(), CX, CY, groups=CG, cv=LeaveOneGroupOut()))
        runs.append({"seed": seed, "soil_type_leaky": type_leaky, "soil_type_source_disjoint": type_disjoint,
                     "soil_condition_leaky": cond_leaky, "soil_condition_source_disjoint": cond_disjoint})
        print(f"seed {seed}: type {type_leaky:.3f} -> {type_disjoint:.3f}   "
              f"condition {cond_leaky:.3f} -> {cond_disjoint:.3f}")
    return runs


if __name__ == "__main__":
    main()
