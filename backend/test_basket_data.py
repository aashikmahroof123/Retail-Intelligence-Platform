import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILE = ROOT / "datasets" / "basket_data.xlsx"

print("=" * 60)
print("BASKET DATA TEST")
print("=" * 60)

print()
print("File:")
print(FILE)

print()
print("File exists:")
print(FILE.exists())

if not FILE.exists():
    print("ERROR: basket_data.xlsx not found.")
    exit()

data = pd.read_excel(FILE)

print()
print("Shape:")
print(data.shape)

print()
print("Columns:")
print(data.columns.tolist())

print()
print("First 10 rows:")
print(data.head(10))

print()
print("Number of unique ProductName values:")

if "ProductName" in data.columns:
    print(
        data["ProductName"]
        .nunique()
    )
else:
    print("ProductName column not found.")

print()
print("Number of unique InvoiceID values:")

if "InvoiceID" in data.columns:
    print(
        data["InvoiceID"]
        .nunique()
    )
else:
    print("InvoiceID column not found.")

print()
print("=" * 60)