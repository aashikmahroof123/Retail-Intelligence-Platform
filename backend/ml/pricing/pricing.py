
import numpy as np


def recommend_price(
    current_price,
    predicted_demand,
    elasticity,
    stock_quantity,
    min_price=None,
    max_price=None,
    low_stock_threshold=10
):
    """
    Recommend a price using predicted demand,
    price elasticity, inventory, and estimated revenue.

    Does not require unit cost or calculate profit.
    """

    # 1. Validate inputs
    if not np.isfinite(current_price) or current_price <= 0:
        raise ValueError("Current price must be greater than 0.")

    if not np.isfinite(predicted_demand) or predicted_demand < 0:
        raise ValueError("Predicted demand cannot be negative.")

    if elasticity is None or not np.isfinite(elasticity):
        raise ValueError("A valid elasticity value is required.")

    if not np.isfinite(stock_quantity) or stock_quantity < 0:
        raise ValueError("Stock quantity cannot be negative.")

    if low_stock_threshold < 0:
        raise ValueError("Low stock threshold cannot be negative.")

    # 2. Analyse inventory
    stock_status = (
        "Low Stock"
        if stock_quantity <= low_stock_threshold
        else "Available"
    )

    # 3. Define candidate price range
    if min_price is None:
        min_price = current_price * 0.80

    if max_price is None:
        max_price = current_price * 1.20

    if (
        not np.isfinite(min_price)
        or not np.isfinite(max_price)
        or min_price <= 0
        or max_price < min_price
    ):
        raise ValueError("Invalid minimum or maximum price.")

    # 4. Generate candidate prices
    candidate_prices = np.linspace(min_price, max_price, 41)
    results = []

    # 5. Estimate demand and revenue at each price
    for price in candidate_prices:

        demand_at_price = predicted_demand * (
            price / current_price
        ) ** elasticity

        demand_at_price = max(0.0, float(demand_at_price))

        # Demand cannot exceed available inventory
        expected_sales = min(demand_at_price, stock_quantity)

        estimated_revenue = float(price) * expected_sales

        results.append({
            "price": round(float(price), 2),
            "predicted_demand": round(demand_at_price, 2),
            "expected_sales": round(expected_sales, 2),
            "revenue": round(estimated_revenue, 2)
        })

    # 6. Select the price with the highest estimated revenue
    best_option = max(
        results,
        key=lambda result: result["revenue"]
    )

    # 7. Return pricing and inventory results
    return {
        "current_price": round(float(current_price), 2),
        "baseline_predicted_demand": round(
            float(predicted_demand), 2
        ),
        "elasticity": round(float(elasticity), 4),
        "stock_quantity": float(stock_quantity),
        "stock_status": stock_status,
        "low_stock_threshold": low_stock_threshold,
        "recommended_price": best_option["price"],
        "expected_demand": best_option["predicted_demand"],
        "expected_sales": best_option["expected_sales"],
        "expected_revenue": best_option["revenue"],
        "evaluated_prices": results
    }
