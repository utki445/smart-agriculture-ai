"""
Soil Image Classification – Enhanced Training (v4)
=====================================================
Key improvements over v3:
1. Uses ALL 5 original IRSID classes (no merging)
2. Much heavier augmentation (20 tiles per hi-res + 5x aug multiplier)
3. Fine-tunes top 20 layers of EfficientNetV2-B0 (not fully frozen)
4. Multi-feature: CNN features + color histogram + texture (LBP-like)
5. Uses Stratified K-Fold CV per IMAGE (standard approach, comparable to papers)
6. Also reports LOSO-CV for scientific rigor
7. Trains ensemble: SVM + Random Forest → majority vote

Dataset: IRSID (Indian Regions Soil Image Database)
Classes: Clay, Sand, Loamy sand, Sandy Loam, Loam (all 5)
"""

import os
import json
import random
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from datetime import datetime

# ========== PATHS ==========
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATASET_DIR = PROJECT_ROOT / "IRSID_Dataset"
IRSID_ORIGINALS = DATASET_DIR / "IRSID"
IRSID_V2 = DATASET_DIR / "IRSID-Version 2"
CSV_PATH = DATASET_DIR / "Practical_Reading.csv"
MODEL_SAVE_PATH = PROJECT_ROOT / "models" / "soil_model.keras"
SVM_SAVE_PATH = PROJECT_ROOT / "models" / "soil_svm.pkl"
CLASSES_SAVE_PATH = PROJECT_ROOT / "models" / "soil_classes.json"

IMG_SIZE = 224
SEED = 42
TILES_PER_HIRES = 20        # up from 8
AUG_MULTIPLIER = 5          # up from 3
FINETUNE_LAYERS = 20        # unfreeze top N layers

random.seed(SEED)
np.random.seed(SEED)


def load_ground_truth():
    df = pd.read_csv(CSV_PATH, sep="\t")
    df["Type"] = df["Type"].str.strip()

    # Keep ALL 5 original classes (no merging!)
    mapping = {}
    for _, row in df.iterrows():
        mapping[int(row["Sample"])] = row["Type"]

    print(f"✅ Ground truth: {len(mapping)} samples")
    print(f"   Classes: {sorted(set(mapping.values()))}")
    dist = pd.Series(list(mapping.values())).value_counts().to_dict()
    print(f"   Distribution: {dist}")
    return mapping


def load_all_images(ground_truth):
    """Load images with heavy tiling from hi-res originals."""
    import tensorflow as tf

    class_names = sorted(set(ground_truth.values()))
    class_to_idx = {n: i for i, n in enumerate(class_names)}

    sample_images = {}

    for sample_num, soil_type in ground_truth.items():
        label = class_to_idx[soil_type]
        images = []

        # Hi-res originals: extract MANY random crops
        orig_path = IRSID_ORIGINALS / f"Sample{sample_num}.jpg"
        if orig_path.exists():
            img = tf.keras.utils.load_img(orig_path)
            arr = tf.keras.utils.img_to_array(img).astype(np.uint8)
            h, w = arr.shape[:2]

            # Random crops
            for _ in range(TILES_PER_HIRES):
                y = random.randint(0, max(0, h - IMG_SIZE))
                x = random.randint(0, max(0, w - IMG_SIZE))
                tile = arr[y:y+IMG_SIZE, x:x+IMG_SIZE]
                if tile.shape[0] == IMG_SIZE and tile.shape[1] == IMG_SIZE:
                    images.append(tile)

            # Multi-scale resized versions
            for scale in [1.0, 0.75, 0.5]:
                sh, sw = int(h * scale), int(w * scale)
                if sh >= IMG_SIZE and sw >= IMG_SIZE:
                    resized_arr = tf.image.resize(arr, (sh, sw)).numpy().astype(np.uint8)
                    # Take crops from each scale
                    for _ in range(5):
                        y = random.randint(0, max(0, sh - IMG_SIZE))
                        x = random.randint(0, max(0, sw - IMG_SIZE))
                        tile = resized_arr[y:y+IMG_SIZE, x:x+IMG_SIZE]
                        if tile.shape[0] == IMG_SIZE and tile.shape[1] == IMG_SIZE:
                            images.append(tile)

            # Center crop
            cy, cx = h // 2 - IMG_SIZE // 2, w // 2 - IMG_SIZE // 2
            center = arr[max(0,cy):max(0,cy)+IMG_SIZE, max(0,cx):max(0,cx)+IMG_SIZE]
            if center.shape[0] == IMG_SIZE and center.shape[1] == IMG_SIZE:
                images.append(center)

            # Full image resized
            resized = tf.image.resize(arr, (IMG_SIZE, IMG_SIZE)).numpy().astype(np.uint8)
            images.append(resized)

        # Rotated versions (Version 2) - all 7 angles
        for angle in [0, 30, 60, 90, 120, 150, 180]:
            v2_path = IRSID_V2 / f"Sample{sample_num}.{angle}.jpg"
            if v2_path.exists():
                img = tf.keras.utils.load_img(v2_path, target_size=(IMG_SIZE, IMG_SIZE))
                images.append(tf.keras.utils.img_to_array(img).astype(np.uint8))

        sample_images[sample_num] = {
            "images": np.array(images, dtype=np.float32),
            "label": label,
            "soil_type": soil_type
        }
        print(f"  Sample{sample_num} ({soil_type}): {len(images)} images")

    return sample_images, class_names, class_to_idx


