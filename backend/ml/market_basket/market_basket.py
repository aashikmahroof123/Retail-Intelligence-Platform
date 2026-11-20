from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]

DATASET_FILE = (
    ROOT
    / "datasets"
    / "basket_data.xlsx"
)

RULES_FILE = (
    ROOT
    / "backend"
    / "ml"
    / "market_basket"
    / "association_rules.csv"
)


# ============================================================
# LOAD BASKET DATA
# ============================================================

if not DATASET_FILE.exists():
    raise FileNotFoundError(
        f"Basket dataset not found:\n{DATASET_FILE}"
    )

basket_data = pd.read_excel(
    DATASET_FILE
)

basket_data = basket_data[
    ["InvoiceID", "ProductName"]
].dropna()

basket_data["InvoiceID"] = (
    basket_data["InvoiceID"]
    .astype(str)
    .str.strip()
)

basket_data["ProductName"] = (
    basket_data["ProductName"]
    .astype(str)
    .str.strip()
)

basket_data = basket_data.drop_duplicates(
    subset=[
        "InvoiceID",
        "ProductName"
    ]
)


# ============================================================
# LOAD ASSOCIATION RULES
# ============================================================

if not RULES_FILE.exists():
    raise FileNotFoundError(
        f"Association rules not found:\n{RULES_FILE}"
    )

rules = pd.read_csv(
    RULES_FILE
)


# ============================================================
# CREATE INVOICE → PRODUCTS
# ============================================================

invoice_products = (
    basket_data
    .groupby("InvoiceID")["ProductName"]
    .apply(list)
)


# ============================================================
# RECOMMEND RELATED PRODUCTS
# ============================================================

def recommend_related_products(
    product_name,
    limit=5
):

    product_name = str(
        product_name
    ).strip()

    if limit < 1:
        return []


    # ========================================================
    # CHECK PRODUCT EXISTS
    # ========================================================

    all_products = set(
        basket_data["ProductName"]
    )

    if product_name not in all_products:
        return []


    # ========================================================
    # STEP 1
    # CHECK ASSOCIATION RULES
    # ========================================================

    matches = rules[
        rules["antecedents"].apply(
            lambda value:
            product_name in [
                item.strip()
                for item in str(value).split(",")
            ]
        )
    ].copy()


    # ========================================================
    # ASSOCIATION RULE EXISTS
    # ========================================================

    if not matches.empty:

        # Sort strongest association first
        if "lift" in matches.columns:

            matches = matches.sort_values(
                by="lift",
                ascending=False
            )

        results = []

        for _, row in matches.head(limit).iterrows():

            related_product = str(
                row["consequents"]
            ).strip()

            if related_product == product_name:
                continue

            results.append(
                {
                    "product":
                        product_name,

                    "related_product":
                        related_product,

                    "method":
                        "Association Rule",

                    "support":
                        round(
                            float(
                                row["support"]
                            ),
                            4
                        ),

                    "confidence":
                        round(
                            float(
                                row["confidence"]
                            ),
                            4
                        ),

                    "lift":
                        round(
                            float(
                                row["lift"]
                            ),
                            4
                        )
                }
            )

        # IMPORTANT:
        # Do NOT use co-purchase if association
        # rules already exist.
        return results


    # ========================================================
    # STEP 2
    # NO ASSOCIATION RULE
    # USE CO-PURCHASE
    # ========================================================

    co_purchase_counts = {}

    product_invoice_count = 0


    for products in invoice_products:

        products = list(
            set(products)
        )

        if product_name not in products:
            continue

        product_invoice_count += 1

        for other_product in products:

            if other_product == product_name:
                continue

            co_purchase_counts[
                other_product
            ] = (
                co_purchase_counts.get(
                    other_product,
                    0
                ) + 1
            )


    # ========================================================
    # NO CO-PURCHASES
    # ========================================================

    if not co_purchase_counts:
        return []


    # ========================================================
    # SORT BY CO-PURCHASE COUNT
    # ========================================================

    sorted_products = sorted(
        co_purchase_counts.items(),
        key=lambda item: item[1],
        reverse=True
    )


    # ========================================================
    # RETURN CO-PURCHASE RECOMMENDATIONS
    # ========================================================

    results = []

    for related_product, count in sorted_products[:limit]:

        co_purchase_rate = (
            count
            / product_invoice_count
        )

        results.append(
            {
                "product":
                    product_name,

                "related_product":
                    related_product,

                "method":
                    "Co-Purchase",

                "co_purchase_count":
                    int(count),

                "co_purchase_rate":
                    round(
                        float(
                            co_purchase_rate
                        ),
                        4
                    )
            }
        )


    return results