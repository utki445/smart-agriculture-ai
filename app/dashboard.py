import streamlit as st
import os
import sys
import json
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ─── PATH FIX ───
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "planner"))

from planner.crop_planner import SimpleCropPlanner
from app.soil_predictor import SoilPredictor
from app.soil_condition_predictor import SoilConditionPredictor
from app.irrigation_scheduler import get_48h_forecast, generate_irrigation_schedule

# ─── PAGE CONFIG ───
st.set_page_config(page_title="Smart Agriculture AI", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")

# ═══════════════════════════════════════════════════════
# CSS THEME — Stitch-Inspired Cobalt Blue
# ═══════════════════════════════════════════════════════
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
    /* Prevent aggressive global overrides from breaking Streamlit Material icons */
    html, body, .stApp, p, h1, h2, h3, div[data-testid="stMarkdownContainer"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #020617 !important; }
    #MainMenu, footer, header, .stDeployButton { display: none !important; }

    /* ─── HERO ─── */
    .hero {
        position: relative; overflow: hidden;
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 40%, #2563eb 100%);
        padding: 2rem 2rem 1.6rem; border-radius: 20px; color: white;
        text-align: center; margin-bottom: 1rem;
        box-shadow: 0 16px 48px rgba(37,99,235,0.2), inset 0 1px 0 rgba(255,255,255,0.1);
    }
    .hero::before {
        content: ''; position: absolute; top: -50%; right: -30%;
        width: 400px; height: 400px; border-radius: 50%;
        background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 70%);
    }
    .hero h1 { font-size: 2rem; font-weight: 900; margin: 0; letter-spacing: -0.5px; position: relative; z-index: 1; }
    .hero p { margin: 0.4rem 0 0 0; opacity: 0.8; font-size: 0.88rem; font-weight: 400; position: relative; z-index: 1; }

    /* ─── GLASS CARDS ─── */
    .glass-card {
        background: rgba(2,6,23,0.8); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(37,99,235,0.2); border-radius: 16px;
        padding: 1.3rem; margin-bottom: 0.8rem;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .glass-card:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(37,99,235,0.1); }

    .sensor-card {
        background: rgba(2,6,23,0.8); backdrop-filter: blur(16px);
        border: 1px solid rgba(37,99,235,0.2); border-radius: 16px;
        padding: 1rem; text-align: center;
    }
    .sensor-icon { font-size: 2rem; margin-bottom: 0.3rem; }
    .sensor-value { font-size: 1.8rem; font-weight: 800; line-height: 1.2; }
    .sensor-label { font-size: 0.7rem; color: rgba(255,255,255,0.45); margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }

    /* ─── STEP PROGRESS (Linear Bar) ─── */
    .progress-wrap { margin: 0.5rem 0 1.2rem 0; }
    .progress-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 0.5rem; }
    .progress-step-name { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #2563eb; }
    .progress-pct { font-size: 0.8rem; font-weight: 600; color: #2563eb; }
    .progress-bars { display: flex; gap: 0.3rem; height: 8px; }
    .progress-seg { flex: 1; border-radius: 999px; background: rgba(255,255,255,0.06); transition: all 0.4s ease; }
    .progress-seg.done { background: #2563eb; }
    .progress-seg.active { background: #2563eb; box-shadow: 0 0 12px rgba(37,99,235,0.4); position: relative; }
    .progress-seg.active::after { content: ''; position: absolute; inset: 0; border-radius: 999px; background: rgba(37,99,235,0.4); animation: pulse 2s infinite; }
    .progress-labels { display: flex; justify-content: space-between; margin-top: 0.35rem; }
    .progress-lbl { font-size: 0.55rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: rgba(255,255,255,0.3); }
    .progress-lbl.active { color: #2563eb; }

    /* ─── WEATHER CARDS ─── */
    .weather-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 0.5rem; margin-bottom: 0.6rem; }
    .weather-card {
        background: rgba(2,6,23,0.8); border: 1px solid rgba(37,99,235,0.15);
        border-radius: 14px; padding: 0.8rem; text-align: center;
    }
    .weather-card-icon { font-size: 1.4rem; margin-bottom: 0.3rem; }
    .weather-card-label { font-size: 0.6rem; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; }
    .weather-card-value { font-size: 1.1rem; font-weight: 800; color: white; margin-top: 0.15rem; }

    /* ─── SECTION / DIVIDERS ─── */
    .section-header { color: rgba(255,255,255,0.92); font-size: 1.15rem; font-weight: 700; margin: 1.2rem 0 0.7rem 0; display: flex; align-items: center; gap: 0.5rem; letter-spacing: -0.3px; }
    .custom-divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(37,99,235,0.2), transparent); margin: 1rem 0; }

    /* ─── CONFIDENCE BARS ─── */
    .confidence-bar-bg { background: rgba(255,255,255,0.06); border-radius: 8px; height: 22px; overflow: hidden; margin: 0.3rem 0; }
    .confidence-bar-fill { height: 100%; border-radius: 8px; display: flex; align-items: center; padding-left: 10px; font-size: 0.7rem; font-weight: 700; color: white; transition: width 0.6s ease; }

    /* ─── BADGES ─── */
    .status-badge { display: inline-block; padding: 3px 12px; border-radius: 20px; font-weight: 600; font-size: 0.75rem; }
    .status-healthy { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.25); }
    .status-warning { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.25); }
    .status-danger { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.25); }

    .tag-excellent { display:inline-block; padding:3px 12px; border-radius:12px; font-size:0.72rem; font-weight:700; background:rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.2); }
    .tag-good { display:inline-block; padding:3px 12px; border-radius:12px; font-size:0.72rem; font-weight:700; background:rgba(59,130,246,0.15); color:#60a5fa; border:1px solid rgba(59,130,246,0.2); }
    .tag-fair { display:inline-block; padding:3px 12px; border-radius:12px; font-size:0.72rem; font-weight:700; background:rgba(245,158,11,0.15); color:#fbbf24; border:1px solid rgba(245,158,11,0.2); }

    .reason-box { background: rgba(2,6,23,0.6); border-left: 3px solid #2563eb; padding: 0.5rem 1rem; margin: 0.3rem 0; border-radius: 0 8px 8px 0; font-size: 0.82rem; color: rgba(255,255,255,0.65); }
    .profit-highlight { font-size: 2.5rem; font-weight: 900; color: white; text-align: center; letter-spacing: -1px; }

    /* ─── WEATHER BAR (legacy) ─── */
    .weather-bar { background: rgba(2,6,23,0.8); border: 1px solid rgba(37,99,235,0.15); border-radius: 14px; padding: 0.7rem 1.2rem; display: flex; justify-content: space-around; flex-wrap: wrap; gap: 0.6rem; margin-bottom: 0.6rem; }
    .weather-item { color: rgba(255,255,255,0.5); font-size: 0.85rem; font-weight: 500; }
    .weather-item b { color: rgba(255,255,255,0.9); font-weight: 700; }

    /* ─── LIVE PULSE ─── */
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
    .live-dot { width: 8px; height: 8px; border-radius: 50%; background: #2563eb; display: inline-block; animation: pulse 2s ease-in-out infinite; margin-right: 6px; vertical-align: middle; }
    .sys-badge { display: inline-flex; align-items: center; gap: 0.3rem; background: rgba(37,99,235,0.15); color: #60a5fa; border: 1px solid rgba(37,99,235,0.25); padding: 4px 14px; border-radius: 20px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }

    /* ─── BUTTONS ─── */
    .stButton > button[kind="primary"] {
        background: #2563eb !important;
        color: white !important; border: none !important; padding: 0.7rem 2rem !important;
        border-radius: 14px !important; font-weight: 800 !important; font-size: 0.95rem !important;
        transition: all 0.3s ease !important; letter-spacing: 0.3px;
    }
    .stButton > button[kind="primary"]:hover { background: #1d4ed8 !important; box-shadow: 0 8px 30px rgba(37,99,235,0.3) !important; transform: scale(1.02); }
    .stButton > button[kind="secondary"], .stButton > button:not([kind="primary"]) {
        background: rgba(37,99,235,0.05) !important; color: #60a5fa !important;
        border: 1px solid rgba(37,99,235,0.2) !important; border-radius: 14px !important; font-weight: 700 !important;
    }

    /* ─── INPUTS ─── */
    .js-plotly-plot .plotly .modebar { display: none !important; }
    div[data-testid="stSelectbox"] label { color: rgba(255,255,255,0.5) !important; font-size: 0.8rem !important; }
    div[data-testid="stSelectbox"] > div > div { background: rgba(2,6,23,0.95) !important; border: 1px solid rgba(37,99,235,0.2) !important; border-radius: 12px !important; color: white !important; }
    div[data-testid="stSelectbox"] > div > div > div { color: white !important; }
    div[data-testid="stSelectbox"] svg { fill: rgba(255,255,255,0.4) !important; }
    div[data-baseweb="select"] { background: rgba(2,6,23,0.95) !important; }
    div[data-baseweb="select"] > div { background: rgba(2,6,23,0.95) !important; border-color: rgba(37,99,235,0.2) !important; }
    ul[data-testid="stSelectboxVirtualDropdown"] { background: rgba(2,6,23,0.98) !important; border: 1px solid rgba(37,99,235,0.2) !important; }
    ul[data-testid="stSelectboxVirtualDropdown"] li { color: rgba(255,255,255,0.8) !important; }
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover { background: rgba(37,99,235,0.15) !important; }
    input, div[data-testid="stNumberInput"] input { background: rgba(2,6,23,0.95) !important; border: 1px solid rgba(37,99,235,0.2) !important; color: white !important; border-radius: 10px !important; }
    div[data-testid="stFileUploader"] { background: rgba(37,99,235,0.05) !important; border: 2px dashed rgba(37,99,235,0.3) !important; border-radius: 14px !important; padding: 1rem !important; }
    div[data-testid="stFileUploader"] label { color: rgba(255,255,255,0.6) !important; }
    div[data-testid="stFileUploader"]:hover { background: rgba(37,99,235,0.1) !important; }
    div[data-testid="stCameraInput"] { border-radius: 14px !important; overflow: hidden; }
    div[data-testid="stTabs"] button { color: rgba(255,255,255,0.4) !important; font-weight: 700 !important; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: #2563eb !important; border-bottom-color: #2563eb !important; background: rgba(37,99,235,0.05) !important; }

    /* ─── EXPANDER ─── */
    div[data-testid="stExpander"] { background: rgba(2,6,23,0.6) !important; border: 1px solid rgba(37,99,235,0.15) !important; border-radius: 12px !important; margin-top: 0.5rem !important; overflow: visible !important; }
    div[data-testid="stExpander"] details { border: none !important; }
    div[data-testid="stExpander"] summary { color: rgba(255,255,255,0.6) !important; font-weight: 600 !important; padding: 0.8rem 1rem !important; gap: 0.5rem !important; }
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] { padding: 0.5rem 1rem 1rem 1rem !important; }

    /* ─── TOGGLE ─── */
    div[data-testid="stCheckbox"] label span { color: rgba(255,255,255,0.7) !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# HERO BANNER
# ═══════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
    <h1>🌱 Smart Agriculture AI</h1>
    <p>IoT Sensor + Deep Learning Soil Analysis + Weather API — Intelligent Crop Recommendation</p>
</div>
""", unsafe_allow_html=True)

# ─── HARDWARE STATUS BADGE ───
@st.fragment(run_every="2s")
def hardware_status_banner():
    try:
        file_path = os.path.join(PROJECT_ROOT, "data", "latest.json")
        if os.path.exists(file_path):
            # Check if file was modified in the last 5 seconds
            mtime = os.path.getmtime(file_path)
            if (datetime.now().timestamp() - mtime) < 5:
                st.markdown("""
                <div style="background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); 
                            padding: 0.6rem 1rem; border-radius: 8px; text-align: center; margin-bottom: 1.5rem;
                            display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    <span class="live-dot" style="background: #10b981;"></span>
                    <span style="color: #34d399; font-weight: 700; font-size: 0.9rem; letter-spacing: 0.5px;">
                        HARDWARE CONNECTED: READY FOR ANALYSIS
                    </span>
                </div>
                """, unsafe_allow_html=True)
                return
    except:
        pass
    
    st.markdown("""
    <div style="background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); 
                padding: 0.6rem 1rem; border-radius: 8px; text-align: center; margin-bottom: 1.5rem;
                display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
        <span class="live-dot" style="background: #ef4444;"></span>
        <span style="color: #f87171; font-weight: 700; font-size: 0.9rem; letter-spacing: 0.5px;">
            HARDWARE DISCONNECTED. PLEASE CHECK USB OR RUN BATCH SCRIPT.
        </span>
    </div>
    """, unsafe_allow_html=True)

hardware_status_banner()

# ─── SESSION STATE ───
defaults = {
    "step": 1, "soil_type": None, "soil_confidence": None,
    "soil_top3": None, "soil_gradcam": None, "area_m2": None,
    "sensor_data": None, "weather_data": None, "uploaded_image": None,
    "soil_condition": None, "soil_condition_confidence": None, "soil_condition_advice": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── CACHED ───
@st.cache_resource
def get_soil_predictor():
    return SoilPredictor()

@st.cache_resource
def get_condition_predictor():
    return SoilConditionPredictor()

# ─── HELPERS ───
def read_sensor():
    try:
        with open(os.path.join(PROJECT_ROOT, "data", "latest.json"), "r") as f:
            return json.load(f)
    except:
        return None

def read_sensor_history():
    try:
        df = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "sensor_log.csv"))
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except:
        return None

# ─── CITY DATABASE ───
CITIES = {
    "Bhopal": (23.26, 77.41),
    "Bangalore": (12.97, 77.59),
    "Delhi": (28.61, 77.21),
    "Mumbai": (19.08, 72.88),
    "Chennai": (13.08, 80.27),
    "Hyderabad": (17.39, 78.49),
    "Kolkata": (22.57, 88.36),
    "Pune": (18.52, 73.86),
    "Jaipur": (26.91, 75.79),
    "Lucknow": (26.85, 80.95),
    "Ahmedabad": (23.02, 72.57),
    "Nagpur": (21.15, 79.09),
    "Indore": (22.72, 75.86),
    "Chandigarh": (30.73, 76.77),
    "Patna": (25.60, 85.10),
}

if "selected_city" not in st.session_state:
    st.session_state.selected_city = "Bhopal"

def get_weather(city_name=None):
    try:
        city_name = city_name or st.session_state.selected_city
        lat, lon = CITIES.get(city_name, (23.26, 77.41))
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": lat, "longitude": lon, "current_weather": True,
                  "hourly": "relativehumidity_2m,precipitation"}
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        return {
            "temperature": data["current_weather"]["temperature"],
            "wind": data["current_weather"]["windspeed"],
            "humidity": data["hourly"]["relativehumidity_2m"][0],
            "rainfall": data["hourly"]["precipitation"][0],
            "city": city_name + ", India"
        }
    except:
        return None

def create_gauge(value, title, min_val=0, max_val=100, unit="", color="#10b981"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        title={"text": title, "font": {"size": 13, "color": "rgba(255,255,255,0.7)"}},
        number={"suffix": unit, "font": {"size": 26, "color": "white"}},
        gauge={"axis": {"range": [min_val, max_val], "tickfont": {"color": "rgba(255,255,255,0.4)"}},
               "bar": {"color": color, "thickness": 0.7},
               "bgcolor": "rgba(255,255,255,0.05)", "borderwidth": 0,
               "steps": [{"range": [min_val, max_val*0.3], "color": "rgba(239,68,68,0.1)"},
                         {"range": [max_val*0.3, max_val*0.7], "color": "rgba(245,158,11,0.1)"},
                         {"range": [max_val*0.7, max_val], "color": "rgba(16,185,129,0.1)"}]}
    ))
    fig.update_layout(height=180, margin=dict(l=20,r=20,t=35,b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"color": "white"})
    return fig

def generate_pdf_report(soil_type, area_m2, plan_result, sensor=None, weather=None, confidence=None):
    reports_dir = os.path.join(PROJECT_ROOT, "data", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(reports_dir, f"crop_plan_{ts}.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph("<b>Smart Agriculture AI — Comprehensive Farm Report</b>", styles['Title']))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 15))

    # Section 1: Soil Analysis
    story.append(Paragraph("<b>1. Soil Analysis</b>", styles['Heading2']))
    story.append(Spacer(1, 6))
    soil_data = [
        ["Parameter", "Value"],
        ["Detected Soil Type", soil_type],
        ["Detection Confidence", f"{confidence*100:.1f}%" if confidence else "N/A"],
        ["Detection Method", "EfficientNetV2 + SVM"],
    ]
    t1 = Table(soil_data, colWidths=[200, 200])
    t1.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#065f46')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t1)
    story.append(Spacer(1, 15))

    # Section 2: Sensor Conditions
    story.append(Paragraph("<b>2. Current Soil Conditions (IoT Sensor)</b>", styles['Heading2']))
    story.append(Spacer(1, 6))
    sensor_data = [
        ["Parameter", "Value", "Status"],
        ["Soil Temperature", f"{sensor.get('temperature', 'N/A')}°C" if sensor else "N/A",
         "Normal" if sensor and 15 <= sensor.get('temperature', 0) <= 35 else "Abnormal"],
        ["Soil Humidity", f"{sensor.get('humidity', 'N/A')}%" if sensor else "N/A",
         "Normal" if sensor and sensor.get('humidity', 0) > 30 else "Low"],
        ["Soil Moisture", f"{sensor.get('moisture', 'N/A')}%" if sensor else "N/A",
         "Healthy" if sensor and sensor.get('moisture', 0) > 40 else "Dry — Needs Irrigation"],
        ["Irrigation Status", sensor.get('action', 'N/A').replace('_', ' ') if sensor else "N/A", ""],
    ]
    t2 = Table(sensor_data, colWidths=[150, 130, 150])
    t2.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t2)
    story.append(Spacer(1, 15))

    # Section 3: Weather
    story.append(Paragraph("<b>3. Weather Conditions</b>", styles['Heading2']))
    story.append(Spacer(1, 6))
    w_data = [
        ["Parameter", "Value"],
        ["City", weather.get('city', 'N/A') if weather else "N/A"],
        ["Outside Temperature", f"{weather.get('temperature', 'N/A')}°C" if weather else "N/A"],
        ["Humidity", f"{weather.get('humidity', 'N/A')}%" if weather else "N/A"],
        ["Rainfall", f"{weather.get('rainfall', 'N/A')} mm/hr" if weather else "N/A"],
        ["Wind Speed", f"{weather.get('wind', 'N/A')} km/h" if weather else "N/A"],
    ]
    t3 = Table(w_data, colWidths=[200, 200])
    t3.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#7c3aed')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t3)
    story.append(Spacer(1, 15))

    # Section 4: Land Details
    story.append(Paragraph("<b>4. Field Details</b>", styles['Heading2']))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Total Area: <b>{area_m2:,.0f} m²</b> ({area_m2/4047:.2f} acres)", styles['Normal']))
    story.append(Spacer(1, 15))

    # Section 5: Crop Recommendation
    story.append(Paragraph("<b>5. AI Crop Recommendation</b>", styles['Heading2']))
    story.append(Spacer(1, 6))
    multi = len(plan_result['crops']) > 1
    story.append(Paragraph(f"Mode: <b>{'Multi-Crop (Zone Allocation)' if multi else 'Single Crop'}</b>", styles['Normal']))
    story.append(Spacer(1, 8))
    crop_data = [["Crop", "Area (ac)", "Alloc %", "Yield (kg)", "Price/kg", "Profit (₹)", "Rating"]]
    for c in plan_result["crops"]:
        crop_data.append([
            c['crop'], f"{c['area_allocated']/4047:.2f}", f"{c['area_fraction']}%",
            f"{c['total_yield']:,.0f}", f"₹{c['price_per_kg']}",
            f"₹{c['estimated_profit']:,.0f}", c['suitability']
        ])
    crop_data.append(["TOTAL", f"{area_m2/4047:.2f}", "100%",
                      f"{plan_result['total_yield']:,.0f}", "",
                      f"₹{plan_result['total_profit']:,.0f}", ""])
    t4 = Table(crop_data, colWidths=[65, 55, 50, 65, 55, 75, 55])
    t4.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#065f46')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#f0fdf4')),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
    ]))
    story.append(t4)
    story.append(Spacer(1, 15))

    # Section 6: Reasoning
    story.append(Paragraph("<b>6. Crop Selection Reasoning</b>", styles['Heading2']))
    story.append(Spacer(1, 6))
    for crop in plan_result['crops']:
        story.append(Paragraph(f"<b>{crop['crop']}</b> (Score: {crop['suitability_score']}):", styles['Normal']))
        for reason in crop.get('reasons', []):
            clean = reason.replace('✅', '[OK]').replace('❌', '[X]').replace('⚠️', '[!]').replace('ℹ️', '[i]')
            story.append(Paragraph(f"  • {clean}", styles['Normal']))
        story.append(Spacer(1, 6))
    story.append(Spacer(1, 10))

    # Footer
    story.append(Paragraph("<i>Report generated by Smart Agriculture AI — IoT + Deep Learning System</i>", styles['Normal']))
    story.append(Paragraph(f"<i>Cost savings: Farmers typically spend ₹10,000-20,000 on lab soil testing.</i>", styles['Normal']))

    doc.build(story)
    return filepath

# ─── STEP PROGRESS (Linear Bar — Stitch style) ───
STEP_LABELS = ["Sensors", "Soil Analysis", "Field Config", "Results"]
def render_progress(step):
    pct = int((step / 4) * 100)
    segs = ""
    for i in range(1, 5):
        cls = "done" if i < step else ("active" if i == step else "")
        segs += f'<div class="progress-seg {cls}"></div>'
    lbls = ""
    for i in range(1, 5):
        cls = "active" if i <= step else ""
        lbls += f'<span class="progress-lbl {cls}">Step {i}: {STEP_LABELS[i-1]}</span>'
    html = f"""<div class="progress-wrap">
<div class="progress-header"><span class="progress-step-name">Step {step} of 4: {STEP_LABELS[step-1]}</span><span class="progress-pct">{pct}% Complete</span></div>
<div class="progress-bars">{segs}</div>
<div class="progress-labels">{lbls}</div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)

render_progress(st.session_state.step)

# ═══════════════════════════════════════════════════════
# STEP 1 — LIVE CONDITIONS + WEATHER + CITY
# ═══════════════════════════════════════════════════════
if st.session_state.step == 1:

    # City selector (outside fragment so it doesn't flicker)
    st.session_state.selected_city = st.selectbox(
        "📍 Select Your City", list(CITIES.keys()),
        index=list(CITIES.keys()).index(st.session_state.selected_city),
        key="city_picker"
    )

    @st.fragment(run_every="1s")
    def live_sensor_panel():
        """Auto-refreshes every 5s — only this section re-runs, not the whole page."""
        sensor = read_sensor()
        weather = get_weather()
        st.session_state.sensor_data = sensor
        st.session_state.weather_data = weather

        # City + Weather Cards (Stitch grid style)
        if weather:
            city = weather.get("city", "Unknown")
            city_html = f'<div class="glass-card" style="text-align:center; padding:0.8rem;"><span style="font-size:0.75rem; color:rgba(255,255,255,0.4); font-weight:700; letter-spacing:1px; text-transform:uppercase;">Select Field Location</span><div style="display:flex; align-items:center; justify-content:center; gap:0.5rem; margin-top:0.3rem;"><span style="font-size:1rem;">📍</span><span style="font-size:1.1rem; font-weight:700; color:#60a5fa;">LOCATION — {city}</span></div></div>'
            weather_html = f"""<div class="weather-grid">
<div class="weather-card"><div class="weather-card-icon">☀️</div><div class="weather-card-label">Temperature</div><div class="weather-card-value">{weather["temperature"]}°C</div></div>
<div class="weather-card"><div class="weather-card-icon">💧</div><div class="weather-card-label">Humidity</div><div class="weather-card-value">{weather["humidity"]}%</div></div>
<div class="weather-card"><div class="weather-card-icon">🌧️</div><div class="weather-card-label">Rainfall</div><div class="weather-card-value">{weather["rainfall"]}mm</div></div>
<div class="weather-card"><div class="weather-card-icon">💨</div><div class="weather-card-label">Wind Speed</div><div class="weather-card-value">{weather["wind"]}km/h</div></div>
</div>"""
            st.markdown(city_html, unsafe_allow_html=True)
            st.markdown(weather_html, unsafe_allow_html=True)

        st.markdown('<div class="section-header"><span class="live-dot"></span>📊 IoT Sensor Data (Live) <span style="font-size:0.65rem; color:rgba(255,255,255,0.25); font-weight:400; margin-left:0.3rem;">auto-refreshes every 1s</span></div>', unsafe_allow_html=True)

        if sensor:
            temp_val = sensor.get('temperature', 0)
            hum_val = sensor.get('humidity', 0)
            moist_val = sensor.get('moisture', 0)
            is_dry = sensor.get("action") == "IRRIGATION_REQUIRED" or moist_val < 30

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.plotly_chart(create_gauge(temp_val, "Soil Temp", 0, 50, "°C", "#f59e0b"), use_container_width=True, key="g1")
            with c2: st.plotly_chart(create_gauge(hum_val, "Humidity", 0, 100, "%", "#3b82f6"), use_container_width=True, key="g2")
            with c3: st.plotly_chart(create_gauge(moist_val, "Moisture", 0, 100, "%", "#10b981"), use_container_width=True, key="g3")
            with c4:
                status_icon = '💦' if is_dry else '✅'
                status_text = 'DRY' if is_dry else 'OK'
                status_color = '#f87171' if is_dry else '#34d399'
                status_label = 'Needs Water' if is_dry else 'Healthy'
                badge_class = 'status-danger' if is_dry else 'status-healthy'
                status_html = f'<div class="sensor-card" style="height:160px;display:flex;flex-direction:column;justify-content:center;"><div class="sensor-icon">{status_icon}</div><div class="sensor-value" style="color:{status_color};">{status_text}</div><div class="sensor-label">Irrigation</div><span class="status-badge {badge_class}" style="margin-top:0.4rem;">{status_label}</span></div>'
                st.markdown(status_html, unsafe_allow_html=True)
            
            st.markdown('<div class="section-header" style="margin-top: 1rem; font-size: 0.95rem;">⚙️ Hardware Override (Pump Control)</div>', unsafe_allow_html=True)
            p1, p2, p3, p4 = st.columns([1,1,1,1.5])
            with p1: 
                if st.button("PUMP ON (Manual)", use_container_width=True):
                    open(os.path.join(PROJECT_ROOT, "data", "pump_command.txt"), "w").write("PUMP_ON")
            with p2: 
                if st.button("PUMP OFF (Manual)", use_container_width=True):
                    open(os.path.join(PROJECT_ROOT, "data", "pump_command.txt"), "w").write("PUMP_OFF")
            with p3: 
                if st.button("AUTO MODE", use_container_width=True):
                    open(os.path.join(PROJECT_ROOT, "data", "pump_command.txt"), "w").write("PUMP_AUTO")
            with p4:
                current_mode = sensor.get("mode", "AUTO")
                current_pump = sensor.get("pump", "OFF")
                raw_adc = sensor.get("raw_soil", "--")
                st.markdown(f'<div class="glass-card" style="padding:0.4rem;text-align:center;margin-bottom:0;"><div style="font-size:0.65rem;color:rgba(255,255,255,0.5);letter-spacing:1px;text-transform:uppercase;">Hardware Status</div><div style="font-weight:800;font-size:1.1rem;color:{"#10b981" if current_pump=="ON" else "#6b7280"};">{current_pump} ({current_mode})</div><div style="font-size:0.7rem; color:rgba(255,255,255,0.4); margin-top:0.2rem;">Raw ADC: {raw_adc}</div></div>', unsafe_allow_html=True)


            # History
            history = read_sensor_history()
            if history is not None and len(history) > 2:
                st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
                st.markdown('<div class="section-header">📈 Sensor History</div>', unsafe_allow_html=True)
                fig = go.Figure()
                if "soil_temp" in history.columns:
                    fig.add_trace(go.Scatter(x=history["timestamp"], y=history["soil_temp"], name="Temp (°C)",
                                             line=dict(color="#f59e0b", width=2), mode="lines+markers", marker=dict(size=3)))
                if "soil_humidity" in history.columns:
                    fig.add_trace(go.Scatter(x=history["timestamp"], y=history["soil_humidity"], name="Humidity (%)",
                                             line=dict(color="#3b82f6", width=2), mode="lines+markers", marker=dict(size=3)))
                if "soil_moisture" in history.columns:
                    fig.add_trace(go.Scatter(x=history["timestamp"], y=history["soil_moisture"], name="Moisture (%)",
                                             line=dict(color="#10b981", width=2), mode="lines+markers", marker=dict(size=3)))
                fig.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="rgba(255,255,255,0.7)"),
                                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                                  xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                                  margin=dict(l=40, r=20, t=10, b=30))
                st.plotly_chart(fig, use_container_width=True, key="hist")
        else:
            st.markdown('<div class="glass-card" style="text-align:center;padding:2.5rem;"><div style="font-size:2.5rem;">📡</div><div style="color:rgba(255,255,255,0.7);margin-top:0.5rem;">No live sensor data — start MQTT collector</div></div>', unsafe_allow_html=True)

    # Run the auto-refreshing panel
    live_sensor_panel()

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ─── SMART IRRIGATION SCHEDULE (Novelty 2) ───
    st.markdown('<div class="section-header">💧 Smart Irrigation Schedule (AI-Powered)</div>', unsafe_allow_html=True)
    sensor = st.session_state.sensor_data or read_sensor()
    city_name = st.session_state.selected_city
    lat, lon = CITIES.get(city_name, (23.26, 77.41))
    forecast = get_48h_forecast(lat, lon)
    current_moisture = sensor.get('moisture') if sensor else None
    soil_cond = st.session_state.get('soil_condition', 'healthy')
    if forecast:
        sched = generate_irrigation_schedule(forecast, soil_condition=soil_cond, current_moisture=current_moisture)
        # Action Badge
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:0.7rem;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:1px;">IRRIGATION RECOMMENDATION</div>
            <div style="font-size:2rem;font-weight:900;color:{sched['action_color']};margin:0.4rem 0;">{sched['action']}</div>
            <div style="font-size:0.85rem;color:rgba(255,255,255,0.8);padding:0 0.5rem;">{sched['recommendation']}</div>
            <div style="font-size:0.7rem;color:rgba(255,255,255,0.4);margin-top:0.5rem;">{sched['condition_note']}</div>
        </div>
        """, unsafe_allow_html=True)
        # Rain forecast summary
        r1, r2, r3 = st.columns(3)
        with r1:
            rain_6_icon = '🌧️' if sched['rain_in_6h'] else '☀️'
            rain_6_color = '#3b82f6' if sched['rain_in_6h'] else '#10b981'
            st.markdown(f'<div class="glass-card" style="text-align:center;padding:0.6rem;"><div style="font-size:1.4rem;">{rain_6_icon}</div><div style="font-size:0.7rem;color:rgba(255,255,255,0.5);">Next 6h</div><div style="font-size:0.9rem;font-weight:700;color:{rain_6_color};">{"Rain Expected" if sched["rain_in_6h"] else "No Rain"}</div></div>', unsafe_allow_html=True)
        with r2:
            rain_24_icon = '🌧️' if sched['rain_in_24h'] else '☀️'
            rain_24_color = '#3b82f6' if sched['rain_in_24h'] else '#10b981'
            st.markdown(f'<div class="glass-card" style="text-align:center;padding:0.6rem;"><div style="font-size:1.4rem;">{rain_24_icon}</div><div style="font-size:0.7rem;color:rgba(255,255,255,0.5);">Next 24h</div><div style="font-size:0.9rem;font-weight:700;color:{rain_24_color};">{sched["total_rain_24h"]:.1f}mm</div></div>', unsafe_allow_html=True)
        with r3:
            st.markdown(f'<div class="glass-card" style="text-align:center;padding:0.6rem;"><div style="font-size:1.4rem;">💧</div><div style="font-size:0.7rem;color:rgba(255,255,255,0.5);">48h Total</div><div style="font-size:0.9rem;font-weight:700;color:#3b82f6;">{sched["total_rain_48h"]:.1f}mm</div></div>', unsafe_allow_html=True)
        # Optimal watering windows
        if sched['optimal_windows']:
            st.markdown('<div style="font-size:0.8rem;color:rgba(255,255,255,0.5);margin:0.5rem 0 0.3rem;">📅 Optimal Watering Windows (Next 24h):</div>', unsafe_allow_html=True)
            for w in sched['optimal_windows']:
                w_color = '#10b981' if w['recommended'] else '#f59e0b'
                w_icon = '✅' if w['recommended'] else '⏭️'
                st.markdown(f'<div style="background:rgba(255,255,255,0.03);border-left:3px solid {w_color};padding:0.4rem 0.6rem;margin-bottom:0.3rem;border-radius:4px;"><span style="font-weight:700;color:{w_color};">{w_icon} {w["date"]} {w["time"]}</span> <span style="color:rgba(255,255,255,0.5);font-size:0.75rem;">({w["temp"]}°C, {w["humidity"]}% RH) — {w["reason"]}</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="glass-card" style="text-align:center;padding:1rem;"><div style="color:rgba(255,255,255,0.5);">Weather forecast unavailable — check internet connection</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    if st.button("Continue to Soil Analysis ➡️", use_container_width=True, type="primary"):
        st.session_state.step = 2; st.rerun()

# ═══════════════════════════════════════════════════════
# STEP 2 — SOIL DETECTION
# ═══════════════════════════════════════════════════════
elif st.session_state.step == 2:
    st.markdown('<div class="section-header">🔬 Soil Type Detection (AI)</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown('<div class="glass-card"><p style="color:rgba(255,255,255,0.7);margin:0;">Upload a photo or use your camera to capture a soil sample for AI classification.</p></div>', unsafe_allow_html=True)

        tab_upload, tab_camera = st.tabs(["📁 Upload Image", "📷 Use Camera"])
        img_source = None
        with tab_upload:
            uploaded = st.file_uploader("Soil Image", type=["jpg","png","jpeg"], label_visibility="collapsed")
            if uploaded:
                img_source = uploaded
        with tab_camera:
            camera_img = st.camera_input("Take a photo of soil", label_visibility="collapsed")
            if camera_img:
                img_source = camera_img

        if img_source:
            st.session_state.uploaded_image = img_source
            # Collapsed preview — user clicks to see
            with st.expander("👁️ Preview uploaded image", expanded=False):
                st.image(Image.open(img_source), caption="Soil Sample", use_container_width=True)
            if st.button("🔍 Analyze with AI", use_container_width=True, type="primary"):
                with st.spinner("🧠 Running Dual-Head AI Analysis (Type + Condition)..."):
                    # Head 1: Soil Type Detection (with Sensor Fusion — Novelty 3)
                    predictor = get_soil_predictor()
                    img_source.seek(0)
                    live_sensor = st.session_state.sensor_data or read_sensor()
                    result = predictor.predict_detailed(img_source, sensor_data=live_sensor)
                    st.session_state.soil_type = result["predicted_class"]
                    st.session_state.soil_confidence = result["confidence"]
                    st.session_state.soil_top3 = result.get("top3", [])
                    img_source.seek(0)
                    st.session_state.soil_gradcam = predictor.generate_gradcam(img_source)
                    # Head 2: Soil Condition Analysis (Novelty 1)
                    condition_predictor = get_condition_predictor()
                    img_source.seek(0)
                    cond_result = condition_predictor.predict(img_source)
                    st.session_state.soil_condition = cond_result["condition"]
                    st.session_state.soil_condition_confidence = cond_result["confidence"]
                    st.session_state.soil_condition_advice = cond_result["advice"]
                    st.rerun()

    with c2:
        if st.session_state.soil_type:
            conf = st.session_state.soil_confidence or 0
            conf_color = "#10b981" if conf > 0.7 else "#f59e0b" if conf > 0.4 else "#ef4444"
            st.markdown(f"""
            <div class="glass-card" style="text-align:center;">
                <div style="font-size:0.8rem;color:rgba(255,255,255,0.5);">DETECTED SOIL TYPE</div>
                <div style="font-size:1.6rem;font-weight:800;color:#10b981;margin:0.4rem 0;">{st.session_state.soil_type}</div>
                <div class="confidence-bar-bg">
                    <div class="confidence-bar-fill" style="width:{conf*100:.0f}%;background:{conf_color};">{conf*100:.1f}%</div>
                </div>
                <div style="font-size:0.7rem;color:rgba(255,255,255,0.4);margin-top:0.2rem;">Confidence</div>
            </div>
            """, unsafe_allow_html=True)
            if st.session_state.soil_top3:
                for item in st.session_state.soil_top3:
                    c = item["confidence"]
                    bc = "#10b981" if c > 0.5 else "#3b82f6" if c > 0.2 else "#6b7280"
                    st.markdown(f"""
                    <div style="margin-bottom:0.3rem;">
                        <div style="display:flex;justify-content:space-between;color:rgba(255,255,255,0.7);font-size:0.8rem;">
                            <span>{item['class']}</span><span>{c*100:.1f}%</span>
                        </div>
                        <div class="confidence-bar-bg" style="height:14px;">
                            <div class="confidence-bar-fill" style="width:{c*100:.0f}%;background:{bc};height:100%;font-size:0;"></div>
                        </div>
                    </div>""", unsafe_allow_html=True)
            if st.session_state.soil_gradcam:
                st.markdown('<div style="color:rgba(255,255,255,0.5);font-size:0.8rem;margin-top:0.8rem;">🔥 Grad-CAM Heatmap</div>', unsafe_allow_html=True)
                st.image(st.session_state.soil_gradcam, caption="Model attention", use_container_width=True)

            # ─── SOIL HEALTH REPORT (Novelty 1: Dual-Head) ───
            if st.session_state.soil_condition:
                adv = st.session_state.soil_condition_advice or {}
                cond_conf = st.session_state.soil_condition_confidence or 0
                cond_color = adv.get('color', '#6b7280')
                st.markdown(f"""
                <div class="glass-card" style="text-align:center; border-color: {cond_color}40;">
                    <div style="font-size:0.7rem;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:1px;">SOIL HEALTH REPORT</div>
                    <div style="font-size:2rem;margin:0.3rem 0;">{adv.get('icon','🔍')}</div>
                    <div style="font-size:1.3rem;font-weight:800;color:{cond_color};">{adv.get('label', st.session_state.soil_condition)}</div>
                    <div class="confidence-bar-bg" style="margin-top:0.5rem;">
                        <div class="confidence-bar-fill" style="width:{cond_conf*100:.0f}%;background:{cond_color};">{cond_conf*100:.1f}%</div>
                    </div>
                    <div style="font-size:0.75rem;color:rgba(255,255,255,0.6);margin-top:0.6rem;text-align:left;padding:0 0.3rem;">
                        {adv.get('description', '')}
                    </div>
                    <div style="font-size:0.7rem;color:{cond_color};margin-top:0.5rem;font-weight:600;text-align:left;padding:0 0.3rem;">
                        💧 {adv.get('irrigation_hint', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    n1, n2 = st.columns(2)
    if n1.button("⬅️ Back", use_container_width=True): st.session_state.step = 1; st.rerun()
    if n2.button("Next ➡️", use_container_width=True, type="primary", disabled=not st.session_state.soil_type):
        st.session_state.step = 3; st.rerun()

# ═══════════════════════════════════════════════════════
# STEP 3 — FIELD SIZE
# ═══════════════════════════════════════════════════════
elif st.session_state.step == 3:
    st.markdown('<div class="section-header">📐 Field Dimensions</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: length = st.number_input("Length (meters)", min_value=1, value=100, step=10)
    with c2: width = st.number_input("Width (meters)", min_value=1, value=100, step=10)
    area_m2 = length * width
    st.session_state.area_m2 = area_m2

    st.markdown(f"""
    <div class="glass-card" style="text-align:center;">
        <div style="color:rgba(255,255,255,0.5);font-size:0.8rem;">TOTAL FIELD AREA</div>
        <div style="font-size:2.2rem;font-weight:800;color:#10b981;">{area_m2:,.0f} m²</div>
        <div style="color:rgba(255,255,255,0.5);">{area_m2/4047:.2f} acres</div>
    </div>
    """, unsafe_allow_html=True)

    # Summary so far
    sensor = st.session_state.sensor_data or read_sensor()
    weather = st.session_state.weather_data or get_weather()
    st.markdown(f"""
    <div class="glass-card">
        <div style="color:rgba(255,255,255,0.5);font-size:0.8rem;margin-bottom:0.5rem;">📋 COLLECTED DATA SUMMARY</div>
        <div style="color:rgba(255,255,255,0.8);font-size:0.9rem;line-height:1.8;">
            🔬 Soil Type: <b style="color:#10b981;">{st.session_state.soil_type}</b>
            {f'({st.session_state.soil_confidence*100:.0f}% conf.)' if st.session_state.soil_confidence else ''}<br>
            🩺 Soil Condition: <b style="color:{(st.session_state.soil_condition_advice or {}).get('color', '#6b7280')};">{(st.session_state.soil_condition_advice or {}).get('label', st.session_state.get('soil_condition', 'N/A'))}</b><br>
            📐 Area: <b style="color:#10b981;">{area_m2/4047:.2f} acres</b><br>
            🌡️ Sensor: <b style="color:#10b981;">{sensor.get('temperature','--') if sensor else 'N/A'}°C</b>,
            Moisture: <b style="color:#10b981;">{sensor.get('moisture','--') if sensor else 'N/A'}%</b><br>
            📍 City: <b style="color:#10b981;">{weather.get('city','N/A') if weather else 'N/A'}</b>,
            Weather: <b style="color:#10b981;">{weather.get('temperature','--') if weather else 'N/A'}°C</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    n1, n2 = st.columns(2)
    if n1.button("⬅️ Back", use_container_width=True): st.session_state.step = 2; st.rerun()
    if n2.button("Generate AI Crop Plan 🚀", use_container_width=True, type="primary"):
        st.session_state.step = 4; st.rerun()

# ═══════════════════════════════════════════════════════
# STEP 4 — CROP RECOMMENDATION (FULL REASONING)
# ═══════════════════════════════════════════════════════
elif st.session_state.step == 4:

    st.markdown('<div class="section-header">🌾 AI Crop Recommendation</div>', unsafe_allow_html=True)

    sensor = st.session_state.sensor_data or read_sensor()
    weather = st.session_state.weather_data or get_weather()

    temp_val = sensor.get("temperature") if sensor else None
    moist_val = sensor.get("moisture") if sensor else None
    hum_val = sensor.get("humidity") if sensor else None
    rain_val = weather.get("rainfall") if weather else None
    wind_val = weather.get("wind") if weather else None
    w_hum = weather.get("humidity") if weather else None
    city = weather.get("city", "Unknown") if weather else "Unknown"

    # Multi-crop toggle
    multi_crop = st.toggle("🌿 Enable Multi-Cropping (divide field into optimal crop zones)", value=True)

    try:
        planner = SimpleCropPlanner(
            soil_type=st.session_state.soil_type,
            area=st.session_state.area_m2,
            temperature=temp_val,
            moisture=moist_val,
            rainfall=rain_val,
            city=city,
            wind=wind_val,
            weather_humidity=w_hum,
            soil_condition=st.session_state.get('soil_condition', 'healthy'),
        )

        plan = planner.generate_plan(multi_crop=multi_crop, max_crops=4 if multi_crop else 1)

        if not plan:
            st.error(f"❌ No crops compatible with {st.session_state.soil_type} soil")
        else:
            # ─── DATA SUMMARY (WHY WE RECOMMEND) ───
            st.markdown('<div class="section-header">📋 Decision Basis</div>', unsafe_allow_html=True)
            w_temp_2 = weather.get('temperature', 'N/A') if weather else 'N/A'
            basis_html = f'<div class="glass-card"><div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:0.8rem; color:rgba(255,255,255,0.85); font-size:0.9rem;"><div>📍 <b>City:</b> {city}</div><div>🔬 <b>Soil Type:</b> {st.session_state.soil_type}</div><div>📐 <b>Area:</b> {st.session_state.area_m2/4047:.2f} acres</div><div>🌡️ <b>Sensor Temp:</b> {temp_val or "N/A"}°C</div><div>💧 <b>Soil Moisture:</b> {moist_val or "N/A"}%</div><div>🌧️ <b>Rainfall:</b> {rain_val or "N/A"} mm/hr</div><div>💨 <b>Wind:</b> {wind_val or "N/A"} km/h</div><div>🌤️ <b>Weather Temp:</b> {w_temp_2}°C</div></div></div>'
            st.markdown(basis_html, unsafe_allow_html=True)

            # ─── TOTAL PROFIT ───
            plan_mode = 'Multi-Crop' if multi_crop else 'Single Crop'
            profit_html = f'<div class="glass-card" style="text-align:center;"><div style="color:rgba(255,255,255,0.5);font-size:0.85rem;">ESTIMATED TOTAL PROFIT</div><div class="profit-highlight">₹{plan["total_profit"]:,.0f}</div><div style="color:rgba(255,255,255,0.4);font-size:0.85rem;">Total Yield: {plan["total_yield"]:,.0f} kg | {plan_mode} Plan</div></div>'
            st.markdown(profit_html, unsafe_allow_html=True)

            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

            # ─── CROP CARDS WITH REASONING ───
            st.markdown(f'<div class="section-header">{"🌿 Multi-Crop Zone Allocation" if multi_crop else "🌾 Recommended Crop"}</div>', unsafe_allow_html=True)

            for idx, crop in enumerate(plan["crops"]):
                suit = crop["suitability"]
                tag = f'tag-{"excellent" if suit=="Excellent" else "good" if suit=="Good" else "fair"}'
                zone_label = f"Zone {idx+1}" if multi_crop else "Full Field"

                area_ac = crop['area_allocated']/4047
                card_html = f'<div class="glass-card"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;"><div><span style="color:rgba(255,255,255,0.5);font-size:0.75rem;">{zone_label}</span><div style="font-size:1.4rem;font-weight:800;color:white;">{crop["crop"]}</div></div><div style="text-align:right;"><span class="{tag}">{suit}</span><div style="font-size:0.75rem;color:rgba(255,255,255,0.4);margin-top:0.2rem;">Score: {crop["suitability_score"]}</div></div></div><div style="display:grid; grid-template-columns:repeat(4,1fr); gap:0.5rem; text-align:center; margin:0.8rem 0;"><div><div style="font-size:1.2rem;font-weight:700;color:#10b981;">{area_ac:.1f} ac</div><div style="font-size:0.7rem;color:rgba(255,255,255,0.5);">Area ({crop["area_fraction"]}%)</div></div><div><div style="font-size:1.2rem;font-weight:700;color:#3b82f6;">{crop["total_yield"]:,.0f} kg</div><div style="font-size:0.7rem;color:rgba(255,255,255,0.5);">Est. Yield</div></div><div><div style="font-size:1.2rem;font-weight:700;color:#f59e0b;">₹{crop["price_per_kg"]}/kg</div><div style="font-size:0.7rem;color:rgba(255,255,255,0.5);">Market Price</div></div><div><div style="font-size:1.2rem;font-weight:700;color:#10b981;">₹{crop["estimated_profit"]:,.0f}</div><div style="font-size:0.7rem;color:rgba(255,255,255,0.5);">Est. Profit</div></div></div></div>'
                st.markdown(card_html, unsafe_allow_html=True)

                # Reasoning
                with st.expander(f"📝 Why {crop['crop']}?", expanded=idx == 0):
                    for reason in crop.get("reasons", []):
                        st.markdown(f'<div class="reason-box">{reason}</div>', unsafe_allow_html=True)

            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

            # ─── CHARTS ───
            df = pd.DataFrame(plan["crops"])
            chart1, chart2 = st.columns(2)

            colors_list = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']

            with chart1:
                st.markdown('<div class="section-header">🥧 Land Split</div>', unsafe_allow_html=True)
                fig_pie = go.Figure(data=[go.Pie(
                    labels=df["crop"], values=df["area_allocated"], hole=0.45,
                    marker=dict(colors=colors_list[:len(df)]),
                    textinfo="label+percent", textfont=dict(size=11, color="white"))])
                fig_pie.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                                      margin=dict(l=10,r=10,t=10,b=10), font=dict(color="white"))
                st.plotly_chart(fig_pie, use_container_width=True, key="pie")

            with chart2:
                st.markdown('<div class="section-header">💰 Profit Breakdown</div>', unsafe_allow_html=True)
                fig_bar = go.Figure(data=[go.Bar(
                    x=df["crop"], y=df["estimated_profit"],
                    marker=dict(color=colors_list[:len(df)], cornerradius=8),
                    text=[f"₹{p:,.0f}" for p in df["estimated_profit"]],
                    textposition="outside", textfont=dict(color="rgba(255,255,255,0.7)", size=11))])
                fig_bar.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      font=dict(color="rgba(255,255,255,0.7)"),
                                      xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                                      margin=dict(l=40,r=20,t=10,b=40))
                st.plotly_chart(fig_bar, use_container_width=True, key="bar")

            # ─── WHY THIS PLAN ───
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-header">💡 Recommendation Summary</div>', unsafe_allow_html=True)

            top_crop = plan["crops"][0]
            other_crops = ', '.join([c['crop'] for c in plan['crops'][1:]]) if len(plan['crops']) > 1 else ''
            other_str = f' and {other_crops}' if other_crops else ''
            plan_type = 'optimal multi-crop combination' if multi_crop else 'best single crop'
            conf_str = f"— detected with {st.session_state.soil_confidence*100:.0f}% confidence" if st.session_state.soil_confidence else ''
            w_temp = weather.get('temperature', 'N/A') if weather else 'N/A'
            explain = 'This multi-crop plan maximizes profit by allocating more area to higher-scoring crops while maintaining crop diversity for risk reduction.' if multi_crop else f'This crop scored highest ({top_crop["suitability_score"]}) considering all environmental and soil factors.'

            summary_html = f'<div class="glass-card" style="border-left:3px solid #10b981;"><div style="color:rgba(255,255,255,0.9); font-size:0.95rem; line-height:1.8;">We recommend <b style="color:#10b981;">{top_crop["crop"]}</b>{other_str} as the {plan_type} because:<br><br>🔬 Your soil type is <b>{st.session_state.soil_type}</b> {conf_str}<br>🌡️ Current sensor readings: <b>{temp_val or "N/A"}°C</b> temperature, <b>{moist_val or "N/A"}%</b> moisture, <b>{hum_val or "N/A"}%</b> humidity<br>📍 Weather in <b>{city}</b>: <b>{w_temp}°C</b>, <b>{rain_val or 0} mm/hr</b> rainfall, <b>{wind_val or "N/A"} km/h</b> wind<br>📐 Field size: <b>{st.session_state.area_m2/4047:.2f} acres</b><br><br>{explain}<br><br><b style="color:#10b981;">Estimated total profit: ₹{plan["total_profit"]:,.0f}</b> | Total yield: <b>{plan["total_yield"]:,.0f} kg</b></div></div>'
            st.markdown(summary_html, unsafe_allow_html=True)

            cost_html = '<div class="glass-card" style="text-align:center; padding:1rem;"><div style="color:rgba(255,255,255,0.5); font-size:0.85rem;">💡 <b>Cost Saved:</b> Farmers typically spend ₹10,000-20,000 on lab soil testing. This IoT + AI system provides instant analysis at a fraction of the cost.</div></div>'
            st.markdown(cost_html, unsafe_allow_html=True)

            # ─── PDF ───
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
            if st.button("📥 Generate PDF Report", use_container_width=True, type="primary"):
                with st.spinner("Generating..."):
                    try:
                        pdf = generate_pdf_report(st.session_state.soil_type, st.session_state.area_m2, plan, sensor=sensor, weather=weather, confidence=st.session_state.soil_confidence)
                        with open(pdf, "rb") as f:
                            st.download_button("⬇️ Download PDF", f, os.path.basename(pdf),
                                               "application/pdf", use_container_width=True)
                        st.success("✅ Report ready!")
                    except Exception as e:
                        st.error(f"Error: {e}")

    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.code(str(e))

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    if st.button("🔄 Start New Analysis", use_container_width=True):
        for k in defaults: st.session_state[k] = defaults[k]
        st.rerun()