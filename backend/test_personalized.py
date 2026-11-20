import pandas as pd

from ml.recommendations.personalized import (
    recommend_for_customer
)


data = pd.read_excel(
    "../datasets/customer_product_features.xlsx"
)


customer_ids = (
    data["CustomerID"]
    .dropna()
    .astype(str)
    .drop_duplicates()
    .head(10)
    .tolist()
)


print("=" * 60)
print("PERSONALIZED RECOMMENDATION TEST")
print("=" * 60)


print()
print("Customers selected:")
print(customer_ids)


for customer_id in customer_ids:

    print()
    print("-" * 60)
    print(
        "Testing CustomerID:",
        customer_id
    )
    print("-" * 60)

    try:

        recommendations = (
            recommend_for_customer(
                customer_id,
                limit=5
            )
        )

        if len(recommendations) == 0:

            print(
                "No recommendations found."
            )

        else:

            for item in recommendations:
                print(item)

    except Exception as error:

        print(
            "ERROR:",
            error
        )


print()
print("=" * 60)
print(
    "PERSONALIZED RECOMMENDATION TEST COMPLETED"
)
print("=" * 60)