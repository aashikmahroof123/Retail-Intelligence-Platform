
"use client";

import { useState } from "react";
import PageLayout from "../../components/PageLayout";
import { apiRequest } from "../../components/api";
import ProductIdSelect from "../../components/ProductIdSelect";

export default function InventoryPage() {
  const [productId, setProductId] = useState("");
  const [result, setResult] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [forecastWarning, setForecastWarning] = useState("");

  async function checkInventory(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setForecastWarning("");
    setResult(null);
    setForecast([]);

    try {
      if (!productId.trim()) {
        throw new Error("Please select a Product ID.");
      }

      const selectedProductId = productId.trim();

      // 1. Get actual available stock
      const inventoryData = await apiRequest("/pricing/recommend", {
        method: "POST",
        body: JSON.stringify({
          product_id: selectedProductId,
        }),
      });

      setResult(inventoryData);

      // 2. Get next 30 days LightGBM demand forecast
      try {
        const forecastData = await apiRequest(
          `/forecast/lightgbm/${encodeURIComponent(
            selectedProductId
          )}?days=30`
        );

        const forecastRows = Array.isArray(forecastData.forecasts)
          ? forecastData.forecasts
          : [];

        if (forecastRows.length === 0) {
          throw new Error(
            "LightGBM did not return any forecast records."
          );
        }

        setForecast(forecastRows);
      } catch (forecastError) {
        setForecastWarning(
          forecastError.message ||
            "Unable to generate the LightGBM forecast."
        );
      }
    } catch (err) {
      setError(err.message || "Unable to check inventory.");
    } finally {
      setLoading(false);
    }
  }

  // 3. Get actual available stock

  const availableStock = Number(result?.available_stock);

  // 4. Filter valid forecast records

  const validForecasts = forecast.filter((item) => {
    const demand = Number(item.PredictedDemand);

    return (
      Number.isFinite(demand) &&
      demand >= 0
    );
  });

  // 5. Calculate total predicted demand

  const monthlyDemand = validForecasts.reduce(
    (total, item) => total + Number(item.PredictedDemand),
    0
  );

  // 6. Calculate average daily demand

  const averageDailyDemand =
    validForecasts.length > 0
      ? monthlyDemand / validForecasts.length
      : 0;

  // 7. Calculate estimated stock remaining days

  const estimatedStockDays =
    Number.isFinite(availableStock) &&
    availableStock > 0 &&
    averageDailyDemand > 0
      ? availableStock / averageDailyDemand
      : Number.isFinite(availableStock) && availableStock <= 0
      ? 0
      : null;

  // 8. Calculate expected stock-out date

  const stockOutDate =
    estimatedStockDays !== null
      ? (() => {
          const date = new Date();

          date.setHours(0, 0, 0, 0);

          date.setDate(
            date.getDate() + Math.ceil(estimatedStockDays)
          );

          const day = String(date.getDate()).padStart(2, "0");
          const month = String(date.getMonth() + 1).padStart(2, "0");
          const year = date.getFullYear();

          return `${day}/${month}/${year}`;
        })()
      : null;

  // 9. Determine inventory status

  const stockStatus =
    Number.isFinite(availableStock) && availableStock <= 0
      ? "Out of Stock"
      : estimatedStockDays === null
      ? "Unable to Calculate"
      : estimatedStockDays <= 3
      ? "Critical"
      : estimatedStockDays <= 7
      ? "Low Stock"
      : "Healthy";

  // ==========================================
  // CHART 1: 30-DAY DAILY DEMAND LINE CHART
  // ==========================================

  const chartWidth = 760;
  const chartHeight = 260;

  const chartLeft = 45;
  const chartRight = 20;
  const chartTop = 20;
  const chartBottom = 40;

  const plotWidth = chartWidth - chartLeft - chartRight;
  const plotHeight = chartHeight - chartTop - chartBottom;

  const dailyDemands = validForecasts.map((item) =>
    Number(item.PredictedDemand)
  );

  const maxDailyDemand = Math.max(1, ...dailyDemands);

  const linePoints = dailyDemands.map((demand, index) => {
    const x =
      chartLeft +
      (index / Math.max(dailyDemands.length - 1, 1)) * plotWidth;

    const y =
      chartTop +
      plotHeight -
      (demand / maxDailyDemand) * plotHeight;

    return { x, y, demand };
  });

  const linePath = linePoints
    .map((point, index) =>
      `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`
    )
    .join(" ");

  const areaPath =
    linePoints.length > 0
      ? `${linePath} L ${
          linePoints[linePoints.length - 1].x
        } ${chartTop + plotHeight} L ${
          linePoints[0].x
        } ${chartTop + plotHeight} Z`
      : "";

  // ==========================================
  // CHART 2: INVENTORY DOUGHNUT CHART
  // ==========================================

  const projectedRemainingStock =
    Number.isFinite(availableStock)
      ? Math.max(0, availableStock - monthlyDemand)
      : 0;

  const doughnutTotal =
    monthlyDemand + projectedRemainingStock;

  const demandPercentage =
    doughnutTotal > 0
      ? (monthlyDemand / doughnutTotal) * 100
      : 0;

  const remainingPercentage =
    doughnutTotal > 0
      ? (projectedRemainingStock / doughnutTotal) * 100
      : 0;

  const doughnutGradient =
    `conic-gradient(
      #8b5cf6 0% ${demandPercentage}%,
      #10b981 ${demandPercentage}% 100%
    )`;

  // ==========================================
  // CHART 3: WEEKLY PREDICTED DEMAND BAR CHART
  // ==========================================

  const weeklyDemand = Array.from(
    { length: Math.ceil(validForecasts.length / 7) },
    (_, weekIndex) => {
      const start = weekIndex * 7;
      const weekItems = validForecasts.slice(start, start + 7);

      const total = weekItems.reduce(
        (sum, item) => sum + Number(item.PredictedDemand),
        0
      );

      return {
        label: `Week ${weekIndex + 1}`,
        total,
        days: weekItems.length,
      };
    }
  );

  const maxWeeklyDemand = Math.max(
    1,
    ...weeklyDemand.map((week) => week.total)
  );

  const barColors = [
    "#8b5cf6",
    "#3b82f6",
    "#06b6d4",
    "#10b981",
    "#f59e0b",
  ];

  return (
    <PageLayout
      title="Inventory Analysis"
      description="Analyse current inventory levels, predict 30-day demand and estimate how many days stock will last using LightGBM forecasting."
    >
      {/* PRODUCT SELECTION */}

      <section className="panel">
        <h2>Check Product Inventory</h2>

        <form className="form-grid" onSubmit={checkInventory}>
          <ProductIdSelect
            value={productId}
            onChange={(value) => {
              setProductId(value);
              setResult(null);
              setForecast([]);
              setError("");
              setForecastWarning("");
            }}
          />

          <button
            className="primary-button"
            type="submit"
            disabled={loading || !productId}
          >
            {loading ? "Analysing..." : "Analyse Inventory"}
          </button>
        </form>

        {error && (
          <p className="error-message">{error}</p>
        )}

        {forecastWarning && (
          <p className="error-message">
            LightGBM Forecast Warning: {forecastWarning}
          </p>
        )}
      </section>

      {result && (
        <>
          {/* INVENTORY SUMMARY */}

          <section className="stats-grid">
            <article className="stat-card purple">
              <p>Product</p>

              <h2 className="small-value">
                {result.product_name ?? "Not returned"}
              </h2>

              <span>
                Product ID: {result.product_id ?? productId}
              </span>
            </article>

            <article className="stat-card blue">
              <p>Available Stock</p>

              <h2>
                {Number.isFinite(availableStock)
                  ? availableStock
                  : "Not returned"}
              </h2>

              <span>Current available units</span>
            </article>

            <article className="stat-card green">
              <p>Predicted Monthly Demand</p>

              <h2>
                {validForecasts.length > 0
                  ? monthlyDemand.toFixed(2)
                  : "N/A"}
              </h2>

              <span>
                Next {validForecasts.length} days (LightGBM)
              </span>
            </article>

            <article className="stat-card orange">
              <p>Average Daily Demand</p>

              <h2>
                {validForecasts.length > 0
                  ? averageDailyDemand.toFixed(2)
                  : "N/A"}
              </h2>

              <span>Units per day</span>
            </article>
          </section>

          {/* INVENTORY STATUS */}

          <section className="panel">
            <h2>Inventory Status</h2>

            <div className="stats-grid">
              <article className="stat-card purple">
                <p>Stock Status</p>

                <h2 className="small-value">
                  {stockStatus}
                </h2>
              </article>

              <article className="stat-card blue">
                <p>Estimated Stock Remaining</p>

                <h2>
                  {estimatedStockDays !== null
                    ? `${estimatedStockDays.toFixed(1)} Days`
                    : "N/A"}
                </h2>

                <span>Based on average daily demand</span>
              </article>

              <article className="stat-card green">
                <p>Expected Stock-Out Date</p>

                <h2 className="small-value">
                  {stockOutDate ?? "Not available"}
                </h2>

                <span>Format: DD/MM/YYYY</span>
              </article>
            </div>

            {stockStatus === "Critical" && (
              <p className="error-message">
                Critical inventory: stock is expected to last
                3 days or less. Consider reordering immediately.
              </p>
            )}

            {stockStatus === "Low Stock" && (
              <p>
                Low inventory: stock is expected to last
                more than 3 days and up to 7 days.
                Consider planning a reorder.
              </p>
            )}

            {stockStatus === "Healthy" && (
              <p>
                Inventory is currently healthy based on
                predicted average daily demand.
              </p>
            )}

            {stockStatus === "Out of Stock" && (
              <p className="error-message">
                This product currently has no available stock.
              </p>
            )}

            {stockStatus === "Unable to Calculate" && (
              <p>
                Inventory status cannot be calculated.
                Check available stock and LightGBM forecast data.
              </p>
            )}
          </section>

          {/* ================================= */}
          {/* THREE INVENTORY CHARTS */}
          {/* ================================= */}

          {validForecasts.length > 0 && (
            <>
              {/* CHART 1: LINE CHART */}

              <section className="panel">
                <h2>30-Day Daily Demand Forecast</h2>

                <p>
                  Daily predicted product demand using LightGBM.
                </p>

                <div
                  style={{
                    width: "100%",
                    overflowX: "auto",
                  }}
                >
                  <svg
                    viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                    style={{
                      width: "100%",
                      minWidth: "520px",
                      height: "auto",
                      display: "block",
                    }}
                    role="img"
                    aria-label="30-day daily demand forecast line chart"
                  >
                    <defs>
                      <linearGradient
                        id="demandAreaGradient"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="0%"
                          stopColor="#8b5cf6"
                          stopOpacity="0.35"
                        />
                        <stop
                          offset="100%"
                          stopColor="#8b5cf6"
                          stopOpacity="0.02"
                        />
                      </linearGradient>

                      <linearGradient
                        id="demandLineGradient"
                        x1="0"
                        y1="0"
                        x2="1"
                        y2="0"
                      >
                        <stop offset="0%" stopColor="#8b5cf6" />
                        <stop offset="100%" stopColor="#06b6d4" />
                      </linearGradient>
                    </defs>

                    {/* Horizontal grid lines */}

                    {[0, 1, 2, 3, 4].map((index) => {
                      const y =
                        chartTop + (plotHeight / 4) * index;

                      return (
                        <g key={index}>
                          <line
                            x1={chartLeft}
                            y1={y}
                            x2={chartWidth - chartRight}
                            y2={y}
                            stroke="currentColor"
                            opacity="0.12"
                            strokeDasharray="4 4"
                          />

                          <text
                            x={chartLeft - 8}
                            y={y + 4}
                            fontSize="10"
                            textAnchor="end"
                            fill="currentColor"
                            opacity="0.7"
                          >
                            {(
                              maxDailyDemand *
                              (1 - index / 4)
                            ).toFixed(1)}
                          </text>
                        </g>
                      );
                    })}

                    {/* Area under the line */}

                    {areaPath && (
                      <path
                        d={areaPath}
                        fill="url(#demandAreaGradient)"
                      />
                    )}

                    {/* Demand line */}

                    {linePath && (
                      <path
                        d={linePath}
                        fill="none"
                        stroke="url(#demandLineGradient)"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    )}

                    {/* Data points */}

                    {linePoints.map((point, index) => (
                      <circle
                        key={index}
                        cx={point.x}
                        cy={point.y}
                        r="3.5"
                        fill="#8b5cf6"
                        stroke="white"
                        strokeWidth="1.5"
                      >
                        <title>
                          {`Day ${index + 1}: ${point.demand.toFixed(2)} units`}
                        </title>
                      </circle>
                    ))}

                    {/* X-axis labels */}

                    {validForecasts.map((item, index) => {
                      if (
                        index % 5 !== 0 &&
                        index !== validForecasts.length - 1
                      ) {
                        return null;
                      }

                      const x =
                        chartLeft +
                        (index /
                          Math.max(validForecasts.length - 1, 1)) *
                          plotWidth;

                      return (
                        <text
                          key={index}
                          x={x}
                          y={chartHeight - 12}
                          fontSize="10"
                          textAnchor="middle"
                          fill="currentColor"
                        >
                          {`Day ${index + 1}`}
                        </text>
                      );
                    })}
                  </svg>
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    marginTop: "12px",
                    fontSize: "13px",
                  }}
                >
                  <span
                    style={{
                      width: "11px",
                      height: "11px",
                      background: "#8b5cf6",
                      borderRadius: "50%",
                    }}
                  />

                  <span>Predicted Daily Demand (Units)</span>
                </div>
              </section>

              {/* CHART 2: DOUGHNUT CHART */}

              <section className="panel">
                <h2>Forecast Demand vs Remaining Stock</h2>

                <p>
                  Comparison of forecast demand with the projected
                  stock remaining after the forecast period.
                </p>

                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "35px",
                    padding: "25px 10px",
                  }}
                >
                  {/* Doughnut */}

                  <div
                    style={{
                      width: "210px",
                      height: "210px",
                      borderRadius: "50%",
                      background: doughnutGradient,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    <div
                      style={{
                        width: "135px",
                        height: "135px",
                        borderRadius: "50%",
                        background: "var(--card-bg, white)",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <strong
                        style={{
                          fontSize: "23px",
                          color: "var(--foreground, #111827)",
                        }}
                      >
                        {doughnutTotal > 0
                          ? `${demandPercentage.toFixed(1)}%`
                          : "N/A"}
                      </strong>

                      <span
                        style={{
                          fontSize: "12px",
                          color: "var(--muted-foreground, #777)",
                        }}
                      >
                        Forecast demand
                      </span>
                    </div>
                  </div>

                  {/* Doughnut values */}

                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "22px",
                      minWidth: "180px",
                    }}
                  >
                    <div>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "9px",
                        }}
                      >
                        <span
                          style={{
                            width: "12px",
                            height: "12px",
                            background: "#8b5cf6",
                            borderRadius: "3px",
                          }}
                        />

                        <strong>Forecast Demand</strong>
                      </div>

                      <h2
                        style={{
                          margin: "7px 0 0 21px",
                          color: "#8b5cf6",
                        }}
                      >
                        {monthlyDemand.toFixed(2)} units
                      </h2>
                    </div>

                    <div>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "9px",
                        }}
                      >
                        <span
                          style={{
                            width: "12px",
                            height: "12px",
                            background: "#10b981",
                            borderRadius: "3px",
                          }}
                        />

                        <strong>Remaining Stock</strong>
                      </div>

                      <h2
                        style={{
                          margin: "7px 0 0 21px",
                          color: "#10b981",
                        }}
                      >
                        {projectedRemainingStock.toFixed(2)} units
                      </h2>
                    </div>

                    <div>
                      <span
                        style={{
                          color: "var(--muted-foreground, #777)",
                          fontSize: "13px",
                        }}
                      >
                        Current Available Stock
                      </span>

                      <h3 style={{ margin: "5px 0" }}>
                        {Number.isFinite(availableStock)
                          ? availableStock
                          : "N/A"}{" "}
                        units
                      </h3>
                    </div>
                  </div>
                </div>

                {monthlyDemand > availableStock &&
                  Number.isFinite(availableStock) && (
                    <p className="error-message">
                      Warning: Forecast demand exceeds current
                      available stock. Additional stock may be
                      required to meet the predicted demand.
                    </p>
                  )}

                
              </section>

              {/* CHART 3: WEEKLY BAR CHART */}

              <section className="panel">
                <h2>Weekly Predicted Demand</h2>

                <p>
                  Comparison of predicted demand across each
                  seven-day period.
                </p>

                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "23px",
                    marginTop: "25px",
                  }}
                >
                  {weeklyDemand.map((week, index) => {
                    const percentage =
                      (week.total / maxWeeklyDemand) * 100;

                    return (
                      <div key={week.label}>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            gap: "10px",
                            marginBottom: "9px",
                          }}
                        >
                          <strong>{week.label}</strong>

                          <span
                            style={{
                              fontWeight: "600",
                              color: barColors[index % barColors.length],
                            }}
                          >
                            {week.total.toFixed(2)} units
                          </span>
                        </div>

                        <div
                          style={{
                            width: "100%",
                            height: "23px",
                            background: "rgba(128,128,128,0.13)",
                            borderRadius: "7px",
                            overflow: "hidden",
                          }}
                        >
                          <div
                            style={{
                              width: `${percentage}%`,
                              height: "100%",
                              minWidth:
                                week.total > 0 ? "3px" : "0",
                              background:
                                `linear-gradient(90deg, ${
                                  barColors[index % barColors.length]
                                }, ${
                                  barColors[(index + 1) % barColors.length]
                                })`,
                              borderRadius: "7px",
                              transition: "width 0.5s ease",
                            }}
                          />
                        </div>

                        <span
                          style={{
                            display: "block",
                            marginTop: "5px",
                            fontSize: "11px",
                            color: "var(--muted-foreground, #777)",
                          }}
                        >
                          {week.days} forecast days
                        </span>
                      </div>
                    );
                  })}
                </div>

                <div
                  style={{
                    marginTop: "25px",
                    padding: "15px",
                    borderRadius: "10px",
                    background: "rgba(139,92,246,0.08)",
                  }}
                >
                  <span
                    style={{
                      fontSize: "13px",
                      color: "var(--muted-foreground, #777)",
                    }}
                  >
                    Total Forecast Demand
                  </span>

                  <h2
                    style={{
                      margin: "5px 0 0",
                      color: "#8b5cf6",
                    }}
                  >
                    {monthlyDemand.toFixed(2)} units
                  </h2>
                </div>
              </section>
            </>
          )}

          {/* 30-DAY LIGHTGBM FORECAST TABLE */}

          {forecast.length > 0 && (
            <section className="panel">
              <h2>30-Day LightGBM Demand Forecast</h2>

              <p>
                Daily predicted demand for the selected product.
              </p>

              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Predicted Demand</th>
                      <th>Model</th>
                    </tr>
                  </thead>

                  <tbody>
                    {forecast.map((item, index) => (
                      <tr
                        key={`${item.ForecastDate}-${index}`}
                      >
                        <td>{item.ForecastDate}</td>

                        <td>
                          {Number(item.PredictedDemand).toFixed(2)}
                        </td>

                        <td>{item.Model ?? "LightGBM"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* INVENTORY CALCULATION */}

          {validForecasts.length > 0 && (
            <section className="panel">
              <h2>Inventory Calculation</h2>

              <p>
                The following calculations use daily demand
                predictions returned by LightGBM.
              </p>

              <div className="calculation-details">
                <p>
                  <strong>Total predicted demand:</strong>{" "}
                  {monthlyDemand.toFixed(2)} units
                </p>

                <p>
                  <strong>Forecast period:</strong>{" "}
                  {validForecasts.length} days
                </p>

                <p>
                  <strong>Average daily demand:</strong>{" "}
                  {monthlyDemand.toFixed(2)} ÷{" "}
                  {validForecasts.length} ={" "}
                  {averageDailyDemand.toFixed(2)} units
                </p>

                <p>
                  <strong>Estimated stock remaining:</strong>{" "}
                  {availableStock} ÷{" "}
                  {averageDailyDemand.toFixed(2)} ={" "}
                  {estimatedStockDays !== null
                    ? `${estimatedStockDays.toFixed(2)} days`
                    : "Unable to calculate"}
                </p>

                <p>
                  <strong>Expected stock-out date:</strong>{" "}
                  {stockOutDate ?? "Not available"}
                </p>
              </div>

            
            </section>
          )}
        </>
      )}
    </PageLayout>
  );
}
