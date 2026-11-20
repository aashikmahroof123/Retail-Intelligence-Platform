from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from zoneinfo import ZoneInfo
import math
from fastapi import Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


from database import get_connection

from ml.segmentation.kmeans_model import (
    predict_customer_segment
)

from ml.forecasting.train_forecast import (
    forecast_with_lightgbm,
    forecast_for_any_product
)

from ml.pricing.demand_model import (
    predict_demand
)

from ml.pricing.pricing import (
    recommend_price
)

from ml.pricing.elasticity import (
    estimate_price_elasticity
)

from ml.market_basket.market_basket import (
    recommend_related_products
)

from ml.recommendations.personalized import (
    recommend_for_customer
)
from auth import (
    password_hash,
    create_access_token,
    get_current_admin,
)

app = FastAPI(
    title="Retail Intelligence Platform API"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(request: LoginRequest):
    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT username, password_hash
            FROM admins
            WHERE username = %s
            """,
            (request.username,),
        )

        admin = cursor.fetchone()
        cursor.close()

    finally:
        connection.close()

    if not admin or not password_hash.verify(
        request.password,
        admin["password_hash"],
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    token = create_access_token(admin["username"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": admin["username"],
    }

# ============================================================
# SAVE LIGHTGBM AND PROPHET FORECASTS TO MYSQL
# ============================================================

def save_demand_forecasts(forecasts, product_id=None, model_name=None):
    """
    Save LightGBM or Prophet forecast results to MySQL.

    Supports:
    1. A list of forecast dictionaries.
    2. The complete response from forecast_for_any_product().
    """

    if isinstance(forecasts, dict):
        # Prophet/product endpoint returns a dictionary
        # containing a Forecast list.
        response = forecasts
        forecast_rows = response.get("Forecast", [])

        product_id = product_id or response.get("ProductID")
        model_name = model_name or response.get("Model")

    elif isinstance(forecasts, list):
        forecast_rows = forecasts

    else:
        raise ValueError("Invalid forecast response format.")

    if not forecast_rows:
        return 0

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        saved_count = 0

        for item in forecast_rows:
            row_product_id = (
                item.get("ProductID") or product_id
            )

            forecast_date = item.get("ForecastDate")
            predicted_demand = item.get("PredictedDemand")

            row_model = (
                item.get("Model") or model_name
            )

            if not row_product_id:
                raise ValueError(
                    "ProductID is missing from a forecast."
                )

            if not forecast_date:
                raise ValueError(
                    "ForecastDate is missing from a forecast."
                )

            if predicted_demand is None:
                raise ValueError(
                    "PredictedDemand is missing from a forecast."
                )

            if not row_model:
                raise ValueError(
                    "Forecast model name is missing."
                )

            predicted_demand = float(predicted_demand)

            if (
                not math.isfinite(predicted_demand)
                or predicted_demand < 0
            ):
                raise ValueError(
                    "Predicted demand must be finite and non-negative."
                )

            # Remove any previous records for this exact
            # product, date, and model. This avoids duplicates
            # when the same forecast is requested again.
            cursor.execute(
                """
                DELETE FROM demand_forecasts
                WHERE ProductID = %s
                  AND ForecastDate = %s
                  AND ModelName = %s
                """,
                (
                    row_product_id,
                    forecast_date,
                    row_model
                )
            )

            # Save the latest prediction.
            cursor.execute(
                """
                INSERT INTO demand_forecasts
                (
                    ProductID,
                    ForecastDate,
                    PredictedDemand,
                    ModelName
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    row_product_id,
                    forecast_date,
                    predicted_demand,
                    row_model
                )
            )

            saved_count += 1

        connection.commit()
        return saved_count

    except Exception:
        if connection is not None:
            connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

# ============================================================
# ROOT
# ============================================================

@app.get("/")
def home():
    return {
        "message": "Retail Intelligence Platform API is running"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }



# ============================================================
# CUSTOMER SEGMENTATION BY CUSTOMER ID
# ============================================================

