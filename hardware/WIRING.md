# Smart Agriculture AI — Wiring Reference

Every pin below is taken from `hardware/smart_agri/smart_agri.ino`. If you
change the firmware, change this file too.

Board: **ESP32-WROOM-32** dev board.

---

## 1. Parts

| Part | Qty | Notes |
|---|---|---|
| ESP32-WROOM-32 dev board | 1 | powered from laptop USB |
| DHT11 temperature + humidity module | 1 | 3-pin breakout |
| Capacitive soil moisture sensor v1.2 | 1 | analogue out |
| 5 V single-channel relay module | 1 | VCC / GND / IN + COM / NO / NC |
| DC mini pump, 3–6 V | 1 | runs off the power bank |
| BC547B NPN transistor | 1 | TO-92 |
| Resistor 1 kΩ | 1 | transistor base |
| Resistor 220 Ω | 2 | one per LED |
| Resistor 10 kΩ | 1 | DHT11 pull-up — only if your module has no on-board pull-up |
| Red LED | 1 | system alive |
| Green LED | 1 | pump running |
| 5 V power bank | 1 | relay coil + pump only |
| Breadboard, jumper wires, tubing | — | |

---

## 2. Pin map

| ESP32 pin | Direction | Connects to | Through |
|---|---|---|---|
| **GPIO 4** | digital in | DHT11 `DATA` | 10 kΩ pull-up to 3.3 V |
| **GPIO 34** | analogue in (ADC1_CH6) | Moisture sensor `AOUT` | direct |
| **GPIO 26** | digital out | BC547B **base** | 1 kΩ |
| **GPIO 13** | digital out | Red LED anode | 220 Ω |
| **GPIO 14** | digital out | Green LED anode | 220 Ω |
| **3.3 V** | power out | DHT11 `VCC`, moisture `VCC` | — |
| **GND** | ground | common ground rail | — |

GPIO 34 is **input-only** and **not 5 V tolerant**.

---

## 3. Connection list

Work through these one at a time and tick them off.

### DHT11
- [ ] `VCC` → ESP32 **3.3 V**
- [ ] `DATA` → ESP32 **GPIO 4**
- [ ] `GND` → ground rail
- [ ] 10 kΩ between `DATA` and 3.3 V — **skip if your 3-pin module already has one**

### Capacitive soil moisture sensor v1.2
- [ ] `VCC` → ESP32 **3.3 V**  ← 3.3 V, not 5 V
- [ ] `AOUT` → ESP32 **GPIO 34**
- [ ] `GND` → ground rail

### Red LED — system alive
- [ ] ESP32 **GPIO 13** → 220 Ω → LED **anode** (long leg)
- [ ] LED **cathode** (short leg, flat edge) → ground rail

### Green LED — pump running (blinks every 250 ms)
- [ ] ESP32 **GPIO 14** → 220 Ω → LED **anode**
- [ ] LED **cathode** → ground rail

### BC547B transistor
TO-92 package. Hold it with the **flat printed face toward you** and the legs
pointing **down**:

```
   flat face toward you
    _______________
   |               |
   |    BC547B     |
   |_______________|
        |  |  |
        C  B  E
       (1)(2)(3)
```

- [ ] **Base** (middle leg) → 1 kΩ → ESP32 **GPIO 26**
- [ ] **Emitter** (right leg) → ground rail
- [ ] **Collector** (left leg) → relay module **`IN`**

> Confirm the pinout against your actual part before powering up. TO-92
> pinouts vary between manufacturers, and swapping C and E is the usual way
> to destroy the transistor.

### 5 V relay module
Control side:
- [ ] `VCC` → power bank **+5 V**
- [ ] `GND` → ground rail
- [ ] `IN` → BC547B **collector**

Switching side:
- [ ] `COM` → power bank **+5 V**
- [ ] `NO` → pump **+**
- [ ] (`NC` unused)

### Pump
- [ ] Pump **+** → relay `NO`
- [ ] Pump **−** → ground rail

### Power
- [ ] ESP32 ← **laptop USB** (this is also the 115200-baud serial link)
- [ ] Power bank **+5 V** → relay `VCC` and relay `COM`
- [ ] Power bank **−** → **ground rail**  ← see §5, this one is mandatory

---

## 4. Firmware constants

From `smart_agri.ino`. The calibration values were measured on this build at
3.3 V — if you re-wire the probe or change its supply voltage, re-measure them.

| Constant | Value | Meaning |
|---|---|---|
| `MOISTURE_AIR` | 2590 | raw ADC with the probe in dry air → 0 % |
| `MOISTURE_WATER` | 1500 | raw ADC with the probe in water → 100 % |
| `MOISTURE_DRY` | 30 | below 30 % → pump ON |
| `MOISTURE_WET` | 60 | above 60 % → pump OFF |
| Serial baud | 115200 | |
| Loop period | 1000 ms | one JSON record per second |
| Green LED blink | 250 ms | while the pump is running |

Between 30 % and 60 % the relay holds its previous state — that is the
hysteresis band, and it is deliberate.

---

## 5. Two things that will waste your afternoon

**Common ground is mandatory.** The power bank's **−** must be tied to an
ESP32 **GND** pin. Without it the transistor has no return path, the relay
never switches, and it looks exactly like a dead transistor or a bad GPIO.

**Check the relay module's trigger polarity.** The firmware sets
`GPIO 26 HIGH` to turn the pump **on**. The BC547B inverts that: GPIO HIGH →
transistor conducts → `IN` pulled **LOW** → relay energises. That is correct
for an **active-LOW** module, which most blue opto-isolated boards are.

If yours is **active-HIGH** the behaviour comes out backwards — the pump will
run when the soil is wet. Test it before putting the probe in soil (§6 step 3).
If it is active-HIGH, either drive `IN` straight from GPIO 26 and drop the
transistor, or swap the `HIGH`/`LOW` on lines 86 and 91 of the firmware.

---

## 6. Bring-up order

Do not wire everything and hope.

1. **Sensors and LEDs only. No transistor, no relay, no pump.**
   Flash the firmware, open the serial monitor at **115200**.
   Expect one JSON line per second, red LED solid on.

2. **Check the readings.** Temperature and humidity should be plausible — if
   you see values in the hundreds, the DHT11 data line is loose or the pull-up
   is missing. Probe in air should read near **0 %**; dipped in water, near
   **100 %**. If not, re-measure and update `MOISTURE_AIR` / `MOISTURE_WATER`.

3. **Add the transistor and relay, pump still disconnected.**
   Hold the probe in air → relay should **click on**, green LED should blink.
   Dip it in water → relay should **click off**.
   If it is the other way round, see §5.

4. **Connect the pump last.**

---

## 7. Known issue

The logging session of 2026-10-24 recorded soil temperature of 717–742 °C and
humidity of 1971–2074 % — physically impossible, 1,241 records. Most likely a
loose DHT11 data line or a missing pull-up. Step 2 above will catch it.

Data before 2026-09-02 is clean and is what the project report uses.
