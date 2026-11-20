"use client";

import { useState } from "react";
import PageLayout from "../../components/PageLayout";
import { apiRequest } from "../../components/api";
import ProductIdSelect from "../../components/ProductIdSelect";

export default function PricingPage() {
  const [productId, setProductId] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function getPricing(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      if (!productId.trim()) {
        throw new Error("Please select a Product ID.");
      }

      const data = await apiRequest("/pricing/recommend", {
        method: "POST",
        body: JSON.stringify({
          product_id: productId.trim(),
        }),
      });

      setResult(data);

    } catch (err) {
      setError(err.message || "Unable to analyse pricing.");
    } finally {
      setLoading(false);
    }
  }

  const priceFields = [
    ["Product", "product_name"],
    ["Current price before discount", "current_price_before_discount"],
    ["Current price after discount", "current_price_after_discount"],
    ["Recommended price before discount", "recommended_price_before_discount"],
    ["Recommended price after discount", "recommended_price_after_discount"],
    ["Recommended discount per unit", "recommended_discount_per_unit"],
    ["Price elasticity", "price_elasticity"],
    ["Baseline predicted demand", "baseline_predicted_demand"],
    ["Predicted demand at recommended price", "predicted_demand"],
    ["Expected units sold", "expected_units_sold"],
    ["Expected revenue", "expected_revenue"],
    ["Available stock", "available_stock"],
    ["Stock status", "stock_status"],
    ["Prediction date", "prediction_date"],
    ["Store", "store_name"],
  ];

  return (
    <PageLayout
      title="Pricing Analysis"
      description="View elasticity-aware pricing, demand and revenue predictions from FastAPI."
    >
      <section className="panel">
        <h2>Get pricing recommendation</h2>

        <form className="form-grid" onSubmit={getPricing}>

          <ProductIdSelect
            value={productId}
            onChange={(value) => {
              setProductId(value);
              setResult(null);
              setError("");
            }}
          />

          <button
            className="primary-button"
            type="submit"
            disabled={loading || !productId}
          >
            {loading ? "Analysing..." : "Analyse pricing"}
          </button>

        </form>

        {error && (
          <p className="error-message">{error}</p>
        )}
      </section>

      {result && (
        <section className="panel">
          <h2>Backend pricing results</h2>

          <div className="details-grid">
            {priceFields.map(([label, key]) => (
              <article className="detail-item" key={key}>
                <p>{label}</p>
                <strong>
                  {result[key] == null
                    ? "Not returned"
                    : String(result[key])}
                </strong>
              </article>
            ))}
          </div>
        </section>
      )}
    </PageLayout>
  );
}