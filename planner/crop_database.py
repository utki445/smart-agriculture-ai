"""
Enhanced Crop Database with IRSID Soil Types
=============================================
Updated for IEEE IRSID dataset soil classifications.
Includes economic data, risk factors, and optimization metrics.
"""

# ======================================================
# SOIL-CROP COMPATIBILITY (IRSID classes)
# ======================================================

CROP_SOIL_COMPATIBILITY = {
    # Primary IRSID classes (merged: 3 broad categories)
    "Clay": ["Rice", "Wheat", "Lettuce", "Cabbage", "Beans", "Cotton", "Sugarcane"],
    "Sandy": ["Groundnut", "Potato", "Carrot", "Watermelon", "Millets", "Pulses", "Cotton", "Wheat", "Maize", "Sunflower"],
    "Loam": ["Rice", "Wheat", "Sugarcane", "Maize", "Cotton", "Jute", "Sunflower", "Groundnut"],
    
    # Legacy / fine-grained types (backward compatibility)
    "Sand": ["Groundnut", "Potato", "Carrot", "Watermelon", "Millets", "Pulses"],
    "Sandy Loam": ["Cotton", "Wheat", "Maize", "Groundnut", "Sunflower", "Pulses"],
    "Loamy Sand": ["Groundnut", "Potato", "Millets", "Pulses", "Carrot", "Maize"],
    "Alluvial": ["Rice", "Wheat", "Sugarcane", "Maize", "Cotton", "Jute"],
    "Black": ["Cotton", "Wheat", "Jowar", "Linseed", "Sunflower", "Millets"],
    "Red": ["Groundnut", "Potato", "Wheat", "Millets", "Pulses", "Cotton"],
}

# ======================================================
# CROP IDEAL CONDITIONS
# ======================================================

CROP_IDEAL_CONDITIONS = {
    "Rice": {
        "temp_range": (20, 35),
        "moisture_range": (60, 100),
        "rainfall_range": (1000, 2500),
        "water_need": "High",
        "duration_days": (120, 150)
    },
    "Wheat": {
        "temp_range": (15, 25),
        "moisture_range": (40, 70),
        "rainfall_range": (500, 1000),
        "water_need": "Medium",
        "duration_days": (110, 130)
    },
    "Cotton": {
        "temp_range": (21, 30),
        "moisture_range": (30, 60),
        "rainfall_range": (600, 1200),
        "water_need": "Medium",
        "duration_days": (150, 180)
    },
    "Sugarcane": {
        "temp_range": (20, 30),
        "moisture_range": (60, 90),
        "rainfall_range": (1500, 2500),
        "water_need": "Very High",
        "duration_days": (300, 365)
    },
    "Maize": {
        "temp_range": (18, 27),
        "moisture_range": (50, 80),
        "rainfall_range": (500, 800),
        "water_need": "Medium",
        "duration_days": (90, 120)
    },
    "Jowar": {
        "temp_range": (25, 32),
        "moisture_range": (30, 60),
        "rainfall_range": (400, 600),
        "water_need": "Low",
        "duration_days": (100, 140)
    },
    "Groundnut": {
        "temp_range": (20, 30),
        "moisture_range": (40, 70),
        "rainfall_range": (500, 1000),
        "water_need": "Medium",
        "duration_days": (120, 150)
    },
    "Potato": {
        "temp_range": (15, 20),
        "moisture_range": (50, 80),
        "rainfall_range": (500, 700),
        "water_need": "Medium",
        "duration_days": (90, 120)
    },
    "Millets": {
        "temp_range": (25, 35),
        "moisture_range": (30, 60),
        "rainfall_range": (400, 600),
        "water_need": "Low",
        "duration_days": (70, 100)
    },
    "Pulses": {
        "temp_range": (20, 30),
        "moisture_range": (40, 70),
        "rainfall_range": (600, 900),
        "water_need": "Medium",
        "duration_days": (100, 130)
    },
    "Sunflower": {
        "temp_range": (20, 25),
        "moisture_range": (40, 70),
        "rainfall_range": (500, 900),
        "water_need": "Medium",
        "duration_days": (90, 120)
    },
    "Jute": {
        "temp_range": (24, 32),
        "moisture_range": (70, 100),
        "rainfall_range": (1500, 2000),
        "water_need": "High",
        "duration_days": (120, 150)
    },
    "Carrot": {
        "temp_range": (15, 20),
        "moisture_range": (40, 70),
        "rainfall_range": (400, 600),
        "water_need": "Medium",
        "duration_days": (70, 90)
    },
    "Watermelon": {
        "temp_range": (25, 35),
        "moisture_range": (40, 70),
        "rainfall_range": (400, 600),
        "water_need": "Medium",
        "duration_days": (80, 100)
    },
    "Lettuce": {
        "temp_range": (10, 20),
        "moisture_range": (50, 80),
        "rainfall_range": (300, 500),
        "water_need": "Medium",
        "duration_days": (45, 65)
    },
    "Cabbage": {
        "temp_range": (15, 20),
        "moisture_range": (50, 80),
        "rainfall_range": (400, 600),
        "water_need": "Medium",
        "duration_days": (80, 100)
    },
    "Beans": {
        "temp_range": (18, 27),
        "moisture_range": (40, 70),
        "rainfall_range": (300, 500),
        "water_need": "Medium",
        "duration_days": (60, 90)
    },
}

