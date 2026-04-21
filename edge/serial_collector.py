import serial
import serial.tools.list_ports
import json
import csv
import os
import time
import requests
from datetime import datetime
import tempfile
import shutil

# ========== CONFIG ==========
BAUD_RATE = 115200
LAT = 23.2547
LON = 77.4029

# ========== PATH FIX ==========
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

CSV_FILE = os.path.join(DATA_DIR, "sensor_log.csv")
LATEST_JSON = os.path.join(DATA_DIR, "latest.json")
COMMAND_FILE = os.path.join(DATA_DIR, "pump_command.txt")

os.makedirs(DATA_DIR, exist_ok=True)

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

# ========== JSON & CSV ==========
def write_latest_json(data):
    try:
        with tempfile.NamedTemporaryFile('w', delete=False, dir=DATA_DIR, suffix='.tmp') as f:
            json.dump(data, f, indent=2)
            temp_path = f.name
        shutil.move(temp_path, LATEST_JSON)
    except Exception as e:
        print("Error saving JSON:", e)

def write_to_csv(data):
    try:
        exists = os.path.isfile(CSV_FILE)
        outside_temp, wind = get_weather()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = [
            timestamp,
            data.get("temperature"),
            data.get("humidity"),
            data.get("moisture"),
            "OK", # status
            "OK" if data.get("pump") == "OFF" else "IRRIGATING", # action
            outside_temp,
            wind,
            "Bhopal"
        ]

        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not exists:
                writer.writerow([
                    "timestamp", "soil_temp", "soil_humidity", "soil_moisture",
                    "status", "action", "outside_temp", "wind_speed", "city"
                ])
            writer.writerow(row)
    except Exception as e:
        print("Error saving CSV:", e)

# ========== SERIAL AUTO-CONNECT ==========
def find_esp_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        desc = p.description.lower()
        if "ch340" in desc or "cp210" in desc or "serial" in desc or "usb" in desc:
            return p.device
    if len(ports) > 0:
        return ports[0].device # Fallback to first port
    return None

def main():
    while True:
        print("Searching for ESP32 on COM ports...")
        port = None
        while not port:
            port = find_esp_port()
            if not port:
                print("No COM port found. Retrying in 2 seconds...")
                time.sleep(2)
                
        print(f"Connecting to ESP32 on {port} at {BAUD_RATE} baud...")
        
        try:
            ser = serial.Serial(port, BAUD_RATE, timeout=1)
            print("Connected! Listening for data...")
        except Exception as e:
            print(f"Failed to open port {port}: {e}")
            time.sleep(2)
            continue

        # Clear old command file
        if os.path.exists(COMMAND_FILE):
            os.remove(COMMAND_FILE)

        try:
            while True:
                # Check for outgoing commands requested by the Dashboard
                if os.path.exists(COMMAND_FILE):
                    with open(COMMAND_FILE, "r") as f:
                        cmd = f.read().strip()
                    os.remove(COMMAND_FILE)
                    
                    if cmd in ["PUMP_ON", "PUMP_OFF", "PUMP_AUTO"]:
                        cmd_bytes = (cmd + "\n").encode('utf-8')
                        ser.write(cmd_bytes)
                        print(f"Sent command to ESP32: {cmd}")

                # Read incoming serial data
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            data = json.loads(line)
                            print(f"Received JSON: {data}")
                            write_latest_json(data)
                            write_to_csv(data)
                        except json.JSONDecodeError:
                            print(f"Invalid JSON received: {line}")
                    elif line:
                        print(f"ESP32 Log: {line}")
                        
                time.sleep(0.01) # Low latency polling
                
        except serial.SerialException as e:
            print(f"Serial connection lost: {e}")
            if ser.is_open:
                ser.close()
            time.sleep(2)
            continue
        except OSError as e:
            print(f"OS Error (Device disconnnected): {e}")
            if ser.is_open:
                ser.close()
            time.sleep(2)
            continue
        except KeyboardInterrupt:
            print("Stopping collector...")
            if 'ser' in locals() and ser.is_open:
                ser.close()
            break

if __name__ == "__main__":
    main()
