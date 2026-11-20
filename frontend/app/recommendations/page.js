
"use client";

import { useEffect, useState } from "react";
import PageLayout from "../../components/PageLayout";
import { apiRequest } from "../../components/api";

function formatMoney(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return "—";
  }

  return `LKR ${amount.toLocaleString("en-LK", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function getPromotionalOffer(segment) {
  const name = String(segment || "").toLowerCase();

  if (name.includes("inactive")) {
    return {
      title: "Re-engagement offer",
      discount: "10%",
      reason: "Encourage an inactive customer to return.",
    };
  }

  if (name.includes("at-risk")) {
    return {
      title: "Return-purchase offer",
      discount: "10%",
      reason: "Encourage an at-risk customer to purchase again.",
    };
  }

  if (name.includes("potential")) {
    return {
      title: "Next-purchase offer",
      discount: "5%",
      reason: "Encourage another purchase.",
    };
  }

  if (name.includes("loyal")) {
    return {
      title: "Loyalty reward",
      discount: "5%",
      reason: "Reward continued customer loyalty.",
    };
  }

  return {
    title: "No predefined offer",
    discount: "Not assigned",
    reason: "This customer segment has no promotional rule configured.",
  };
}

export default function RecommendationsPage() {
  const [customerIds, setCustomerIds] = useState([]);
  const [customerId, setCustomerId] = useState("");

  const [loadingCustomers, setLoadingCustomers] = useState(true);
  const [recommendationData, setRecommendationData] = useState(null);
  const [segmentData, setSegmentData] = useState(null);
  const [historyData, setHistoryData] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load all Customer IDs from MySQL.
  useEffect(() => {
    async function loadCustomerIds() {
      try {
        const data = await apiRequest("/customer-ids");

        setCustomerIds(
          Array.isArray(data.customer_ids)
            ? data.customer_ids
            : []
        );
      } catch (err) {
        setError(err.message || "Unable to load Customer IDs.");
      } finally {
        setLoadingCustomers(false);
      }
    }

    loadCustomerIds();
  }, []);

  // Get recommendations and customer details.
  async function getCustomerDetails(event) {
    event.preventDefault();

    const id = customerId.trim();

    if (!id) {
      setError("Please select a Customer ID.");
      return;
    }

    setLoading(true);
    setError("");
    setRecommendationData(null);
    setSegmentData(null);
    setHistoryData(null);

    try {
      const [recommendations, segment, history] = await Promise.all([
        apiRequest(
          `/recommendations/${encodeURIComponent(id)}`
        ),
        apiRequest(
          `/customer-segment/${encodeURIComponent(id)}`
        ),
        apiRequest(
          `/customer-history/${encodeURIComponent(id)}`
        ),
      ]);

      setRecommendationData(recommendations);
      setSegmentData(segment);
      setHistoryData(history);
    } catch (err) {
      setError(
        err.message ||
          "Could not load the customer details. Please check the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  const recommendations = Array.isArray(
    recommendationData?.recommendations
  )
    ? recommendationData.recommendations
    : [];

  const history = Array.isArray(historyData?.purchase_history)
    ? historyData.purchase_history
    : [];

  const offer = segmentData
    ? getPromotionalOffer(segmentData.segment)
    : null;

  return (
    <PageLayout
      title="Personalized Recommendations"
      description="View customer clustering, purchase history, recommended products, and suggested promotional offers."
    >
      <section className="panel">
        <h2>Find a customer</h2>

        <form
          className="form-grid"
          onSubmit={getCustomerDetails}
        >
          <div className="field">
            <label htmlFor="customerId">Customer ID</label>

            <select
              id="customerId"
              value={customerId}
              onChange={(event) => {
                setCustomerId(event.target.value);
                setRecommendationData(null);
                setSegmentData(null);
                setHistoryData(null);
                setError("");
              }}
              disabled={loadingCustomers || customerIds.length === 0}
              required
            >
              <option value="">
                {loadingCustomers
                  ? "Loading Customer IDs..."
                  : customerIds.length === 0
                    ? "No Customer IDs available"
                    : "Select a Customer ID"}
              </option>

              {customerIds.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>

            <small>
              {loadingCustomers
                ? "Loading customers from MySQL..."
                : `${customerIds.length} Customer IDs available`}
            </small>
          </div>

          <button
            className="primary-button"
            type="submit"
            disabled={loading || loadingCustomers || !customerId}
          >
            {loading ? "Loading customer data..." : "View customer"}
          </button>
        </form>

        {error && (
          <p className="error-message">{error}</p>
        )}
      </section>

      {segmentData && (
        <>
          <section className="stats-grid">
            <article className="stat-card purple">
              <p>Customer ID</p>
              <h2>{segmentData.customer_id}</h2>
              <span>Customer selected</span>
            </article>

            <article className="stat-card blue">
              <p>Customer cluster</p>
              <h2>
                {segmentData.cluster ?? "Not returned"}
              </h2>
              <span>Cluster predicted by your model</span>
            </article>

            <article className="stat-card green">
              <p>Customer segment</p>
              <h2>{segmentData.segment ?? "Not returned"}</h2>
              <span>Segment predicted by your model</span>
            </article>

            <article className="stat-card orange">
              <p>Purchase frequency</p>
              <h2>
                {segmentData.rfm?.frequency ?? "Not returned"}
              </h2>
              <span>Distinct invoices in the RFM calculation</span>
            </article>
          </section>

          <section className="panel">
            <h2>Customer RFM analysis</h2>

            <div className="details-grid">
              <div className="detail-item">
                <span>Recency</span>
                <strong>
                  {segmentData.rfm?.recency ?? "Not returned"}
                </strong>
                <small>Days since the last recorded purchase</small>
              </div>

              <div className="detail-item">
                <span>Frequency</span>
                <strong>
                  {segmentData.rfm?.frequency ?? "Not returned"}
                </strong>
                <small>Number of distinct invoices</small>
              </div>

              <div className="detail-item">
                <span>Monetary value</span>
                <strong>
                  {formatMoney(segmentData.rfm?.monetary)}
                </strong>
                <small>Total transaction amount used for RFM</small>
              </div>
            </div>
          </section>
        </>
      )}

      {offer && segmentData && (
        <section className="panel offer-panel">
          <p className="eyebrow">PERSONALIZED MARKETING</p>
          <h2>{offer.title}</h2>

          <div className="offer-discount">
            {offer.discount}
          </div>

          <p>{offer.reason}</p>

          <p className="footnote">
            This is a proposed offer based on the customer's
            predicted segment. It has not been issued to the
            customer or saved as an active promotion.
          </p>
        </section>
      )}

      {recommendationData && (
        <section className="panel">
          <h2>Recommended products</h2>
          <p className="page-description">
            Products returned by your personalized recommendation model.
          </p>

          {recommendations.length === 0 ? (
            <p className="notice">
              The model did not return any recommendations for this customer.
              Check that the customer exists in the model's input dataset.
            </p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Product ID</th>
                    <th>Product name</th>
                    <th>Category</th>
                    <th>Subcategory</th>
                    <th>Recommendation score</th>
                  </tr>
                </thead>

                <tbody>
                  {recommendations.map((item, index) => (
                    <tr key={`${item.ProductID}-${index}`}>
                      <td>{item.ProductID ?? "—"}</td>
                      <td>{item.ProductName ?? "Name unavailable"}</td>
                      <td>{item.Category ?? "—"}</td>
                      <td>{item.SubCategory ?? "—"}</td>
                      <td>{item.Score ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {historyData && (
        <section className="panel">
          <h2>Previous purchase history</h2>
          <p className="page-description">
            Actual transaction records returned by your database.
          </p>

          {history.length === 0 ? (
            <p className="notice">
              No purchase history was returned for this customer.
            </p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Invoice</th>
                    <th>Date</th>
                    <th>Product name</th>
                    <th>Quantity</th>
                    <th>Unit price</th>
                    <th>Discount</th>
                    <th>Total amount</th>
                  </tr>
                </thead>

                <tbody>
                  {history.map((item, index) => (
                    <tr
                      key={`${item.InvoiceID ?? "invoice"}-${item.ProductID ?? "product"}-${index}`}
                    >
                      <td>{item.InvoiceID ?? "—"}</td>
                      <td>
                        {item.InvoiceDate
                          ? String(item.InvoiceDate).replace("T", " ")
                          : "—"}
                      </td>
                      <td>{item.ProductName ?? "Name unavailable"}</td>
                      <td>{item.Quantity ?? "—"}</td>
                      <td>{formatMoney(item.UnitPrice)}</td>
                      <td>{formatMoney(item.Discount)}</td>
                      <td>{formatMoney(item.TotalAmount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <p className="footnote">
            The history endpoint returns at most 100 records, ordered by
            purchase date, newest first.
          </p>
        </section>
      )}
    </PageLayout>
  );
}
