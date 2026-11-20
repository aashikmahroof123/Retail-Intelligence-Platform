import pandas as pd
import pickle
from pathlib import Path

from prophet import Prophet
from prophet.serialize import model_to_json


# ============================================================
# 1. Project paths
# ============================================================

model_folder = Path(
    "../backend/ml/forecasting/models/prophet_models"
)

model_folder.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 2. Load cleaned dataset
# ============================================================

file_path = Path(
    "../datasets/amez_dataset_cleaned.xlsx"
)

data = pd.read_excel(
    file_path,
    sheet_name="Overall_Transactions"
)


# ============================================================
# 3. Prepare data
# ============================================================

data["InvoiceDate"] = pd.to_datetime(
    data["InvoiceDate"]
)

data = data.dropna(
    subset=[
        "ProductID",
        "InvoiceDate",
        "Quantity"
    ]
)

# Demand should not contain negative quantities
data = data[
    data["Quantity"] > 0
].copy()

data["Date"] = (
    data["InvoiceDate"]
    .dt.normalize()
)


# ============================================================
# 4. Create daily demand for every product
# ============================================================

daily_demand = (
    data.groupby(
        [
            "ProductID",
            "Date"
        ],
        as_index=False
    )
    .agg(
        Demand=("Quantity", "sum")
    )
)

print(
    "Products found:",
    daily_demand["ProductID"].nunique()
)

print(
    "Daily demand rows:",
    len(daily_demand)
)


# ============================================================
# 5. Latest available date
# ============================================================

latest_date = daily_demand["Date"].max()

print(
    "Latest transaction date:",
    latest_date
)


# ============================================================
# 6. Train one Prophet model for each product
# ============================================================

model_index = {}

training_summary = []


for product_id, product_data in daily_demand.groupby(
    "ProductID"
):

    print(
        f"Training Prophet for ProductID: {product_id}"
    )

    # --------------------------------------------------------
    # Prepare product history
    # --------------------------------------------------------

    product_series = (
        product_data
        .set_index("Date")["Demand"]
        .sort_index()
    )

    # --------------------------------------------------------
    # Create continuous daily dates
    # --------------------------------------------------------

    date_range = pd.date_range(
        start=product_series.index.min(),
        end=latest_date,
        freq="D"
    )

    product_series = product_series.reindex(
        date_range,
        fill_value=0
    )

    # --------------------------------------------------------
    # Prophet format
    # --------------------------------------------------------

    prophet_data = pd.DataFrame({
        "ds": product_series.index,
        "y": product_series.values
    })

    # --------------------------------------------------------
    # Check amount of history
    # --------------------------------------------------------

    number_of_days = len(prophet_data)

    non_zero_days = int(
        (prophet_data["y"] > 0).sum()
    )

    # --------------------------------------------------------
    # Skip products with insufficient history
    # --------------------------------------------------------

    if (
        number_of_days < 30
        or non_zero_days < 3
    ):

        training_summary.append({
            "ProductID": product_id,
            "Status": "Insufficient history",
            "Days": number_of_days,
            "NonZeroDays": non_zero_days
        })

        print(
            f"Skipped ProductID {product_id} "
            f"- insufficient history"
        )

        continue

    # --------------------------------------------------------
    # Create Prophet model
    # --------------------------------------------------------

    model = Prophet(
    yearly_seasonality=False,
    weekly_seasonality=True,
    daily_seasonality=False,
    changepoint_prior_scale=0.1,
    seasonality_prior_scale=10,
    seasonality_mode="additive"
)

    # --------------------------------------------------------
    # Train model
    # --------------------------------------------------------

    model.fit(
        prophet_data
    )

    # --------------------------------------------------------
    # Create model filename
    # --------------------------------------------------------

    model_number = len(model_index)

    model_filename = (
        f"product_{model_number:04d}.json"
    )

    model_path = (
        model_folder / model_filename
    )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    with open(
        model_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            model_to_json(model)
        )

    # --------------------------------------------------------
    # Save ProductID → model filename
    # --------------------------------------------------------

    model_index[
        str(product_id)
    ] = model_filename

    # --------------------------------------------------------
    # Save training information
    # --------------------------------------------------------

    training_summary.append({
        "ProductID": product_id,
        "Status": "Model trained",
        "Days": number_of_days,
        "NonZeroDays": non_zero_days,
        "ModelFile": model_filename
    })

    print(
        f"Saved: {model_filename}"
    )


# ============================================================
# 7. Save ProductID → Prophet model mapping
# ============================================================

index_file = (
    model_folder / "model_index.pkl"
)

with open(
    index_file,
    "wb"
) as file:

    pickle.dump(
        model_index,
        file
    )


# ============================================================
# 8. Save training summary
# ============================================================

summary = pd.DataFrame(
    training_summary
)

summary_file = (
    model_folder / "training_summary.csv"
)

summary.to_csv(
    summary_file,
    index=False
)


# ============================================================
# 9. Final training information
# ============================================================

total_products = (
    daily_demand["ProductID"]
    .nunique()
)

trained_products = len(
    model_index
)

skipped_products = (
    total_products - trained_products
)

print()
print("=" * 60)
print("PROPHET TRAINING COMPLETED")
print("=" * 60)

print(
    "Total products:",
    total_products
)

print(
    "Prophet models trained:",
    trained_products
)

print(
    "Products without Prophet model:",
    skipped_products
)

print(
    "Model folder:",
    model_folder
)

print(
    "Model index:",
    index_file
)

print(
    "Training summary:",
    summary_file
)

print("=" * 60)

print(summary.head(20))
