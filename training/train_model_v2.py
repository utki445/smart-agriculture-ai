"""
Crop Recommendation – Deep Neural Network
============================================
Trains a multi-layer DNN on crop recommendation dataset using
temperature, humidity, rainfall, and soil moisture as features.

Replaces the previous GradientBoosting model with a deep learning
approach for better generalization and IEEE publication novelty.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# ========== PATHS ==========
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATASET_DIR = PROJECT_ROOT / "IRSID_Dataset"

# Try .xlsx first (new IEEE data), then .csv fallback
XLSX_PATH = DATASET_DIR / "Crop_recommendation.xlsx"
CSV_PATH = PROJECT_ROOT / "data" / "crop_data.csv"
MODEL_SAVE_KERAS = PROJECT_ROOT / "models" / "crop_model.keras"
MODEL_SAVE_PKL = PROJECT_ROOT / "models" / "crop_model.pkl"
LABEL_ENCODER_PATH = PROJECT_ROOT / "models" / "crop_label_encoder.json"

# ========== CONFIG ==========
EPOCHS = 100
BATCH_SIZE = 32
LEARNING_RATE = 1e-3
TEST_SIZE = 0.2
SEED = 42

np.random.seed(SEED)


def load_dataset():
    """Load crop recommendation dataset from xlsx or csv"""
    
    # Try xlsx first (new IEEE version)
    if XLSX_PATH.exists():
        print(f"📁 Loading data from: {XLSX_PATH}")
        try:
            df = pd.read_excel(str(XLSX_PATH))
        except Exception as e:
            print(f"⚠️ Could not read xlsx ({e}), trying csv...")
            df = pd.read_csv(str(CSV_PATH))
    elif CSV_PATH.exists():
        print(f"📁 Loading data from: {CSV_PATH}")
        df = pd.read_csv(str(CSV_PATH))
    else:
        raise FileNotFoundError("No crop dataset found!")
    
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Sample:\n{df.head()}")
    
    return df


def prepare_features(df):
    """
    Prepare features for the DNN.
    Uses: temperature, humidity, rainfall
    Also includes N, P, K, ph if available (for richer features)
    """
    
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()
    
    # Find the label column
    label_col = None
    for candidate in ["label", "crop", "class", "target"]:
        if candidate in df.columns:
            label_col = candidate
            break
    
    if label_col is None:
        # Use last column as label
        label_col = df.columns[-1]
        print(f"⚠️ Using last column as label: {label_col}")
    
    # Select feature columns
    feature_candidates = ["temperature", "humidity", "rainfall", "n", "p", "k", "ph"]
    feature_cols = [col for col in feature_candidates if col in df.columns]
    
    if not feature_cols:
        # Try alternative names
        alt_names = {
            "temp": "temperature", "soil_temp": "temperature",
            "hum": "humidity", "soil_humidity": "humidity",
            "rain": "rainfall", "precipitation": "rainfall",
            "nitrogen": "n", "phosphorus": "p", "potassium": "k"
        }
        for alt, standard in alt_names.items():
            if alt in df.columns:
                df = df.rename(columns={alt: standard})
                if standard not in feature_cols:
                    feature_cols.append(standard)
    
    print(f"\n📊 Features used: {feature_cols}")
    print(f"   Label column: {label_col}")
    print(f"   Unique crops: {df[label_col].nunique()}")
    print(f"   Crops: {sorted(df[label_col].unique())}")
    
    X = df[feature_cols].values.astype(np.float32)
    y = df[label_col].values
    
    return X, y, feature_cols, label_col


def build_dnn(input_dim, num_classes):
    """
    Build a multi-layer DNN for crop recommendation.
    
    Architecture:
    Input → BatchNorm → Dense(256) → Dropout → Dense(128) → 
    Dropout → Dense(64) → Dropout → Dense(32) → Softmax
    """
    import tensorflow as tf
    
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(input_dim,)),
        tf.keras.layers.BatchNormalization(),
        
        tf.keras.layers.Dense(256, activation="relu",
                               kernel_regularizer=tf.keras.regularizers.l2(0.001)),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.3),
        
        tf.keras.layers.Dense(128, activation="relu",
                               kernel_regularizer=tf.keras.regularizers.l2(0.001)),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.25),
        
        tf.keras.layers.Dense(64, activation="relu",
                               kernel_regularizer=tf.keras.regularizers.l2(0.001)),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.2),
        
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dense(num_classes, activation="softmax")
    ], name="crop_dnn")
    
    print(f"\n🏗️ DNN Model:")
    model.summary()
    
    return model


def train():
    """Main training pipeline"""
    import tensorflow as tf
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    from sklearn.metrics import classification_report, accuracy_score
    
    print("=" * 60)
    print("🌾 CROP RECOMMENDATION DNN TRAINING")
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 1. Load data
    df = load_dataset()
    X, y_raw, feature_cols, label_col = prepare_features(df)
    
    # 2. Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_raw)
    num_classes = len(label_encoder.classes_)
    
    print(f"\n🏷️ Label encoding: {num_classes} classes")
    label_mapping = {name: int(idx) for idx, name in enumerate(label_encoder.classes_)}
    print(f"   {label_mapping}")
    
    # 3. Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 4. Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=TEST_SIZE, random_state=SEED, stratify=y
    )
    
    print(f"\n📊 Split: {len(X_train)} train / {len(X_test)} test")
    
    # 5. Build model
    model = build_dnn(X_train.shape[1], num_classes)
    
    # 6. Compile
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    
    # 7. Callbacks
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=15, restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=7, min_lr=1e-6
        ),
        tf.keras.callbacks.LearningRateScheduler(
            lambda epoch, lr: lr * 0.99 if epoch > 20 else lr
        ),
    ]
    
    # 8. Train
    print("\n" + "=" * 60)
    print("📈 TRAINING")
    print("=" * 60)
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1
    )
    
    # 9. Evaluate
    print("\n" + "=" * 60)
    print("📊 FINAL EVALUATION")
    print("=" * 60)
    
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"   Test Loss: {test_loss:.4f}")
    print(f"   Test Accuracy: {test_acc:.4f}")
    
    y_pred = np.argmax(model.predict(X_test, verbose=0), axis=1)
    
    print(f"\n📋 Classification Report:")
    print(classification_report(y_test, y_pred, 
                                 target_names=label_encoder.classes_))
    
    # 10. Compare with traditional methods
    print("\n" + "=" * 60)
    print("📊 COMPARISON WITH TRADITIONAL METHODS")
    print("=" * 60)
    
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.svm import SVC
    
    comparisons = {
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=SEED),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=200, random_state=SEED),
    }
    
    for name, clf in comparisons.items():
        clf.fit(X_train, y_train)
        clf_pred = clf.predict(X_test)
        clf_acc = accuracy_score(y_test, clf_pred)
        print(f"   {name}: {clf_acc:.4f}")
    
    print(f"   DNN (Ours): {test_acc:.4f}")
    
    # 11. Save model
    print("\n💾 Saving models...")
    
    # Save Keras model
    model.save(str(MODEL_SAVE_KERAS))
    print(f"   Keras model → {MODEL_SAVE_KERAS}")
    
    # Save label encoder and scaler for inference
    encoder_data = {
        "classes": list(label_encoder.classes_),
        "feature_cols": feature_cols,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "accuracy": float(test_acc)
    }
    with open(str(LABEL_ENCODER_PATH), "w") as f:
        json.dump(encoder_data, f, indent=2)
    print(f"   Encoder/scaler → {LABEL_ENCODER_PATH}")
    
    # Also save as pkl for backward compat (using a wrapper)
    import pickle
    wrapper = {
        "model_type": "keras_dnn",
        "keras_path": str(MODEL_SAVE_KERAS),
        "encoder": encoder_data
    }
    with open(str(MODEL_SAVE_PKL), "wb") as f:
        pickle.dump(wrapper, f)
    print(f"   PKL wrapper → {MODEL_SAVE_PKL}")
    
    # 12. Summary
    print("\n" + "=" * 60)
    print("🎉 TRAINING COMPLETE")
    print(f"   DNN Accuracy: {test_acc:.4f}")
    print(f"   Classes: {list(label_encoder.classes_)}")
    print(f"   Features: {feature_cols}")
    print("=" * 60)
    
    return model, label_encoder, scaler


if __name__ == "__main__":
    train()