@app.get("/customer-segment/{customer_id}")
def customer_segment_by_id(customer_id: str):
    connection = None
    cursor = None

    try:
        # Connect to MySQL
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # Calculate RFM values for this customer
        cursor.execute(
            """
            SELECT
                CustomerID,
                DATEDIFF(
                    DATE_ADD(
                        (SELECT MAX(InvoiceDate)
                         FROM transactions
                         WHERE InvoiceDate IS NOT NULL),
                        INTERVAL 1 DAY
                    ),
                    MAX(InvoiceDate)
                ) AS Recency,

                COUNT(DISTINCT InvoiceID) AS Frequency,

                COALESCE(SUM(TotalAmount), 0) AS Monetary

            FROM transactions
            WHERE CustomerID = %s
            GROUP BY CustomerID
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        # Check whether the customer exists
        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer ID not found."
            )

        # Read the calculated RFM values
        recency = customer["Recency"]
        frequency = customer["Frequency"]
        monetary = customer["Monetary"]

        if recency is None:
            raise HTTPException(
                status_code=400,
                detail="This customer's purchase dates are unavailable."
            )

        recency = float(recency)
        frequency = float(frequency)
        monetary = float(monetary or 0)

        # Predict the customer's cluster using your existing model
        prediction = predict_customer_segment(
            recency,
            frequency,
            monetary
        )

        # Return everything needed by the frontend
        return {
            "customer_id": customer["CustomerID"],

            "rfm": {
                "recency": recency,
                "frequency": frequency,
                "monetary": monetary
            },

            "cluster": int(prediction["cluster"]),
            "segment": str(prediction["segment"])
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

# ============================================================
# GET ALL CUSTOMER IDs FOR DROPDOWN
# ============================================================

@app.get("/customer-ids")
def get_customer_ids():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT DISTINCT CustomerID
            FROM customers
            WHERE CustomerID IS NOT NULL
            ORDER BY CustomerID
        """)

        customers = cursor.fetchall()

        return {
            "customer_ids": [
                str(customer["CustomerID"])
                for customer in customers
            ]
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# LIGHTGBM FORECAST — SAVE RESULTS TO MYSQL
# ============================================================

@app.get("/forecast/lightgbm/{product_id}")
def lightgbm_forecast(
    product_id: str,
    days: int = 7
   
):
    if days < 1 or days > 30:
        raise HTTPException(
            status_code=400,
            detail="Days must be between 1 and 30."
        )

    try:
        # Generate LightGBM forecasts
        forecasts = forecast_with_lightgbm(
            product_id=product_id,
            days=days
        )

        # Save the predictions to MySQL
        saved_count = save_demand_forecasts(
            forecasts,
            product_id=product_id,
            model_name="LightGBM"
        )

        return {
            "status": "success",
            "message": "LightGBM forecasts generated and saved to MySQL.",
            "product_id": product_id,
            "model": "LightGBM",
            "saved_records": saved_count,
            "forecasts": forecasts
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )



# ============================================================
# PROPHET / PRODUCT FORECAST — SAVE RESULTS TO MYSQL
# ============================================================

@app.get("/forecast/product/{product_id}")
def get_product_forecast(
    product_id: str,
    days: int = 7
):
    if days < 1 or days > 30:
        raise HTTPException(
            status_code=400,
            detail="Days must be between 1 and 30."
        )

    try:
        # Generate forecasts using Prophet when available,
        # otherwise use the existing LightGBM fallback.
        result = forecast_for_any_product(
            product_id=product_id,
            days=days
        )

        # Save the forecasts and preserve the actual model name
        # returned by forecast_for_any_product().
        saved_count = save_demand_forecasts(result)

        # Preserve the existing forecast response and add
        # confirmation of the database save.
        result["status"] = "success"
        result["message"] = (
            "Product forecasts generated and saved to MySQL."
        )
        result["saved_records"] = saved_count

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )





# ============================================================
# PRICING REQUEST MODEL
# ============================================================

class PricingRequest(BaseModel):
    product_id: str = Field(
        min_length=1,
        max_length=100
    )


# ============================================================
# ELASTICITY-AWARE DEMAND MODELLING,
# INVENTORY ANALYSIS AND PRICING
# ============================================================

