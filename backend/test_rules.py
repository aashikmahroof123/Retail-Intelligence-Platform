from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

RULES_FILE = (
    ROOT
    / "backend"
    / "ml"
    / "market_basket"
    / "association_rules.csv"
)

print("=" * 60)
print("MARKET BASKET RULES TEST")
print("=" * 60)

print()
print("Rules file:")
print(RULES_FILE)

print()
print("File exists:")
print(RULES_FILE.exists())

if not RULES_FILE.exists():
    print()
    print("ERROR: association_rules.csv was not found.")
    exit()

rules = pd.read_csv(RULES_FILE)

print()
print("Number of rows:")
print(len(rules))

print()
print("Columns:")
print(rules.columns.tolist())

print()
print("First 10 rows:")
print(rules.head(10))

print()
print("=" * 60)

product_name = "Pulse OLED Smartwatch Series 5"

print()
print("Testing product:")
print(product_name)

matches = rules[
    rules["antecedents"].apply(
        lambda value:
        product_name in [
            item.strip()
            for item in str(value).split(",")
        ]
    )
]

print()
print("Matching rules:")
print(len(matches))

print()

if len(matches) == 0:
    print("NO MATCHING RULES FOUND.")

    print()
    print("Sample antecedents:")

    print(
        rules["antecedents"]
        .head(20)
        .tolist()
    )

else:
    print("MATCHING RULES FOUND:")
    print(matches.head(10))

print()
print("=" * 60)