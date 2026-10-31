#include <DHT.h>

// ================= PIN DEFINITIONS =================
#define DHT_PIN       4
#define DHT_TYPE      DHT11

#define MOISTURE_PIN  34

#define RED_LED       13
#define GREEN_LED     14

#define RELAY_PIN     26    // Signal to BC547B Base (via 1kΩ resistor)

// ================= MOISTURE CALIBRATION =================
// Your actual sensor reading in air
#define MOISTURE_AIR    2590

// Sensor reading in water
#define MOISTURE_WATER  1500

// Below this = soil needs water → pump ON
#define MOISTURE_DRY    30

// Above this = soil is wet enough → pump OFF
#define MOISTURE_WET    60

DHT dht(DHT_PIN, DHT_TYPE);

unsigned long previousBlink = 0;
bool greenState = false;
bool pumpRunning = false;

void setup() {

  Serial.begin(115200);

  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(MOISTURE_PIN, INPUT);
  pinMode(RELAY_PIN, OUTPUT);

  dht.begin();

  // Red LED = system ON
  digitalWrite(RED_LED, HIGH);

  // Green initially OFF
  digitalWrite(GREEN_LED, LOW);

  // Pump initially OFF
  digitalWrite(RELAY_PIN, LOW);

  delay(2000);

  Serial.println("===== SMART AGRI HARDWARE TEST =====");
}

void loop() {

  // ================= DHT11 =================
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  // ================= SOIL SENSOR =================
  int soilRaw = analogRead(MOISTURE_PIN);

  int moisture = map(
    soilRaw,
    MOISTURE_AIR,
    MOISTURE_WATER,
    0,
    100
  );

  moisture = constrain(moisture, 0, 100);

  // ================= RED LED =================
  // Always ON = system alive
  digitalWrite(RED_LED, HIGH);

  // ================= RELAY / PUMP CONTROL =================
  // Hysteresis logic: ON below 30%, OFF above 60%
  // This prevents rapid ON/OFF switching near the threshold
  if (moisture < MOISTURE_DRY) {
    // Soil is dry → turn pump ON
    digitalWrite(RELAY_PIN, HIGH);   // BC547B turns ON → relay clicks → pump runs
    pumpRunning = true;
  }
  else if (moisture > MOISTURE_WET) {
    // Soil is wet enough → turn pump OFF
    digitalWrite(RELAY_PIN, LOW);    // BC547B turns OFF → relay releases → pump stops
    pumpRunning = false;
  }
  // Between 30-60%: keep current state (hysteresis band)

  // ================= GREEN LED =================
  if (pumpRunning) {
    // Pump is running → fast blink to indicate watering
    if (millis() - previousBlink >= 250) {
      previousBlink = millis();
      greenState = !greenState;
      digitalWrite(GREEN_LED, greenState);
    }
  }
  else {
    // Pump is off → Green LED OFF
    greenState = false;
    digitalWrite(GREEN_LED, LOW);
  }

  // ================= SERIAL OUTPUT =================
  Serial.println("-----------------------------");

  if (isnan(temperature) || isnan(humidity)) {

    Serial.println("DHT11: ERROR");

  }
  else {

    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.println(" C");

    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");
  }

  Serial.print("Soil Raw: ");
  Serial.println(soilRaw);

  Serial.print("Soil Moisture: ");
  Serial.print(moisture);
  Serial.println(" %");

  Serial.print("Pump: ");
  Serial.println(pumpRunning ? "ON" : "OFF");

  if (pumpRunning) {
    Serial.println("ALERT: SOIL DRY -> PUMP ON + GREEN LED BLINKING");
  }
  else {
    Serial.println("STATUS: SOIL MOISTURE OK -> PUMP OFF");
  }

  // ================= JSON OUTPUT (for dashboard) =================
  Serial.print("{\"temperature\":");
  if (!isnan(temperature)) Serial.print(temperature); else Serial.print("null");
  Serial.print(",\"humidity\":");
  if (!isnan(humidity)) Serial.print(humidity); else Serial.print("null");
  Serial.print(",\"moisture\":");
  Serial.print(moisture);
  Serial.print(",\"soil_raw\":");
  Serial.print(soilRaw);
  Serial.print(",\"pump\":\"");
  Serial.print(pumpRunning ? "ON" : "OFF");
  Serial.println("\"}");

  delay(1000);
}