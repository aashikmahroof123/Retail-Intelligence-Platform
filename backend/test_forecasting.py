import pandas as pd

from ml.forecasting.train_forecast import (
    forecast_with_lightgbm,
    forecast_with_prophet,
    forecast_for_any_product
)


# Load the cleaned dataset
data = pd.read_excel(
    "../datasets/amez_dataset_cleaned.xlsx",
    sheet_name="Overall_Transactions"
)


# Get some real ProductIDs from the dataset
product_ids = (
    data["ProductID"]
    .dropna()
    .astype(str)
    .drop_duplicates()
    .head(10)
    .tolist()
)


print("=" * 60)
print("DEMAND FORECASTING TEST")
print("=" * 60)

print()
print("Products selected for testing:")
print(product_ids)


# Test 10 different products
for product_id in product_ids:

    print()
    print("-" * 60)
    print("Testing ProductID:", product_id)
    print("-" * 60)

    try:

        result = forecast_for_any_product(
            product_id=product_id,
            days=7
        )

        print("Model used:", result["Model"])
        print()

        for row in result["Forecast"]:
            print(row)

    except ValueError as error:

        print("ERROR:", error)


print()
print("=" * 60)
print("TEST COMPLETED")
print("=" * 60)