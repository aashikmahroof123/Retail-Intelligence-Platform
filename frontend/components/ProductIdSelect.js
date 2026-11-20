"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "./api";

export default function ProductIdSelect({ value, onChange }) {
  const [productIds, setProductIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadProductIds() {
      try {
        const data = await apiRequest("/product-ids");

        setProductIds(
          Array.isArray(data.product_ids)
            ? data.product_ids
            : []
        );
      } catch (err) {
        setError(err.message || "Unable to load Product IDs.");
      } finally {
        setLoading(false);
      }
    }

    loadProductIds();
  }, []);

  return (
    <div className="field">
      <label htmlFor="productId">Product ID</label>

      <select
        id="productId"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={loading || productIds.length === 0}
        required
      >
        <option value="">
          {loading
            ? "Loading Product IDs..."
            : productIds.length === 0
              ? "No Product IDs available"
              : "Select a Product ID"}
        </option>

        {productIds.map((id) => (
          <option key={id} value={id}>
            {id}
          </option>
        ))}
      </select>

      {loading && (
        <small>Loading products from MySQL...</small>
      )}

      {!loading && !error && (
        <small>{productIds.length} Product IDs available</small>
      )}

      {error && (
        <p className="error-message">{error}</p>
      )}
    </div>
  );
}