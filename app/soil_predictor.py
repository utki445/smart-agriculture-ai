# app/soil_predictor.py
"""
Soil Type Predictor – EfficientNetV2 + SVM Hybrid
===================================================
Uses pretrained EfficientNetV2 as feature extractor + SVM classifier.
Also supports Keras end-to-end model as fallback.
Provides confidence scores, top-3 predictions, and Grad-CAM.
"""

import os
import numpy as np
import json
import pickle
from PIL import Image

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("WARNING: TensorFlow not available.")


class SoilPredictor:
    """
    Soil type predictor using EfficientNetV2 features + SVM classifier.
    Falls back to Keras model or color-based heuristic.
    """

    IMG_SIZE = 224

    def __init__(self, model_path="models/soil_model.keras",
                 svm_path="models/soil_svm.pkl",
                 classes_path="models/soil_classes.json"):
        self.keras_model = None
        self.svm_model = None
        self.feature_extractor = None
        self.scaler = None
        self.class_indices = None
        self.index_to_class = None
        self.model_loaded = False
        self.model_type = None  # "svm" or "keras" or "fallback"
        self._last_gradcam = None

        # Resolve paths
        def resolve(path):
            candidates = [
                path,
                os.path.join("models", os.path.basename(path)),
                os.path.join("..", "models", os.path.basename(path)),
                os.path.join(os.path.dirname(__file__), "..", "models", os.path.basename(path))
            ]
            for c in candidates:
                if os.path.exists(c):
                    return c
            return None

        # 1. Try SVM model (best approach)
        svm_file = resolve(svm_path)
        if svm_file:
            try:
                with open(svm_file, "rb") as f:
                    svm_data = pickle.load(f)
                self.svm_model = svm_data["svm"]
                self.scaler = svm_data["scaler"]
                class_names = svm_data["class_names"]
                self.class_indices = {n: i for i, n in enumerate(class_names)}
                self.index_to_class = {i: n for i, n in enumerate(class_names)}
                self.model_type = "svm"
                self.model_loaded = True

                # Build feature extractor
                if TF_AVAILABLE:
                    self.feature_extractor = tf.keras.applications.EfficientNetV2B0(
                        include_top=False, weights="imagenet",
                        input_shape=(self.IMG_SIZE, self.IMG_SIZE, 3),
                        pooling="avg"
                    )
                    self.feature_extractor.trainable = False

                cv_acc = svm_data.get("cv_accuracy", "N/A")
                print(f"✅ SVM model loaded (CV accuracy: {cv_acc})")
                print(f"   Classes: {class_names}")
            except Exception as e:
                print(f"⚠️ SVM load failed: {e}")

        # 2. Fallback: try Keras model
        if not self.model_loaded and TF_AVAILABLE:
            keras_file = resolve(model_path)
            if keras_file:
                try:
                    self.keras_model = tf.keras.models.load_model(keras_file)
                    self.model_type = "keras"
                    self.model_loaded = True
                    print(f"✅ Keras model loaded from: {keras_file}")
                except Exception as e:
                    print(f"⚠️ Keras load failed: {e}")

        # 3. Load class mapping
        if self.class_indices is None:
            cls_file = resolve(classes_path)
            if cls_file:
                try:
                    with open(cls_file, "r") as f:
                        self.class_indices = json.load(f)
                    self.index_to_class = {v: k for k, v in self.class_indices.items()}
                except:
                    pass

        if self.class_indices is None:
            self.class_indices = {"Clay": 0, "Loam": 1, "Loamy sand": 2, "Sand": 3, "Sandy Loam": 4}
            self.index_to_class = {v: k for k, v in self.class_indices.items()}

        if not self.model_loaded:
            self.model_type = "fallback"
            print("⚠️ Soil predictor using fallback mode")
        
        print(f"   Mode: {self.model_type}")

    def _preprocess_image(self, image_input):
        """Load and preprocess image."""
        if isinstance(image_input, str):
            img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        else:
            img = Image.open(image_input).convert("RGB")

        img = img.resize((self.IMG_SIZE, self.IMG_SIZE))
        img_array = np.array(img, dtype=np.float32)
        return img_array, img

    def predict(self, image_input):
        """Predict soil type. Returns string."""
        return self.predict_detailed(image_input)["predicted_class"]

    def predict_detailed(self, image_input, sensor_data=None):
        """Get detailed prediction with confidence and top-3.
        
        Args:
            image_input: Image file path, PIL Image, or file-like object
            sensor_data: Optional dict with IoT sensor readings for multimodal fusion
                         Keys: 'temperature', 'humidity', 'moisture' (Novelty 3)
        """
        try:
            img_array, pil_img = self._preprocess_image(image_input)
            img_batch = np.expand_dims(img_array, axis=0)

            if self.model_type == "svm" and self.svm_model and self.feature_extractor:
                # SVM path: extract features → scale → predict
                preprocessed = tf.keras.applications.efficientnet_v2.preprocess_input(img_batch.copy())
                cnn_features = self.feature_extractor.predict(preprocessed, verbose=0)
                
                # Extract color histogram features
                img_uint8 = img_array.astype(np.uint8)
                color_features = []
                for c in range(3):
                    hist, _ = np.histogram(img_uint8[:,:,c], bins=32, range=(0, 256))
                    hist = hist / (hist.sum() + 1e-8)
                    color_features.extend(hist)
                for c in range(3):
                    color_features.append(np.mean(img_uint8[:,:,c]) / 255.0)
                    color_features.append(np.std(img_uint8[:,:,c]) / 255.0)
                
                combined_features = np.concatenate([cnn_features[0], color_features])
                
                # Sensor-Vision Fusion (Novelty 3): append IoT sensor features
                fusion_mode = "vision-only"
                if sensor_data and isinstance(sensor_data, dict):
                    temp = sensor_data.get('temperature')
                    hum = sensor_data.get('humidity')
                    moist = sensor_data.get('moisture')
                    if temp is not None and hum is not None and moist is not None:
                        # Normalize sensor features to [0, 1] range
                        sensor_features = [
                            float(temp) / 50.0,    # Temp: 0-50°C → 0-1
                            float(hum) / 100.0,    # Humidity: 0-100% → 0-1
                            float(moist) / 100.0,   # Moisture: 0-100% → 0-1
                        ]
                        combined_features = np.concatenate([combined_features, sensor_features])
                        fusion_mode = "sensor-fused"
                
                combined_features = combined_features.reshape(1, -1)
                
                # Handle feature dimension mismatch gracefully
                expected_dim = self.scaler.n_features_in_
                actual_dim = combined_features.shape[1]
                if actual_dim > expected_dim:
                    # Trim extra sensor features if scaler wasn't trained with them
                    combined_features = combined_features[:, :expected_dim]
                    fusion_mode = "vision-only (scaler compat)"
                elif actual_dim < expected_dim:
                    # Pad with zeros if somehow shorter
                    pad = np.zeros((1, expected_dim - actual_dim))
                    combined_features = np.concatenate([combined_features, pad], axis=1)
                
                features_scaled = self.scaler.transform(combined_features)

                probs = self.svm_model.predict_proba(features_scaled)[0]
                predicted_idx = int(np.argmax(probs))
                confidence = float(probs[predicted_idx])
                predicted_class = self.index_to_class.get(predicted_idx, "Unknown")

            elif self.model_type == "keras" and self.keras_model:
                # Keras path
                prediction = self.keras_model.predict(img_batch / 255.0, verbose=0)
                probs = prediction[0]
                predicted_idx = int(np.argmax(probs))
                confidence = float(probs[predicted_idx])
                predicted_class = self.index_to_class.get(predicted_idx, "Unknown")

            else:
                # Fallback
                predicted_class = self._color_based_fallback(img_array / 255.0)
                return {
                    "predicted_class": predicted_class,
                    "confidence": 0.5,
                    "top3": [{"class": predicted_class, "confidence": 0.5}],
                    "all_probabilities": {predicted_class: 0.5}
                }

            # Top 3
            top3_indices = np.argsort(probs)[::-1][:3]
            top3 = [{"class": self.index_to_class.get(int(i), "Unknown"),
                      "confidence": float(probs[i])} for i in top3_indices]

            all_probs = {self.index_to_class.get(i, f"class_{i}"): float(probs[i])
                         for i in range(len(probs))}

            print(f"[PREDICTION] {predicted_class} ({confidence:.1%}) [method: {self.model_type}, fusion: {fusion_mode if self.model_type == 'svm' else 'N/A'}]")

            return {
                "predicted_class": predicted_class,
                "confidence": confidence,
                "top3": top3,
                "all_probabilities": all_probs
            }

        except Exception as e:
            print(f"ERROR in prediction: {e}")
            return {
                "predicted_class": "Clay",
                "confidence": 0.0,
                "top3": [{"class": "Clay", "confidence": 0.0}],
                "all_probabilities": {},
                "error": str(e)
            }

    def generate_gradcam(self, image_input, target_class=None):
        """Generate Grad-CAM heatmap."""
        if not TF_AVAILABLE:
            return None

        try:
            img_array, pil_img = self._preprocess_image(image_input)
            img_batch = np.expand_dims(img_array, axis=0)

            # Get the base model (feature extractor)
            if self.model_type == "svm" and self.feature_extractor:
                base = self.feature_extractor
                preprocessed = tf.keras.applications.efficientnet_v2.preprocess_input(img_batch.copy())
            elif self.model_type == "keras" and self.keras_model:
                # Try to find base model inside keras model
                base = None
                for layer in self.keras_model.layers:
                    if hasattr(layer, 'layers') and len(layer.layers) > 10:
                        base = layer
                        break
                if base is None:
                    return None
                preprocessed = img_batch / 255.0
            else:
                return None

            # Find last conv layer
            last_conv = None
            for layer in reversed(base.layers):
                if 'conv' in layer.name.lower() and len(layer.output.shape) == 4:
                    last_conv = layer
                    break

            if last_conv is None:
                return None

            # Build grad model
            grad_model = tf.keras.Model(
                inputs=base.inputs,
                outputs=[last_conv.output, base.output]
            )

            with tf.GradientTape() as tape:
                conv_out, features = grad_model(preprocessed)
                if target_class is None:
                    if self.model_type == "svm":
                        features_np = features.numpy()
                        features_scaled = self.scaler.transform(features_np)
                        target_class = int(self.svm_model.predict(features_scaled)[0])
                # Use the feature magnitude as loss proxy
                loss = tf.reduce_sum(features)

            grads = tape.gradient(loss, conv_out)
            if grads is None:
                return None

            pooled = tf.reduce_mean(grads, axis=(0, 1, 2))
            heatmap = conv_out[0] @ pooled[..., tf.newaxis]
            heatmap = tf.squeeze(heatmap)
            heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)
            heatmap = heatmap.numpy()

            import cv2
            heatmap_resized = cv2.resize(heatmap, (self.IMG_SIZE, self.IMG_SIZE))
            heatmap_colored = cv2.applyColorMap(np.uint8(255 * heatmap_resized), cv2.COLORMAP_JET)
            heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)

            original = np.uint8(img_array)
            overlay = cv2.addWeighted(original, 0.6, heatmap_colored, 0.4, 0)
            self._last_gradcam = Image.fromarray(overlay)
            return self._last_gradcam

        except Exception as e:
            print(f"⚠️ Grad-CAM failed: {e}")
            return None

    def _color_based_fallback(self, img_array):
        """Simple color-based soil classification."""
        avg = np.mean(img_array, axis=(0, 1))
        r, g, b = avg
        brightness = (r + g + b) / 3

        if brightness > 0.6 and r > 0.5:
            return "Sand"
        elif brightness < 0.25:
            return "Clay"
        elif r > 0.4 and g > 0.35:
            return "Sandy Loam"
        elif r > 0.35 and g > 0.3 and b > 0.25:
            return "Loam"
        else:
            return "Loamy sand"

    def get_available_classes(self):
        return list(self.class_indices.keys())


if __name__ == "__main__":
    print("=" * 60)
    print("SOIL PREDICTOR TEST")
    print("=" * 60)

    predictor = SoilPredictor()
    print(f"\nModel: {predictor.model_type}")
    print(f"Classes: {predictor.get_available_classes()}")

    test_img = Image.new('RGB', (224, 224), color=(80, 60, 40))
    result = predictor.predict_detailed(test_img)
    print(f"Predicted: {result['predicted_class']} ({result['confidence']:.1%})")
    print(f"Top 3: {result['top3']}")