
import numpy as np
import pandas as pd

from database import get_connection


def estimate_price_elasticity(product_id: str):
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                InvoiceDate,
                Quantity,
                TotalAmount
            FROM transactions
            WHERE ProductID = %s
              AND Quantity > 0
              AND TotalAmount > 0
            ORDER BY InvoiceDate
            """,
            (product_id,)
        )

        rows = cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    if not rows:
        return None

    df = pd.DataFrame(rows)

    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Quantity"] = pd.to_numeric(df["Quantity"])
    df["TotalAmount"] = pd.to_numeric(df["TotalAmount"])

    # Combine transactions occurring on the same day.
    df["Date"] = df["InvoiceDate"].dt.date

    daily = (
        df.groupby("Date")
        .agg(
            Quantity=("Quantity", "sum"),
            Revenue=("TotalAmount", "sum")
        )
        .reset_index()
    )

    # Average realized selling price per unit.
    daily["EffectivePrice"] = (
        daily["Revenue"] / daily["Quantity"]
    )

    # Log-log regression requires positive values.
    daily = daily[
        (daily["Quantity"] > 0)
        & (daily["EffectivePrice"] > 0)
    ]

    # Do not invent an elasticity if the history is insufficient.
    if len(daily) < 5:
        return None

    if daily["EffectivePrice"].nunique() < 3:
        return None

    log_price = np.log(daily["EffectivePrice"].to_numpy())
    log_quantity = np.log(daily["Quantity"].to_numpy())

    elasticity, intercept = np.polyfit(
        log_price,
        log_quantity,
        1
    )

    if not np.isfinite(elasticity):
        return None

    return round(float(elasticity), 4)
