
"use client";

import { useState } from "react";
import PageLayout from "../../components/PageLayout";
import { apiRequest } from "../../components/api";
import ProductNameSelect from "../../components/ProductNameSelect";

function getProductName(item) {
  return (
    item.related_product ??
    item.product_name ??
    item.ProductName ??
    "Unknown Product"
  );
}

function formatPercentage(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) return "—";

  return `${(number * 100).toFixed(2)}%`;
}

function formatLift(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) return "—";

  return number.toFixed(2);
}

// Pure SVG horizontal bar chart
function SVGMetricChart({
  title,
  description,
  data,
  metric,
  color,
  percentage = false,
  liftChart = false,
}) {
  const chartData = data
    .map((item) => ({
      name: getProductName(item),
      value: Number(item[metric]),
    }))
    .filter((item) => {
      if (!Number.isFinite(item.value) || item.value < 0) {
        return false;
      }

      if (percentage && item.value > 1) {
        return false;
      }

      return true;
    });

  if (chartData.length === 0) {
    return (
      <section className="panel">
        <h2>{title}</h2>
        <p className="notice">
          No valid {title.toLowerCase()} values are available.
        </p>
      </section>
    );
  }

  const chartWidth = 700;
  const leftSpace = 10;
  const rightSpace = 80;
  const plotWidth = chartWidth - leftSpace - rightSpace;

  const rowHeight = 75;
  const topSpace = 25;
  const chartHeight = topSpace + chartData.length * rowHeight + 20;

  const maximumValue = Math.max(
    ...chartData.map((item) => item.value),
    0
  );

  const scaleMaximum = liftChart
    ? Math.max(maximumValue * 1.15, 1.2)
    : percentage
      ? 1
      : maximumValue * 1.15 || 1;

  const referenceX = leftSpace + (1 / scaleMaximum) * plotWidth;

  return (
    <section className="panel svg-chart-panel">
      <h2>{title}</h2>

      <p className="page-description">{description}</p>

      <div className="svg-chart-container">
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          width="100%"
          height="auto"
          role="img"
          aria-label={title}
        >
          {/* Background grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((tick) => {
            const x = leftSpace + tick * plotWidth;

            return (
              <g key={tick}>
                <line
                  x1={x}
                  y1={10}
                  x2={x}
                  y2={chartHeight - 15}
                  stroke="currentColor"
                  strokeOpacity="0.13"
                  strokeDasharray="4 5"
                />

                <text
                  x={x}
                  y={chartHeight - 2}
                  fill="currentColor"
                  opacity="0.65"
                  fontSize="11"
                  textAnchor="middle"
                >
                  {percentage
                    ? `${Math.round(tick * 100)}%`
                    : (tick * scaleMaximum).toFixed(1)}
                </text>
              </g>
            );
          })}

          {/* Lift = 1 reference line */}
          {liftChart && scaleMaximum >= 1 && (
            <g>
              <line
                x1={referenceX}
                y1={5}
                x2={referenceX}
                y2={chartHeight - 15}
                stroke="#ef4444"
                strokeWidth="2"
                strokeDasharray="6 4"
              />

              <text
                x={Math.min(referenceX + 5, chartWidth - 90)}
                y={15}
                fill="#ef4444"
                fontSize="11"
                fontWeight="bold"
              >
                Lift = 1
              </text>
            </g>
          )}

          {/* Product bars */}
          {chartData.map((item, index) => {
            const y = topSpace + index * rowHeight;
            const barWidth = (item.value / scaleMaximum) * plotWidth;

            return (
              <g key={`${item.name}-${index}`}>
                {/* Product name */}
                <text
                  x={leftSpace}
                  y={y + 12}
                  fill="currentColor"
                  fontSize="13"
                  fontWeight="600"
                >
                  {item.name.length > 48
                    ? item.name.substring(0, 45) + "..."
                    : item.name}
                </text>

                {/* Bar background */}
                <rect
                  x={leftSpace}
                  y={y + 22}
                  width={plotWidth}
                  height={20}
                  rx={7}
                  fill="currentColor"
                  opacity="0.08"
                />

                {/* Actual value bar */}
                <rect
                  x={leftSpace}
                  y={y + 22}
                  width={Math.max(barWidth, item.value > 0 ? 2 : 0)}
                  height={20}
                  rx={7}
                  fill={color}
                >
                  <title>
                    {item.name}:{" "}
                    {percentage
                      ? formatPercentage(item.value)
                      : formatLift(item.value)}
                  </title>
                </rect>

                {/* Value label */}
                <text
                  x={Math.min(
                    leftSpace + barWidth + 9,
                    chartWidth - 65
                  )}
                  y={y + 37}
                  fill="currentColor"
                  fontSize="12"
                  fontWeight="bold"
                >
                  {percentage
                    ? formatPercentage(item.value)
                    : formatLift(item.value)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {liftChart && (
        <p className="chart-note">
          Lift above 1 indicates a positive association.
          Lift below 1 indicates a negative association.
        </p>
      )}
    </section>
  );
}

export default function MarketBasketPage() {
  const [productName, setProductName] = useState("");
  const [result, setResult] = useState(null);
  const [searchedProduct, setSearchedProduct] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSearch(event) {
    event.preventDefault();

    const name = productName.trim();

    if (!name) {
      setError("Please select a product name.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setSearchedProduct(name);

    try {
      const data = await apiRequest(
        `/market-basket/${encodeURIComponent(name)}?limit=5`,
        { method: "GET" }
      );

      setResult(data);
    } catch (err) {
      setError(
        err.message || "Unable to retrieve related products."
      );
    } finally {
      setLoading(false);
    }
  }

  const recommendations = Array.isArray(result?.related_products)
    ? result.related_products
    : [];

  const validMetricValues = (metric) =>
    recommendations
      .map((item) => Number(item[metric]))
      .filter((value) => Number.isFinite(value));

  const supports = validMetricValues("support");
  const confidences = validMetricValues("confidence");
  const lifts = validMetricValues("lift");

  const highestSupport =
    supports.length > 0 ? Math.max(...supports) : null;

  const highestConfidence =
    confidences.length > 0 ? Math.max(...confidences) : null;

  const highestLift =
    lifts.length > 0 ? Math.max(...lifts) : null;

  return (
    <PageLayout
      title="Market Basket Analysis"
      description="Discover products frequently purchased together using Apriori association rules and co-purchase analysis."
    >
      {/* Search */}
      <section className="panel">
        <h2>Find Related Products</h2>

        <p className="page-description">
          Select a product name to discover products purchased together.
        </p>

        <form className="form-grid" onSubmit={handleSearch}>
          <ProductNameSelect
            value={productName}
            onChange={(value) => {
              setProductName(value);
              setResult(null);
              setError("");
              setSearchedProduct("");
            }}
          />

          <button
            type="submit"
            className="primary-button"
            disabled={loading || !productName}
          >
            {loading ? "Searching..." : "Find Related Products"}
          </button>
        </form>

        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}
      </section>

      {result && (
        <>
          {/* Overview */}
          <section className="panel">
            <h2>Analysis Overview</h2>

            <p className="page-description">
              Results for: {result.product_name ?? searchedProduct}
            </p>

            <div className="stats-grid">
              <div className="stat-card purple">
                <span>Total Related Products</span>
                <h3>{recommendations.length}</h3>
              </div>

              <div className="stat-card blue">
                <span>Highest Support</span>
                <h3>
                  {highestSupport !== null
                    ? formatPercentage(highestSupport)
                    : "—"}
                </h3>
              </div>

              <div className="stat-card green">
                <span>Highest Confidence</span>
                <h3>
                  {highestConfidence !== null
                    ? formatPercentage(highestConfidence)
                    : "—"}
                </h3>
              </div>

              <div className="stat-card orange">
                <span>Highest Lift</span>
                <h3>
                  {highestLift !== null
                    ? formatLift(highestLift)
                    : "—"}
                </h3>
              </div>
            </div>
          </section>

          {recommendations.length === 0 ? (
            <section className="panel">
              <p className="notice">
                No related products were found. Try selecting another product.
              </p>
            </section>
          ) : (
            <>
              {/* Graph 1: Support */}
              <SVGMetricChart
                title="Support Analysis"
                description="Percentage of all transactions containing both products."
                data={recommendations}
                metric="support"
                color="#8b5cf6"
                percentage
              />

              {/* Graph 2: Confidence */}
              <SVGMetricChart
                title="Confidence Analysis"
                description="Probability of purchasing the related product when the selected product is purchased."
                data={recommendations}
                metric="confidence"
                color="#10b981"
                percentage
              />

              {/* Graph 3: Lift */}
              <SVGMetricChart
                title="Lift Analysis"
                description="Measures the strength of the association between two products."
                data={recommendations}
                metric="lift"
                color="#f59e0b"
                liftChart
              />

              {/* Details Table */}
              <section className="panel">
                <h2>Related Products Details</h2>

                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Related Product</th>
                        <th>Method</th>
                        <th>Support</th>
                        <th>Confidence</th>
                        <th>Lift</th>
                        <th>Co-purchases</th>
                      </tr>
                    </thead>

                    <tbody>
                      {recommendations.map((item, index) => (
                        <tr key={`${getProductName(item)}-${index}`}>
                          <td>{getProductName(item)}</td>
                          <td>{item.method ?? "—"}</td>
                          <td>{formatPercentage(item.support)}</td>
                          <td>{formatPercentage(item.confidence)}</td>
                          <td>{formatLift(item.lift)}</td>
                          <td>{item.co_purchase_count ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* Explanation */}
              <section className="panel">
                <h2>Understanding the Metrics</h2>

                <div className="metric-explanation">
                  <div>
                    <h3>Support</h3>
                    <p>
                      Shows how frequently two products appear together
                      across all transactions.
                    </p>
                  </div>

                  <div>
                    <h3>Confidence</h3>
                    <p>
                      Shows the likelihood of purchasing a related
                      product when the selected product is purchased.
                    </p>
                  </div>

                  <div>
                    <h3>Lift</h3>
                    <p>
                      Lift greater than 1 indicates a positive
                      association. Lift equal to 1 indicates
                      independence, while lift below 1 indicates
                      a negative association.
                    </p>
                  </div>
                </div>
              </section>
            </>
          )}
        </>
      )}

      <style jsx>{`
        .svg-chart-panel {
          overflow: hidden;
        }

        .svg-chart-container {
          width: 100%;
          margin-top: 20px;
          overflow-x: auto;
        }

        .svg-chart-container svg {
          display: block;
          width: 100%;
          min-width: 300px;
          height: auto;
          overflow: visible;
        }

        .chart-note {
          margin-top: 15px;
          font-size: 13px;
          color: var(--muted-foreground, #888);
        }

        .metric-explanation {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 18px;
          margin-top: 20px;
        }

        .metric-explanation > div {
          padding: 18px;
          border: 1px solid var(--border, rgba(128, 128, 128, 0.2));
          border-radius: 12px;
        }

        .metric-explanation h3 {
          margin: 0 0 10px;
          font-size: 16px;
        }

        .metric-explanation p {
          margin: 0;
          line-height: 1.6;
          font-size: 13px;
          color: var(--muted-foreground, #888);
        }

        @media (max-width: 700px) {
          .metric-explanation {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </PageLayout>
  );
}
