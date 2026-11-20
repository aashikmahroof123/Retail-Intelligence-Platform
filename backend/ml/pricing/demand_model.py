import joblib
import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]


# ============================================================
# MODEL PATH
# ============================================================

MODEL_FOLDER = (
    BASE_DIR
    / "backend"
    / "ml"
    / "pricing"
    / "models"
)


MODEL_PATH = (
    MODEL_FOLDER
    / "lightgbm_demand_model.pkl"
)


FEATURES_PATH = (
    MODEL_FOLDER
    / "pricing_features.pkl"
)


# ============================================================
# CHECK FILES
# ============================================================

if not MODEL_PATH.exists():

    raise FileNotFoundError(
        f"LightGBM model not found:\n{MODEL_PATH}"
    )


if not FEATURES_PATH.exists():

    raise FileNotFoundError(
        f"Pricing features file not found:\n{FEATURES_PATH}"
    )


# ============================================================
# LOAD MODEL
# ============================================================

model = joblib.load(
    MODEL_PATH
)


FEATURES = joblib.load(
    FEATURES_PATH
)


# ============================================================
# PREDICT DEMAND
# ============================================================

def predict_demand(
    effective_price,
    discount,
    day_of_week,
    month,
    day,
    stock_quantity,
    elasticity
):

    input_data = pd.DataFrame([
        {
            "EffectivePrice": float(effective_price),
            "Discount": float(discount),
            "DayOfWeek": int(day_of_week),
            "Month": int(month),
            "Day": int(day),
            "StockQuantity": float(stock_quantity),
            "Elasticity": float(elasticity)
        }
    ])


    # Make sure the columns are
    # exactly the same as training
    input_data = input_data[FEATURES]


    # LightGBM prediction
    prediction = model.predict(
        input_data
    )


    predicted_demand = float(
        prediction[0]
    )


    # Demand cannot be negative
    predicted_demand = max(
        0.0,
        predicted_demand
    )


    return predicted_demand