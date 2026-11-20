import pandas as pd


def calculate_rfm(data):

    data = data.copy()

    data["InvoiceDate"] = pd.to_datetime(
        data["InvoiceDate"]
    )

    reference_date = (
        data["InvoiceDate"].max()
        + pd.Timedelta(days=1)
    )

    rfm = data.groupby(
        "CustomerID"
    ).agg(
        LastPurchase=("InvoiceDate", "max"),
        Frequency=("InvoiceID", "nunique"),
        Monetary=("TotalAmount", "sum")
    ).reset_index()

    rfm["Recency"] = (
        reference_date
        - rfm["LastPurchase"]
    ).dt.days

    rfm = rfm[
        [
            "CustomerID",
            "Recency",
            "Frequency",
            "Monetary"
        ]
    ]

    return rfm



    frequency.columns = [

        "CustomerID",

        "Frequency"

    ]



    # Monetary

    monetary = data.groupby(

        "CustomerID"

    )["TotalAmount"].sum().reset_index()



    monetary.columns = [

        "CustomerID",

        "Monetary"

    ]



    # Combine RFM

    rfm = recency.merge(

        frequency,

        on="CustomerID"

    )



    rfm = rfm.merge(

        monetary,

        on="CustomerID"

    )



    return rfm               