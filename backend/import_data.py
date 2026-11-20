import pandas as pd
from database import get_connection


file_path = "C:/Users/RSCH/Desktop/DWD/Final project/Retail-Intelligence-Platform/datasets/amez_dataset_cleaned.xlsx"

data = pd.read_excel(
    file_path,
    sheet_name="Overall_Transactions"
)

print("Excel loaded successfully.")
print("Rows:", len(data))

customers = data[
    ["CustomerID"]
].drop_duplicates()

customers = customers.dropna(
    subset=["CustomerID"]
)

print("Customers:", len(customers))


products = data[
    [
        "ProductID",
        "ProductName",
        "Category",
        "SubCategory"
    ]
].drop_duplicates(
    subset=["ProductID"]
)

products = products.dropna(
    subset=["ProductID"]
)

print("Products:", len(products))


stores = data[
    [
        "StoreID",
        "StoreName"
    ]
].drop_duplicates(
    subset=["StoreID"]
)

stores = stores.dropna(
    subset=["StoreID"]
)

print("Stores:", len(stores))


transactions = data[
    [
        "InvoiceID",
        "InvoiceDate",
        "CustomerID",
        "ProductID",
        "Quantity",
        "UnitPrice",
        "Discount",
        "TotalAmount",
        "StockQuantity",
        "StoreID",
        "ProductName",
        "Category",
        "SubCategory",
        "StoreName"
    ]
].copy()

print("Transactions:", len(transactions))


connection = get_connection()

cursor = connection.cursor()

print("Connected to MySQL.")


for _, row in customers.iterrows():

    cursor.execute(
        """
        INSERT IGNORE INTO customers
        (CustomerID)
        VALUES (%s)
        """,
        (str(row["CustomerID"]),)
    )

connection.commit()

print("Customers inserted.")


for _, row in products.iterrows():

    cursor.execute(
        """
        INSERT IGNORE INTO products
        (
            ProductID,
            ProductName,
            Category,
            SubCategory
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            str(row["ProductID"]),
            row["ProductName"],
            row["Category"],
            row["SubCategory"]
        )
    )

connection.commit()

print("Products inserted.")


for _, row in stores.iterrows():

    cursor.execute(
        """
        INSERT IGNORE INTO stores
        (
            StoreID,
            StoreName
        )
        VALUES (%s, %s)
        """,
        (
            str(row["StoreID"]),
            row["StoreName"]
        )
    )

connection.commit()

print("Stores inserted.")


for _, row in transactions.iterrows():

    cursor.execute(
        """
        INSERT INTO transactions
        (
            InvoiceID,
            InvoiceDate,
            CustomerID,
            ProductID,
            Quantity,
            UnitPrice,
            Discount,
            TotalAmount,
            StockQuantity,
            StoreID,
            Category,
            SubCategory,
            ProductName,
            StoreName
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            row["InvoiceID"],
            row["InvoiceDate"],
            str(row["CustomerID"]),
            str(row["ProductID"]),
            row["Quantity"],
            row["UnitPrice"],
            row["Discount"],
            row["TotalAmount"],
            row["StockQuantity"],
            str(row["StoreID"]),
            row["Category"],
            row["SubCategory"],
            row["ProductName"],
            row["StoreName"]
        )
    )

connection.commit()

print("Transactions inserted.")

cursor.close()
connection.close()

print("Database import completed successfully.")