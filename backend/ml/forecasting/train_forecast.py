
from pathlib import Path
import pickle
from datetime import datetime
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd

from prophet.serialize import model_from_json


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_DIR = BASE_DIR / "models"

PROPHET_MODEL_DIR = MODEL_DIR / "prophet_models"


# ============================================================
# SRI LANKA CURRENT DATE
# ============================================================

def get_today():
    """Return today's date in Sri Lanka, without a time component."""
    return pd.Timestamp(
        datetime.now(ZoneInfo("Asia/Colombo")).date()
    )


# ============================================================
# LOAD LIGHTGBM MODEL
# ============================================================

lightgbm_artifact = joblib.load(
    MODEL_DIR / "lightgbm_model.pkl"
)

lightgbm_model = lightgbm_artifact["model"]

feature_columns = lightgbm_artifact["feature_columns"]

product_code_map = {
    str(key): value
    for key, value in lightgbm_artifact["product_code_map"].items()
}


# ============================================================
# LOAD DAILY HISTORY
# ============================================================

history = joblib.load(
    MODEL_DIR / "daily_history.pkl"
).copy()

history["ProductID"] = history["ProductID"].astype(str)

history["Date"] = pd.to_datetime(
    history["Date"]
).dt.normalize()

history["Demand"] = pd.to_numeric(
    history["Demand"],
    errors="coerce"
)

history = history.dropna(
    subset=["ProductID", "Date", "Demand"]
)


# ============================================================
# LOAD PROPHET MODEL INDEX
# ============================================================

PROPHET_INDEX_FILE = PROPHET_MODEL_DIR / "model_index.pkl"

if PROPHET_INDEX_FILE.exists():
    with open(PROPHET_INDEX_FILE, "rb") as file:
        PROPHET_MODEL_INDEX = pickle.load(file)

    PROPHET_MODEL_INDEX = {
        str(key): value
        for key, value in PROPHET_MODEL_INDEX.items()
    }
else:
    PROPHET_MODEL_INDEX = {}


# ============================================================
# VALIDATE FORECAST HORIZON
# ============================================================

def validate_days(days):
    try:
        days = int(days)
    except (TypeError, ValueError):
        raise ValueError(
            "Days must be an integer between 1 and 30."
        )

    if days < 1 or days > 30:
        raise ValueError(
            "Days must be between 1 and 30."
        )

    return days


# ============================================================
# LIGHTGBM FORECAST
# ============================================================

def forecast_with_lightgbm(product_id, days=7):

    product_id = str(product_id)
    days = validate_days(days)
    today = get_today()

    # Check whether the product was included in training.
    if product_id not in product_code_map:
        raise ValueError(
            "Product was not included in LightGBM model training."
        )

    # Retrieve the product's historical daily demand.
    product_history = (
        history[history["ProductID"] == product_id]
        .sort_values("Date")
        .copy()
    )

    if len(product_history) < 14:
        raise ValueError(
            "At least 14 days of history are required for this product."
        )

    # Start from the final date available for this product.
    values = (
        product_history["Demand"]
        .astype(float)
        .tolist()
    )

    last_date = product_history["Date"].max().normalize()

    product_code = product_code_map[product_id]

    # If the history ends before today, predict the missing dates
    # recursively first, then return only dates after today.
    # If history is already current, forecast from its last date.
    total_days = max(
        days,
        (today - last_date).days + days
    )

    results = []

    for step in range(1, total_days + 1):

        forecast_date = last_date + pd.Timedelta(days=step)

        row = {
            "ProductCode": product_code,
            "DayOfWeek": forecast_date.dayofweek,
            "DayOfMonth": forecast_date.day,
            "Month": forecast_date.month,
            "Lag_1": values[-1],
            "Lag_7": values[-7],
            "Lag_14": values[-14],
            "RollingMean_7": float(np.mean(values[-7:])),
            "RollingMean_14": float(np.mean(values[-14:])),
        }

        input_data = pd.DataFrame(
            [row],
            columns=feature_columns
        )

        prediction = float(
            lightgbm_model.predict(input_data)[0]
        )

        prediction = max(0.0, prediction)

        # Keep predictions for the next day's lag features.
        values.append(prediction)

        # Return only dates strictly after today.
        if forecast_date > today:
            results.append({
                "ProductID": product_id,
                "ForecastDate": forecast_date.strftime("%Y-%m-%d"),
                "PredictedDemand": round(prediction, 2),
                "Model": "LightGBM",
            })

        # Stop after returning the requested number of future days.
        if len(results) == days:
            break

    return results


# ============================================================
# PROPHET FORECAST FOR ONE PRODUCT
# ============================================================

def forecast_with_prophet(product_id, days=7):

    product_id = str(product_id)
    days = validate_days(days)
    today = get_today()

    # Check whether a saved Prophet model exists for this product.
    if product_id not in PROPHET_MODEL_INDEX:
        return None

    model_filename = PROPHET_MODEL_INDEX[product_id]
    model_path = PROPHET_MODEL_DIR / model_filename

    if not model_path.exists():
        return None

    # Load the product-specific Prophet model.
    with open(model_path, "r", encoding="utf-8") as file:
        model = model_from_json(file.read())

    # Get the model's actual training end date.
    model_history = getattr(model, "history", None)

    if (
        model_history is not None
        and not model_history.empty
        and "ds" in model_history.columns
    ):
        last_training_date = pd.to_datetime(
            model_history["ds"]
        ).max().normalize()
    else:
        # Fallback to the saved daily history for this product.
        product_history = history[
            history["ProductID"] == product_id
        ]

        if product_history.empty:
            raise ValueError(
                "Cannot determine the last training date for this product."
            )

        last_training_date = product_history["Date"].max().normalize()

    # Generate enough dates to cover the gap between the
    # training end date and today, plus the requested horizon.
    gap_days = max(
        0,
        (today - last_training_date).days
    )

    periods = gap_days + days

    future = model.make_future_dataframe(
        periods=periods,
        freq="D"
    )

    forecast = model.predict(future)

    forecast["ds"] = pd.to_datetime(
        forecast["ds"]
    ).dt.normalize()

    # Keep future dates only, excluding today and historical dates.
    future_forecast = (
        forecast[forecast["ds"] > today]
        .sort_values("ds")
        .head(days)
    )

    if len(future_forecast) < days:
        raise ValueError(
            "Prophet did not generate enough future forecast dates."
        )

    results = []

    for row in future_forecast.itertuples():

        predicted = max(0.0, float(row.yhat))
        lower = max(0.0, float(row.yhat_lower))
        upper = max(0.0, float(row.yhat_upper))

        results.append({
            "ProductID": product_id,
            "ForecastDate": row.ds.strftime("%Y-%m-%d"),
            "PredictedDemand": round(predicted, 2),
            "LowerBound": round(lower, 2),
            "UpperBound": round(upper, 2),
            "Model": "Prophet",
        })

    return results


# ============================================================
# FORECAST ANY PRODUCT
# ============================================================

def forecast_for_any_product(product_id, days=7):

    product_id = str(product_id)
    days = validate_days(days)

    # Prefer Prophet when a saved product-specific model exists.
    prophet_result = forecast_with_prophet(
        product_id=product_id,
        days=days
    )

    if prophet_result is not None:
        return {
            "ProductID": product_id,
            "Model": "Prophet",
            "Forecast": prophet_result,
        }

    # Otherwise, use the all-product LightGBM model.
    lightgbm_result = forecast_with_lightgbm(
        product_id=product_id,
        days=days
    )

    return {
        "ProductID": product_id,
        "Model": "LightGBM",
        "Forecast": lightgbm_result,
    }
