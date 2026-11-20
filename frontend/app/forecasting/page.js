
"use client";

import { useState } from "react";
import PageLayout from "../../components/PageLayout";
import { apiRequest } from "../../components/api";
import ProductIdSelect from "../../components/ProductIdSelect";

function getForecastRows(response) {
  if (Array.isArray(response?.forecasts)) return response.forecasts;
  if (Array.isArray(response?.Forecast)) return response.Forecast;
  if (Array.isArray(response?.forecast)) return response.forecast;
  if (Array.isArray(response)) return response;
  return [];
}

function getModelName(response, fallback) {
  return response?.Model || response?.model || fallback;
}

function getDate(row) {
  return (
    row?.ForecastDate ||
    row?.forecast_date ||
    row?.ds ||
    row?.date ||
    ""
  );
}

function getDemand(row) {
  const value =
    row?.PredictedDemand ??
    row?.predicted_demand ??
    row?.yhat ??
    row?.prediction;

  return value == null ? null : Number(value);
}

function formatDemand(value) {
  return value == null || !Number.isFinite(value)
    ? "—"
    : value.toLocaleString("en-LK", {
        maximumFractionDigits: 2,
      });
}

function formatDate(date) {
  if (!date) return "—";

  const parts = String(date).slice(0, 10).split("-");

  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
  }

  return date;
}

