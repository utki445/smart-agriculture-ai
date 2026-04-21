# app/soil_condition_predictor.py
"""
Soil Condition Predictor — Dual-Head Novelty (Novelty 1)
=========================================================
Classifies soil images into physical condition classes:
  - healthy: Normal soil without visible defects
  - cracked: Dry stress cracks on surface
  - waterlogged: Saturated/flooded soil
  - compacted: Dense, lumpy, hard-packed soil

Uses EfficientNetV2-B0 (frozen) + Dense classifier.
"""

import os
import numpy as np
import json
from PIL import Image

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# Condition → Recommendation mapping for crop planner integration
CONDITION_ADVICE = {
    "healthy": {
        "icon": "✅",
        "color": "#10b981",
        "label": "Healthy",
        "description": "Soil is in good physical condition with no visible defects.",
        "crop_modifier": "standard",
        "irrigation_hint": "Normal watering schedule recommended.",
    },
    "cracked": {
        "icon": "🔶",
        "color": "#f59e0b",
        "label": "Cracked (Drought Stress)",
        "description": "Soil shows desiccation cracks indicating severe moisture deficit.",
        "crop_modifier": "drought_tolerant",
        "irrigation_hint": "Immediate deep watering required. Consider mulching to retain moisture.",
    },
    "waterlogged": {
        "icon": "🔵",
        "color": "#3b82f6",
        "label": "Waterlogged",
        "description": "Soil is oversaturated with standing water. Root rot risk is high.",
        "crop_modifier": "flood_tolerant",
        "irrigation_hint": "Stop irrigation immediately. Improve drainage before planting.",
    },
    "compacted": {
        "icon": "🟤",
        "color": "#a16207",
        "label": "Compacted / Dense",
        "description": "Soil appears hard-packed with poor porosity. Root penetration will be difficult.",
        "crop_modifier": "shallow_root",
        "irrigation_hint": "Aerate and till before planting. Drip irrigation recommended.",
    },
}


class SoilConditionPredictor:
    """
    Soil condition classifier using EfficientNetV2-B0 transfer learning.
    """

    IMG_SIZE = 224

    def __init__(self):
        self.model = None
        self.class_map = None
        self.loaded = False

        if not TF_AVAILABLE:
            print("⚠️ TensorFlow not available for condition predictor.")
            return

        # Resolve model paths
        base = os.path.dirname(os.path.abspath(__file__))
        model_candidates = [
            os.path.join(base, "..", "models", "soil_condition_model.keras"),
            os.path.join("models", "soil_condition_model.keras"),
        ]
        classes_candidates = [
            os.path.join(base, "..", "models", "soil_condition_classes.json"),
            os.path.join("models", "soil_condition_classes.json"),
        ]

        model_path = None
        for c in model_candidates:
            if os.path.exists(c):
                model_path = c
                break

        classes_path = None
        for c in classes_candidates:
            if os.path.exists(c):
                classes_path = c
                break

        if model_path and classes_path:
            try:
                self.model = tf.keras.models.load_model(model_path)
                with open(classes_path, "r") as f:
                    self.class_map = json.load(f)
                self.loaded = True
                print(f"✅ Soil Condition model loaded: {list(self.class_map.values())}")
            except Exception as e:
                print(f"⚠️ Condition model load failed: {e}")
        else:
            print(f"⚠️ Condition model files not found.")

    def predict(self, image_input):
        """
        Predict soil condition from an image.
        Returns dict with condition, confidence, advice, and all probabilities.
        """
        if not self.loaded or not self.model:
            return self._fallback_predict(image_input)

        try:
            # Preprocess
            if isinstance(image_input, str):
                img = Image.open(image_input).convert("RGB")
            elif isinstance(image_input, Image.Image):
                img = image_input.convert("RGB")
            else:
                img = Image.open(image_input).convert("RGB")

            img = img.resize((self.IMG_SIZE, self.IMG_SIZE))
            img_array = np.array(img, dtype=np.float32)
            img_batch = np.expand_dims(img_array, axis=0)

            # Predict
            probs = self.model.predict(img_batch, verbose=0)[0]
            predicted_idx = int(np.argmax(probs))
            condition = self.class_map.get(str(predicted_idx), "unknown")
            confidence = float(probs[predicted_idx])

            advice = CONDITION_ADVICE.get(condition, CONDITION_ADVICE["healthy"])

            all_probs = {}
            for i, p in enumerate(probs):
                cls_name = self.class_map.get(str(i), f"class_{i}")
                all_probs[cls_name] = float(p)

            return {
                "condition": condition,
                "confidence": confidence,
                "advice": advice,
                "all_probabilities": all_probs,
            }

        except Exception as e:
            print(f"⚠️ Condition prediction error: {e}")
            return self._fallback_predict(image_input)

    def _fallback_predict(self, image_input):
        """Color-based fallback when model is unavailable."""
        try:
            if isinstance(image_input, str):
                img = Image.open(image_input).convert("RGB")
            elif isinstance(image_input, Image.Image):
                img = image_input.convert("RGB")
            else:
                img = Image.open(image_input).convert("RGB")

            img = img.resize((self.IMG_SIZE, self.IMG_SIZE))
            arr = np.array(img, dtype=np.float32) / 255.0
            avg = np.mean(arr, axis=(0, 1))
            brightness = np.mean(avg)

            if brightness > 0.55:
                condition = "cracked"
            elif brightness < 0.2:
                condition = "waterlogged"
            else:
                condition = "healthy"
        except:
            condition = "healthy"

        return {
            "condition": condition,
            "confidence": 0.5,
            "advice": CONDITION_ADVICE.get(condition, CONDITION_ADVICE["healthy"]),
            "all_probabilities": {condition: 0.5},
        }