# ======================================================
# YIELD RANGES (kg per m²)
# ======================================================

CROP_TYPICAL_YIELD = {
    "Rice": {"yield_range_kg_per_m2": (0.3, 0.6), "factors": "Variety, irrigation, fertilizer", "variance": "±30-50%"},
    "Wheat": {"yield_range_kg_per_m2": (0.25, 0.5), "factors": "Rainfall timing, seed quality", "variance": "±30-40%"},
    "Cotton": {"yield_range_kg_per_m2": (0.15, 0.35), "factors": "Pest management, soil quality", "variance": "±40-60%"},
    "Sugarcane": {"yield_range_kg_per_m2": (6, 12), "factors": "Water, variety, fertilization", "variance": "±25-35%"},
    "Maize": {"yield_range_kg_per_m2": (0.3, 0.6), "factors": "Hybrid variety, irrigation", "variance": "±30-40%"},
    "Jowar": {"yield_range_kg_per_m2": (0.15, 0.3), "factors": "Rainfall, soil quality", "variance": "±35-45%"},
    "Groundnut": {"yield_range_kg_per_m2": (0.2, 0.4), "factors": "Soil type, rainfall", "variance": "±30-50%"},
    "Potato": {"yield_range_kg_per_m2": (2, 4), "factors": "Seed quality, irrigation", "variance": "±25-35%"},
    "Millets": {"yield_range_kg_per_m2": (0.1, 0.25), "factors": "Rainfall, soil fertility", "variance": "±35-50%"},
    "Pulses": {"yield_range_kg_per_m2": (0.15, 0.3), "factors": "Rainfall, soil quality", "variance": "±30-45%"},
    "Sunflower": {"yield_range_kg_per_m2": (0.2, 0.35), "factors": "Irrigation, fertilizer", "variance": "±30-40%"},
    "Jute": {"yield_range_kg_per_m2": (0.25, 0.45), "factors": "Water, soil quality", "variance": "±30-50%"},
    "Carrot": {"yield_range_kg_per_m2": (2, 4), "factors": "Soil drainage, seed quality", "variance": "±25-35%"},
    "Watermelon": {"yield_range_kg_per_m2": (3, 6), "factors": "Water, temperature", "variance": "±30-40%"},
    "Lettuce": {"yield_range_kg_per_m2": (1.5, 3), "factors": "Temperature, moisture", "variance": "±25-35%"},
    "Cabbage": {"yield_range_kg_per_m2": (2, 4.5), "factors": "Temperature, fertility", "variance": "±25-35%"},
    "Beans": {"yield_range_kg_per_m2": (0.2, 0.4), "factors": "Temperature, soil quality", "variance": "±30-40%"},
}

