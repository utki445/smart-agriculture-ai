# Smart Water Management for Urban Green Infrastructure

> A low-cost, network-resilient edge-IoT irrigation node with deep-learning soil analysis.
> Built for the water domain of smart-city design: parks, urban forests, road medians,
> green belts, green roofs and community gardens.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange.svg)](https://tensorflow.org)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red.svg)](https://streamlit.io)
[![ESP32](https://img.shields.io/badge/Hardware-ESP32--WROOM--32-green.svg)](https://espressif.com)

---

## Overview

Cities irrigate a great deal of land, and almost all of it runs on a timer. A timer cannot
tell that it rained yesterday, that one bed drains faster than another, or that a pump has
failed — so the same green space is over-watered in places and under-watered in others,
and the system reports success either way.

This project is an irrigation node that waters by **measurement** instead. It:

1. Measures soil moisture with a capacitive probe and air temperature/humidity with a DHT11
2. Switches a pump through a relay using a **two-threshold hysteresis rule** (on below 30 %, off above 60 %)
3. Runs that decision loop **entirely on the ESP32**, once per second
4. Logs telemetry to a host over USB serial for monitoring and analysis
5. Classifies soil **type** and **condition** from a photograph using transfer learning
6. Produces a weather-aware watering advisory from a 48-hour Open-Meteo forecast
7. Generates a PDF site report

**Cost: approximately ₹970 per node (about US$11–12).**

### The design decision that matters

The node never asks a server whether to irrigate. The host logs, classifies and advises,
but is **physically incapable of operating the relay**. On a single unit that is a
convenience; across a fleet it means a network outage degrades *visibility*, not *service*.
Adding city-wide monitoring does not add a city-wide failure mode.

---

## Honest results

These are measured under a **source-disjoint** protocol — every image derived from a
held-out photograph is excluded from training, so the classifier is tested only on soil it
has genuinely never seen.

| Metric | Result |
|---|---|
| Cost per node | ₹970 (~US$11–12) |
| Control-loop execution | Entirely on-node, 1 Hz, no network dependence |
| Reduction in relay transitions vs a single set point | ~17 % |
| Telemetry captured | 8,171 records, 33 sessions, ~4.5 hours |
| Median telemetry interval | 1.00 s (IQR 1.00–2.00 s) |
| Functional/fault tests passed | 5 of 7 (2 documented as undetected faults) |
| Soil **condition** accuracy, unseen photographs | **75.5–86.1 %** |
| Soil **type** accuracy, unseen photographs | **44.6–46.8 %** — *not deployable* |

### Why soil type is reported as not deployable

Evaluated the conventional way — shuffling all augmented samples before splitting — the
soil-type classifier appears to reach **91.9–94.0 %**. Under the source-disjoint protocol it
falls to **44.6–46.8 %**, close to the 43.3 % obtainable by always guessing the most common
class.

Most of that apparent accuracy came from the classifier recognising *which photograph* a
crop came from, not learning about soil. The gap held across three network architectures and
five randomisations, so it is a property of the dataset (only 16 source photographs, two
classes with a single photograph each), not of one model.

Reproduce it with:

```bash
python training/source_disjoint_eval.py
```

### Known undetected faults

| Fault | Behaviour |
|---|---|
| **Pump loses power (TC-07)** | Pump stops, but the firmware keeps reporting it as running. The relay is commanded but never measured. |
| **Probe unplugged (TC-06)** | Reading clamps to 0 % and the pump runs as a fail-safe, but the fault itself is not detected. |

An ACS712 current sensor (~₹145, about 15 % of unit cost) on the pump supply closes the
TC-07 gap directly. This is the highest-value single addition to the design.

> **Note on sensor–image fusion.** The inference code appends three normalised sensor values
> to the image feature vector, but the saved classifier was trained on image features only,
> so the vector is trimmed back to its training length and the sensor values are dropped.
> **Every prediction from the deployed system is image-only**, which is also what is evaluated
> above.

---

## Hardware

| Component | Specification |
|---|---|
| Microcontroller | ESP32-WROOM-32 DevKit |
| Temperature / humidity sensor | **DHT11** |
| Soil moisture sensor | Capacitive Soil Moisture Sensor v1.2 |
| Relay | 5 V single-channel relay module (opto-isolated) |
| Relay driver | BC547B NPN transistor + 1 kΩ base resistor |
| Pump | DC mini submersible pump, 3–6 V |
| Indicators | Red + green LEDs with 220 Ω resistors |
| Power | USB for the ESP32; separate 5 V supply for relay coil and pump |

### Pin map

Taken from `hardware/smart_agri/smart_agri.ino`. Full build instructions, including the
BC547B pinout and a bring-up order, are in **[hardware/WIRING.md](hardware/WIRING.md)**.

```
ESP32 GPIO 4  → DHT11 DATA        (10 kΩ pull-up to 3.3 V)
ESP32 GPIO 34 → Moisture AOUT     (analogue in, ADC1_CH6, input-only pin)
ESP32 GPIO 26 → BC547B base       (via 1 kΩ) → relay module IN
ESP32 GPIO 13 → Red LED           (via 220 Ω → GND)   system alive
ESP32 GPIO 14 → Green LED         (via 220 Ω → GND)   pump running
ESP32 3.3 V   → DHT11 VCC, moisture sensor VCC
ESP32 GND     → common ground rail  (MUST be tied to the pump supply ground)
Relay COM/NO  → pump + external 5 V supply
```

Two things that will waste an afternoon:

- **Common ground is mandatory.** Without it the transistor has no return path and the relay
  never switches — which looks exactly like a dead transistor.
- **Check the relay module's trigger polarity.** The firmware drives GPIO 26 HIGH to turn the
  pump on; the BC547B inverts that, so `IN` goes LOW. That is correct for an **active-LOW**
  module (most blue opto-isolated boards). If yours is active-HIGH the behaviour comes out
  backwards. Test before putting the probe in soil.

### Firmware constants

| Constant | Value | Meaning |
|---|---|---|
| `MOISTURE_AIR` | 2590 | raw ADC in dry air → 0 % |
| `MOISTURE_WATER` | 1500 | raw ADC in water → 100 % |
| `MOISTURE_DRY` | 30 | below 30 % → pump ON |
| `MOISTURE_WET` | 60 | above 60 % → pump OFF |
| Serial baud | 115200 | one JSON record per second |
| Loop period | 1000 ms | |

Between 30 % and 60 % the relay holds its previous state — that is the hysteresis band, and
it is deliberate.

---

## Project structure

```
app/              Streamlit dashboard, soil predictors, irrigation scheduler
edge/             Serial telemetry collector (pyserial)
planner/          Crop suitability reasoning and report generation
hardware/         ESP32 firmware + WIRING.md
training/         Model training and the source-disjoint evaluation
  figures/        Scripts that regenerate every report figure at 600 dpi
results/          Evaluation outputs (JSON) and generated figures
data/             Telemetry logs and generated reports
Docs/new_docs/    Project report, proposal, slide deck
```

---

## Installation

```bash
git clone https://github.com/utki445/smart-agriculture-ai.git
cd smart-agriculture-ai

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
```

Flash `hardware/smart_agri/smart_agri.ino` to the ESP32 with the Arduino IDE
(board: *ESP32 Dev Module*). Install the **DHT sensor library** first.

---

## Running

**One-click (Windows):** double-click `start_smart_agri.bat` — starts the serial collector,
waits for the hardware, then launches the dashboard.

**Manual:**

```bash
.\venv\Scripts\python.exe edge\serial_collector.py     # terminal 1
.\venv\Scripts\streamlit.exe run app\dashboard.py      # terminal 2
```

The dashboard opens at `http://localhost:8501`.

**Without hardware:** the dashboard still runs. Soil classification, crop recommendation and
the weather advisory all work; sensor gauges replay the last record in `data/latest.json`
and the banner reads `HARDWARE DISCONNECTED`.

**Quick check that the models load:**

```bash
python demo_inference.py          # classifies clay.jpg and loam.jpg
```

---

## Reproducing the results

```bash
python training/source_disjoint_eval.py        # accuracies, intervals, p-values
python training/simulate_probe_check.py        # probe-validity simulation
python training/figures/make_data_figures.py   # all result figures at 600 dpi
```

Every figure in the report is regenerated from files in `results/` and `data/` — nothing is
hard-coded.

---

## Dashboard

| Step | Feature |
|---|---|
| 1 | Site configuration — location, area, soil preferences |
| 2 | Live sensor view — temperature, humidity, moisture, pump state |
| 3 | AI soil analysis — upload a photo, classify type and condition |
| 4 | Irrigation advisory — 48 h forecast + soil state → watering windows |
| 5 | Crop/planting suitability |
| 6 | PDF site report |

---

## Datasets

| Dataset | Source | Purpose |
|---|---|---|
| IRSID (Indian Regions Soil Image Database) | IEEE DataPort, doi:10.21227/2zz3-f173 | Soil type classification |
| Soil condition images | Web image search, curated | Soil condition classification |
| Telemetry log | This node | Control-law and noise characterisation |

Trained model weights are committed under `models/` (~124 MB in total), so the dashboard
runs straight after cloning. They can also be regenerated from scratch with
`training/train_soil_model.py` and `training/train_condition_model.py`.

---

## Limitations

- A pump that loses power is reported as running (TC-07)
- A drifted or fouled probe is trusted
- Water saving is **not measured** — no flow meter is fitted, so no claim is made in litres
- Soil type is not deployable at its measured accuracy on unseen photographs
- Validated in a sealed soil container over hours, not a live site over a season
- One probe represents a whole irrigation zone
- Telemetry link is wired USB serial; wireless backhaul is future work

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError` | `pip install -r requirements.txt` inside the venv |
| Serial port not detected | Check the USB connection; install CP2102 drivers |
| `Permission denied` on COM port | Close the Arduino IDE Serial Monitor first |
| Dashboard won't start | `pip install streamlit` |
| Models not loading | Confirm the files exist in `models/` |
| Sensor shows N/A | ESP32 not connected — dashboard runs in software-only mode |
| Relay never clicks | Check the common ground between the ESP32 and the pump supply |
| Pump runs when soil is wet | Relay module is active-HIGH — see `hardware/WIRING.md` |
| Temperature reads in the hundreds | Loose DHT11 data line or missing pull-up |

---

## License

Academic project submission. All rights reserved; unauthorised reproduction or distribution
is prohibited.