@app.post("/pricing/recommend")
def pricing_recommend(
    request: PricingRequest
):
    connection = None
    cursor = None

    try:
        # ----------------------------------------------------
        # 1. Validate the product ID
        # ----------------------------------------------------

        product_id = request.product_id.strip()

        if not product_id:
            raise HTTPException(
                status_code=400,
                detail="Product ID is required."
            )

        # ----------------------------------------------------
        # 2. Retrieve the latest product transaction
        # ----------------------------------------------------

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                p.ProductID,
                p.ProductName,
                t.StoreID,
                t.StoreName,
                t.InvoiceDate,
                t.UnitPrice,
                t.Discount,
                t.TotalAmount,
                t.Quantity,
                t.StockQuantity,
                t.TransactionID
            FROM products p
            INNER JOIN transactions t
                ON p.ProductID = t.ProductID
            WHERE p.ProductID = %s
            ORDER BY
                t.InvoiceDate DESC,
                t.TransactionID DESC
            LIMIT 1
            """,
            (product_id,)
        )

        product = cursor.fetchone()

        if product is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Product not found or no transaction "
                    "history is available."
                )
            )

        # ----------------------------------------------------
        # 3. Read and validate transaction values
        # ----------------------------------------------------

        product_name = product["ProductName"]
        store_id = product["StoreID"]
        store_name = product["StoreName"]

        current_listed_price = float(
            product["UnitPrice"] or 0
        )

        quantity = float(
            product["Quantity"] or 0
        )

        total_amount = float(
            product["TotalAmount"] or 0
        )

        stock_quantity = float(
            product["StockQuantity"] or 0
        )

        if (
            not all(
                math.isfinite(value)
                for value in [
                    current_listed_price,
                    quantity,
                    total_amount,
                    stock_quantity
                ]
            )
            or current_listed_price <= 0
            or quantity <= 0
            or total_amount <= 0
            or stock_quantity < 0
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Invalid price, quantity, transaction "
                    "amount, or stock quantity."
                )
            )

        # TotalAmount is assumed to be the net transaction
        # amount after discount.
        current_price_after_discount = (
            total_amount / quantity
        )

        if (
            not math.isfinite(current_price_after_discount)
            or current_price_after_discount <= 0
        ):
            raise HTTPException(
                status_code=422,
                detail="Invalid effective selling price."
            )

        current_discount_per_unit = max(
            0.0,
            current_listed_price
            - current_price_after_discount
        )

        # ----------------------------------------------------
        # 4. Calculate historical discount rate
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(
                        GREATEST(
                            0,
                            (UnitPrice * Quantity) - TotalAmount
                        )
                    )
                    /
                    NULLIF(
                        SUM(UnitPrice * Quantity),
                        0
                    ),
                    0
                ) AS average_discount_rate
            FROM transactions
            WHERE ProductID = %s
              AND Quantity > 0
              AND UnitPrice > 0
            """,
            (product_id,)
        )

        discount_row = cursor.fetchone() or {}

        historical_discount_rate = float(
            discount_row.get("average_discount_rate") or 0
        )

        if not math.isfinite(historical_discount_rate):
            historical_discount_rate = 0.0

        # Prevent an invalid discount rate.
        historical_discount_rate = min(
            max(historical_discount_rate, 0.0),
            0.95
        )

        # ----------------------------------------------------
        # 5. Get the current date in Sri Lanka
        # ----------------------------------------------------

        today = datetime.now(
            ZoneInfo("Asia/Colombo")
        )

        day_of_week = today.weekday()
        month = today.month
        day = today.day

        # ----------------------------------------------------
        # 6. Estimate product price elasticity
        # ----------------------------------------------------

        elasticity = estimate_price_elasticity(
            product_id
        )

        if (
            elasticity is None
            or not math.isfinite(float(elasticity))
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "A valid price elasticity estimate "
                    "is unavailable for this product."
                )
            )

        elasticity = float(elasticity)

        # ----------------------------------------------------
        # 7. Predict baseline demand
        # ----------------------------------------------------

        predicted_demand = predict_demand(
            effective_price=current_price_after_discount,
            discount=current_discount_per_unit,
            day_of_week=day_of_week,
            month=month,
            day=day,
            stock_quantity=stock_quantity,
            elasticity=elasticity
        )

        predicted_demand = float(predicted_demand)

        if (
            not math.isfinite(predicted_demand)
            or predicted_demand < 0
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "The demand model returned an invalid "
                    "demand prediction."
                )
            )

        # ----------------------------------------------------
        # 8. Recommend a price
        #
        # Updated pricing.py does not accept unit_cost
        # and does not calculate estimated profit.
        #
        # Its recommended_price is treated as the final
        # after-discount selling price.
        # ----------------------------------------------------

        pricing_result = recommend_price(
            current_price=current_price_after_discount,
            predicted_demand=predicted_demand,
            elasticity=elasticity,
            stock_quantity=stock_quantity
        )

        recommended_price_after_discount = float(
            pricing_result["recommended_price"]
        )

        if (
            not math.isfinite(
                recommended_price_after_discount
            )
            or recommended_price_after_discount <= 0
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "The pricing model returned an invalid "
                    "recommended price."
                )
            )

        # ----------------------------------------------------
        # 9. Calculate the recommended listed price
        #
        # The historical discount rate is used to derive
        # a listed price from the recommended final price.
        # ----------------------------------------------------

        recommended_price_before_discount = (
            recommended_price_after_discount
            / (1.0 - historical_discount_rate)
        )

        recommended_discount_per_unit = max(
            0.0,
            recommended_price_before_discount
            - recommended_price_after_discount
        )

        # ----------------------------------------------------
        # 10. Predict demand at the recommended price
        # ----------------------------------------------------

        final_predicted_demand = predict_demand(
            effective_price=recommended_price_after_discount,
            discount=recommended_discount_per_unit,
            day_of_week=day_of_week,
            month=month,
            day=day,
            stock_quantity=stock_quantity,
            elasticity=elasticity
        )

        final_predicted_demand = float(
            final_predicted_demand
        )

        if (
            not math.isfinite(final_predicted_demand)
            or final_predicted_demand < 0
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "The final demand prediction is invalid."
                )
            )

        # ----------------------------------------------------
        # 11. Inventory analysis
        # ----------------------------------------------------

        expected_units_sold = min(
            final_predicted_demand,
            stock_quantity
        )

        if stock_quantity == 0:
            stock_status = "Out of Stock"
        elif stock_quantity <= 10:
            stock_status = "Low Stock"
        else:
            stock_status = "Available"

        # ----------------------------------------------------
        # 12. Estimate revenue
        # ----------------------------------------------------

        expected_revenue = (
            recommended_price_after_discount
            * expected_units_sold
        )

        # ----------------------------------------------------
        # 13. Return the pricing recommendation
        # ----------------------------------------------------

        return {
            "status": "success",

            # Product and store
            "product_id": product_id,
            "product_name": product_name,
            "store_id": store_id,
            "store_name": store_name,

            # Current prices
            "current_price_before_discount": round(
                current_listed_price, 2
            ),
            "current_discount_per_unit": round(
                current_discount_per_unit, 2
            ),
            "current_price_after_discount": round(
                current_price_after_discount, 2
            ),

            # Recommended prices
            "recommended_price_before_discount": round(
                recommended_price_before_discount, 2
            ),
            "recommended_discount_per_unit": round(
                recommended_discount_per_unit, 2
            ),
            "recommended_price_after_discount": round(
                recommended_price_after_discount, 2
            ),
            "historical_discount_rate_percent": round(
                historical_discount_rate * 100, 2
            ),

            # Demand and revenue
            "baseline_predicted_demand": round(
                predicted_demand, 2
            ),
            "predicted_demand": round(
                final_predicted_demand, 2
            ),
            "expected_units_sold": round(
                expected_units_sold, 2
            ),
            "expected_revenue": round(
                expected_revenue, 2
            ),

            # Inventory
            "available_stock": round(
                stock_quantity, 2
            ),
            "stock_status": stock_status,

            # Elasticity
            "price_elasticity": round(
                elasticity, 4
            ),

            # Prediction date
            "prediction_date": today.strftime(
                "%Y-%m-%d"
            ),
            "prediction_month": today.strftime(
                "%B"
            )
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# DASHBOARD OVERVIEW - OVERALL AND MONTHLY FILTER
# ============================================================

@app.get("/dashboard/overview")
def dashboard_overview(month: str = "all"):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # Validate the selected month: YYYY-MM or all
        if month != "all":
            try:
                datetime.strptime(month, "%Y-%m")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid month. Use YYYY-MM format."
                )

        # 1. Get all months available in the transactions table
        cursor.execute("""
            SELECT DISTINCT
                DATE_FORMAT(InvoiceDate, '%Y-%m') AS month_value,
                DATE_FORMAT(InvoiceDate, '%M %Y') AS month_label
            FROM transactions
            WHERE InvoiceDate IS NOT NULL
            ORDER BY month_value ASC
        """)

        available_months = cursor.fetchall()

        # Build the date filter for the selected month
        if month == "all":
            date_condition = ""
            date_parameters = ()
        else:
            date_condition = """
                AND DATE_FORMAT(t.InvoiceDate, '%Y-%m') = %s
            """
            date_parameters = (month,)

        # 2. Total sales for the selected period
        cursor.execute(f"""
            SELECT COALESCE(SUM(t.TotalAmount), 0) AS total_sales
            FROM transactions t
            WHERE 1 = 1
            {date_condition}
        """, date_parameters)

        total_sales = cursor.fetchone()["total_sales"]

        # 3. Total customers in the database
        cursor.execute("""
            SELECT COUNT(*) AS total_customers
            FROM customers
        """)

        total_customers = cursor.fetchone()["total_customers"]

        # 4. Total products in the database
        cursor.execute("""
            SELECT COUNT(*) AS total_products
            FROM products
        """)

        total_products = cursor.fetchone()["total_products"]

        # 5. Top-selling products for the selected period
        cursor.execute(f"""
            SELECT
                p.ProductID,
                p.ProductName,
                COALESCE(SUM(t.Quantity), 0) AS units_sold,
                COALESCE(SUM(t.TotalAmount), 0) AS total_sales
            FROM products p
            INNER JOIN transactions t
                ON p.ProductID = t.ProductID
            WHERE 1 = 1
            {date_condition}
            GROUP BY p.ProductID, p.ProductName
            ORDER BY total_sales DESC, units_sold DESC
            LIMIT 5
        """, date_parameters)

        top_products = cursor.fetchall()

        # 6. Lowest-selling products for the selected period
        cursor.execute(f"""
            SELECT
                p.ProductID,
                p.ProductName,
                COALESCE(SUM(t.Quantity), 0) AS units_sold,
                COALESCE(SUM(t.TotalAmount), 0) AS total_sales
            FROM products p
            INNER JOIN transactions t
                ON p.ProductID = t.ProductID
            WHERE 1 = 1
            {date_condition}
            GROUP BY p.ProductID, p.ProductName
            ORDER BY total_sales ASC, units_sold ASC
            LIMIT 5
        """, date_parameters)

        low_products = cursor.fetchall()

        # 7. Monthly sales across all available months
        cursor.execute("""
            SELECT
                DATE_FORMAT(InvoiceDate, '%Y-%m') AS month,
                DATE_FORMAT(InvoiceDate, '%M %Y') AS month_label,
                COALESCE(SUM(TotalAmount), 0) AS total_sales
            FROM transactions
            WHERE InvoiceDate IS NOT NULL
            GROUP BY
                DATE_FORMAT(InvoiceDate, '%Y-%m'),
                DATE_FORMAT(InvoiceDate, '%M %Y')
            ORDER BY month ASC
        """)

        monthly_sales = cursor.fetchall()

        # 8. Recent transactions for the selected period
        cursor.execute(f"""
            SELECT
                t.TransactionID,
                t.InvoiceDate,
                t.CustomerID,
                t.ProductID,
                p.ProductName,
                t.Quantity,
                t.TotalAmount
            FROM transactions t
            LEFT JOIN products p
                ON t.ProductID = p.ProductID
            WHERE 1 = 1
            {date_condition}
            ORDER BY
                t.InvoiceDate DESC,
                t.TransactionID DESC
            LIMIT 10
        """, date_parameters)

        recent_transactions = cursor.fetchall()

        return {
            "selected_month": month,
            "available_months": available_months,
            "total_sales": float(total_sales or 0),
            "total_customers": int(total_customers or 0),
            "total_products": int(total_products or 0),
            "top_products": top_products,
            "low_products": low_products,
            "monthly_sales": monthly_sales,
            "recent_transactions": recent_transactions
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load dashboard: {error}"
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

# ============================================================
# MARKET BASKET ANALYSIS
# ============================================================

@app.get("/market-basket/{product_name}")
def get_related_products(
    product_name: str,
    limit: int = 5
):
    if limit < 1 or limit > 20:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 20."
        )

    try:
        recommendations = recommend_related_products(
            product_name,
            limit
        )

        return {
            "product_name": product_name,
            "related_products": recommendations
        }

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )



