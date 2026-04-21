# app/ml_predictor.py
"""
ML-based Crop Predictor – DNN Version
=======================================
Uses trained Deep Neural Network for crop prediction
based on environmental sensor data (temperature, humidity, rainfall).
"""

import os
import json
import numpy as np
import pandas as pd

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("WARNING: TensorFlow not available")

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False

try:
    import pickle
    PICKLE_AVAILABLE = True
except ImportError:
    PICKLE_AVAILABLE = False


class MLCropPredictor:
    """
    DNN-based crop predictor with fallback to traditional ML.
    Accepts real-time sensor data and returns crop recommendations.
    """
    
    def __init__(self, model_path="models/crop_model.keras", 
                 encoder_path="models/crop_label_encoder.json"):
        
        self.model = None
        self.model_loaded = False
        self.model_type = None  # 'keras' or 'sklearn'
        self.classes = None
        self.feature_cols = None
        self.scaler_mean = None
        self.scaler_scale = None
        
        # Try to load encoder info first
        possible_encoder_paths = [
            encoder_path,
            os.path.join("models", "crop_label_encoder.json"),
            os.path.join("..", "models", "crop_label_encoder.json"),
            os.path.join(os.path.dirname(__file__), "..", "models", "crop_label_encoder.json")
        ]
        
        for path in possible_encoder_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        encoder_data = json.load(f)
                    self.classes = encoder_data["classes"]
                    self.feature_cols = encoder_data.get("feature_cols", 
                                                          ["temperature", "humidity", "rainfall"])
                    self.scaler_mean = np.array(encoder_data.get("scaler_mean", []))
                    self.scaler_scale = np.array(encoder_data.get("scaler_scale", []))
                    print(f"✅ Encoder loaded: {len(self.classes)} classes, features={self.feature_cols}")
                    break
                except Exception as e:
                    print(f"⚠️ Could not load encoder from {path}: {e}")
        
        # Try to load Keras DNN model
        possible_keras_paths = [
            model_path,
            os.path.join("models", "crop_model.keras"),
            os.path.join("..", "models", "crop_model.keras"),
            os.path.join(os.path.dirname(__file__), "..", "models", "crop_model.keras")
        ]
        
        if TF_AVAILABLE:
            for path in possible_keras_paths:
                if os.path.exists(path):
                    try:
                        self.model = tf.keras.models.load_model(path)
                        self.model_type = "keras"
                        self.model_loaded = True
                        print(f"✅ Keras DNN loaded from: {path}")
                        break
                    except Exception as e:
                        print(f"⚠️ Could not load Keras model from {path}: {e}")
        
        # Fallback: try sklearn pkl model
        if not self.model_loaded:
            possible_pkl_paths = [
                os.path.join("models", "crop_model.pkl"),
                os.path.join("..", "models", "crop_model.pkl"),
                os.path.join(os.path.dirname(__file__), "..", "models", "crop_model.pkl")
            ]
            
            for path in possible_pkl_paths:
                if os.path.exists(path):
                    try:
                        if JOBLIB_AVAILABLE:
                            loaded = joblib.load(path)
                        elif PICKLE_AVAILABLE:
                            with open(path, 'rb') as f:
                                loaded = pickle.load(f)
                        else:
                            continue
                        
                        # Check if it's a wrapper dict or actual sklearn model
                        if isinstance(loaded, dict) and loaded.get("model_type") == "keras_dnn":
                            # This is our wrapper, skip - Keras model should handle it
                            continue
                        else:
                            self.model = loaded
                            self.model_type = "sklearn"
                            self.model_loaded = True
                            if self.classes is None and hasattr(loaded, 'classes_'):
                                self.classes = list(loaded.classes_)
                            print(f"✅ sklearn model loaded from: {path}")
                            break
                    except Exception as e:
                        print(f"⚠️ Could not load pkl from {path}: {e}")
        
        if not self.model_loaded:
            print("⚠️ ML predictor using fallback mode (no model)")
    
    def _prepare_input(self, soil_temp, humidity, rainfall, soil_moisture=None):
        """Prepare and scale input features"""
        
        # Build feature dict matching training features
        feature_dict = {
            "temperature": soil_temp,
            "humidity": humidity,
            "rainfall": rainfall,
        }
        
        if soil_moisture is not None:
            feature_dict["soil_moisture"] = soil_moisture
        
        # If we have specific feature columns from training, use those
        if self.feature_cols:
            # Map our sensor names to training feature names
            name_mapping = {
                "soil_temp": "temperature",
                "soil_humidity": "humidity", 
                "soil_moisture": "moisture",
            }
            
            values = []
            for col in self.feature_cols:
                val = feature_dict.get(col, 0.0)
                values.append(val)
            
            input_array = np.array([values], dtype=np.float32)
        else:
            input_array = np.array([[soil_temp, humidity, rainfall]], dtype=np.float32)
        
        # Apply scaling if available
        if len(self.scaler_mean) > 0 and len(self.scaler_scale) > 0:
            if input_array.shape[1] == len(self.scaler_mean):
                input_array = (input_array - self.scaler_mean) / self.scaler_scale
        
        return input_array
    
    def predict_crop(self, soil_temp, humidity, rainfall, soil_moisture=None):
        """
        Predict best crop based on conditions.
        
        Returns:
            Predicted crop name (string)
        """
        result = self.predict_detailed(soil_temp, humidity, rainfall, soil_moisture)
        return result["predicted_crop"]
    
    def predict_detailed(self, soil_temp, humidity, rainfall, soil_moisture=None):
        """
        Get detailed prediction with probabilities.
        
        Returns:
            dict with predicted_crop, confidence, top3, all_probabilities
        """
        try:
            input_array = self._prepare_input(soil_temp, humidity, rainfall, soil_moisture)
            
            if self.model_loaded and self.model is not None:
                if self.model_type == "keras":
                    # DNN prediction
                    probs = self.model.predict(input_array, verbose=0)[0]
                    predicted_idx = int(np.argmax(probs))
                    confidence = float(probs[predicted_idx])
                    predicted_crop = self.classes[predicted_idx] if self.classes else f"class_{predicted_idx}"
                    
                    # Top 3
                    top3_indices = np.argsort(probs)[::-1][:3]
                    top3 = []
                    for idx in top3_indices:
                        crop_name = self.classes[int(idx)] if self.classes else f"class_{idx}"
                        top3.append({
                            "crop": crop_name,
                            "confidence": float(probs[idx])
                        })
                    
                    # All probabilities
                    all_probs = {}
                    for i, p in enumerate(probs):
                        crop_name = self.classes[i] if self.classes else f"class_{i}"
                        all_probs[crop_name] = float(p)
                    
                elif self.model_type == "sklearn":
                    # Build DataFrame for sklearn
                    if self.feature_cols:
                        input_df = pd.DataFrame(input_array, columns=self.feature_cols)
                    else:
                        input_df = pd.DataFrame(input_array, 
                                                 columns=["soil_temp", "humidity", "rainfall"])
                    
                    predicted_crop = str(self.model.predict(input_df)[0])
                    
                    if hasattr(self.model, 'predict_proba'):
                        probs = self.model.predict_proba(input_df)[0]
                        classes = self.model.classes_
                        confidence = float(max(probs))
                        
                        sorted_idx = np.argsort(probs)[::-1]
                        top3 = [{"crop": str(classes[i]), "confidence": float(probs[i])} 
                                for i in sorted_idx[:3]]
                        all_probs = {str(classes[i]): float(probs[i]) for i in range(len(classes))}
                    else:
                        confidence = 0.8
                        top3 = [{"crop": predicted_crop, "confidence": 0.8}]
                        all_probs = {predicted_crop: 0.8}
                
                print(f"[CROP PREDICTION] {predicted_crop} ({confidence:.1%})")
                
                return {
                    "predicted_crop": predicted_crop,
                    "confidence": confidence,
                    "top3": top3,
                    "all_probabilities": all_probs,
                    "model_type": self.model_type
                }
            else:
                # Fallback
                predicted_crop = self._rule_based_fallback(soil_temp, humidity, rainfall)
                return {
                    "predicted_crop": predicted_crop,
                    "confidence": 0.5,
                    "top3": [{"crop": predicted_crop, "confidence": 0.5}],
                    "all_probabilities": {predicted_crop: 0.5},
                    "model_type": "fallback"
                }
        
        except Exception as e:
            print(f"ERROR in ML prediction: {e}")
            predicted_crop = self._rule_based_fallback(soil_temp, humidity, rainfall)
            return {
                "predicted_crop": predicted_crop,
                "confidence": 0.0,
                "top3": [{"crop": predicted_crop, "confidence": 0.0}],
                "all_probabilities": {},
                "model_type": "fallback",
                "error": str(e)
            }
    
    def predict_proba(self, soil_temp, humidity, rainfall, soil_moisture=None):
        """Get probability distribution (backward compat)"""
        result = self.predict_detailed(soil_temp, humidity, rainfall, soil_moisture)
        return result["all_probabilities"]
    
    def _rule_based_fallback(self, temp, humidity, rainfall):
        """Simple rule-based crop suggestion (fallback)"""
        if rainfall > 100 and temp > 20:
            return "rice"
        elif 15 < temp < 25 and rainfall < 100:
            return "wheat"
        elif temp > 20 and 50 < rainfall < 150:
            return "cotton"
        else:
            return "maize"


