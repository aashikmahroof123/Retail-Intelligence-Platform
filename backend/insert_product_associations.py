import pandas as pd

from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import (
    apriori,
    association_rules
)

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

print("Loading dataset...")

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
# 3. CREATE PRODUCT BASKETS
# ============================================================

basket_data = data[
    [
        "InvoiceID",
        "ProductID"
    ]
].drop_duplicates()


transactions = (
    basket_data
    .groupby("InvoiceID")["ProductID"]
    .apply(list)
    .tolist()
)


print(
    "Number of baskets:",
    len(transactions)
)


# ============================================================
# 4. REMOVE SINGLE-PRODUCT BASKETS
# ============================================================

transactions = [
    basket
    for basket in transactions
    if len(basket) >= 2
]


print(
    "Baskets with multiple products:",
    len(transactions)
)


# ============================================================
# 5. ENCODE TRANSACTIONS
# ============================================================

encoder = TransactionEncoder()

encoded_data = encoder.fit(
    transactions
).transform(
    transactions
)


basket = pd.DataFrame(
    encoded_data,
    columns=encoder.columns_
)


print(
    "Basket matrix created."
)

print(
    "Shape:",
    basket.shape
)


# ============================================================
# 6. FIND FREQUENT ITEMSETS
# ============================================================

print(
    "\nRunning Apriori..."
)


frequent_itemsets = apriori(
    basket,
    min_support=0.005,
    use_colnames=True
)


print(
    "Frequent itemsets:",
    len(frequent_itemsets)
)


# ============================================================
# 7. GENERATE ASSOCIATION RULES
# ============================================================

if len(frequent_itemsets) > 0:

    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=0.05
    )

else:

    rules = pd.DataFrame()


print(
    "Association rules:",
    len(rules)
)


# ============================================================
# 8. CHECK RULES BEFORE MYSQL
# ============================================================

if len(rules) > 0:

    print(
        "\nTop association rules:"
    )

    display_columns = [
        "antecedents",
        "consequents",
        "support",
        "confidence",
        "lift"
    ]

    print(
        rules[
            display_columns
        ]
        .sort_values(
            "lift",
            ascending=False
        )
        .head(10)
        .to_string(index=False)
    )

else:

    print(
        "\nNo association rules were generated."
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
# 10. CLEAR OLD ASSOCIATIONS
# ============================================================

cursor.execute(
    "DELETE FROM product_associations"
)

connection.commit()

print(
    "Old association results cleared."
)


# ============================================================
# 11. INSERT ASSOCIATION RULES
# ============================================================

inserted = 0


if len(rules) > 0:

    for _, row in rules.iterrows():

        antecedents = list(
            row["antecedents"]
        )

        consequents = list(
            row["consequents"]
        )


        # ----------------------------------------------------
        # Only one product on each side
        # ----------------------------------------------------

        if len(antecedents) != 1:
            continue


        if len(consequents) != 1:
            continue


        product_a = str(
            antecedents[0]
        )

        product_b = str(
            consequents[0]
        )


        # ----------------------------------------------------
        # Insert into MySQL
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO product_associations
            (
                ProductA,
                ProductB,
                Support,
                Confidence,
                Lift
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
                product_a,
                product_b,
                float(row["support"]),
                float(row["confidence"]),
                float(row["lift"])
            )
        )


        inserted += 1


# ============================================================
# 12. COMMIT
# ============================================================

connection.commit()


print(
    "\nAssociation records inserted:",
    inserted
)


# ============================================================
# 13. CHECK MYSQL
# ============================================================

cursor.execute(
    """
    SELECT COUNT(*)
    FROM product_associations
    """
)

total_associations = cursor.fetchone()[0]


print(
    "Total product associations in MySQL:",
    total_associations
)


# ============================================================
# 14. CLOSE CONNECTION
# ============================================================

cursor.close()

connection.close()


print(
    "\nMySQL connection closed."
)

print(
    "Apriori database update completed."
)