// Reusable colourful line chart
function ForecastLineChart({ title, description, series }) {
  const chartWidth = 900;
  const chartHeight = 340;

  const chartLeft = 75;
  const chartRight = 25;
  const chartTop = 30;
  const chartBottom = 65;

  const plotWidth = chartWidth - chartLeft - chartRight;
  const plotHeight = chartHeight - chartTop - chartBottom;

  const allDates = [
    ...new Set(
      series.flatMap((item) =>
        item.rows.map((row) => row.date)
      )
    ),
  ].sort();

  const allValues = series.flatMap((item) =>
    item.rows
      .map((row) => row.value)
      .filter(
        (value) =>
          value != null && Number.isFinite(value)
      )
  );

  if (allDates.length === 0 || allValues.length === 0) {
    return (
      <section className="panel">
        <h2>{title}</h2>
        <p className="notice">
          No valid dated forecast records are available for this chart.
        </p>
      </section>
    );
  }

  // Include zero in the scale and support negative model predictions.
  const minimumValue = Math.min(0, ...allValues);
  const maximumValue = Math.max(0, ...allValues);

  const valueRange =
    maximumValue - minimumValue || 1;

  const chartMinimum =
    minimumValue - valueRange * 0.08;

  const chartMaximum =
    maximumValue + valueRange * 0.08;

  const chartRange = chartMaximum - chartMinimum || 1;

  const getX = (index) => {
    if (allDates.length <= 1) {
      return chartLeft + plotWidth / 2;
    }

    return (
      chartLeft +
      (index / (allDates.length - 1)) * plotWidth
    );
  };

  const getY = (value) => {
    return (
      chartTop +
      ((chartMaximum - value) / chartRange) * plotHeight
    );
  };

  const yAxisLabels = Array.from(
    { length: 5 },
    (_, index) =>
      chartMinimum + (chartRange / 4) * index
  );

  const xLabelIndexes = [
    ...new Set([
      0,
      Math.floor((allDates.length - 1) / 4),
      Math.floor((allDates.length - 1) / 2),
      Math.floor(((allDates.length - 1) * 3) / 4),
      allDates.length - 1,
    ]),
  ];

  function getSeriesPath(item) {
    const valueMap = new Map(
      item.rows.map((row) => [
        row.date,
        row.value,
      ])
    );

    return allDates
      .map((date, index) => {
        const value = valueMap.get(date);

        if (
          value == null ||
          !Number.isFinite(value)
        ) {
          return null;
        }

        return {
          x: getX(index),
          y: getY(value),
        };
      })
      .filter(Boolean)
      .map(
        (point, index) =>
          `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`
      )
      .join(" ");
  }

  return (
    <section className="panel">
      <h2>{title}</h2>

      {description && (
        <p className="page-description">
          {description}
        </p>
      )}

      {/* Chart legend */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 24,
          margin: "20px 0",
          alignItems: "center",
        }}
      >
        {series.map((item) => (
          <div
            key={item.name}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span
              style={{
                width: 28,
                height: 4,
                borderRadius: 5,
                background: item.color,
                display: "inline-block",
              }}
            />

            <strong>{item.name}</strong>
          </div>
        ))}
      </div>

      {/* SVG line chart */}
      <div
        style={{
          width: "100%",
          overflowX: "auto",
        }}
      >
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          role="img"
          aria-label={title}
          style={{
            width: "100%",
            minWidth: 500,
            height: "auto",
            display: "block",
            overflow: "visible",
          }}
        >
          {/* Y-axis grid lines */}
          {yAxisLabels.map((value, index) => {
            const y = getY(value);

            return (
              <g key={index}>
                <line
                  x1={chartLeft}
                  y1={y}
                  x2={chartWidth - chartRight}
                  y2={y}
                  stroke="#d1d5db"
                  strokeDasharray="5 5"
                  strokeWidth="1"
                />

                <text
                  x={chartLeft - 12}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="12"
                  fill="currentColor"
                >
                  {formatDemand(value)}
                </text>
              </g>
            );
          })}

          {/* X-axis */}
          <line
            x1={chartLeft}
            y1={chartTop + plotHeight}
            x2={chartWidth - chartRight}
            y2={chartTop + plotHeight}
            stroke="#9ca3af"
            strokeWidth="1.5"
          />

          {/* Forecast lines */}
          {series.map((item) => (
            <g key={item.name}>
              <path
                d={getSeriesPath(item)}
                fill="none"
                stroke={item.color}
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Individual data points */}
              {allDates.map((date, index) => {
                const row = item.rows.find(
                  (record) => record.date === date
                );

                if (
                  !row ||
                  row.value == null ||
                  !Number.isFinite(row.value)
                ) {
                  return null;
                }

                return (
                  <circle
                    key={`${item.name}-${date}`}
                    cx={getX(index)}
                    cy={getY(row.value)}
                    r="5"
                    fill={item.color}
                    stroke="white"
                    strokeWidth="2"
                  >
                    <title>
                      {item.name} | {formatDate(date)} |{" "}
                      {formatDemand(row.value)} units
                    </title>
                  </circle>
                );
              })}
            </g>
          ))}

          {/* X-axis date labels */}
          {xLabelIndexes.map((index) => (
            <text
              key={`date-${index}`}
              x={getX(index)}
              y={chartTop + plotHeight + 25}
              textAnchor="middle"
              fontSize="12"
              fill="currentColor"
            >
              {formatDate(allDates[index])}
            </text>
          ))}

          {/* Axis titles */}
          <text
            x={chartLeft + plotWidth / 2}
            y={chartHeight - 8}
            textAnchor="middle"
            fontSize="13"
            fontWeight="600"
            fill="currentColor"
          >
            Forecast Date
          </text>

          <text
            x="18"
            y={chartTop + plotHeight / 2}
            textAnchor="middle"
            fontSize="13"
            fontWeight="600"
            fill="currentColor"
            transform={`rotate(-90 18 ${
              chartTop + plotHeight / 2
            })`}
          >
            Predicted Demand (Units)
          </text>
        </svg>
      </div>

    </section>
  );
}

