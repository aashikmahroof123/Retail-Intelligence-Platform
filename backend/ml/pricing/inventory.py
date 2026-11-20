from typing import Dict


# ============================================================
# Inventory analysis
# ============================================================

def analyze_inventory(
    stock_quantity,
    low_stock_threshold=10
) -> Dict:
    """
    Analyze the current inventory level.

    Parameters
    ----------
    stock_quantity : float
        Current available stock.

    low_stock_threshold : float
        Stock level below or equal to this value
        is considered low stock.

    Returns
    -------
    dict
        Inventory analysis result.
    """

    # --------------------------------------------------------
    # Validate stock
    # --------------------------------------------------------

    if stock_quantity < 0:
        raise ValueError(
            "Stock quantity cannot be negative."
        )

    if low_stock_threshold < 0:
        raise ValueError(
            "Low stock threshold cannot be negative."
        )

    # --------------------------------------------------------
    # Determine stock status
    # --------------------------------------------------------

    if stock_quantity <= low_stock_threshold:

        stock_status = "Low Stock"

    else:

        stock_status = "Available"

    # --------------------------------------------------------
    # Return inventory information
    # --------------------------------------------------------

    return {
        "stock_quantity": round(
            float(stock_quantity),
            2
        ),
        "low_stock_threshold": round(
            float(low_stock_threshold),
            2
        ),
        "stock_status": stock_status,
        "is_low_stock": (
            stock_quantity <= low_stock_threshold
        )
    }