"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "./api";

export default function ProductNameSelect({ value, onChange }) {
  const [productNames, setProductNames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadProductNames() {
      try {
        const data = await apiRequest("/product-names");

        setProductNames(
          Array.isArray(data.product_names)
            ? data.product_names
            : []
        );
      } catch (err) {
        setError(err.message || "Unable to load product names.");
      } finally {
        setLoading(false);
      }
    }

    loadProductNames();
  }, []);

  return (
    <div className="field">
      <label htmlFor="productName">Product Name</label>

      <select
        id="productName"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={loading || productNames.length === 0}
        required
      >
        <option value="">
          {loading
            ? "Loading product names..."
            : productNames.length === 0
              ? "No products available"
              : "Select a Product Name"}
        </option>

        {productNames.map((name) => (
          <option key={name} value={name}>
            {name}
          </option>
        ))}
      </select>

      {loading && (
        <small>Loading products from MySQL...</small>
      )}

      {!loading && !error && (
        <small>
          {productNames.length} product names available
        </small>
      )}

      {error && (
        <p className="error-message">{error}</p>
      )}
    </div>
  );
}