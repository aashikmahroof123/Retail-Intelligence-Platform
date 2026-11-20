
"use client";

import { useEffect, useMemo, useState } from "react";
import PageLayout from "../../components/PageLayout";
import { apiRequest } from "../../components/api";

export default function OverallInventoryPage() {
  const [products, setProducts] = useState([]);
  const [summary, setSummary] = useState({
    total_products: 0,
    total_stock: 0,
    low_stock: 0,
    out_of_stock: 0,
  });

  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadInventory() {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/inventory/overview");

      if (!Array.isArray(data.products)) {
        throw new Error("Invalid inventory data returned by the server.");
      }

      setProducts(data.products);
      setSummary({
        total_products: Number(data.summary?.total_products ?? 0),
        total_stock: Number(data.summary?.total_stock ?? 0),
        low_stock: Number(data.summary?.low_stock ?? 0),
        out_of_stock: Number(data.summary?.out_of_stock ?? 0),
      });
    } catch (err) {
      setError(err.message || "Unable to load overall inventory.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadInventory();
  }, []);

  const categories = useMemo(() => {
    return [
      "All",
      ...new Set(
        products
          .map((item) => item.category)
          .filter(Boolean)
      ),
    ];
  }, [products]);

  const filteredProducts = useMemo(() => {
    return products.filter((item) => {
      const searchText = search.trim().toLowerCase();

      const matchesSearch =
        !searchText ||
        String(item.product_name ?? "").toLowerCase().includes(searchText) ||
        String(item.product_id ?? "").toLowerCase().includes(searchText);

      const matchesCategory =
        categoryFilter === "All" ||
        item.category === categoryFilter;

      const matchesStatus =
        statusFilter === "All" ||
        item.status === statusFilter;

      return matchesSearch && matchesCategory && matchesStatus;
    });
  }, [products, search, categoryFilter, statusFilter]);

  function statusColor(status) {
    if (status === "Out of Stock") return "#dc2626";
    if (status === "Low Stock") return "#d97706";
    return "#059669";
  }

  function recommendationText(item) {
    if (item.status === "Out of Stock") {
      return "Reorder immediately";
    }

    if (item.status === "Low Stock") {
      return "Plan a reorder soon";
    }

    return "Stock level is healthy";
  }

  const cardStyle = {
    padding: "22px",
    borderRadius: "14px",
    background: "var(--card-bg, white)",
    border: "1px solid rgba(128,128,128,0.18)",
    boxShadow: "0 4px 14px rgba(0,0,0,0.04)",
  };

  const inputStyle = {
    width: "100%",
    padding: "11px 13px",
    borderRadius: "8px",
    border: "1px solid rgba(128,128,128,0.35)",
    background: "var(--card-bg, white)",
    color: "var(--foreground, #111827)",
    fontSize: "14px",
  };

  return (
    <PageLayout
      title="Overall Inventory Management"
      description="Monitor total stock, identify low-stock products and view product-wise reorder recommendations."
    >
      <section
        style={{
          display: "flex",
          justifyContent: "flex-end",
          marginBottom: "18px",
        }}
      >
        <button
          type="button"
          onClick={loadInventory}
          disabled={loading}
          className="primary-button"
        >
          {loading ? "Refreshing..." : "Refresh Inventory"}
        </button>
      </section>

      {error && (
        <section className="panel">
          <p className="error-message">{error}</p>
        </section>
      )}

      {loading && products.length === 0 && !error && (
        <section className="panel">
          <p>Loading overall inventory...</p>
        </section>
      )}

      {!loading && !error && (
        <>
          {/* SUMMARY CARDS */}
          <section
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
              gap: "16px",
              marginBottom: "22px",
            }}
          >
            <article style={cardStyle}>
              <p style={{ color: "#8b5cf6", fontWeight: 600 }}>
                Total Products
              </p>
              <h2 style={{ fontSize: "30px", margin: "8px 0" }}>
                {summary.total_products}
              </h2>
              <span style={{ color: "#777", fontSize: "13px" }}>
                Products in the system
              </span>
            </article>

            <article style={cardStyle}>
              <p style={{ color: "#2563eb", fontWeight: 600 }}>
                Total Stock
              </p>
              <h2 style={{ fontSize: "30px", margin: "8px 0" }}>
                {summary.total_stock.toLocaleString()}
              </h2>
              <span style={{ color: "#777", fontSize: "13px" }}>
                Available units across products
              </span>
            </article>

            <article style={cardStyle}>
              <p style={{ color: "#d97706", fontWeight: 600 }}>
                Low Stock
              </p>
              <h2 style={{ fontSize: "30px", margin: "8px 0" }}>
                {summary.low_stock}
              </h2>
              <span style={{ color: "#777", fontSize: "13px" }}>
                Products with 1–10 units
              </span>
            </article>

            <article style={cardStyle}>
              <p style={{ color: "#dc2626", fontWeight: 600 }}>
                Out of Stock
              </p>
              <h2 style={{ fontSize: "30px", margin: "8px 0" }}>
                {summary.out_of_stock}
              </h2>
              <span style={{ color: "#777", fontSize: "13px" }}>
                Products with zero units
              </span>
            </article>
          </section>

          {/* REORDER RECOMMENDATIONS */}
          <section className="panel">
            <h2>Reorder Recommendations</h2>
            <p>
              Review products that need replenishment based on their
              recorded stock levels.
            </p>

            {products.filter(
              (item) =>
                item.status === "Low Stock" ||
                item.status === "Out of Stock"
            ).length === 0 ? (
              <p>No low-stock or out-of-stock products were returned.</p>
            ) : (
              <div style={{ display: "grid", gap: "10px" }}>
                {products
                  .filter(
                    (item) =>
                      item.status === "Low Stock" ||
                      item.status === "Out of Stock"
                  )
                  .map((item) => (
                    <div
                      key={item.product_id}
                      style={{
                        padding: "14px",
                        borderRadius: "9px",
                        border: "1px solid rgba(128,128,128,0.2)",
                        display: "flex",
                        flexWrap: "wrap",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "10px",
                      }}
                    >
                      <div>
                        <strong>{item.product_name}</strong>
                        <div style={{ fontSize: "12px", color: "#777" }}>
                          Product ID: {item.product_id}
                        </div>
                      </div>

                      <div>
                        <strong>
                          {Number(item.available_stock).toLocaleString()} units
                        </strong>
                      </div>

                      <span
                        style={{
                          color: statusColor(item.status),
                          fontWeight: 700,
                        }}
                      >
                        {recommendationText(item)}
                      </span>
                    </div>
                  ))}
              </div>
            )}
          </section>

          {/* SEARCH AND FILTERS */}
          <section className="panel">
            <h2>Product-wise Inventory</h2>
            <p>Search and filter products to check their stock status.</p>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
                gap: "12px",
                margin: "18px 0",
              }}
            >
              <input
                style={inputStyle}
                type="text"
                placeholder="Search product name or ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />

              <select
                style={inputStyle}
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category === "All" ? "All Categories" : category}
                  </option>
                ))}
              </select>

              <select
                style={inputStyle}
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="All">All Stock Statuses</option>
                <option value="Healthy">Healthy</option>
                <option value="Low Stock">Low Stock</option>
                <option value="Out of Stock">Out of Stock</option>
              </select>
            </div>

            <div style={{ marginBottom: "12px", color: "#777", fontSize: "13px" }}>
              Showing {filteredProducts.length} of {products.length} products
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Product ID</th>
                    <th>Product Name</th>
                    <th>Category</th>
                    <th>Available Stock</th>
                    <th>Stock Status</th>
                    <th>Recommendation</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredProducts.map((item) => (
                    <tr key={item.product_id}>
                      <td>{item.product_id}</td>
                      <td>{item.product_name || "Unnamed Product"}</td>
                      <td>{item.category || "Uncategorised"}</td>
                      <td>
                        {Number(item.available_stock).toLocaleString()} units
                      </td>
                      <td>
                        <span
                          style={{
                            display: "inline-block",
                            padding: "5px 10px",
                            borderRadius: "20px",
                            background: `${statusColor(item.status)}18`,
                            color: statusColor(item.status),
                            fontWeight: 700,
                            fontSize: "12px",
                          }}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td>{recommendationText(item)}</td>
                    </tr>
                  ))}

                  {filteredProducts.length === 0 && (
                    <tr>
                      <td colSpan="6" style={{ textAlign: "center", padding: "25px" }}>
                        No matching products found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </PageLayout>
  );
}
