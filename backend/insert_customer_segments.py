import pandas as pd
import numpy as np
import joblib

from database import get_connection


# ============================================================
# 1. FILE PATHS
# ============================================================

rfm_file = (
    "C:/Users/RSCH/Desktop/DWD/Final project/"
    "Retail-Intelligence-Platform/datasets/customer_rfm.xlsx"
)

model_file = (
    "C:/Users/RSCH/Desktop/DWD/Final project/"
    "Retail-Intelligence-Platform/backend/ml/segmentation/"
    "kmeans_model.pkl"
)

scaler_file = (
    "C:/Users/RSCH/Desktop/DWD/Final project/"
    "Retail-Intelligence-Platform/backend/ml/segmentation/"
    "rfm_scaler.pkl"
)

labels_file = (
    "C:/Users/RSCH/Desktop/DWD/Final project/"
    "Retail-Intelligence-Platform/backend/ml/segmentation/"
    "cluster_labels.pkl"
)


# ============================================================
# 2. LOAD RFM DATA
# ============================================================

print("Loading RFM data...")

rfm = pd.read_excel(rfm_file)

print("RFM data loaded successfully.")
print("Rows:", len(rfm))
print("Columns:", rfm.columns.tolist())


# ============================================================
# 3. CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "CustomerID",
    "Recency",
    "Frequency",
    "Monetary"
]

for column in required_columns:

    if column not in rfm.columns:

        raise ValueError(
            f"Required column is missing: {column}"
        )


# ============================================================
# 4. LOAD K-MEANS MODEL
# ============================================================

print("Loading K-Means model...")

kmeans_model = joblib.load(model_file)

print("K-Means model loaded.")


# ============================================================
# 5. LOAD RFM SCALER
# ============================================================

print("Loading RFM scaler...")

scaler = joblib.load(scaler_file)

print("RFM scaler loaded.")


# ============================================================
# 6. LOAD CLUSTER LABELS
# ============================================================

print("Loading cluster labels...")

cluster_labels = joblib.load(labels_file)

print("Cluster labels loaded.")

print("Cluster labels:")
print(cluster_labels)


# ============================================================
# 7. PREPARE RFM FEATURES
# ============================================================

features = rfm[
    [
        "Recency",
        "Frequency",
        "Monetary"
    ]
].copy()


# ============================================================
# 8. APPLY SAME TRANSFORMATION USED DURING TRAINING
# ============================================================

features["Recency"] = np.log1p(
    features["Recency"]
)

features["Frequency"] = np.log1p(
    features["Frequency"]
)

features["Monetary"] = np.log1p(
    features["Monetary"]
)


# ============================================================
# 9. APPLY SAVED SCALER
# ============================================================

rfm_scaled = scaler.transform(features)

print("RFM data scaled successfully.")

print(
    "Scaled data shape:",
    rfm_scaled.shape
)


# ============================================================
# 10. PREDICT CUSTOMER CLUSTERS
# ============================================================

print("Predicting customer clusters...")

clusters = kmeans_model.predict(
    rfm_scaled
)

rfm["Cluster"] = clusters

print("Clusters predicted successfully.")


# ============================================================
# 11. CONVERT CLUSTERS TO BUSINESS SEGMENTS
# ============================================================

rfm["Segment"] = rfm["Cluster"].map(
    cluster_labels
)

print("\nSegment distribution:")

print(
    rfm["Segment"].value_counts()
)


# ============================================================
# 12. CONNECT TO MYSQL
# ============================================================

print("\nConnecting to MySQL...")

connection = get_connection()

cursor = connection.cursor()

print("MySQL connection successful.")


# ============================================================
# 13. CLEAR OLD ML RESULTS
# ============================================================

cursor.execute(
    "DELETE FROM customer_segments"
)

connection.commit()

print(
    "Old customer segmentation results cleared."
)


# ============================================================
# 14. INSERT CUSTOMER SEGMENTS
# ============================================================

print("Inserting customer segments...")


for _, row in rfm.iterrows():

    cursor.execute(
        """
        INSERT INTO customer_segments
        (
            CustomerID,
            Recency,
            Frequency,
            Monetary,
            Segment
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
            str(row["CustomerID"]),
            int(row["Recency"]),
            int(row["Frequency"]),
            float(row["Monetary"]),
            row["Segment"]
        )
    )


# ============================================================
# 15. COMMIT
# ============================================================

connection.commit()

print(
    "Customer segmentation results inserted successfully."
)


# ============================================================
# 16. CHECK INSERTED RECORDS
# ============================================================

cursor.execute(
    """
    SELECT COUNT(*)
    FROM customer_segments
    """
)

total_segments = cursor.fetchone()[0]

print(
    "\nTotal customer segments in MySQL:",
    total_segments
)


# ============================================================
# 17. CLOSE CONNECTION
# ============================================================

cursor.close()

connection.close()

print(
    "\nMySQL connection closed."
)

print(
    "Customer segmentation database update completed."
)