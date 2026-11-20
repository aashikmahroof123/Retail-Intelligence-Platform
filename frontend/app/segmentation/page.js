"use client";

import { useEffect, useState } from "react";
import PageLayout from "../../components/PageLayout";
import { apiRequest } from "../../components/api";

export default function SegmentationPage() {
  const [customerIds, setCustomerIds] = useState([]);
  const [customerId, setCustomerId] = useState("");

  const [loadingCustomers, setLoadingCustomers] = useState(true);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load all Customer IDs when the page opens.
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
        setError(
          err.message || "Unable to load Customer IDs."
        );
      } finally {
        setLoadingCustomers(false);
      }
    }

    loadCustomerIds();
  }, []);

  // Analyse the selected customer.
  async function analyseCustomer(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const id = customerId.trim();

      if (!id) {
        throw new Error("Please select a Customer ID.");
      }

      const data = await apiRequest(
        `/customer-segment/${encodeURIComponent(id)}`
      );

      setResult(data);
    } catch (err) {
      setError(
        err.message || "Unable to analyse this customer."
      );
    } finally {
      setLoading(false);
    }
  }

  const rfm = result?.rfm ?? result ?? {};

  const recency = Number(rfm.recency ?? rfm.Recency ?? 0);
  const frequency = Number(rfm.frequency ?? rfm.Frequency ?? 0);
  const monetary = Number(rfm.monetary ?? rfm.Monetary ?? 0);

  const rfmValues = [
    { label: "Recency", value: recency, unit: "days" },
    { label: "Frequency", value: frequency, unit: "orders" },
    { label: "Monetary", value: monetary, unit: "LKR" },
  ];

  const largestLog = Math.max(
    1,
    ...rfmValues.map((item) =>
      Math.log10(Math.max(0, item.value) + 1)
    )
  );

  const cluster = result?.cluster ?? result?.Cluster;

  const segment =
    result?.segment ??
    result?.Segment ??
    result?.cluster_name ??
    "Not returned";

  return (
    <PageLayout
      title="Customer Segmentation"
      description="Select a Customer ID to view RFM values and the predicted customer group."
    >
      <section className="panel">
        <h2>Analyse a customer</h2>

        <form className="form-grid" onSubmit={analyseCustomer}>
          <div className="field">
            <label htmlFor="customerId">Customer ID</label>

            <select
              id="customerId"
              value={customerId}
              onChange={(event) => {
                setCustomerId(event.target.value);
                setResult(null);
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
                ? "Loading customers from the database..."
                : `${customerIds.length} Customer IDs available`}
            </small>
          </div>

          <button
            className="primary-button"
            disabled={loading || loadingCustomers || !customerId}
          >
            {loading ? "Analysing..." : "Analyse customer"}
          </button>
        </form>

        {error && <p className="error-message">{error}</p>}
      </section>

      {result && (
        <>
          <section className="stats-grid">
            <article className="stat-card purple">
              <p>Customer ID</p>
              <h2 className="small-value">
                {result.customer_id ?? result.CustomerID ?? customerId}
              </h2>
            </article>

            <article className="stat-card blue">
              <p>Cluster</p>
              <h2 className="small-value">
                {cluster ?? "Not returned"}
              </h2>
            </article>

            <article className="stat-card green">
              <p>Customer Group</p>
              <h2 className="small-value">{segment}</h2>
            </article>
          </section>

          <section className="panel">
            <h2>Customer RFM values</h2>

            <div className="stats-grid">
              {rfmValues.map((item) => (
                <article className="stat-card" key={item.label}>
                  <p>{item.label}</p>
                  <h2 className="small-value">
                    {item.value.toLocaleString()}
                  </h2>
                  <small>{item.unit}</small>
                </article>
              ))}
            </div>
          </section>

          
<section className="panel">
  <h2>RFM Bar Chart</h2>
  <p>
    Comparison of Recency, Frequency, and Monetary values
    for the selected customer.
  </p>

  <div
    style={{
      display: "flex",
      alignItems: "flex-end",
      justifyContent: "space-around",
      gap: "24px",
      height: "280px",
      padding: "24px 12px 12px",
      borderBottom: "1px solid var(--border-color, #e5e7eb)",
    }}
  >
    {rfmValues.map((item, index) => {
      const maxValue = Math.max(
        1,
        ...rfmValues.map((value) => Math.max(0, value.value))
      );

      const height = Math.max(
        item.value > 0 ? 3 : 0,
        (Math.max(0, item.value) / maxValue) * 200
      );

      const barColors = ["#805ad5", "#3182ce", "#16a34a"];

      return (
        <div
          key={item.label}
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "flex-end",
            height: "100%",
            minWidth: 0,
          }}
        >
          <strong style={{ marginBottom: "8px", textAlign: "center" }}>
            {item.value.toLocaleString()}
          </strong>

          <div
            style={{
              width: "min(65px, 75%)",
              height: `${height}px`,
              background: barColors[index],
              borderRadius: "8px 8px 0 0",
              transition: "height 0.4s ease",
            }}
          />

          <strong style={{ marginTop: "10px" }}>
            {item.label}
          </strong>

          <small>{item.unit}</small>
        </div>
      );
    })}
  </div>

  <p style={{ marginTop: "12px", fontSize: "13px" }}>
  </p>
</section>
        </>
      )}
    </PageLayout>
  );
}