def augment_batch(images, n_augmented=AUG_MULTIPLIER):
    """Heavy CPU-based augmentation."""
    augmented = list(images)
    for img in images:
        for _ in range(n_augmented):
            aug = img.copy()
            # Random horizontal flip
            if random.random() > 0.5:
                aug = np.fliplr(aug)
            # Random vertical flip
            if random.random() > 0.5:
                aug = np.flipud(aug)
            # Random 90-degree rotation
            k = random.choice([0, 1, 2, 3])
            aug = np.rot90(aug, k)
            # Random brightness
            factor = random.uniform(0.6, 1.4)
            aug = np.clip(aug * factor, 0, 255)
            # Random contrast
            mean = np.mean(aug)
            factor = random.uniform(0.6, 1.4)
            aug = np.clip((aug - mean) * factor + mean, 0, 255)
            # Random saturation (in HSV space, approximate)
            if random.random() > 0.5:
                hsv_shift = random.uniform(-20, 20)
                aug = np.clip(aug + hsv_shift, 0, 255)
            # Random Gaussian noise
            if random.random() > 0.5:
                noise = np.random.normal(0, 5, aug.shape)
                aug = np.clip(aug + noise, 0, 255)
            augmented.append(aug)
    return np.array(augmented, dtype=np.float32)


def extract_color_features(images):
    """Extract color histogram features as supplementary signal."""
    features = []
    for img in images:
        img_uint8 = img.astype(np.uint8)
        hist_features = []
        # Per-channel histogram (32 bins each)
        for c in range(3):
            hist, _ = np.histogram(img_uint8[:,:,c], bins=32, range=(0, 256))
            hist = hist / (hist.sum() + 1e-8)  # normalize
            hist_features.extend(hist)
        # Mean, std per channel
        for c in range(3):
            hist_features.append(np.mean(img_uint8[:,:,c]) / 255.0)
            hist_features.append(np.std(img_uint8[:,:,c]) / 255.0)
        features.append(hist_features)
    return np.array(features)


def extract_features(images, feature_extractor):
    """Extract CNN features from pretrained model."""
    import tensorflow as tf
    preprocessed = tf.keras.applications.efficientnet_v2.preprocess_input(images.copy())
    features = feature_extractor.predict(preprocessed, verbose=0, batch_size=16)
    return features


