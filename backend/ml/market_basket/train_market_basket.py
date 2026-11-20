from pathlib import Path

import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[3]

DATASET_FILE = (
    ROOT
    / "datasets"
    / "basket_data.xlsx"
)

OUTPUT_FILE = (
    ROOT
    / "backend"
    / "ml"
    / "market_basket"
    / "association_rules.csv"
)


# ============================================================
# SETTINGS
# ============================================================

MIN_SUPPORT = 0.002
MIN_CONFIDENCE = 0.05
MIN_LIFT = 1.0

# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("MARKET BASKET ANALYSIS - TRAINING")
print("=" * 70)

print()
print("Dataset:")
print(DATASET_FILE)

if not DATASET_FILE.exists():
    raise FileNotFoundError(
        f"Dataset not found:\n{DATASET_FILE}"
    )

data = pd.read_excel(DATASET_FILE)

print()
print("Dataset shape:")
print(data.shape)

print()
print("Columns:")
print(data.columns.tolist())


# ============================================================
# VALIDATE COLUMNS
# ============================================================

required_columns = [
    "InvoiceID",
    "ProductName"
]

for column in required_columns:
    if column not in data.columns:
        raise ValueError(
            f"Required column not found: {column}"
        )


# ============================================================
# CLEAN DATA
# ============================================================

data = data[
    required_columns
].dropna()

data["InvoiceID"] = (
    data["InvoiceID"]
    .astype(str)
    .str.strip()
)

data["ProductName"] = (
    data["ProductName"]
    .astype(str)
    .str.strip()
)

data = data[
    (data["InvoiceID"] != "")
    & (data["ProductName"] != "")
]

# Remove duplicate product inside the same invoice
data = data.drop_duplicates(
    subset=[
        "InvoiceID",
        "ProductName"
    ]
)

print()
print("Cleaned shape:")
print(data.shape)

print()
print("Unique invoices:")
print(data["InvoiceID"].nunique())

print()
print("Unique products:")
print(data["ProductName"].nunique())


# ============================================================
# CREATE TRANSACTIONS
# ============================================================

transactions = (
    data
    .groupby("InvoiceID")["ProductName"]
    .apply(list)
    .tolist()
)

print()
print("Number of transactions:")
print(len(transactions))


# ============================================================
# TRANSACTION ENCODING
# ============================================================

encoder = TransactionEncoder()

transaction_array = encoder.fit(
    transactions
).transform(
    transactions
)

basket_matrix = pd.DataFrame(
    transaction_array,
    columns=encoder.columns_
)

print()
print("Basket matrix shape:")
print(basket_matrix.shape)


# ============================================================
# FIND FREQUENT ITEMSETS
# ============================================================

print()
print("Finding frequent itemsets...")

frequent_itemsets = apriori(
    basket_matrix,
    min_support=MIN_SUPPORT,
    use_colnames=True
)

print()
print("Number of frequent itemsets:")
print(len(frequent_itemsets))

if frequent_itemsets.empty:
    raise ValueError(
        "No frequent itemsets were found. "
        "Try reducing MIN_SUPPORT."
    )


# ============================================================
# GENERATE ASSOCIATION RULES
# ============================================================

print()
print("Generating association rules...")

rules = association_rules(
    frequent_itemsets,
    metric="confidence",
    min_threshold=MIN_CONFIDENCE
)

print()
print("Number of rules before lift filtering:")
print(len(rules))


# ============================================================
# FILTER RULES
# ============================================================

if not rules.empty:

    rules = rules[
        rules["lift"] >= MIN_LIFT
    ].copy()

print()
print("Number of rules after lift filtering:")
print(len(rules))


# ============================================================
# CONVERT FROZEN SETS TO PRODUCT NAMES
# ============================================================

if not rules.empty:

    rules["antecedents"] = rules[
        "antecedents"
    ].apply(
        lambda items:
        ", ".join(
            sorted(
                str(item)
                for item in items
            )
        )
    )

    rules["consequents"] = rules[
        "consequents"
    ].apply(
        lambda items:
        ", ".join(
            sorted(
                str(item)
                for item in items
            )
        )
    )


# ============================================================
# SORT RULES
# ============================================================

if not rules.empty:

    rules = rules.sort_values(
        by=[
            "lift",
            "confidence",
            "support"
        ],
        ascending=[
            False,
            False,
            False
        ]
    )


# ============================================================
# SAVE RULES
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

rules.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print()
print("=" * 70)
print("TRAINING COMPLETED")
print("=" * 70)

print()
print("Output file:")
print(OUTPUT_FILE)

print()
print("Final number of rules:")
print(len(rules))

if not rules.empty:

    print()
    print("Top 10 association rules:")

    print(
        rules[
            [
                "antecedents",
                "consequents",
                "support",
                "confidence",
                "lift"
            ]
        ].head(10).to_string(
            index=False
        )
    )

else:

    print()
    print(
        "WARNING: No association rules were generated."
    )

print()
print("=" * 70)