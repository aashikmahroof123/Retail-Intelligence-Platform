
import os
import joblib
import numpy as np
import pandas as pd


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# MODEL FILE PATHS
# ============================================================

model_path = os.path.join(
    BASE_DIR,
    "kmeans_model.pkl"
)

scaler_path = os.path.join(
    BASE_DIR,
    "rfm_scaler.pkl"
)

labels_path = os.path.join(
    BASE_DIR,
    "cluster_labels.pkl"
)


# ============================================================
# LOAD SAVED MODEL, SCALER AND CLUSTER LABELS
# ============================================================

kmeans_model = joblib.load(model_path)

scaler = joblib.load(scaler_path)

cluster_labels = joblib.load(labels_path)


# ============================================================
# PREDICT CUSTOMER SEGMENT
# ============================================================

def predict_customer_segment(
    recency,
    frequency,
    monetary
):

    # --------------------------------------------------------
    # 1. Create RFM DataFrame
    # --------------------------------------------------------
    # The column names must match the names used during
    # model training.
    # --------------------------------------------------------

    values = pd.DataFrame({
        "Recency": [recency],
        "Frequency": [frequency],
        "Monetary": [monetary]
    })


    # --------------------------------------------------------
    # 2. Apply Log Transformation
    # --------------------------------------------------------
    # This must be the same transformation used during
    # model training.
    # --------------------------------------------------------

    values = np.log1p(values)


    # --------------------------------------------------------
    # 3. Standardize RFM Values
    # --------------------------------------------------------

    values_scaled = scaler.transform(values)


    # --------------------------------------------------------
    # 4. Convert Scaled Values back to DataFrame
    # --------------------------------------------------------
    # This keeps the feature names for K-Means.
    # --------------------------------------------------------

    values_scaled = pd.DataFrame(
        values_scaled,
        columns=[
            "Recency",
            "Frequency",
            "Monetary"
        ]
    )


    # --------------------------------------------------------
    # 5. Predict Customer Cluster
    # --------------------------------------------------------

    cluster = kmeans_model.predict(
        values_scaled
    )[0]


    # --------------------------------------------------------
    # 6. Get Business Segment Name
    # --------------------------------------------------------

    segment = cluster_labels[cluster]


    # --------------------------------------------------------
    # 7. Return Prediction
    # --------------------------------------------------------

    return {
        "cluster": int(cluster),
        "segment": segment
    }

