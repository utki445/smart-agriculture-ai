# planner/crop_planner.py
"""
Smart Crop Planner – Profit-Optimized Multi-Cropping
=====================================================
Combines soil type + sensor data + weather + field dimensions
to produce a fully reasoned crop recommendation with profit estimates.
Supports both single-crop and multi-crop (zone-based) allocation.
"""

from planner.crop_database import (
    CROP_SOIL_COMPATIBILITY,
    CROP_TYPICAL_YIELD,
    CROP_IDEAL_CONDITIONS,
    CROP_RISK_FACTORS,
    CROP_MARKET_PRICES,
    CROP_WATER_CONSUMPTION,
    score_crop_for_conditions,
    get_crop_economics,
)


class SimpleCropPlanner:

    def __init__(self, soil_type, area, strategy="balanced",
                 temperature=None, moisture=None, rainfall=None,
                 city=None, wind=None, weather_humidity=None,
                 soil_condition=None):
        self.soil_type = soil_type
        self.area = area
        self.strategy = strategy
        self.temperature = temperature
        self.moisture = moisture
        self.rainfall = rainfall
        self.city = city
        self.wind = wind
        self.weather_humidity = weather_humidity
        self.soil_condition = soil_condition or "healthy"

    def _normalize_soil(self):
        if not self.soil_type:
            return None
        soil = self.soil_type.strip()
        
        name_map = {
            "clay": "Clay", "sandy": "Sandy", "loam": "Loam",
            "sand": "Sandy", "sandy loam": "Sandy", "loamy sand": "Sandy",
            "alluvial": "Alluvial", "black": "Black", "red": "Red",
        }
        
        return name_map.get(soil.lower(), soil.title())

    def get_viable_crops(self):
        normalized = self._normalize_soil()
        return CROP_SOIL_COMPATIBILITY.get(normalized, [])

    def _score_crop(self, crop):
        """Score a crop based on ALL available metrics."""
        score = 0.5  # base score
        reasons = []
        
        # 1. Soil Compatibility (must-have)
        viable = self.get_viable_crops()
        if crop not in viable:
            return 0.0, ["❌ Not compatible with soil type"]
        reasons.append(f"✅ Compatible with {self.soil_type} soil")
        score += 0.1
        
        # 2. Temperature match (from sensor)
        conditions = CROP_IDEAL_CONDITIONS.get(crop, {})
        if self.temperature is not None and conditions:
            t_min, t_max = conditions.get("temp_range", (0, 50))
            if t_min <= self.temperature <= t_max:
                score += 0.15
                reasons.append(f"✅ Temperature {self.temperature}°C ideal (range: {t_min}-{t_max}°C)")
            else:
                diff = min(abs(self.temperature - t_min), abs(self.temperature - t_max))
                penalty = min(diff / 15, 0.2)
                score -= penalty
                reasons.append(f"⚠️ Temperature {self.temperature}°C outside ideal range ({t_min}-{t_max}°C)")
        
        # 3. Moisture match (from sensor)
        if self.moisture is not None and conditions:
            m_min, m_max = conditions.get("moisture_range", (0, 100))
            if m_min <= self.moisture <= m_max:
                score += 0.15
                reasons.append(f"✅ Soil moisture {self.moisture}% ideal (range: {m_min}-{m_max}%)")
            else:
                diff = min(abs(self.moisture - m_min), abs(self.moisture - m_max))
                penalty = min(diff / 30, 0.15)
                score -= penalty
                reasons.append(f"⚠️ Soil moisture {self.moisture}% outside ideal ({m_min}-{m_max}%)")
        
        # 4. Rainfall match (from weather API)
        if self.rainfall is not None and conditions:
            # Convert hourly rainfall to estimated annual
            est_annual = self.rainfall * 365 * 24  # very rough
            r_min, r_max = conditions.get("rainfall_range", (0, 3000))
            reasons.append(f"ℹ️ Current rainfall: {self.rainfall}mm/hr")
        
        # 5. Risk factor
        risk = CROP_RISK_FACTORS.get(crop, 0.5)
        if risk < 0.3:
            score += 0.05
            reasons.append(f"✅ Low risk crop (risk factor: {risk})")
        elif risk > 0.5:
            score -= 0.05
            reasons.append(f"⚠️ Higher risk crop (risk factor: {risk})")
        
        # 6. Water need check
        water_info = CROP_WATER_CONSUMPTION.get(crop, {})
        if water_info and conditions:
            water_need = conditions.get("water_need", "Medium")
            if self.moisture is not None and self.moisture < 30 and water_need in ["High", "Very High"]:
                score -= 0.1
                reasons.append(f"⚠️ High water need but low soil moisture")
        
        # 7. Soil Condition Adjustment (Novelty 1 integration)
        if self.soil_condition == "cracked":
            # Cracked soil → favor drought-tolerant crops, penalize water-hungry ones
            drought_tolerant = ["Millet", "Sorghum", "Chickpea", "Groundnut", "Mustard", "Sesame"]
            if crop in drought_tolerant:
                score += 0.1
                reasons.append("✅ Drought-tolerant crop — ideal for cracked soil condition")
            else:
                water_need = conditions.get("water_need", "Medium") if conditions else "Medium"
                if water_need in ["High", "Very High"]:
                    score -= 0.15
                    reasons.append("⚠️ High water demand — risky in cracked/dry soil conditions")
                else:
                    reasons.append("ℹ️ Soil shows cracking — monitor moisture closely")
        elif self.soil_condition == "waterlogged":
            # Waterlogged → favor flood-tolerant crops
            flood_tolerant = ["Rice", "Jute", "Sugarcane"]
            if crop in flood_tolerant:
                score += 0.1
                reasons.append("✅ Flood-tolerant crop — suitable for waterlogged conditions")
            else:
                score -= 0.15
                reasons.append("⚠️ Waterlogged soil — root rot risk for this crop. Improve drainage first.")
        elif self.soil_condition == "compacted":
            # Compacted → penalize deep-root crops, favor shallow-root ones
            shallow_root = ["Rice", "Wheat", "Onion", "Lettuce", "Mustard"]
            if crop in shallow_root:
                score += 0.05
                reasons.append("✅ Shallow-root crop — can grow in compacted soil")
            else:
                score -= 0.08
                reasons.append("⚠️ Compacted soil may restrict root growth — aerate before planting")
        else:
            # Healthy soil — small bonus
            score += 0.02
            reasons.append("✅ Soil condition: Healthy — optimal for all crops")
        
        score = max(0.0, min(1.0, score))
        return score, reasons

    def generate_plan(self, multi_crop=True, max_crops=4):
        """
        Generate crop allocation plan with profit estimates.
        
        Args:
            multi_crop: If True, recommend multiple crops for different zones
            max_crops: Maximum number of crops in multi-crop mode
        """
        crops = self.get_viable_crops()
        if not crops:
            return None

        # Score all crops
        scored = []
        for crop in crops:
            score, reasons = self._score_crop(crop)
            if score > 0:
                economics = get_crop_economics(crop, self.area) or {}
                scored.append({
                    "crop": crop,
                    "score": score,
                    "reasons": reasons,
                    "economics": economics,
                })

        scored.sort(key=lambda x: x["score"], reverse=True)

        if not multi_crop:
            # Single crop: just take the best one
            scored = scored[:1]
            max_crops = 1
        else:
            scored = scored[:max_crops]

        if not scored:
            return None

        # Allocate area proportional to scores
        total_score = sum(c["score"] for c in scored)
        if total_score == 0:
            total_score = len(scored)

        results = []
        total_profit = 0
        total_yield = 0

        for item in scored:
            fraction = item["score"] / total_score
            area_allocated = self.area * fraction

            yield_info = CROP_TYPICAL_YIELD.get(item["crop"], {})
            yield_range = yield_info.get("yield_range_kg_per_m2", (0.2, 0.4))
            avg_yield_per_m2 = (yield_range[0] + yield_range[1]) / 2
            crop_yield = avg_yield_per_m2 * area_allocated

            price_info = CROP_MARKET_PRICES.get(item["crop"], {})
            avg_price = price_info.get("avg_price", 20)
            profit = crop_yield * avg_price

            suitability = "Excellent" if item["score"] > 0.75 else \
                         "Good" if item["score"] > 0.55 else "Fair"

            total_profit += profit
            total_yield += crop_yield

            results.append({
                "crop": item["crop"],
                "area_allocated": round(area_allocated, 2),
                "area_fraction": round(fraction * 100, 1),
                "yield_per_m2": round(avg_yield_per_m2, 3),
                "total_yield": round(crop_yield, 2),
                "price_per_kg": avg_price,
                "estimated_profit": round(profit, 0),
                "suitability_score": round(item["score"], 2),
                "suitability": suitability,
                "reasons": item["reasons"],
            })

        return {
            "crops": results,
            "total_profit": round(total_profit, 0),
            "total_yield": round(total_yield, 0),
            "multi_crop": multi_crop,
            "summary": self._build_summary(results),
        }

    def _build_summary(self, results):
        """Build a human-readable recommendation summary."""
        lines = []
        lines.append(f"📍 **Location**: {self.city or 'Unknown'}")
        
        if self.temperature is not None:
            lines.append(f"🌡️ **Sensor Temperature**: {self.temperature}°C")
        if self.moisture is not None:
            lines.append(f"💧 **Soil Moisture**: {self.moisture}%")
        if self.weather_humidity is not None:
            lines.append(f"💨 **Weather Humidity**: {self.weather_humidity}%")
        if self.rainfall is not None:
            lines.append(f"🌧️ **Current Rainfall**: {self.rainfall} mm/hr")
        if self.wind is not None:
            lines.append(f"🌬️ **Wind Speed**: {self.wind} km/h")
        
        lines.append(f"🔬 **Soil Type**: {self.soil_type}")
        lines.append(f"📐 **Field Area**: {self.area:,.0f} m² ({self.area/4047:.2f} acres)")
        
        return "\n".join(lines)