# ======================================================
# MARKET PRICES (₹/kg)
# ======================================================

CROP_MARKET_PRICES = {
    "Rice": {"min_price": 14, "max_price": 17, "avg_price": 15.79},      # Paddy (Common) 2025-26 MSP ₹1579/Q
    "Wheat": {"min_price": 20, "max_price": 23, "avg_price": 21.25},     # (Retained 2024 value)
    "Cotton": {"min_price": 48, "max_price": 55, "avg_price": 51.40},    # Cotton (Medium) 2025-26 MSP ₹5140/Q
    "Sugarcane": {"min_price": 3, "max_price": 4, "avg_price": 3.40},    # (Retained 2024 value)
    "Maize": {"min_price": 13, "max_price": 18, "avg_price": 15.08},     # Maize 2025-26 MSP ₹1508/Q
    "Jowar": {"min_price": 22, "max_price": 27, "avg_price": 24.66},     # Jowar (Hybrid) 2025-26 MSP ₹2466/Q
    "Groundnut": {"min_price": 45, "max_price": 52, "avg_price": 48.42}, # Groundnut 2025-26 MSP ₹4842/Q
    "Potato": {"min_price": 10, "max_price": 20, "avg_price": 15},       # Mandi
    "Millets": {"min_price": 15, "max_price": 35, "avg_price": 24.80},   # Avg of Bajra (17.03) and Ragi (32.57)
    "Pulses": {"min_price": 48, "max_price": 60, "avg_price": 53.32},    # Avg of Tur(50.38), Moong(58.45), Urad(51.14)
    "Sunflower": {"min_price": 48, "max_price": 55, "avg_price": 51.47}, # Sunflower Seed 2025-26 MSP ₹5147/Q
    "Jute": {"min_price": 45, "max_price": 55, "avg_price": 50.50},      # (Retained 2024 value)
    "Carrot": {"min_price": 15, "max_price": 30, "avg_price": 22},       # Mandi
    "Watermelon": {"min_price": 8, "max_price": 20, "avg_price": 14},    # Mandi
    "Lettuce": {"min_price": 30, "max_price": 60, "avg_price": 45},      # Mandi
    "Cabbage": {"min_price": 10, "max_price": 25, "avg_price": 18},      # Mandi
    "Beans": {"min_price": 40, "max_price": 70, "avg_price": 55},        # Mandi
}

# ======================================================
# RISK FACTORS (0-1, lower is better)
# ======================================================

CROP_RISK_FACTORS = {
    "Rice": 0.4, "Wheat": 0.3, "Cotton": 0.6, "Sugarcane": 0.5,
    "Maize": 0.3, "Jowar": 0.2, "Groundnut": 0.4, "Potato": 0.4,
    "Millets": 0.2, "Pulses": 0.3, "Sunflower": 0.3, "Jute": 0.4,
    "Carrot": 0.3, "Watermelon": 0.4, "Lettuce": 0.5, "Cabbage": 0.3,
    "Beans": 0.3,
}

# ======================================================
# WATER CONSUMPTION (Liters per m² per week)
# ======================================================

CROP_WATER_CONSUMPTION = {
    "Rice": {"min": 40, "max": 60, "avg": 50},
    "Wheat": {"min": 20, "max": 30, "avg": 25},
    "Cotton": {"min": 25, "max": 35, "avg": 30},
    "Sugarcane": {"min": 50, "max": 70, "avg": 60},
    "Maize": {"min": 25, "max": 35, "avg": 30},
    "Jowar": {"min": 10, "max": 20, "avg": 15},
    "Groundnut": {"min": 20, "max": 30, "avg": 25},
    "Potato": {"min": 25, "max": 35, "avg": 30},
    "Millets": {"min": 10, "max": 15, "avg": 12},
    "Pulses": {"min": 20, "max": 30, "avg": 25},
    "Sunflower": {"min": 20, "max": 30, "avg": 25},
    "Jute": {"min": 40, "max": 55, "avg": 47},
    "Carrot": {"min": 20, "max": 30, "avg": 25},
    "Watermelon": {"min": 25, "max": 40, "avg": 32},
    "Lettuce": {"min": 15, "max": 25, "avg": 20},
    "Cabbage": {"min": 20, "max": 30, "avg": 25},
    "Beans": {"min": 15, "max": 25, "avg": 20},
}

