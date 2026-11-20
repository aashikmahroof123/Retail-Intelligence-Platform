from ml.segmentation.kmeans_model import (
    predict_customer_segment
)


result = predict_customer_segment(
    recency=20,
    frequency=1,
    monetary=210000
)

print(result)