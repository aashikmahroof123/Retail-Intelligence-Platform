from pathlib import Path

import pandas as pd

from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parents[3]

DATASETS = ROOT / "datasets"


customer_product = pd.read_excel(
    DATASETS /
    "customer_product_features.xlsx"
)


product_features = pd.read_excel(
    DATASETS /
    "product_features.xlsx"
)


customer_product = customer_product.dropna(
    subset=[
        "CustomerID",
        "ProductID"
    ]
).copy()


customer_product["CustomerID"] = (
    customer_product["CustomerID"]
    .astype(str)
)

customer_product["ProductID"] = (
    customer_product["ProductID"]
    .astype(str)
)


purchase_matrix = customer_product.pivot_table(
    index="CustomerID",
    columns="ProductID",
    values="TotalQuantity",
    aggfunc="sum",
    fill_value=0
)


similarity_matrix = cosine_similarity(
    purchase_matrix
)


similarity = pd.DataFrame(
    similarity_matrix,
    index=purchase_matrix.index,
    columns=purchase_matrix.index
)


def recommend_for_customer(
    customer_id,
    limit=5
):

    customer_id = str(customer_id)

    if customer_id not in purchase_matrix.index:
        return []

    similar_customers = (
        similarity[customer_id]
        .drop(index=customer_id)
        .sort_values(
            ascending=False
        )
    )

    scores = (
        purchase_matrix
        .loc[similar_customers.index]
        .T
        .dot(similar_customers)
    )

    bought = purchase_matrix.loc[
        customer_id
    ]

    scores = scores[
        bought == 0
    ]

    scores = scores[
        scores > 0
    ]

    scores = scores.sort_values(
        ascending=False
    ).head(limit)

    return [
        {
            "ProductID": product_id,
            "Score": round(
                float(score),
                4
            )
        }
        for product_id, score
        in scores.items()
    ]