from database import get_connection

from ml.recommendations.personalized import (
    recommend_for_customer
)


# ============================================================
# 1. CONNECT TO MYSQL
# ============================================================

print("Connecting to MySQL...")

connection = get_connection()

cursor = connection.cursor()

print(
    "MySQL connection successful."
)


# ============================================================
# 2. GET CUSTOMERS
# ============================================================

cursor.execute(
    """
    SELECT CustomerID
    FROM customers
    """
)

customers = cursor.fetchall()

print(
    "Customers found:",
    len(customers)
)


# ============================================================
# 3. CLEAR OLD RECOMMENDATIONS
# ============================================================

cursor.execute(
    "DELETE FROM recommendations"
)

connection.commit()

print(
    "Old recommendation results cleared."
)


# ============================================================
# 4. GENERATE RECOMMENDATIONS
# ============================================================

inserted = 0


for customer in customers:

    customer_id = str(
        customer[0]
    )


    try:

        results = recommend_for_customer(
            customer_id=customer_id,
            limit=5
        )


        if not results:

            continue


        for result in results:

            product_id = result.get(
                "ProductID"
            )

            reason = result.get(
                "RecommendationReason",
                "Personalized recommendation"
            )


            if product_id is None:

                continue


            cursor.execute(
                """
                INSERT INTO recommendations
                (
                    CustomerID,
                    ProductID,
                    RecommendationReason
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    customer_id,
                    str(product_id),
                    reason
                )
            )


            inserted += 1


    except Exception as error:

        print(
            f"Recommendation failed for "
            f"{customer_id}: {error}"
        )


# ============================================================
# 5. COMMIT
# ============================================================

connection.commit()


print(
    "\nRecommendation records inserted:",
    inserted
)


# ============================================================
# 6. CHECK DATABASE
# ============================================================

cursor.execute(
    """
    SELECT COUNT(*)
    FROM recommendations
    """
)

total_recommendations = cursor.fetchone()[0]


print(
    "Total recommendations in MySQL:",
    total_recommendations
)


# ============================================================
# 7. CLOSE CONNECTION
# ============================================================

cursor.close()

connection.close()

print(
    "\nMySQL connection closed."
)

print(
    "Recommendation database update completed."
)