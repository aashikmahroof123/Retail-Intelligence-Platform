import pandas as pd

from ml.market_basket.market_basket import (
    recommend_related_products
)


data = pd.read_excel(
    "../datasets/basket_data.xlsx"
)


product_names = (
    data["ProductName"]
    .dropna()
    .astype(str)
    .drop_duplicates()
    .head(5)
    .tolist()
)


print("=" * 60)
print("MARKET BASKET TEST")
print("=" * 60)


print()
print("Products selected:")
print(product_names)


for product_name in product_names:

    print()
    print("-" * 60)
    print("Testing Product:", product_name)
    print("-" * 60)

    try:

        results = recommend_related_products(
            product_name,
            limit=5
        )

        if len(results) == 0:

            print(
                "No related products found."
            )

        else:

            for result in results:
                print(result)

    except Exception as error:

        print("ERROR:", error)


print()
print("=" * 60)
print("MARKET BASKET TEST COMPLETED")
print("=" * 60)