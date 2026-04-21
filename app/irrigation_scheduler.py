# app/irrigation_scheduler.py
"""
Predictive Smart Drip Irrigation Scheduler (Novelty 2)
=======================================================
Fuses weather forecast + soil condition + IoT sensor data to generate
intelligent irrigation schedules that prevent over/under-watering.

Key Innovation: No existing system combines computer vision soil condition
analysis with weather forecast APIs to make irrigation decisions.
"""

import requests
from datetime import datetime, timedelta


def get_48h_forecast(lat, lon):
    """Pull 48-hour hourly weather forecast from Open-Meteo."""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,relativehumidity_2m,precipitation_probability,precipitation",
            "forecast_days": 2,
            "timezone": "Asia/Kolkata",
        }
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        hourly = data.get("hourly", {})
        
        forecast = []
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        humidity = hourly.get("relativehumidity_2m", [])
        rain_prob = hourly.get("precipitation_probability", [])
        rain_mm = hourly.get("precipitation", [])
        
        for i in range(min(48, len(times))):
            forecast.append({
                "time": times[i],
                "hour": datetime.fromisoformat(times[i]).strftime("%I %p"),
                "date": datetime.fromisoformat(times[i]).strftime("%b %d"),
                "temp": temps[i] if i < len(temps) else 0,
                "humidity": humidity[i] if i < len(humidity) else 0,
                "rain_prob": rain_prob[i] if i < len(rain_prob) else 0,
                "rain_mm": rain_mm[i] if i < len(rain_mm) else 0,
            })
        return forecast
    except Exception as e:
        print(f"Forecast error: {e}")
        return []


def generate_irrigation_schedule(forecast, soil_condition=None, current_moisture=None):
    """
    Generate a smart irrigation schedule using:
    - 48-hour weather forecast (rain prediction)
    - Soil condition from AI (cracked, waterlogged, etc.)
    - Current IoT moisture reading
    
    Returns a list of irrigation window recommendations.
    """
    schedule = []
    
    # Soil condition modifiers
    condition = soil_condition or "healthy"
    if condition == "cracked":
        moisture_threshold = 40  # Higher threshold — soil needs more water
        skip_rain_threshold = 70  # Only skip if very likely to rain
        priority = "HIGH"
        note = "Cracked soil detected — deep watering recommended to restore moisture."
    elif condition == "waterlogged":
        moisture_threshold = 80  # Very high — almost never irrigate
        skip_rain_threshold = 20  # Skip at low rain probability
        priority = "SKIP"
        note = "Waterlogged soil — halt all irrigation. Improve drainage first."
    elif condition == "compacted":
        moisture_threshold = 35
        skip_rain_threshold = 50
        priority = "MEDIUM"
        note = "Compacted soil — use slow drip irrigation to allow water penetration."
    else:  # healthy
        moisture_threshold = 30
        skip_rain_threshold = 50
        priority = "NORMAL"
        note = "Soil is healthy — standard irrigation schedule."
    
    # Current moisture assessment
    needs_water_now = False
    if current_moisture is not None:
        needs_water_now = current_moisture < moisture_threshold
    
    # Scan forecast for rain windows
    rain_windows = []
    for i, hour in enumerate(forecast):
        if hour["rain_prob"] > 40 or hour["rain_mm"] > 0.5:
            rain_windows.append(i)
    
    # Check if rain is coming in next 6 hours
    rain_in_6h = any(i < 6 for i in rain_windows)
    rain_in_12h = any(i < 12 for i in rain_windows)
    rain_in_24h = any(i < 24 for i in rain_windows)
    
    # Calculate total expected rainfall
    total_rain_24h = sum(h["rain_mm"] for h in forecast[:24])
    total_rain_48h = sum(h["rain_mm"] for h in forecast[:48])
    
    # Find optimal watering windows (early morning 5-7AM, evening 5-7PM)
    optimal_windows = []
    for i, hour in enumerate(forecast[:24]):
        parsed = datetime.fromisoformat(hour["time"])
        h = parsed.hour
        # Early morning (5-7 AM) or evening (5-7 PM)
        if h in [5, 6, 17, 18]:
            # Check if rain is expected within 4 hours of this window
            rain_nearby = any(abs(j - i) <= 4 and forecast[j]["rain_prob"] > skip_rain_threshold for j in rain_windows)
            
            if not rain_nearby and condition != "waterlogged":
                optimal_windows.append({
                    "time": hour["hour"],
                    "date": hour["date"],
                    "temp": hour["temp"],
                    "humidity": hour["humidity"],
                    "recommended": True,
                    "reason": "Optimal window — low evaporation, no rain expected nearby"
                })
            elif rain_nearby:
                optimal_windows.append({
                    "time": hour["hour"],
                    "date": hour["date"],
                    "temp": hour["temp"],
                    "humidity": hour["humidity"],
                    "recommended": False,
                    "reason": f"Rain expected — skip irrigation (save water)"
                })
    
    # Build the final schedule
    if condition == "waterlogged":
        action = "HALT"
        action_color = "#3b82f6"
        recommendation = "🛑 STOP all irrigation immediately. Soil is oversaturated."
    elif rain_in_6h and not needs_water_now:
        action = "DELAY"
        action_color = "#f59e0b"
        recommendation = f"⏳ Rain predicted within 6 hours ({total_rain_24h:.1f}mm expected in 24h). Delay irrigation."
    elif rain_in_12h and current_moisture and current_moisture > 20:
        action = "DELAY"
        action_color = "#f59e0b"
        recommendation = f"⏳ Rain expected within 12 hours. Current moisture ({current_moisture}%) is adequate."
    elif needs_water_now and condition == "cracked":
        action = "URGENT"
        action_color = "#ef4444"
        recommendation = "🚨 URGENT: Cracked soil with low moisture. Begin deep drip irrigation immediately."
    elif needs_water_now:
        action = "IRRIGATE"
        action_color = "#10b981"
        recommendation = f"💧 Soil moisture ({current_moisture}%) below threshold ({moisture_threshold}%). Irrigate now."
    else:
        action = "STANDBY"
        action_color = "#6b7280"
        recommendation = f"✅ Moisture adequate ({current_moisture}%). No irrigation needed right now."
    
    return {
        "action": action,
        "action_color": action_color,
        "recommendation": recommendation,
        "priority": priority,
        "condition_note": note,
        "rain_in_6h": rain_in_6h,
        "rain_in_12h": rain_in_12h,
        "rain_in_24h": rain_in_24h,
        "total_rain_24h": total_rain_24h,
        "total_rain_48h": total_rain_48h,
        "optimal_windows": optimal_windows[:4],  # Show max 4 windows
        "forecast_summary": forecast[:24],
        "moisture_threshold": moisture_threshold,
    }
