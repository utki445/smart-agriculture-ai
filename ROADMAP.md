# 🗺️ SmartAgro — Future Development Roadmap

> **For Team Reference:** This document outlines the full development plan for the SmartAgro platform beyond the current baseline. Each phase has clear deliverables, assigned focus areas, and technical specifications.

---

## 📌 Current State (What's Already Done)

| Module | Status | Description |
|--------|--------|-------------|
| ESP32 + Sensors + Relay | ✅ Complete | DHT22 + Capacitive Moisture + Relay pump control via USB-Serial |
| AI Soil Type Classifier | ✅ Complete | EfficientNetV2-B0 + SVM → 94.4% accuracy (5 soil types) |
| AI Soil Condition Classifier | ✅ Complete | EfficientNetV2-B0 + Dense → 100% accuracy (4 conditions) |
| Sensor-Vision Fusion | ✅ Complete | 1,385-Dim tensor → SVM → 98.7% accuracy |
| Crop Recommendation Engine | ✅ Complete | Weighted scoring with MSP economics → 99.1% accuracy |
| Multi-Crop Zone Allocation | ✅ Complete | Acreage distribution proportional to profitability scores |
| Streamlit Dashboard | ✅ Complete | 6-step wizard: Config → Sensors → AI → Irrigation → Crops → Report |
| PDF Farm Report Generator | ✅ Complete | Auto-generated comprehensive farm report |

---

## 🔨 Phase 1: Closed-Loop Self-Correcting Irrigation (Priority: HIGH)

**Goal:** Convert the current open-loop irrigation (predict → act) into a closed-loop feedback system (predict → act → measure → correct).

### Tasks
- [ ] **Firmware Update:** Modify `hardware/smart_agri/smart_agri.ino` to implement post-actuation moisture re-reading
  - After pump ON → wait 120 seconds → re-read moisture sensor
  - Compare actual moisture increase vs expected absorption rate
  - If moisture did NOT increase → flag soil compaction issue
- [ ] **Pulsed Watering Mode:** Add adaptive watering strategy in firmware
  - Normal mode: continuous pump until threshold
  - Pulsed mode: 5 sec ON → 10 sec OFF → repeat (for compacted soil)
  - Auto-switch between modes based on feedback loop results
- [ ] **Dashboard Integration:** Add feedback loop status to `app/dashboard.py`
  - Show "Irrigation Cycle" panel: Expected vs Actual moisture after watering
  - Show alert if soil is not absorbing water
- [ ] **Alert System:** Send "Soil needs tilling" warning when repeated feedback failures detected

### Technical Specs
```
Feedback Loop Cycle:
  1. Read moisture (M1)
  2. Pump ON for T seconds
  3. Wait 120 seconds (absorption time)
  4. Read moisture (M2)
  5. Delta = M2 - M1
  6. If Delta < expected_threshold → Switch to pulsed mode or alert
```

---

## 🔨 Phase 2: Cross-Modal Sensor Fault Detection (Priority: HIGH)

**Goal:** Use disagreement between camera AI and hardware sensors to detect faulty/drifting sensors automatically.

### Tasks
- [ ] **Fault Detection Logic:** Create `app/fault_detector.py`
  - Compare CNN soil condition output vs sensor readings
  - Example: CNN says "Waterlogged" but moisture sensor reads 0% → FAULT
  - Example: CNN says "Cracked/Dry" but moisture sensor reads 95% → FAULT
- [ ] **Fallback Mechanism:** When fault detected:
  - Log the fault event with timestamp
  - Auto-switch to vision-only mode OR sensor-only mode (whichever is reliable)
  - Display warning banner on dashboard
- [ ] **Confidence Scoring:** Add agreement score (0-100%) between modalities
  - High agreement (>80%) → system is reliable
  - Low agreement (<50%) → potential hardware issue

### Decision Matrix
```
| Camera Says      | Sensor Says  | Action                        |
|------------------|--------------|-------------------------------|
| Waterlogged      | Moisture 0%  | SENSOR FAULT → Trust Camera   |
| Cracked/Dry      | Moisture 95% | SENSOR FAULT → Trust Camera   |
| Healthy          | Moisture 45% | AGREEMENT ✅ → Normal mode     |
| Waterlogged      | Moisture 90% | AGREEMENT ✅ → Normal mode     |
```

---

## 🔨 Phase 3: WiFi/BLE Wireless Transmission (Priority: MEDIUM)

**Goal:** Replace USB-Serial with wireless communication so the kit becomes truly plug-and-play for farmers.

### Tasks
- [ ] **WiFi Mode:** Update firmware to transmit JSON telemetry over WiFi (HTTP POST to backend)
  - ESP32 connects to local WiFi network
  - Sends sensor data every 2 seconds to REST API endpoint
  - Handles reconnection on WiFi drop
- [ ] **BLE Mode (Fallback):** For areas with no WiFi
  - ESP32 advertises as BLE peripheral
  - Phone app connects and reads sensor characteristics
  - Lower power consumption for remote deployments
- [ ] **Cloud Backend:** Set up Firebase Realtime Database or Flask API
  - Endpoint: `POST /api/telemetry` → stores sensor readings per farmer
  - Endpoint: `GET /api/telemetry/{farmer_id}` → retrieves latest data