export default function ForecastingPage() {
  const [productId, setProductId] = useState("");
  const [days, setDays] = useState("7");
  const [lightgbm, setLightgbm] = useState(null);
  const [prophet, setProphet] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [warnings, setWarnings] = useState([]);

  async function handleForecast(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setWarnings([]);
    setLightgbm(null);
    setProphet(null);

    const id = productId.trim();
    const numberOfDays = Number(days);

    if (!id) {
      setError("Enter a product ID.");
      setLoading(false);
      return;
    }

    if (
      !Number.isInteger(numberOfDays) ||
      numberOfDays < 1 ||
      numberOfDays > 30
    ) {
      setError(
        "Forecast days must be between 1 and 30."
      );
      setLoading(false);
      return;
    }

    const encodedId = encodeURIComponent(id);

    const requests = await Promise.allSettled([
      apiRequest(
        `/forecast/lightgbm/${encodedId}?days=${numberOfDays}`
      ),
      apiRequest(
        `/forecast/product/${encodedId}?days=${numberOfDays}`
      ),
    ]);

    const messages = [];

    if (requests[0].status === "fulfilled") {
      setLightgbm(requests[0].value);
    } else {
      messages.push(
        `LightGBM failed: ${
          requests[0].reason?.message || "Unknown error"
        }`
      );
    }

    if (requests[1].status === "fulfilled") {
      const response = requests[1].value;
      const actualModel = String(
        getModelName(response, "")
      );

      if (
        actualModel.toLowerCase().includes("prophet")
      ) {
        setProphet(response);
      } else {
        messages.push(
          `The product endpoint returned "${
            actualModel || "an unspecified model"
          }", not Prophet. A separate Prophet comparison is unavailable for this response.`
        );
      }
    } else {
      messages.push(
        `Prophet/product endpoint failed: ${
          requests[1].reason?.message || "Unknown error"
        }`
      );
    }

    setWarnings(messages);
    setLoading(false);

    if (
      requests[0].status === "rejected" &&
      requests[1].status === "rejected"
    ) {
      setError(
        "Both forecasting requests failed. Check your backend."
      );
    }
  }

  const lightgbmRows = getForecastRows(lightgbm);
  const prophetRows = getForecastRows(prophet);

  // Prepare individual model chart data
  const lightgbmChartRows = lightgbmRows
    .map((row) => ({
      date: String(getDate(row)).slice(0, 10),
      value: getDemand(row),
    }))
    .filter(
      (row) =>
        row.date &&
        row.value != null &&
        Number.isFinite(row.value)
    )
    .sort((a, b) => a.date.localeCompare(b.date));

  const prophetChartRows = prophetRows
    .map((row) => ({
      date: String(getDate(row)).slice(0, 10),
      value: getDemand(row),
    }))
    .filter(
      (row) =>
        row.date &&
        row.value != null &&
        Number.isFinite(row.value)
    )
    .sort((a, b) => a.date.localeCompare(b.date));

  // Prepare combined comparison data
  const lightgbmByDate = new Map(
    lightgbmChartRows.map((row) => [
      row.date,
      row.value,
    ])
  );

  const prophetByDate = new Map(
    prophetChartRows.map((row) => [
      row.date,
      row.value,
    ])
  );

  const dates = [
    ...new Set([
      ...lightgbmByDate.keys(),
      ...prophetByDate.keys(),
    ]),
  ].sort();

  const comparisonRows = dates.map((date) => {
    const lightgbmDemand = lightgbmByDate.get(date);
    const prophetDemand = prophetByDate.get(date);

    return {
      date,
      lightgbmDemand,
      prophetDemand,
      difference:
        lightgbmDemand != null &&
        prophetDemand != null
          ? Math.abs(
              lightgbmDemand - prophetDemand
            )
          : null,
    };
  });

  const sumDemand = (rows) =>
    rows.reduce((sum, row) => {
      const value = getDemand(row);

      return (
        sum +
        (value != null && Number.isFinite(value)
          ? value
          : 0)
      );
    }, 0);

  const lightgbmTotal = sumDemand(lightgbmRows);
  const prophetTotal = sumDemand(prophetRows);

  const lightgbmModel = lightgbm
    ? getModelName(lightgbm, "LightGBM")
    : "LightGBM";

  const prophetModel = prophet
    ? getModelName(prophet, "Prophet")
    : "Prophet";

  const hasComparison =
    lightgbmChartRows.length > 0 &&
    prophetChartRows.length > 0 &&
    comparisonRows.some(
      (row) =>
        row.lightgbmDemand != null &&
        row.prophetDemand != null
    );

  const chartMaximum = Math.max(
    1,
    lightgbmTotal,
    prophetTotal
  );

  return (
    <PageLayout
      title="Demand Forecasting"
      description="Generate and compare LightGBM and Prophet demand forecasts."
    >
      {/* Generate Forecast */}
      <section className="panel">
        <h2>Generate Forecast</h2>

        <form
          className="form-grid"
          onSubmit={handleForecast}
        >
          <ProductIdSelect
            value={productId}
            onChange={setProductId}
          />

          <div className="field">
            <label htmlFor="days">
              Forecast Period
            </label>

            <select
              id="days"
              value={days}
              onChange={(event) =>
                setDays(event.target.value)
              }
            >
              {[7, 14, 30].map((day) => (
                <option key={day} value={day}>
                  {day} days
                </option>
              ))}
            </select>
          </div>

          <button
            className="primary-button"
            disabled={loading}
          >
            {loading
              ? "Generating forecasts..."
              : "Compare Forecasts"}
          </button>
        </form>

        {error && (
          <p className="error-message">{error}</p>
        )}

        {warnings.map((warning, index) => (
          <p className="notice" key={index}>
            {warning}
          </p>
        ))}
      </section>

      {(lightgbm || prophet) && (
        <>
          {/* Summary cards */}
          <section className="stats-grid">
            {lightgbm && (
              <article className="stat-card purple">
                <p>
                  LightGBM Total Predicted Demand
                </p>
                <h2>
                  {formatDemand(lightgbmTotal)}
                </h2>
                <span>
                  {lightgbmRows.length} forecast records
                </span>
              </article>
            )}

            {prophet && (
              <article className="stat-card blue">
                <p>
                  Prophet Total Predicted Demand
                </p>
                <h2>
                  {formatDemand(prophetTotal)}
                </h2>
                <span>
                  {prophetRows.length} forecast records
                </span>
              </article>
            )}

            {lightgbm && prophet && (
              <article className="stat-card green">
                <p>Difference in Total Demand</p>
                <h2>
                  {formatDemand(
                    Math.abs(
                      lightgbmTotal - prophetTotal
                    )
                  )}
                </h2>
                <span>
                  Absolute difference between model totals
                </span>
              </article>
            )}
          </section>

          {/* Model comparison bars */}
          <section className="panel">
            <h2>Forecast Model Comparison</h2>

            <p className="page-description">
              Product: {productId} · Forecast period: {days} days
            </p>

            {lightgbm && (
              <div
                style={{
                  marginTop: 20,
                  marginBottom: 24,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 12,
                  }}
                >
                  <strong>{lightgbmModel}</strong>
                  <span>
                    {formatDemand(lightgbmTotal)} units
                  </span>
                </div>

                <div
                  style={{
                    height: 14,
                    background: "#e9e7f5",
                    borderRadius: 8,
                    marginTop: 8,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${
                        (lightgbmTotal / chartMaximum) * 100
                      }%`,
                      height: "100%",
                      background: "#7657e8",
                    }}
                  />
                </div>
              </div>
            )}

            {prophet && (
              <div style={{ marginBottom: 20 }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 12,
                  }}
                >
                  <strong>{prophetModel}</strong>
                  <span>
                    {formatDemand(prophetTotal)} units
                  </span>
                </div>

                <div
                  style={{
                    height: 14,
                    background: "#e9e7f5",
                    borderRadius: 8,
                    marginTop: 8,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${
                        (prophetTotal / chartMaximum) * 100
                      }%`,
                      height: "100%",
                      background: "#159b80",
                    }}
                  />
                </div>
              </div>
            )}

            {hasComparison && (
              <p className="notice">
              </p>
            )}

            {lightgbm && prophet && !hasComparison && (
              <p className="notice">
                Both responses were received, but matching daily
                predictions were not found. Check the date and
                demand field names in the API responses.
              </p>
            )}
          </section>

          {/* 1. Combined line chart */}
          <ForecastLineChart
            title="Combined Daily Forecast Comparison"
            description="Compare LightGBM and Prophet predictions on the same chart."
            series={[
              ...(lightgbm
                ? [
                    {
                      name: "LightGBM",
                      color: "#8b5cf6",
                      rows: lightgbmChartRows,
                    },
                  ]
                : []),
              ...(prophet
                ? [
                    {
                      name: "Prophet",
                      color: "#10b981",
                      rows: prophetChartRows,
                    },
                  ]
                : []),
            ]}
          />

          {/* 2. Individual LightGBM chart */}
          {lightgbm && (
            <ForecastLineChart
              title="Individual LightGBM Demand Forecast"
              description={`Daily demand predictions from ${lightgbmModel} for ${productId}.`}
              series={[
                {
                  name: "LightGBM Predicted Demand",
                  color: "#8b5cf6",
                  rows: lightgbmChartRows,
                },
              ]}
            />
          )}

          {/* 3. Individual Prophet chart */}
          {prophet && (
            <ForecastLineChart
              title="Individual Prophet Demand Forecast"
              description={`Daily demand predictions from ${prophetModel} for ${productId}.`}
              series={[
                {
                  name: "Prophet Predicted Demand",
                  color: "#06b6d4",
                  rows: prophetChartRows,
                },
              ]}
            />
          )}

          {/* Daily comparison table */}
          <section className="panel">
            <h2>Daily Forecast Comparison</h2>

            {comparisonRows.length === 0 ? (
              <p className="notice">
                No dated forecast records were returned.
                Check the API response fields.
              </p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Forecast Date</th>
                      <th>LightGBM Demand</th>
                      <th>Prophet Demand</th>
                      <th>Absolute Difference</th>
                    </tr>
                  </thead>

                  <tbody>
                    {comparisonRows.map((row) => (
                      <tr key={row.date}>
                        <td>{formatDate(row.date)}</td>
                        <td>
                          {formatDemand(row.lightgbmDemand)}
                        </td>
                        <td>
                          {formatDemand(row.prophetDemand)}
                        </td>
                        <td>
                          {formatDemand(row.difference)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Individual model results */}
          <section className="panel">
            <h2>Individual Model Results</h2>

            {lightgbm && (
              <>
                <h3>LightGBM Forecast</h3>

                <p className="page-description">
                  Saved records:{" "}
                  {lightgbm.saved_records ?? "Not returned"}
                </p>

                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Predicted Demand</th>
                      </tr>
                    </thead>

                    <tbody>
                      {lightgbmRows.map((row, index) => (
                        <tr key={getDate(row) || index}>
                          <td>
                            {formatDate(getDate(row))}
                          </td>
                          <td>
                            {formatDemand(getDemand(row))}
                          </td>
                        </tr>
                      ))}

                      {lightgbmRows.length === 0 && (
                        <tr>
                          <td colSpan={2}>
                            No LightGBM forecast rows returned.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            )}

            {prophet && (
              <>
                <h3 style={{ marginTop: 24 }}>
                  Prophet Forecast
                </h3>

                <p className="page-description">
                  Saved records:{" "}
                  {prophet.saved_records ?? "Not returned"}
                </p>

                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Predicted Demand</th>
                      </tr>
                    </thead>

                    <tbody>
                      {prophetRows.map((row, index) => (
                        <tr key={getDate(row) || index}>
                          <td>
                            {formatDate(getDate(row))}
                          </td>
                          <td>
                            {formatDemand(getDemand(row))}
                          </td>
                        </tr>
                      ))}

                      {prophetRows.length === 0 && (
                        <tr>
                          <td colSpan={2}>
                            No Prophet forecast rows returned.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </section>
        </>
      )}
    </PageLayout>
  );
}

