"""
Synthetic Crop Yield Dataset Generator
----------------------------------------
Generates a realistic training dataset calibrated to ICAR-style optimal
agronomic ranges for Rice, Wheat, and Maize across major Indian growing
states. Yield is computed using a Mitscherlich/Liebig-style crop response
model (each factor scored for closeness to its optimal range, combined
with domain-informed weights), plus Gaussian noise to simulate real-world
variability (pest pressure, micro-climate, farmer practice, etc).

NOTE: This is a SYNTHETIC dataset built to let the model learn genuine
agronomic relationships for demo/prototype purposes. For the actual SIH
submission, replace this with real historical yield data from
data.gov.in (Ministry of Agriculture) and Soil Health Card data
(soilhealth.dac.gov.in) joined with IMD rainfall/temperature records.
"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

# Crop-specific optimal ranges and base yield potential (quintal/acre)
CROP_PARAMS = {
    "Rice": {
        "rainfall": (1000, 1500), "temp": (25, 35),
        "N": (100, 140), "P": (50, 70), "K": (35, 50), "pH": (5.5, 6.5),
        "base_yield": 25, "weights": {"rainfall": 0.30, "temp": 0.15, "N": 0.20, "P": 0.13, "K": 0.10, "pH": 0.12},
    },
    "Wheat": {
        "rainfall": (400, 650), "temp": (15, 25),
        "N": (100, 140), "P": (50, 70), "K": (35, 50), "pH": (6.0, 7.5),
        "base_yield": 20, "weights": {"rainfall": 0.25, "temp": 0.20, "N": 0.20, "P": 0.13, "K": 0.10, "pH": 0.12},
    },
    "Maize": {
        "rainfall": (500, 800), "temp": (21, 27),
        "N": (100, 140), "P": (60, 80), "K": (35, 50), "pH": (5.5, 7.0),
        "base_yield": 22, "weights": {"rainfall": 0.28, "temp": 0.18, "N": 0.20, "P": 0.12, "K": 0.10, "pH": 0.12},
    },
}

REGIONS = ["Bihar", "Punjab", "Uttar Pradesh", "Madhya Pradesh", "Maharashtra", "West Bengal"]


def suitability_score(value, low, high, spread_factor=0.6):
    """1.0 inside optimal range, decays linearly outside it."""
    if low <= value <= high:
        return 1.0
    span = high - low
    if value < low:
        dist = low - value
    else:
        dist = value - high
    decay = max(0.0, 1 - dist / (span * spread_factor + 1e-6))
    return max(0.15, decay)  # floor so yield never collapses to zero


def sample_crop_rows(crop, n):
    p = CROP_PARAMS[crop]
    rows = []
    for _ in range(n):
        rainfall = rng.uniform(p["rainfall"][0] * 0.4, p["rainfall"][1] * 1.4)
        temp = rng.uniform(p["temp"][0] * 0.7, p["temp"][1] * 1.25)
        N = rng.uniform(p["N"][0] * 0.4, p["N"][1] * 1.3)
        P = rng.uniform(p["P"][0] * 0.4, p["P"][1] * 1.3)
        K = rng.uniform(p["K"][0] * 0.4, p["K"][1] * 1.3)
        pH = rng.uniform(p["pH"][0] * 0.85, p["pH"][1] * 1.1)
        area = rng.uniform(0.5, 10)
        region = rng.choice(REGIONS)

        scores = {
            "rainfall": suitability_score(rainfall, *p["rainfall"]),
            "temp": suitability_score(temp, *p["temp"]),
            "N": suitability_score(N, *p["N"]),
            "P": suitability_score(P, *p["P"]),
            "K": suitability_score(K, *p["K"]),
            "pH": suitability_score(pH, *p["pH"]),
        }
        suitability = sum(scores[k] * p["weights"][k] for k in scores)
        yield_per_acre = p["base_yield"] * (0.35 + 0.65 * suitability)
        yield_per_acre *= rng.normal(1.0, 0.06)  # real-world noise
        yield_per_acre = max(2.0, yield_per_acre)

        rows.append({
            "crop": crop, "region": region, "rainfall_mm": round(rainfall, 1),
            "avg_temp_c": round(temp, 1), "N_kg_ha": round(N, 1), "P_kg_ha": round(P, 1),
            "K_kg_ha": round(K, 1), "soil_ph": round(pH, 2), "area_acres": round(area, 2),
            "yield_quintal_per_acre": round(yield_per_acre, 2),
        })
    return rows


if __name__ == "__main__":
    all_rows = []
    for crop in CROP_PARAMS:
        all_rows += sample_crop_rows(crop, 1200)
    df = pd.DataFrame(all_rows).sample(frac=1, random_state=42).reset_index(drop=True)
    df.to_csv("/home/claude/crop_ml/synthetic_crop_data.csv", index=False)
    print(f"Generated {len(df)} rows")
    print(df.groupby("crop")["yield_quintal_per_acre"].describe())
