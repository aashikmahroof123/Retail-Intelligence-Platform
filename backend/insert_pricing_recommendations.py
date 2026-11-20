import pandas as pd
import numpy as np

from database import get_connection


# ============================================================
# 1. DATASET PATH
# ============================================================

file_path = (
    "C:/Users/RSCH/Desktop/DWD/Final project/"
    "Retail-Intelligence-Platform/datasets/"
    "amez_dataset_cleaned.xlsx"
)


# ============================================================
# 2. LOAD DATA
# ============================================================

print("Loading cleaned dataset...")

data = pd.read_excel(
    file_path,
    sheet_name="Overall_Transactions"
)

print(
    "Dataset loaded successfully."
)

print(
    "Rows:",
    len(data)
)


# ============================================================
# 3. PREPARE DATA
# ============================================================

data["InvoiceDate"] = pd.to_datetime(
    data["InvoiceDate"]
)

data = data.dropna(
    subset=[
        "ProductID",
        "Quantity",
        "UnitPrice",
        "TotalAmount"
    ]
).copy()


data = data[
    (data["Quantity"] > 0) &
    (data["UnitPrice"] > 0)
].copy()


# ============================================================
# 4. EFFECTIVE PRICE
# ============================================================

data["EffectivePrice"] = (
    data["TotalAmount"] /
    data["Quantity"]
)


# ============================================================
# 5. ESTIMATE ELASTICITY
# ============================================================

def estimate_elasticity(product_data):

    product_data = product_data[
        (product_data["EffectivePrice"] > 0) &
        (product_data["Quantity"] > 0)
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
        product_data["Quantity"]
    )


    slope = np.polyfit(
        log_price,
        log_demand,
        1
    )[0]


    return float(slope)


# ============================================================
# 6. ESTIMATE DEMAND
# ============================================================

def estimate_demand(
    current_demand,
    current_price,
    new_price,
    elasticity
):

    if pd.isna(elasticity):

        return None


    if current_price <= 0:

        return None


    demand = (
        current_demand *
        (new_price / current_price) ** elasticity
    )


    return max(
        0,
        float(demand)
    )


# ============================================================
# 7. CREATE PRODUCT PRICING DATA
# ============================================================

pricing_results = []


for product_id, product_data in data.groupby(
    "ProductID"
):

    elasticity = estimate_elasticity(
        product_data
    )


    current_price = (
        product_data["EffectivePrice"]
        .mean()
    )


    current_demand = (
        product_data["Quantity"]
        .mean()
    )


    current_stock = (
        product_data["StockQuantity"]
        .iloc[-1]
    )


    # --------------------------------------------------------
    # If elasticity cannot be calculated
    # --------------------------------------------------------

    if elasticity is None:

        pricing_results.append(
            {
                "ProductID": str(product_id),
                "CurrentPrice": float(
                    current_price
                ),
                "RecommendedPrice": None,
                "ExpectedDemand": None,
                "Elasticity": None
            }
        )

        continue


    # --------------------------------------------------------
    # Candidate prices
    # --------------------------------------------------------

    prices = [
        current_price * 0.90,
        current_price,
        current_price * 1.10
    ]


    best_price = current_price

    best_demand = current_demand

    best_revenue = (
        current_price *
        current_demand
    )


    # --------------------------------------------------------
    # Test candidate prices
    # --------------------------------------------------------

    for price in prices:

        demand = estimate_demand(
            current_demand,
            current_price,
            price,
            elasticity
        )


        if demand is None:

            continue


        revenue = (
            price *
            demand
        )


        if revenue > best_revenue:

            best_price = price

            best_demand = demand

            best_revenue = revenue


    # --------------------------------------------------------
    # Store result
    # --------------------------------------------------------

    pricing_results.append(
        {
            "ProductID": str(product_id),

            "CurrentPrice": float(
                current_price
            ),

            "RecommendedPrice": float(
                best_price
            ),

            "ExpectedDemand": float(
                best_demand
            ),

            "Elasticity": float(
                elasticity
            )
        }
    )


# ============================================================
# 8. CONVERT TO DATAFRAME
# ============================================================

pricing_df = pd.DataFrame(
    pricing_results
)


print(
    "\nPricing results created."
)

print(
    "Products:",
    len(pricing_df)
)


# ============================================================
# 9. CONNECT TO MYSQL
# ============================================================

print(
    "\nConnecting to MySQL..."
)

connection = get_connection()

cursor = connection.cursor()

print(
    "MySQL connection successful."
)


# ============================================================
# 10. CLEAR OLD PRICING RESULTS
# ============================================================

cursor.execute(
    "DELETE FROM pricing_recommendations"
)

connection.commit()

print(
    "Old pricing results cleared."
)


# ============================================================
# 11. INSERT PRICING RESULTS
# ============================================================

inserted = 0


for _, row in pricing_df.iterrows():

    cursor.execute(
        """
        INSERT INTO pricing_recommendations
        (
            ProductID,
            CurrentPrice,
            RecommendedPrice,
            ExpectedDemand,
            Elasticity
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            row["ProductID"],
            row["CurrentPrice"],
            row["RecommendedPrice"],
            row["ExpectedDemand"],
            row["Elasticity"]
        )
    )

    inserted += 1


connection.commit()


print(
    "\nPricing records inserted:",
    inserted
)


# ============================================================
# 12. CHECK DATABASE
# ============================================================

cursor.execute(
    """
    SELECT COUNT(*)
    FROM pricing_recommendations
    """
)

total_pricing = cursor.fetchone()[0]


print(
    "Total pricing records in MySQL:",
    total_pricing
)


# ============================================================
# 13. CLOSE CONNECTION
# ============================================================

cursor.close()

connection.close()

print(
    "\nMySQL connection closed."
)

print(
    "Pricing database update completed."
)