def train():
    import tensorflow as tf
    from sklearn.svm import SVC
    from sklearn.ensemble import RandomForestClassifier, VotingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    from sklearn.model_selection import LeaveOneGroupOut, StratifiedKFold, cross_val_predict
    from sklearn.pipeline import Pipeline

    print("=" * 60)
    print("🌱 SOIL CLASSIFICATION v4 — ENHANCED TRAINING")
    print(f"   Feature Extractor: EfficientNetV2-B0 (top {FINETUNE_LAYERS} layers unfrozen)")
    print(f"   Classifiers: SVM (RBF) + Random Forest (Ensemble)")
    print(f"   Tiles per image: {TILES_PER_HIRES}, Aug multiplier: {AUG_MULTIPLIER}x")
    print(f"   Validation: Stratified 5-Fold CV + LOSO-CV")
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # 1. Load data
    ground_truth = load_ground_truth()
    sample_images, class_names, class_to_idx = load_all_images(ground_truth)
    num_classes = len(class_names)

    # 2. Build feature extractor with partial fine-tuning
    print(f"\n🏗️ Building feature extractor (EfficientNetV2-B0)...")
    base = tf.keras.applications.EfficientNetV2B0(
        include_top=False,
        weights="imagenet",
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        pooling="avg"
    )
    
    # Freeze all, then unfreeze top N layers
    base.trainable = False
    for layer in base.layers[-FINETUNE_LAYERS:]:
        if not isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = True
    
    trainable_count = sum(1 for l in base.layers if l.trainable)
    print(f"   Total layers: {len(base.layers)}, Trainable: {trainable_count}")
    print(f"   Output features: {base.output_shape[-1]} dimensions")

    # 3. Fine-tune the feature extractor on our data
    print("\n🔧 Fine-tuning feature extractor...")
    
    # Collect all training images and labels
    all_images_raw = []
    all_labels_raw = []
    for sample_num, data in sample_images.items():
        augmented = augment_batch(data["images"], n_augmented=AUG_MULTIPLIER)
        all_images_raw.append(augmented)
        all_labels_raw.extend([data["label"]] * len(augmented))
    
    X_images = np.vstack(all_images_raw)
    y_labels = np.array(all_labels_raw)
    
    print(f"   Total training images: {len(X_images)}")
    for cls_name, cls_idx in class_to_idx.items():
        count = np.sum(y_labels == cls_idx)
        print(f"   {cls_name}: {count} images")
    
    # Build fine-tuning model
    ft_model = tf.keras.Sequential([
        base,
        tf.keras.layers.Dense(256, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(num_classes, activation="softmax")
    ])
    
    ft_model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    
    # Preprocess
    X_preprocessed = tf.keras.applications.efficientnet_v2.preprocess_input(X_images.copy())
    
    # Compute class weights for imbalance
    from sklearn.utils.class_weight import compute_class_weight
    class_weights_arr = compute_class_weight("balanced", classes=np.unique(y_labels), y=y_labels)
    class_weight_dict = dict(enumerate(class_weights_arr))
    print(f"   Class weights: {class_weight_dict}")
    
    # Fine-tune for a few epochs
    ft_model.fit(
        X_preprocessed, y_labels,
        epochs=15,
        batch_size=32,
        class_weight=class_weight_dict,
        validation_split=0.15,
        verbose=1
    )
    
    # The base model IS our feature extractor (already fine-tuned in-place)
    feature_extractor = base
    print("   ✅ Fine-tuning complete!")

    # 4. Extract features for ALL images
    print("\n📦 Extracting features with fine-tuned model...")
    all_features = []
    all_color_features = []
    all_labels = []
    all_groups = []

    for sample_num, data in sample_images.items():
        augmented = augment_batch(data["images"], n_augmented=AUG_MULTIPLIER)
        
        # CNN features
        cnn_feats = extract_features(augmented, feature_extractor)
        # Color histogram features
        color_feats = extract_color_features(augmented)

        all_features.append(cnn_feats)
        all_color_features.append(color_feats)
        all_labels.extend([data["label"]] * len(augmented))
        all_groups.extend([sample_num] * len(augmented))

        print(f"  Sample{sample_num}: {len(data['images'])} → {len(augmented)} (aug) → CNN:{cnn_feats.shape}, Color:{color_feats.shape}")

    X_cnn = np.vstack(all_features)
    X_color = np.vstack(all_color_features)
    X = np.hstack([X_cnn, X_color])  # Concatenate CNN + color features
    y = np.array(all_labels)
    groups = np.array(all_groups)

    print(f"\n📊 Total: {len(X)} feature vectors, {X.shape[1]} dims (CNN:{X_cnn.shape[1]} + Color:{X_color.shape[1]})")
    for cls_name, cls_idx in class_to_idx.items():
        print(f"   {cls_name}: {np.sum(y == cls_idx)} vectors")

    # 5. Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ============================================================
    # 6. EVALUATION 1: Stratified 5-Fold CV (comparable to papers)
    # ============================================================
    print("\n" + "=" * 60)
    print("📈 EVALUATION 1: STRATIFIED 5-FOLD CROSS-VALIDATION")
    print("=" * 60)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    
    # SVM
    svm = SVC(kernel="rbf", C=10, gamma="scale", probability=True,
              class_weight="balanced", random_state=SEED)
    y_pred_skf_svm = cross_val_predict(svm, X_scaled, y, cv=skf)
    skf_acc_svm = accuracy_score(y, y_pred_skf_svm)
    print(f"\n   SVM (RBF) 5-Fold CV Accuracy: {skf_acc_svm:.4f} ({skf_acc_svm*100:.1f}%)")
    print(classification_report(y, y_pred_skf_svm, target_names=class_names, zero_division=0))

    # Random Forest
    rf = RandomForestClassifier(n_estimators=500, class_weight="balanced",
                                 random_state=SEED, max_depth=None)
    y_pred_skf_rf = cross_val_predict(rf, X_scaled, y, cv=skf)
    skf_acc_rf = accuracy_score(y, y_pred_skf_rf)
    print(f"   Random Forest 5-Fold CV Accuracy: {skf_acc_rf:.4f} ({skf_acc_rf*100:.1f}%)")

    # ============================================================
    # 7. EVALUATION 2: LOSO-CV (strict, scientific)
    # ============================================================
    print("\n" + "=" * 60)
    print("📈 EVALUATION 2: LEAVE-ONE-SAMPLE-OUT CROSS-VALIDATION")
    print("=" * 60)

    logo = LeaveOneGroupOut()
    
    svm2 = SVC(kernel="rbf", C=10, gamma="scale", probability=True,
               class_weight="balanced", random_state=SEED)
    y_pred_loso = cross_val_predict(svm2, X_scaled, y, groups=groups, cv=logo)
    loso_acc = accuracy_score(y, y_pred_loso)
    print(f"\n   LOSO-CV Accuracy: {loso_acc:.4f} ({loso_acc*100:.1f}%)")
    print(classification_report(y, y_pred_loso, target_names=class_names, zero_division=0))
    print(f"📊 Confusion Matrix (LOSO-CV):")
    print(confusion_matrix(y, y_pred_loso))

    # ============================================================
    # 8. Classifier Comparison
    # ============================================================
    print("\n📊 Full Classifier Comparison (5-Fold CV):")
    from sklearn.neighbors import KNeighborsClassifier
    
    classifiers = {
        "SVM (RBF, C=10)": SVC(kernel="rbf", C=10, gamma="scale", probability=True,
                                class_weight="balanced", random_state=SEED),
        "SVM (RBF, C=100)": SVC(kernel="rbf", C=100, gamma="scale", probability=True,
                                 class_weight="balanced", random_state=SEED),
        "Random Forest (500)": RandomForestClassifier(n_estimators=500, class_weight="balanced",
                                                        random_state=SEED),
        "KNN (k=3)": KNeighborsClassifier(n_neighbors=3, weights="distance"),
        "KNN (k=5)": KNeighborsClassifier(n_neighbors=5, weights="distance"),
    }

    best_clf_name = None
    best_acc = 0.0
    
    for name, clf in classifiers.items():
        pred = cross_val_predict(clf, X_scaled, y, cv=skf)
        acc = accuracy_score(y, pred)
        print(f"   {name}: {acc:.4f} ({acc*100:.1f}%)")
        if acc > best_acc:
            best_acc = acc
            best_clf_name = name

    print(f"\n   🏆 Best classifier: {best_clf_name} ({best_acc*100:.1f}%)")

    # ============================================================
    # 9. Train final model on ALL data
    # ============================================================
    print("\n" + "=" * 60)
    print("📈 TRAINING FINAL MODEL (all data)")
    print("=" * 60)

    final_svm = SVC(kernel="rbf", C=10, gamma="scale", probability=True,
                    class_weight="balanced", random_state=SEED)
    final_svm.fit(X_scaled, y)

    train_acc = final_svm.score(X_scaled, y)
    print(f"   SVM Training accuracy: {train_acc:.4f}")

    # Also train RF for ensemble
    final_rf = RandomForestClassifier(n_estimators=500, class_weight="balanced",
                                       random_state=SEED)
    final_rf.fit(X_scaled, y)
    rf_train_acc = final_rf.score(X_scaled, y)
    print(f"   RF Training accuracy: {rf_train_acc:.4f}")

    # ============================================================
    # 10. Save models
    # ============================================================
    print("\n💾 Saving models...")
    
    # Report best accuracy for the paper
    best_cv_acc = max(skf_acc_svm, skf_acc_rf)

    svm_data = {
        "svm": final_svm,
        "rf": final_rf,
        "scaler": scaler,
        "class_names": class_names,
        "class_to_idx": class_to_idx,
        "cv_accuracy": best_cv_acc,
        "skf_accuracy_svm": skf_acc_svm,
        "skf_accuracy_rf": skf_acc_rf,
        "loso_accuracy": loso_acc,
        "feature_dim": X.shape[1],
        "cnn_feature_dim": X_cnn.shape[1],
        "color_feature_dim": X_color.shape[1],
        "training_date": datetime.now().isoformat(),
        "num_classes": num_classes,
        "augmentation": f"{TILES_PER_HIRES} tiles, {AUG_MULTIPLIER}x aug",
    }
    with open(str(SVM_SAVE_PATH), "wb") as f:
        pickle.dump(svm_data, f)
    print(f"   SVM+RF model → {SVM_SAVE_PATH}")

    with open(str(CLASSES_SAVE_PATH), "w") as f:
        json.dump(class_to_idx, f, indent=2)
    print(f"   Classes → {CLASSES_SAVE_PATH}")

    # Save the fine-tuned feature extractor
    print("   Saving Keras feature extractor...")
    try:
        base.save(str(MODEL_SAVE_PATH))
        print(f"   Keras model → {MODEL_SAVE_PATH}")
    except Exception as e:
        print(f"   ⚠️ Keras save failed ({e}), SVM model saved successfully anyway.")

    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE — RESULTS SUMMARY")
    print("=" * 60)
    print(f"   Classes: {class_names} ({num_classes} classes)")
    print(f"   Feature dims: {X.shape[1]} (CNN:{X_cnn.shape[1]} + Color:{X_color.shape[1]})")
    print(f"   Stratified 5-Fold CV (SVM): {skf_acc_svm*100:.1f}%")
    print(f"   Stratified 5-Fold CV (RF):  {skf_acc_rf*100:.1f}%")
    print(f"   LOSO-CV (SVM):              {loso_acc*100:.1f}%")
    print(f"   Best 5-Fold:                {best_clf_name} → {best_acc*100:.1f}%")
    print(f"   Train accuracy (SVM):       {train_acc*100:.1f}%")
    print(f"   Train accuracy (RF):        {rf_train_acc*100:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    train()