# ============================================================
# PERSONALIZED RECOMMENDATIONS WITH PRODUCT NAMES
# ============================================================

@app.get("/recommendations/{customer_id}")
def get_personalized_recommendations(
    customer_id: str,
    limit: int = 5
):
    if limit < 1 or limit > 20:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 20."
        )

    connection = None
    cursor = None

    try:
        # Get recommendations from the existing ML model
        results = recommend_for_customer(
            customer_id,
            limit
        )

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # Add actual product details to each recommendation
        recommendations = []

        for item in results:
            product_id = str(item["ProductID"])

            cursor.execute(
                """
                SELECT ProductID, ProductName, Category, SubCategory
                FROM products
                WHERE ProductID = %s
                """,
                (product_id,)
            )

            product = cursor.fetchone()

            # Try the transaction table if the product table
            # does not contain this product
            if product is None:
                cursor.execute(
                    """
                    SELECT
                        ProductID,
                        ProductName,
                        Category,
                        SubCategory
                    FROM transactions
                    WHERE ProductID = %s
                    LIMIT 1
                    """,
                    (product_id,)
                )
                product = cursor.fetchone()

            recommendations.append({
                "ProductID": product_id,
                "ProductName": (
                    product["ProductName"]
                    if product else None
                ),
                "Category": (
                    product.get("Category")
                    if product else None
                ),
                "SubCategory": (
                    product.get("SubCategory")
                    if product else None
                ),
                "Score": item["Score"]
            })

        return {
            "customer_id": customer_id,
            "recommendations": recommendations
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# CUSTOMER PREVIOUS PURCHASE HISTORY
# ============================================================

@app.get("/customer-history/{customer_id}")
def get_customer_history(customer_id: str):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                t.InvoiceID,
                t.InvoiceDate,
                t.CustomerID,
                t.ProductID,
                COALESCE(p.ProductName, t.ProductName) AS ProductName,
                t.Quantity,
                t.UnitPrice,
                t.Discount,
                t.TotalAmount
            FROM transactions t
            LEFT JOIN products p
                ON t.ProductID = p.ProductID
            WHERE t.CustomerID = %s
            ORDER BY t.InvoiceDate DESC
            LIMIT 100
            """,
            (customer_id,)
        )

        history = cursor.fetchall()

        return {
            "customer_id": customer_id,
            "purchase_history": history
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()
# ============================================================
# GET ALL PRODUCT IDs FOR DROPDOWNS
# ============================================================

@app.get("/product-ids")
def get_product_ids():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT DISTINCT ProductID
            FROM products
            WHERE ProductID IS NOT NULL
            ORDER BY ProductID
        """)

        products = cursor.fetchall()

        return {
            "product_ids": [
                str(product["ProductID"])
                for product in products
            ]
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

@app.get("/product-names")
def get_product_names():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT DISTINCT ProductName
            FROM products
            WHERE ProductName IS NOT NULL
              AND TRIM(ProductName) != ''
            ORDER BY ProductName
        """)

        products = cursor.fetchall()

        return {
            "product_names": [
                str(product["ProductName"])
                for product in products
            ]
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()    

@app.get("/inventory/overview")
def get_overall_inventory():

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                p.ProductID,
                p.ProductName,
                p.Category,
                latest.StockQuantity

            FROM products p

            LEFT JOIN transactions latest
                ON latest.TransactionID = (
                    SELECT t.TransactionID
                    FROM transactions t
                    WHERE t.ProductID = p.ProductID
                    ORDER BY
                        t.InvoiceDate DESC,
                        t.TransactionID DESC
                    LIMIT 1
                )

            ORDER BY p.ProductName ASC
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        products = []

        total_stock = 0
        low_stock_count = 0
        out_of_stock_count = 0

        for row in rows:

            stock_value = row["StockQuantity"]

            if stock_value is None:
                available_stock = None
                status = "Stock Not Recorded"

            else:
                available_stock = int(stock_value)

                total_stock += available_stock

                if available_stock <= 0:
                    status = "Out of Stock"
                    out_of_stock_count += 1

                elif available_stock <= 10:
                    status = "Low Stock"
                    low_stock_count += 1

                else:
                    status = "Healthy"

            products.append({
                "product_id": row["ProductID"],
                "product_name": row["ProductName"],
                "category": row["Category"],
                "available_stock": available_stock,
                "status": status
            })

        return {
            "summary": {
                "total_products": len(products),
                "total_stock": total_stock,
                "low_stock": low_stock_count,
                "out_of_stock": out_of_stock_count
            },
            "products": products
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve inventory: {str(error)}"
        )

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
# ============================================================
# CUSTOMERS
# ============================================================

@app.get("/customers")
def get_customers():
    connection = None
    cursor = None

    admin: dict = Depends(get_current_admin),
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM customers
            LIMIT 100
            """
        )

        return cursor.fetchall()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# TRANSACTIONS
# ============================================================

@app.get("/transactions")
def get_transactions():
    connection = None
    cursor = None
    admin: dict = Depends(get_current_admin),
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM transactions
            LIMIT 100
            """
        )

        return cursor.fetchall()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()
