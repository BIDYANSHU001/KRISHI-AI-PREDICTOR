"""
Crop Yield Prediction - Model Training
----------------------------------------
Trains a Random Forest Regressor on crop yield data (rainfall, temperature,
soil N/P/K, pH, area, crop, region) and evaluates performance.

Swap `synthetic_crop_data.csv` for real historical data from data.gov.in +
Soil Health Card + IMD before final submission -- the pipeline itself
does not need to change.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import json

df = pd.read_csv("/home/claude/crop_ml/synthetic_crop_data.csv")

FEATURES = ["crop", "region", "rainfall_mm", "avg_temp_c", "N_kg_ha", "P_kg_ha", "K_kg_ha", "soil_ph", "area_acres"]
TARGET = "yield_quintal_per_acre"

X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

categorical = ["crop", "region"]
numeric = [c for c in FEATURES if c not in categorical]

preprocess = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
], remainder="passthrough")

model = Pipeline([
    ("prep", preprocess),
    ("rf", RandomForestRegressor(n_estimators=300, max_depth=14, random_state=42, n_jobs=-1)),
])

model.fit(X_train, y_train)
preds = model.predict(X_test)

r2 = r2_score(y_test, preds)
rmse = np.sqrt(mean_squared_error(y_test, preds))
mae = mean_absolute_error(y_test, preds)

print(f"R2: {r2:.4f}")
print(f"RMSE: {rmse:.3f} quintal/acre")
print(f"MAE:  {mae:.3f} quintal/acre")

# Feature importance (mapped back to readable names)
ohe = model.named_steps["prep"].named_transformers_["cat"]
cat_names = list(ohe.get_feature_names_out(categorical))
all_feature_names = cat_names + numeric
importances = model.named_steps["rf"].feature_importances_

imp_df = pd.DataFrame({"feature": all_feature_names, "importance": importances})
imp_df = imp_df.groupby(imp_df["feature"].apply(lambda f: f.split("_")[0] if f.startswith(("crop", "region")) else f))["importance"].sum()
imp_df = imp_df.sort_values(ascending=True)

plt.figure(figsize=(8, 5))
plt.barh(imp_df.index, imp_df.values, color="#7FB069")
plt.xlabel("Relative importance")
plt.title("Feature Importance - Crop Yield Prediction Model")
plt.tight_layout()
plt.savefig("/home/claude/crop_ml/feature_importance.png", dpi=150)
print("Saved feature_importance.png")

# Save model + metrics
joblib.dump(model, "/home/claude/crop_ml/crop_yield_model.pkl")
with open("/home/claude/crop_ml/metrics.json", "w") as f:
    json.dump({"r2": round(r2, 4), "rmse": round(rmse, 3), "mae": round(mae, 3),
               "n_train": len(X_train), "n_test": len(X_test)}, f, indent=2)
print("Saved crop_yield_model.pkl and metrics.json")
