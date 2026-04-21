/*
 * Smart Agriculture IoT — ESP32 Firmware v2.0
 * 
 * Sensors:
 *   - DHT22 (Temperature + Humidity)  → GPIO 4
 *   - Capacitive Soil Moisture Sensor → GPIO 34 (ADC)
 * 
 * Actuators:
 *   - 5V Relay (Water Pump Control)   → GPIO 26
 *   - Red LED   (System Health)       → GPIO 2
 *   - Green LED (Pump Active)         → GPIO 15
 * 
 * Communication:
 *   - USB-Serial @ 115200 Baud (JSON telemetry)
 * 
 * Authors: Utkarsh Persai, Devansh Rathore
 * Project: VIT Vellore — IoT Architecture for Precision Agriculture
 */

#include <DHT.h>
#include <ArduinoJson.h>

// =================== PIN DEFINITIONS ===================
#define DHT_PIN          4       // DHT22 data pin
#define MOISTURE_PIN     34      // Capacitive moisture sensor (ADC1_CH6)
#define RELAY_PIN        26      // Relay module IN
#define LED_RED          2       // System health indicator
#define LED_GREEN        15      // Pump active indicator

// =================== SENSOR CONFIG ===================
#define DHT_TYPE         DHT22
#define SERIAL_BAUD      115200
#define READ_INTERVAL    2000    // Read sensors every 2 seconds

// =================== MOISTURE CALIBRATION ===================
// Capacitive sensor v1.2 typical ranges (adjust for your sensor)
#define MOISTURE_AIR     3500    // Sensor in dry air (0% moisture)
#define MOISTURE_WATER   1500    // Sensor in water (100% moisture)

// =================== IRRIGATION THRESHOLDS ===================
#define MOISTURE_DRY     30      // Below this % → pump ON
#define MOISTURE_WET     60      // Above this % → pump OFF (hysteresis)

// =================== GLOBAL STATE ===================
DHT dht(DHT_PIN, DHT_TYPE);

bool pumpActive = false;
unsigned long lastReadTime = 0;
unsigned long bootTime = 0;
int readCount = 0;

// Rolling average for moisture (prevents jitter)
#define AVG_SAMPLES 5
int moistureBuffer[AVG_SAMPLES];
int bufferIndex = 0;
bool bufferFull = false;

// =================== SETUP ===================
void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(500);

  // Pin modes
  pinMode(MOISTURE_PIN, INPUT);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);

  // Initial state — pump OFF, red LED ON (booting)
  digitalWrite(RELAY_PIN, LOW);
  digitalWrite(LED_RED, HIGH);
  digitalWrite(LED_GREEN, LOW);

  // Initialize DHT sensor
  dht.begin();

  // Initialize moisture buffer
  for (int i = 0; i < AVG_SAMPLES; i++) {
    moistureBuffer[i] = 0;
  }

  bootTime = millis();

  // Boot event
  StaticJsonDocument<200> bootDoc;
  bootDoc["event"] = "boot";
  bootDoc["device"] = "SMART_AGRI_001";
  bootDoc["firmware"] = "2.0.0";
  serializeJson(bootDoc, Serial);
  Serial.println();

  // Wait for DHT22 to stabilize
  delay(2000);

  // Ready
  StaticJsonDocument<100> readyDoc;
  readyDoc["event"] = "ready";
  serializeJson(readyDoc, Serial);
  Serial.println();
}

// =================== HELPER FUNCTIONS ===================

// Map raw ADC to moisture percentage (0-100%)
int rawToMoisturePercent(int raw) {
  int percent = map(raw, MOISTURE_AIR, MOISTURE_WATER, 0, 100);
  return constrain(percent, 0, 100);
}

// Push value into rolling average buffer
void pushMoisture(int value) {
  moistureBuffer[bufferIndex] = value;
  bufferIndex = (bufferIndex + 1) % AVG_SAMPLES;
  if (bufferIndex == 0) bufferFull = true;
}

// Get averaged moisture
int getAverageMoisture() {
  int count = bufferFull ? AVG_SAMPLES : bufferIndex;
  if (count == 0) return 0;
  long sum = 0;
  for (int i = 0; i < count; i++) {
    sum += moistureBuffer[i];
  }
  return (int)(sum / count);
}

// Control pump with hysteresis logic
void updatePump(int moisturePercent) {
  if (!pumpActive && moisturePercent < MOISTURE_DRY) {
    // Soil is dry → activate pump
    pumpActive = true;
    digitalWrite(RELAY_PIN, HIGH);
    digitalWrite(LED_GREEN, HIGH);

    StaticJsonDocument<100> pumpDoc;
    pumpDoc["event"] = "pump_on";
    pumpDoc["moisture"] = moisturePercent;
    serializeJson(pumpDoc, Serial);
    Serial.println();
  }
  else if (pumpActive && moisturePercent > MOISTURE_WET) {
    // Soil is wet enough → deactivate pump
    pumpActive = false;
    digitalWrite(RELAY_PIN, LOW);
    digitalWrite(LED_GREEN, LOW);

    StaticJsonDocument<100> pumpDoc;
    pumpDoc["event"] = "pump_off";
    pumpDoc["moisture"] = moisturePercent;
    serializeJson(pumpDoc, Serial);
    Serial.println();
  }
}

// =================== MAIN LOOP ===================
void loop() {
  unsigned long now = millis();

  // Only read at defined interval
  if (now - lastReadTime < READ_INTERVAL) {
    return;
  }
  lastReadTime = now;
  readCount++;

  // ─── Read DHT22 ───
  float temperature = dht.readTemperature();    // Celsius
  float humidity = dht.readHumidity();           // Percent

  // ─── Read Moisture Sensor ───
  int rawMoisture = analogRead(MOISTURE_PIN);
  int moisturePercent = rawToMoisturePercent(rawMoisture);

  // Push into rolling average
  pushMoisture(moisturePercent);
  int avgMoisture = getAverageMoisture();

  // ─── Validate readings ───
  bool dhtValid = !isnan(temperature) && !isnan(humidity);

  // ─── Irrigation Logic ───
  updatePump(avgMoisture);

  // ─── Blink red LED as heartbeat (system alive) ───
  digitalWrite(LED_RED, (readCount % 2 == 0) ? HIGH : LOW);

  // ─── Build JSON telemetry payload ───
  StaticJsonDocument<300> doc;

  if (dhtValid) {
    doc["temperature"] = round(temperature * 10.0) / 10.0;  // 1 decimal
    doc["humidity"] = round(humidity * 10.0) / 10.0;
  } else {
    doc["temperature"] = nullptr;
    doc["humidity"] = nullptr;
    doc["dht_error"] = true;
  }

  doc["moisture_raw"] = rawMoisture;
  doc["moisture"] = avgMoisture;
  doc["pump"] = pumpActive ? "ON" : "OFF";
  doc["uptime_s"] = (now - bootTime) / 1000;

  // ─── Transmit over Serial ───
  serializeJson(doc, Serial);
  Serial.println();
}