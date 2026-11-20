
"use client";

import { useEffect, useState } from "react";
import PageLayout from "../../components/PageLayout";
import { apiRequest } from "../../components/api";

const chartColors = [
  "#7657e8",
  "#3198d4",
  "#20a779",
  "#f0a43c",
  "#e45d78",
];

function ProductPieChart({ products, number, money }) {
  const validProducts = products.filter(
    (item) => Number(item.total_sales) > 0
  );

  const total = validProducts.reduce(
    (sum, item) => sum + Number(item.total_sales || 0),
    0
  );

  if (validProducts.length === 0 || total <= 0) {
    return (
      <p className="notice">
        No product sales available.
      </p>
    );
  }

  let currentPercentage = 0;

  const gradientParts = validProducts.map((item, index) => {
    const percentage = (Number(item.total_sales) / total) * 100;
    const start = currentPercentage;
    currentPercentage += percentage;

    return `${chartColors[index % chartColors.length]} ${start}% ${currentPercentage}%`;
  });

  return (
    <div className="pie-chart-layout">
      <div
        className="product-pie-chart"
        style={{
          background: `conic-gradient(${gradientParts.join(", ")})`,
        }}
        role="img"
        aria-label="Pie chart showing product sales contribution"
      >
        <div className="pie-chart-hole">
          <strong>{money(total)}</strong>
          <span>Total sales</span>
        </div>
      </div>

      <div className="pie-chart-legend">
        {validProducts.map((item, index) => {
          const percentage =
            (Number(item.total_sales) / total) * 100;

          return (
            <div className="pie-legend-item" key={item.ProductID}>
              <span
                className="pie-legend-color"
                style={{
                  backgroundColor:
                    chartColors[index % chartColors.length],
                }}
              />

              <div className="pie-legend-details">
                <strong>{item.ProductName}</strong>
                <span>
                  {money(item.total_sales)} ({percentage.toFixed(1)}%)
                </span>
                <small>
                  {number(item.units_sold)} units sold
                </small>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");

        // Load overall dashboard data without a month filter.
        const result = await apiRequest("/dashboard/overview");

        setData(result);
      } catch (err) {
        setError(err.message || "Failed to load dashboard.");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const number = (value) =>
    new Intl.NumberFormat("en-LK", {
      maximumFractionDigits: 0,
    }).format(Number(value) || 0);

  const money = (value) => "LKR " + number(value);

  const monthlySales = data?.monthly_sales || [];
  const topProducts = data?.top_products || [];
  const lowProducts = data?.low_products || [];
  const recentTransactions = data?.recent_transactions || [];

  const maxSales = Math.max(
    1,
    ...monthlySales.map(
      (item) => Number(item.total_sales) || 0
    )
  );

  return (
    <PageLayout
      title="Dashboard"
      description="Retail Intelligence Platform — business overview"
    >
      {loading && (
        <p className="notice">Loading dashboard data...</p>
      )}

      {error && (
        <section className="panel">
          <p className="error-message">{error}</p>

          <button
            className="primary-button"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </section>
      )}

      {!loading && !error && data && (
        <>
          {/* OVERALL SUMMARY CARDS */}
          <section className="stats-grid">
            <article className="stat-card purple">
              <p>Total Sales</p>
              <h2>{money(data.total_sales)}</h2>
              <span>Overall sales</span>
            </article>

            <article className="stat-card blue">
              <p>Total Customers</p>
              <h2>{number(data.total_customers)}</h2>
              <span>Customers in database</span>
            </article>

            <article className="stat-card green">
              <p>Total Products</p>
              <h2>{number(data.total_products)}</h2>
              <span>Products in database</span>
            </article>

            <article className="stat-card orange">
              <p>Top-Selling Products</p>
              <h2>{number(topProducts.length)}</h2>
              <span>Top five overall</span>
            </article>
          </section>

          {/* MONTHLY SALES CHART */}
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Monthly Sales Analysis</h2>
                <p>
                  Sales performance across all months in the dataset
                </p>
              </div>
            </div>

            {monthlySales.length === 0 ? (
              <p className="notice">
                No monthly sales available.
              </p>
            ) : (
              <div className="monthly-sales-list">
                {monthlySales.map((item) => {
                  const sales =
                    Number(item.total_sales) || 0;

                  const width = (sales / maxSales) * 100;

                  return (
                    <div
                      key={item.month}
                      className="monthly-sales-item"
                    >
                      <div className="monthly-sales-label">
                        <strong>
                          {item.month_label || item.month}
                        </strong>

                        <span>{money(sales)}</span>
                      </div>

                      <div className="monthly-sales-track">
                        <div
                          className="monthly-sales-bar"
                          style={{
                            width: `${width}%`,
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          {/* TOP-SELLING PRODUCTS */}
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Top-Selling Products</h2>
                <p>
                  Sales contribution of the five highest-selling
                  products across all months
                </p>
              </div>
            </div>

            <ProductPieChart
              products={topProducts}
              number={number}
              money={money}
            />
          </section>

          {/* LOW-SELLING PRODUCTS */}
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Low-Selling Products</h2>
                <p>
                  Sales contribution of the five lowest-selling
                  products across all months
                </p>
              </div>
            </div>

            <ProductPieChart
              products={lowProducts}
              number={number}
              money={money}
            />
          </section>

          {/* RECENT TRANSACTIONS */}
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Recent Transactions</h2>
                <p>
                  Latest transactions across all months
                </p>
              </div>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Transaction ID</th>
                    <th>Customer ID</th>
                    <th>Product</th>
                    <th>Date</th>
                    <th>Quantity</th>
                    <th>Total Amount</th>
                  </tr>
                </thead>

                <tbody>
                  {recentTransactions.map((item, index) => (
                    <tr
                      key={
                        item.TransactionID ??
                        `${item.ProductID}-${index}`
                      }
                    >
                      <td>{item.TransactionID ?? "—"}</td>
                      <td>{item.CustomerID ?? "—"}</td>
                      <td>
                        {item.ProductName || item.ProductID || "—"}
                      </td>
                      <td>
                        {item.InvoiceDate
                          ? String(item.InvoiceDate).slice(0, 10)
                          : "—"}
                      </td>
                      <td>{number(item.Quantity)}</td>
                      <td>{money(item.TotalAmount)}</td>
                    </tr>
                  ))}

                  {recentTransactions.length === 0 && (
                    <tr>
                      <td colSpan={6}>
                        No recent transactions available.
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