# ======================================================
# OPTIMIZATION CONSTRAINTS
# ======================================================

OPTIMIZATION_CONSTRAINTS = {
    "min_plot_size_m2": 4047,
    "max_crops_per_field": 4,
    "max_single_crop_fraction": 0.6,
    "min_single_crop_fraction": 0.1,
    "min_diversity_score": 0.3,
}

# ======================================================
# HELPER FUNCTIONS
# ======================================================

def get_crop_economics(crop, area_m2):
    """Calculate economic metrics for a crop"""
    yield_info = CROP_TYPICAL_YIELD.get(crop, {})
    price_info = CROP_MARKET_PRICES.get(crop, {})
    
    if not yield_info or not price_info:
        return None
    
    low_yield = yield_info["yield_range_kg_per_m2"][0] * area_m2
    high_yield = yield_info["yield_range_kg_per_m2"][1] * area_m2
    mid_yield = (low_yield + high_yield) / 2
    
    return {
        "yield_kg": {"low": round(low_yield, 0), "mid": round(mid_yield, 0), "high": round(high_yield, 0)},
        "revenue_inr": {
            "conservative": round(low_yield * price_info["min_price"], 0),
            "expected": round(mid_yield * price_info["avg_price"], 0),
            "optimistic": round(high_yield * price_info["max_price"], 0)
        },
        "price_per_kg": price_info["avg_price"],
        "variance": yield_info["variance"]
    }


def get_water_need(crop, area_m2):
    """Calculate weekly water requirement"""
    water_info = CROP_WATER_CONSUMPTION.get(crop, {})
    if not water_info:
        return None
    return {
        "liters_per_week_low": round(area_m2 * water_info["min"], 0),
        "liters_per_week_avg": round(area_m2 * water_info["avg"], 0),
        "liters_per_week_high": round(area_m2 * water_info["max"], 0)
    }


def get_risk_score(crop):
    """Get normalized risk factor"""
    return CROP_RISK_FACTORS.get(crop, 0.5)


def score_crop_for_conditions(crop, temperature, moisture, rainfall=None):
    """
    Score how well a crop matches current environmental conditions.
    Returns 0.0 to 1.0 (higher = better match).
    """
    conditions = CROP_IDEAL_CONDITIONS.get(crop)
    if not conditions:
        return 0.5
    
    score = 0.0
    factors = 0
    
    # Temperature match
    t_min, t_max = conditions["temp_range"]
    if t_min <= temperature <= t_max:
        score += 1.0
    elif temperature < t_min:
        score += max(0, 1 - (t_min - temperature) / 10)
    else:
        score += max(0, 1 - (temperature - t_max) / 10)
    factors += 1
    
    # Moisture match
    m_min, m_max = conditions["moisture_range"]
    if m_min <= moisture <= m_max:
        score += 1.0
    elif moisture < m_min:
        score += max(0, 1 - (m_min - moisture) / 20)
    else:
        score += max(0, 1 - (moisture - m_max) / 20)
    factors += 1
    
    # Rainfall match (annual, if available)
    if rainfall is not None:
        r_min, r_max = conditions["rainfall_range"]
        if r_min <= rainfall <= r_max:
            score += 1.0
        elif rainfall < r_min:
            score += max(0, 1 - (r_min - rainfall) / 500)
        else:
            score += max(0, 1 - (rainfall - r_max) / 500)
        factors += 1
    
    return score / factors if factors > 0 else 0.5