### Tech Stack
```
ESP32 → WiFi HTTP POST → Flask/FastAPI Backend → SQLite/Firebase → Dashboard
ESP32 → BLE GATT → Phone App (Flutter/React Native) → Cloud API
```

---

## 🔨 Phase 4: Cloud Backend + User Authentication (Priority: MEDIUM)

**Goal:** Multi-user system where each farmer has their own account, farm profile, and historical data.

### Tasks
- [ ] **Backend API:** Build `backend/` folder with Flask/FastAPI
  - `POST /auth/register` — Farmer/Buyer registration
  - `POST /auth/login` — JWT token authentication
  - `GET /farm/{id}` — Get farm profile + historical data
  - `POST /farm/{id}/telemetry` — Store new sensor reading
  - `GET /marketplace/search?crop=wheat` — Search crops across region
- [ ] **Database Schema:**
  ```
  Users: id, name, role (farmer/buyer), phone, location, created_at
  Farms: id, user_id, area_acres, location_lat, location_lng, soil_type
  Telemetry: id, farm_id, temperature, humidity, moisture, timestamp
  CropPlans: id, farm_id, crop_name, area_allocated, expected_yield, msp_price
  Orders: id, buyer_id, farm_id, crop, quantity, price, status
  ```
- [ ] **Farmer Dashboard:** Extend Streamlit or build new web app
  - Login page → Farm profile → Live sensors → AI analysis → Crop plan → History

---

## 🔨 Phase 5: Crop Quality Monitoring via Camera (Priority: MEDIUM)

**Goal:** Periodically photograph growing crops to generate a health/quality score that buyers can see.

### Tasks
- [ ] **Crop Health Classifier:** Train a new CNN model
  - Dataset: PlantVillage or custom field photos
  - Classes: Healthy, Nutrient Deficient, Pest Infected, Diseased
  - Architecture: EfficientNetV2 or MobileNetV3 (lightweight for phone)
- [ ] **Quality Score Algorithm:** Generate a 1-10 score based on:
  - Soil health score (from existing soil classifier)
  - Crop visual health score (from new crop classifier)
  - Environmental consistency (stable temp/humidity over time)
- [ ] **Timeline Tracking:** Store weekly crop photos with scores
  - Farmers can see their crop health trend over time
  - Buyers can see the growth progression before purchasing

---

## 🔨 Phase 6: Regional Crop Marketplace (Priority: LOW — Final Phase)

**Goal:** Connect farmers and buyers on a single platform with AI-scored quality transparency.

### Tasks
- [ ] **Farmer View:**
  - List their crops with auto-generated quality scores
  - Set expected price (system suggests MSP-based fair price)
  - See regional competition: "5 other farmers in your area growing Wheat"
  - Get recommendation: "Consider growing Mustard — low competition, high MSP"
- [ ] **Buyer View:**
  - Search by crop type, region, quality score
  - Compare farmers side-by-side (soil health, crop health, price)
  - Place order directly → notification to farmer
- [ ] **Insurance & Schemes Module:**
  - Database of PMFBY (crop insurance) premiums per crop
  - Eligibility checker based on farm size, location, crop type
  - Links to apply for PM-KISAN, soil health card, KCC loan

---

## 📅 Timeline Overview

| Phase | Deliverable | Duration | Dependencies |
|-------|-------------|----------|-------------|
| Phase 1 | Closed-loop irrigation | 2 weeks | None (can start now) |
| Phase 2 | Sensor fault detection | 1 week | Phase 1 |
| Phase 3 | WiFi/BLE transmission | 2 weeks | Phase 1 |
| Phase 4 | Cloud backend + auth | 3 weeks | Phase 3 |
| Phase 5 | Crop quality monitoring | 2 weeks | Phase 4 |
| Phase 6 | Marketplace + schemes | 3 weeks | Phase 4, 5 |
| **Total** | **Full Platform** | **~13 weeks** | |

---

## 🛠️ Tech Stack Summary

| Layer | Current | Future |
|-------|---------|--------|
| Hardware | ESP32 + USB-Serial | ESP32 + WiFi/BLE |
| Firmware | Arduino C++ (threshold) | Arduino C++ (closed-loop + pulsed) |
| AI Models | EfficientNetV2 + SVM (local) | + Crop health classifier |
| Dashboard | Streamlit (single user) | Streamlit/React (multi-user) |
| Backend | None (local only) | Flask/FastAPI + Firebase |
| Database | CSV + JSON files | SQLite / Firebase Realtime DB |
| Auth | None | JWT token-based login |
| Deployment | Local laptop | Cloud (Render/Railway/Firebase) |

---

## 👥 Team Task Distribution

> **Note:** Assign phases to team members based on strengths. Suggested split:

| Member | Focus Area | Phases |
|--------|-----------|--------|
| **Member 1 (IoT/Hardware)** | Firmware, closed-loop logic, WiFi/BLE | Phase 1, 3 |
| **Member 2 (AI/ML)** | Fault detection, crop health classifier | Phase 2, 5 |
| **Member 3 (Full-Stack)** | Backend API, database, marketplace UI | Phase 4, 6 |

---

## 📎 How to Contribute

1. Clone the repo: `git clone https://github.com/utki445/smart-agriculture-ai.git`
2. Create your branch: `git checkout -b feature/phase-1-closed-loop`
3. Make changes, test locally
4. Push and create a Pull Request: `git push origin feature/phase-1-closed-loop`
5. Get review from team lead before merging to `main`
