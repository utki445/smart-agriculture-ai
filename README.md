# 🌾 Smart Agriculture AI — Multimodal Sensor-Vision Fusion System

> **AI-Enabled Precision Agriculture using Multimodal Sensor-Vision Fusion for Precise Irrigation and Profit-Optimized Crop Recommendation**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange.svg)](https://tensorflow.org)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red.svg)](https://streamlit.io)
[![ESP32](https://img.shields.io/badge/Hardware-ESP32-green.svg)](https://espressif.com)

> 📋 **For future development plans, see [ROADMAP.md](ROADMAP.md)**

---

## 📌 Overview

This project implements a complete edge-to-intelligence precision agriculture system that:

1. **Classifies soil type** from an uploaded image using EfficientNetV2-B0 + SVM (94.4% accuracy)
2. **Detects soil physical condition** (Healthy / Cracked / Waterlogged / Compacted) using a Dual-Head CNN (100% validation accuracy)
3. **Fuses live IoT sensor data with visual CNN embeddings** (Multimodal Sensor-Vision Fusion — 1,385-Dim tensor)
4. **Predicts optimal irrigation schedules** using 48-hour weather forecasts from Open-Meteo API
5. **Recommends the most profitable crop** using a weighted scoring algorithm factoring soil type, weather, and government MSP (Minimum Support Price) data
6. **Supports multi-crop zone allocation** for larger farms to maximize seasonal revenue

---

## 🏗️ System Architecture

```
Layer 1 – Sensor Layer:       Capacitive Moisture Probe | DHT22 Temp/Humidity
        ↓
Layer 2 – Microcontroller:    ESP32 Board (ADC Processing + JSON Serialization)
        ↓
Layer 3 – Communication:      Local USB-Serial Hardline (115200 Baud)
        ↓
Layer 4 – Intelligence:       Image CNN (1,382-Dim) + Telemetry (3-Dim) = Fused Tensor → SVM Classification
        ↓
Layer 5 – Application:        Predictive Irrigation Relay | MSP-Optimized Crop Recommendation
```

---

## 📁 Project Structure

```
smart_agri/
│
├── app/                           # Main application layer
│   ├── dashboard.py               # Streamlit UI (902 lines) — the main entry point
│   ├── soil_predictor.py          # Soil type classifier (EfficientNetV2 + SVM)
│   ├── soil_condition_predictor.py# Soil condition classifier (Healthy/Cracked/etc.)
│   ├── irrigation_scheduler.py    # Predictive irrigation engine (Open-Meteo API)
│   └── ml_predictor.py            # Crop recommendation neural network
│
├── edge/                          # Hardware-software interface
│   ├── serial_collector.py        # USB-Serial listener for ESP32 telemetry
│   └── collector.py               # Data collection utilities
│
├── hardware/                      # Embedded firmware
│   └── smart_agri/
│       └── smart_agri.ino         # ESP32 Arduino firmware (DHT22 + Moisture + Relay)
│
├── models/                        # Pre-trained AI model weights
│   ├── soil_model.keras           # EfficientNetV2-B0 feature extractor (soil type)
│   ├── soil_svm.pkl               # SVM classifier for soil type (RBF kernel)
│   ├── soil_classes.json          # Soil type class labels
│   ├── soil_condition_model.keras # EfficientNetV2-B0 for soil condition
│   ├── condition_feature_extractor.keras
│   ├── soil_condition_classes.json
│   ├── crop_model.keras           # Crop recommendation neural network
│   ├── crop_model.pkl             # Crop model (sklearn)
│   └── crop_label_encoder.json    # Crop label mappings
│
├── planner/                       # Economic crop planning engine
│   ├── crop_planner.py            # Multi-crop zone allocation + profit estimation
│   └── crop_database.py           # 22+ Indian crops with MSP, yield, soil compatibility
│
├── training/                      # Model training scripts
│   ├── train_soil_model.py        # EfficientNetV2 + SVM training pipeline
│   ├── train_condition_model.py   # Soil condition classifier training
│   ├── train_model_v2.py          # Crop recommendation model training
│   ├── build_condition_dataset.py # Dataset builder for soil conditions
│   ├── validate_fusion_model.py   # Fusion model validation script
│   └── generate_figure6_cm.py     # Confusion matrix generator for paper
│
├── data/                          # Runtime data
│   ├── crop_data.csv              # Kaggle crop recommendation dataset
│   ├── sensor_log.csv             # Historical sensor telemetry log
│   ├── latest.json                # Most recent sensor reading
│   └── reports/                   # Auto-generated PDF farm reports
│
├── IRSID_Dataset/                 # IEEE DataPort soil image dataset
│   ├── IRSID/                     # Original soil type images
│   ├── IRSID-Version 2/           # Extended dataset
│   ├── soil_conditions/           # Condition images (healthy/cracked/waterlogged/compacted)
│   ├── Crop_recommendation.xlsx   # Economic reference data
│   └── Practical_Reading.csv      # Field calibration readings
│
├── Docs/                          # Research papers and patent documents
├── start_smart_agri.bat           # One-click system launcher (Windows)
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore rules
├── ROADMAP.md                     # Future development roadmap
└── README.md                      # This file
```

---

## ⚙️ Prerequisites

### Hardware Requirements
| Component | Specification |
|-----------|--------------|
| Microcontroller | ESP32 DevKit v1 |
| Temperature/Humidity Sensor | DHT22 |
| Soil Moisture Sensor | Capacitive Soil Moisture Sensor v1.2 |
| Relay Module | 5V Single-Channel Relay |
| Water Pump | Small DC Water Pump (3-6V) |
| LEDs | Red + Green (with 220Ω resistors) |
| Power | USB (for ESP32) + External 5V (for pump) |

### Hardware Wiring (ESP32 Pin Map)
```
ESP32 GPIO 4  → DHT22 Data Pin (with 10kΩ pull-up to 3.3V)
ESP32 GPIO 34 → Capacitive Moisture Sensor (Analog Out)
ESP32 GPIO 26 → Relay Module IN (controls water pump)
ESP32 GPIO 2  → Red LED (+ 220Ω resistor → GND)
ESP32 GPIO 15 → Green LED (+ 220Ω resistor → GND)
ESP32 3.3V    → DHT22 VCC, Moisture Sensor VCC
ESP32 5V (Vin)→ Relay VCC
ESP32 GND     → Common Ground for all components
Relay NO/COM  → Water pump + external 5V supply
```

### Software Requirements
- **Python 3.10+**
- **Arduino IDE 2.x** (for flashing ESP32 firmware)
- **Windows 10/11** (tested; Linux/macOS should work with minor path adjustments)

---

## 🚀 Installation & Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/utki445/smart-agriculture-ai.git
cd smart-agriculture-ai
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment
```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (CMD)
.\venv\Scripts\activate.bat
```

### Step 4: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Flash ESP32 Firmware (Hardware Setup)
1. Open `hardware/smart_agri/smart_agri.ino` in **Arduino IDE**
2. Install the **ESP32 Board Package** via Board Manager
3. Install required libraries: `DHT sensor library`, `ArduinoJson`
4. Select Board: `ESP32 Dev Module`
5. Select the correct COM port
6. Click **Upload**

### Step 6: Verify Models Are Present
Ensure the `models/` directory contains all `.keras` and `.pkl` files. These are pre-trained and must not be deleted.

---

## ▶️ Running the System

### Option A: One-Click Launch (Windows)
Simply double-click `start_smart_agri.bat`. This will:
1. Start the serial collector (hardware telemetry link)
2. Wait 3 seconds for hardware connection
3. Launch the Streamlit dashboard in your default browser

### Option B: Manual Launch (Step-by-Step)

**Terminal 1 — Start the Hardware Telemetry Collector:**
```bash
.\venv\Scripts\python.exe edge\serial_collector.py
```

**Terminal 2 — Launch the AI Dashboard:**
```bash
.\venv\Scripts\streamlit.exe run app\dashboard.py
```

The dashboard will open automatically at `http://localhost:8501`

### Running Without Hardware (Software-Only Mode)
If the ESP32 is not connected, the dashboard will still function:
- Soil image classification works fully (upload any soil photo)
- Crop recommendation works fully
- Sensor values will show as `N/A` or use cached data from `data/latest.json`
- Irrigation scheduling will use weather API data with default moisture values

---

## 🖥️ Dashboard Walkthrough

The dashboard operates in a **step-by-step wizard flow**:

| Step | Feature | Description |
|------|---------|-------------|
| **1** | Field Configuration | Enter farm location, area (acres), soil preferences |
| **2** | Live Sensor Dashboard | Real-time temperature, humidity, moisture from ESP32 |
| **3** | AI Soil Detection | Upload soil photo → CNN classifies type + condition |
| **4** | Smart Irrigation | 48h forecast + soil state → irrigation override logic |
| **5** | Crop Recommendation | Profit-optimized single/multi-crop allocation with MSP |
| **6** | Farm Report | Auto-generated comprehensive PDF report |

---

## 🧠 AI Models & Datasets

### Datasets Used
| # | Dataset | Source | Purpose |
|---|---------|--------|---------|
| 1 | IRSID (Indian Regional Soil Image Dataset) | IEEE DataPort | Soil type image classification |
| 2 | Crop Recommendation Dataset | Kaggle | Crop-to-environment mapping (temp, humidity, rainfall) |
| 3 | Government MSP Data | data.gov.in | Minimum Support Price for profit calculation |

### Model Summary
| Model | Architecture | Task | Accuracy |
|-------|-------------|------|----------|
| Soil Type Classifier | EfficientNetV2-B0 + SVM (RBF) | 5-class soil classification | 94.4% |
| Soil Condition Classifier | EfficientNetV2-B0 + Dense | 4-class condition detection | 100.0% |
| Crop Recommender | Neural Network (Dense layers) | 22-crop recommendation | 99.1% |
| Sensor-Vision Fusion | CNN Embedding + Normalized Telemetry → SVM | Multimodal soil classification | 98.7% |

---

## 🔁 Retraining Models (Optional)

If you want to retrain from scratch:

```bash
# Train soil type classifier
.\venv\Scripts\python.exe training\train_soil_model.py

# Train soil condition classifier
.\venv\Scripts\python.exe training\train_condition_model.py

# Train crop recommendation model
.\venv\Scripts\python.exe training\train_model_v2.py

# Validate fusion model
.\venv\Scripts\python.exe training\validate_fusion_model.py
```

> **Note:** Training requires the `IRSID_Dataset/` folder with all images present.

---

## 📊 Key Results

| Metric | Value |
|--------|-------|
| Vision-Only Soil Classification | 94.4% |
| Multimodal Fusion (1,385-Dim Tensor) | 100.0% |
| Crop Recommendation Accuracy | 99.1% |
| Sensor Polling Rate | 2 seconds |
| Irrigation Decision Latency | < 500ms |
| Weather Forecast Integration | 48-hour (Open-Meteo API) |

---

## 👥 Authors

| Name |
|------|
| **Hrishi Samay Jetty** | 

---

## 📄 License

This project is part of an academic submission and patent filing . All rights reserved. Unauthorized reproduction or distribution is prohibited.

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|---------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside venv |
| Serial port not detected | Check ESP32 USB connection, install CP2102 drivers |
| Dashboard won't start | Ensure `streamlit` is installed: `pip install streamlit` |
| Models not loading | Verify all files exist in `models/` directory |
| Sensor shows N/A | ESP32 not connected; dashboard runs in software-only mode |
| `Permission denied` on COM port | Close Arduino IDE Serial Monitor before running collector |
