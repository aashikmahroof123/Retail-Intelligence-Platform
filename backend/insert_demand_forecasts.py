import sys
from pathlib import Path

import mysql.connector


# ============================================================
# 1. PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(
    "C:/Users/RSCH/Desktop/DWD/Final project/"
    "Retail-Intelligence-Platform"
)

BACKEND_PATH = PROJECT_ROOT / "backend"

sys.path.insert(
    0,
    str(BACKEND_PATH)
)


# ============================================================
# 2. IMPORT FORECASTING FUNCTIONS
# ============================================================

from ml.forecasting.train_forecast import (
    forecast_with_lightgbm,
    forecast_with_prophet
)


# ============================================================
# 3. MYSQL CONNECTION
# ============================================================

from database import get_connection


# ============================================================
# 4. SETTINGS
# ============================================================

LIGHTGBM_DAYS = 7
PROPHET_DAYS = 14


# ============================================================
# 5. CONNECT TO MYSQL
# ============================================================

print("Connecting to MySQL...")

connection = get_connection()

cursor = connection.cursor()

print("MySQL connection successful.")


# ============================================================
# 6. CLEAR OLD FORECAST RESULTS
# ============================================================

cursor.execute(
    "DELETE FROM demand_forecasts"
)

connection.commit()

print(
    "Old demand forecast results cleared."
)


# ============================================================
# 7. GET PRODUCT IDS FROM LIGHTGBM MODEL
# ============================================================

from ml.forecasting.train_forecast import (
    product_code_map
)

product_ids = list(
    product_code_map.keys()
)

print(
    "Products available for LightGBM:",
    len(product_ids)
)


# ============================================================
# 8. LIGHTGBM FORECASTING
# ============================================================

print("\nStarting LightGBM forecasting...")

lightgbm_inserted = 0


for product_id in product_ids:

    try:

        results = forecast_with_lightgbm(
            product_id=product_id,
            days=LIGHTGBM_DAYS
        )

        for result in results:

            cursor.execute(
                """
                INSERT INTO demand_forecasts
                (
                    ProductID,
                    ForecastDate,
                    PredictedDemand,
                    ModelName
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    result["ProductID"],
                    result["ForecastDate"],
                    result["PredictedDemand"],
                    result["Model"]
                )
            )

            lightgbm_inserted += 1

    except Exception as error:

        print(
            f"LightGBM failed for ProductID "
            f"{product_id}: {error}"
        )


connection.commit()


print(
    "\nLightGBM forecast rows inserted:",
    lightgbm_inserted
)


# ============================================================
# 9. PROPHET FORECASTING
# ============================================================

print("\nStarting Prophet forecasting...")


try:

    prophet_results = forecast_with_prophet(
        days=PROPHET_DAYS
    )

    prophet_inserted = 0

    for result in prophet_results:

        cursor.execute(
            """
            INSERT INTO demand_forecasts
            (
                ProductID,
                ForecastDate,
                PredictedDemand,
                ModelName
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                result["ProductID"],
                result["ForecastDate"],
                result["PredictedDemand"],
                result["Model"]
            )
        )

        prophet_inserted += 1


    connection.commit()


    print(
        "Prophet forecast rows inserted:",
        prophet_inserted
    )


except Exception as error:

    print(
        "Prophet forecasting failed:",
        error
    )


# ============================================================
# 10. CHECK DATABASE
# ============================================================

cursor.execute(
    """
    SELECT COUNT(*)
    FROM demand_forecasts
    """
)

total_forecasts = cursor.fetchone()[0]


print(
    "\nTotal demand forecast records in MySQL:",
    total_forecasts
)


# ============================================================
# 11. CLOSE CONNECTION
# ============================================================

cursor.close()

connection.close()

print(
    "\nMySQL connection closed."
)

print(
    "Demand forecasting database update completed."
)