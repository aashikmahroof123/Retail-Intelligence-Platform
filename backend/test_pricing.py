import pandas as pd
from pathlib import Path

from ml.pricing.demand_model import predict_demand
from ml.pricing.pricing import recommend_price


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    BASE_DIR
    / "datasets"
    / "amez_dataset_cleaned.xlsx"
)

ELASTICITY_PATH = (
    BASE_DIR
    / "datasets"
    / "elasticity_features.xlsx"
)


# ============================================================
# LOAD MAIN DATASET
# ============================================================

data = pd.read_excel(
    DATASET_PATH,
    sheet_name="Overall_Transactions"
)


# ============================================================
# LOAD ELASTICITY DATASET
# ============================================================

elasticity_data = pd.read_excel(
    ELASTICITY_PATH
)


# ============================================================
# PREPARE MAIN DATA
# ============================================================

data["InvoiceDate"] = pd.to_datetime(
    data["InvoiceDate"]
)

data["EffectivePrice"] = (
    data["UnitPrice"]
    - data["Discount"]
)

data["DayOfWeek"] = (
    data["InvoiceDate"].dt.dayofweek
)

data["Month"] = (
    data["InvoiceDate"].dt.month
)

data["Day"] = (
    data["InvoiceDate"].dt.day
)


# ============================================================
# PREPARE ELASTICITY DATA
# ============================================================

elasticity_data["InvoiceDate"] = pd.to_datetime(
    elasticity_data["InvoiceDate"]
)


# ============================================================
# CREATE PRICE-DEMAND DATA
# ============================================================

price_demand = (
    elasticity_data
    .groupby(
        ["ProductID", "EffectivePrice"],
        as_index=False
    )
    .agg(
        TotalDemand=("Quantity", "sum"),
        SalesObservations=("InvoiceDate", "count")
    )
)


# ============================================================
# ESTIMATE ELASTICITY
# ============================================================

import numpy as np


def estimate_elasticity(product_data):

    product_data = product_data[
        (product_data["EffectivePrice"] > 0)
        &
        (product_data["TotalDemand"] > 0)
    ].copy()

    product_data = product_data.drop_duplicates(
        subset=["EffectivePrice"]
    )

    if len(product_data) < 3:
        return None

    log_price = np.log(
        product_data["EffectivePrice"]
    )

    log_demand = np.log(
        product_data["TotalDemand"]
    )

    slope = np.polyfit(
        log_price,
        log_demand,
        1
    )[0]

    return float(slope)


# ============================================================
# CALCULATE ELASTICITY FOR PRODUCTS
# ============================================================

elasticity_results = []

for product_id, group in price_demand.groupby(
    "ProductID"
):

    elasticity = estimate_elasticity(
        group
    )

    elasticity_results.append(
        {
            "ProductID": product_id,
            "Elasticity": elasticity,
            "PriceObservations":
                group["EffectivePrice"].nunique()
        }
    )


elasticity_df = pd.DataFrame(
    elasticity_results
)


# ============================================================
# SELECT PRODUCTS WITH VALID ELASTICITY
# ============================================================

valid_elasticity = elasticity_df[
    elasticity_df["Elasticity"].notna()
].copy()


if valid_elasticity.empty:

    raise ValueError(
        "No products with valid elasticity were found."
    )


# ============================================================
# SELECT A REAL TRANSACTION
# ============================================================

test_data = data.merge(
    valid_elasticity[
        [
            "ProductID",
            "Elasticity"
        ]
    ],
    on="ProductID",
    how="inner"
)


if test_data.empty:

    raise ValueError(
        "No matching products were found "
        "between the main dataset and "
        "elasticity dataset."
    )


# Remove invalid values

test_data = test_data[
    (test_data["EffectivePrice"] > 0)
    &
    (test_data["UnitPrice"] > 0)
    &
    (test_data["StockQuantity"] >= 0)
]


# ============================================================
# SELECT FIRST REAL RECORD
# ============================================================

test_row = test_data.iloc[0]


# ============================================================
# GET REAL VALUES
# ============================================================

product_id = test_row["ProductID"]

product_name = test_row["ProductName"]

current_price = float(
    test_row["UnitPrice"]
)

discount = float(
    test_row["Discount"]
)

effective_price = float(
    test_row["EffectivePrice"]
)

day_of_week = int(
    test_row["DayOfWeek"]
)

month = int(
    test_row["Month"]
)

day = int(
    test_row["Day"]
)

stock_quantity = float(
    test_row["StockQuantity"]
)

elasticity = float(
    test_row["Elasticity"]
)

unit_cost = 0.0


# ============================================================
# DISPLAY REAL DATA USED
# ============================================================

print()
print("=" * 60)
print("REAL DATA SELECTED FOR PRICING TEST")
print("=" * 60)

print("Product ID:", product_id)
print("Product Name:", product_name)
print("Invoice Date:", test_row["InvoiceDate"])
print("Unit Price:", current_price)
print("Discount:", discount)
print("Effective Price:", effective_price)
print("Day of Week:", day_of_week)
print("Month:", month)
print("Day:", day)
print("Stock Quantity:", stock_quantity)
print("Elasticity:", round(elasticity, 4))


# ============================================================
# LIGHTGBM DEMAND PREDICTION
# ============================================================

predicted_demand = predict_demand(
    effective_price=effective_price,
    discount=discount,
    day_of_week=day_of_week,
    month=month,
    day=day,
    stock_quantity=stock_quantity,
    elasticity=elasticity
)


print()
print("=" * 60)
print("LIGHTGBM DEMAND PREDICTION")
print("=" * 60)

print(
    "Predicted Demand:",
    round(predicted_demand, 2)
)


# ============================================================
# PRICING RECOMMENDATION
# ============================================================

result = recommend_price(
    current_price=current_price,
    predicted_demand=predicted_demand,
    elasticity=elasticity,
    stock_quantity=stock_quantity,
    unit_cost=unit_cost
)


# ============================================================
# INVENTORY ANALYSIS
# ============================================================

print()
print("=" * 60)
print("INVENTORY ANALYSIS")
print("=" * 60)

print(
    "Stock Quantity:",
    result["stock_quantity"]
)

print(
    "Stock Status:",
    result["stock_status"]
)

print(
    "Low Stock Threshold:",
    result["low_stock_threshold"]
)


# ============================================================
# PRICING RECOMMENDATION
# ============================================================

print()
print("=" * 60)
print("PRICING RECOMMENDATION")
print("=" * 60)

print(
    "Current Price:",
    result["current_price"]
)

print(
    "Elasticity:",
    result["elasticity"]
)

print(
    "Baseline Predicted Demand:",
    result["baseline_predicted_demand"]
)

print(
    "Recommended Price:",
    result["recommended_price"]
)

print(
    "Expected Demand:",
    result["expected_demand"]
)

print(
    "Expected Sales:",
    result["expected_sales"]
)

print(
    "Expected Revenue:",
    result["expected_revenue"]
)

print(
    "Estimated Profit:",
    result["estimated_profit"]
)


# ============================================================
# TEST COMPLETED
# ============================================================

print()
print("=" * 60)
print("PRICING TEST COMPLETED SUCCESSFULLY")
print("=" * 60)