# ======================================================
# LEGACY FUNCTION
# ======================================================

_predictor = None

def predict_crop(soil_temp, humidity, rainfall, soil_moisture=None):
    """Legacy function for backward compatibility"""
    global _predictor
    if _predictor is None:
        _predictor = MLCropPredictor()
    return _predictor.predict_crop(soil_temp, humidity, rainfall, soil_moisture)


# ======================================================
# TESTING
# ======================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ML CROP PREDICTOR TEST (DNN)")
    print("=" * 60)
    
    predictor = MLCropPredictor()
    
    print(f"\nModel loaded: {predictor.model_loaded}")
    print(f"Model type: {predictor.model_type}")
    
    test_cases = [
        {"temp": 25, "humidity": 80, "rainfall": 150, "name": "High moisture"},
        {"temp": 20, "humidity": 60, "rainfall": 50, "name": "Moderate"},
        {"temp": 28, "humidity": 50, "rainfall": 80, "name": "Warm, moderate"},
    ]
    
    for case in test_cases:
        print(f"\nTest: {case['name']}")
        result = predictor.predict_detailed(case['temp'], case['humidity'], case['rainfall'])
        print(f"  Prediction: {result['predicted_crop']} ({result['confidence']:.1%})")
        print(f"  Top 3: {result['top3']}")