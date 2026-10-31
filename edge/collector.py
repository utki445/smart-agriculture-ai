import paho.mqtt.client as mqtt
import json
import csv
import os
import requests
from datetime import datetime
import tempfile
import shutil

# ========== CONFIG ==========
# Credentials are read from the environment, never hard-coded. Copy
# .env.example to .env, fill it in, and keep .env out of version control.
#
#   set MQTT_BROKER=your-broker.s1.eu.hivemq.cloud     (Windows)
#   export MQTT_BROKER=your-broker.s1.eu.hivemq.cloud  (Linux / macOS)
BROKER = os.environ.get("MQTT_BROKER", "")
PORT = int(os.environ.get("MQTT_PORT", "8883"))
USERNAME = os.environ.get("MQTT_USERNAME", "")
PASSWORD = os.environ.get("MQTT_PASSWORD", "")
TOPIC = os.environ.get("MQTT_TOPIC", "smartagri/data")

LAT = float(os.environ.get("SITE_LAT", "23.2547"))
LON = float(os.environ.get("SITE_LON", "77.4029"))

if not all((BROKER, USERNAME, PASSWORD)):
    raise SystemExit(
        "MQTT credentials are not configured.\n"
        "Set MQTT_BROKER, MQTT_USERNAME and MQTT_PASSWORD in your environment\n"
        "(see .env.example). This collector is the optional MQTT path; the\n"
        "default serial path used by start_smart_agri.bat is\n"
        "edge/serial_collector.py and needs no credentials."
    )

# ========== PATH FIX ==========
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

CSV_FILE = os.path.join(DATA_DIR, "sensor_log.csv")
LATEST_JSON = os.path.join(DATA_DIR, "latest.json")

print("Writing to:")
print("CSV:", CSV_FILE)
print("JSON:", LATEST_JSON)

# ========== WEATHER ==========
def get_weather():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current_weather=true"
        data = requests.get(url, timeout=5).json()
        cw = data["current_weather"]
        return cw["temperature"], cw["windspeed"]
    except:
        return None, None

# ========== JSON ==========
def write_latest_json(data):
    with tempfile.NamedTemporaryFile('w', delete=False, dir=DATA_DIR, suffix='.tmp') as f:
        json.dump(data, f, indent=2)
        temp_path = f.name

    shutil.move(temp_path, LATEST_JSON)
    print("Updated latest.json")

# ========== CSV ==========
def write_to_csv(data):
    exists = os.path.isfile(CSV_FILE)

    outside_temp, wind = get_weather()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [
        timestamp,
        data.get("temperature"),
        data.get("humidity"),
        data.get("moisture"),
        data.get("status"),
        data.get("action"),
        outside_temp,
        wind,
        "Bhopal"
    ]

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not exists:
            writer.writerow([
                "timestamp",
                "soil_temp",
                "soil_humidity",
                "soil_moisture",
                "status",
                "action",
                "outside_temp",
                "wind_speed",
                "city"
            ])

        writer.writerow(row)

    print("Logged to CSV")

# ========== MQTT ==========
def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected:", reason_code)
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print("Received:", data)

    write_latest_json(data)
    write_to_csv(data)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT)
client.loop_forever()
