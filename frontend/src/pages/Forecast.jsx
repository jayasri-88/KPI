import React, { useState, useEffect, useMemo } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import {
  LineChart as LineChartIcon,
  TrendingUp,
  Sparkles,
  RefreshCw,
  AlertCircle,
  Calendar,
  DollarSign,
  CheckCircle2,
  BarChart3,
  HelpCircle,
  Activity,
  Layers,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  getSalesForecast,
  retrainForecast,
  getForecastFeatures,
  getSalesTrendAnalytics,
  listStores,
} from "../services/api";
import { formatCurrency, formatPercent } from "../utils/formatters";
import { SkeletonCard, SkeletonChart } from "../components/common/LoadingSkeleton";
import { ErrorState } from "../components/common/EmptyState";

export default function Forecast() {
  const [horizonDays, setHorizonDays] = useState(30);
  const [selectedStoreId, setSelectedStoreId] = useState("");
  const [storesList, setStoresList] = useState([]);

  // Data states
  const [forecastData, setForecastData] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [featuresDict, setFeaturesDict] = useState({});

  // UI state
  const [loading, setLoading] = useState(true);
  const [retraining, setRetraining] = useState(false);
  const [retrainSuccess, setRetrainSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [showFeatureDrawer, setShowFeatureDrawer] = useState(false);

  // Load stores list once
  useEffect(() => {
    const fetchStores = async () => {
      try {
        const res = await listStores({ size: 50 });
        setStoresList(res.items || []);
      } catch (e) {
        console.error("Failed to load stores list:", e);
      }
    };
    fetchStores();
  }, []);

  // Fetch forecast and trend analytics
  const fetchForecastAndAnalytics = async (isRetrain = false) => {
    if (isRetrain) {
      setRetraining(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const params = {
        days: horizonDays,
        store_id: selectedStoreId || undefined,
        force_retrain: isRetrain,
      };

      const [fcRes, trendRes, featRes] = await Promise.all([
        getSalesForecast(params),
        getSalesTrendAnalytics({ store_id: selectedStoreId || undefined, days: 90 }),
        getForecastFeatures(),
      ]);

      setForecastData(fcRes);
      setTrendData(trendRes);
      setFeaturesDict(featRes || {});

      if (isRetrain) {
        setRetrainSuccess(true);
        setTimeout(() => setRetrainSuccess(false), 4000);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to load forecasting pipeline.");
    } finally {
      setLoading(false);
      setRetraining(false);
    }
  };

  useEffect(() => {
    fetchForecastAndAnalytics(false);
  }, [horizonDays, selectedStoreId]);

  const handleRetrain = () => {
    fetchForecastAndAnalytics(true);
  };

  // Prepare chart series: combine actual historical points and future projections
  const chartData = useMemo(() => {
    if (!forecastData?.data) return [];
    return forecastData.data.map((item) => ({
      date: item.date.slice(5), // 'MM-DD' for compact X-axis
      fullDate: item.date,
      actualSales: item.actual_sales !== null ? Number(item.actual_sales) : undefined,
      forecastSales: item.forecast_sales !== null ? Number(item.forecast_sales) : undefined,
      lowerBound: item.lower_bound !== null ? Math.max(0, Number(item.lower_bound)) : undefined,
      upperBound: item.upper_bound !== null ? Number(item.upper_bound) : undefined,
      isForecast: item.is_forecast,
    }));
  }, [forecastData]);

  const evalMetrics = forecastData?.evaluation_metrics || {
    mae: 0,
    rmse: 0,
    mape: 0,
    wape: 0,
    r2: 0,
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center shadow-inner">
              <LineChartIcon className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Prophet Sales Demand Forecasting & Predictive ML
              </h1>
              <p className="text-xs text-slate-400">
                Out-of-time evaluated retail demand modeling with uncertainty bounds and zero-leakage lag features
              </p>
            </div>
          </div>
        </div>

        {/* Global Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Horizon Toggle */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1 shadow-md">
            <button
              onClick={() => setHorizonDays(7)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                horizonDays === 7
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              7-Day Horizon
            </button>
            <button
              onClick={() => setHorizonDays(30)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                horizonDays === 30
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              30-Day Horizon
            </button>
          </div>

          {/* Store Filter */}
          <select
            value={selectedStoreId}
            onChange={(e) => setSelectedStoreId(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-xl px-3 py-2 focus:outline-none focus:border-indigo-500 shadow-md cursor-pointer"
          >
            <option value="">All Stores (Network Total)</option>
            {storesList.map((st) => (
              <option key={st.id} value={st.id}>
                {st.name} ({st.city})
              </option>
            ))}
          </select>

          {/* Retrain Action */}
          <button
            onClick={handleRetrain}
            disabled={retraining}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition shadow-md cursor-pointer disabled:opacity-50"
            title="Train model on latest sales records and update artifact on disk"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${retraining ? "animate-spin text-indigo-400" : ""}`} />
            <span>{retraining ? "Training..." : "Retrain Model"}</span>
          </button>
        </div>
      </div>

      {retrainSuccess && (
        <div className="p-3 bg-emerald-950/60 border border-emerald-700/60 rounded-xl text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Model successfully retrained on full historical series and saved to disk artifact.</span>
        </div>
      )}

      {error && <ErrorState message={error} onRetry={() => fetchForecastAndAnalytics(false)} />}

      {/* Evaluation Metrics Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Model Architecture */}
        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm col-span-2 sm:col-span-1 lg:col-span-2">
          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-indigo-400" />
            <span>Architecture</span>
          </span>
          <p className="text-sm font-extrabold text-white mt-1 truncate">
            {forecastData?.model_name || "Meta Prophet Regressor"}
          </p>
          <span className="text-[11px] text-slate-400 block mt-0.5">
            Weekly + Trend Changepoints &bull; 80% Intervals
          </span>
        </div>

        {/* MAE */}
        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
            MAE (Mean Abs Error)
          </span>
          <p className="text-sm font-extrabold text-white mt-1">
            {formatCurrency(evalMetrics.mae, { compact: true })}
          </p>
          <span className="text-[10px] text-slate-500 block mt-0.5">Unweighted daily error</span>
        </div>

        {/* RMSE */}
        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
            RMSE (Out-of-Time)
          </span>
          <p className="text-sm font-extrabold text-white mt-1">
            {formatCurrency(evalMetrics.rmse, { compact: true })}
          </p>
          <span className="text-[10px] text-slate-500 block mt-0.5">Penalizes large variance</span>
        </div>

        {/* WAPE */}
        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
            WAPE (Retail Standard)
          </span>
          <p className="text-sm font-extrabold text-indigo-400 mt-1">
            {evalMetrics.wape?.toFixed(1)}%
          </p>
          <span className="text-[10px] text-slate-500 block mt-0.5">Weighted % error</span>
        </div>

        {/* R-squared */}
        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
            R² (Holdout Split)
          </span>
          <p className="text-sm font-extrabold text-white mt-1">
            {evalMetrics.r2 !== undefined ? evalMetrics.r2.toFixed(3) : "N/A"}
          </p>
          <span className="text-[10px] text-slate-500 block mt-0.5">Variance explained</span>
        </div>
      </div>

      {/* Main Interactive Forecast Chart (Recharts) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-md space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" />
              <h2 className="text-base font-bold text-white">
                Historical Actual Sales vs. {horizonDays}-Day Projected Forecast
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Continuity bridge connects historical observations with forward trajectory and 80% confidence corridor
            </p>
          </div>

          {/* Forecast Revenue Highlights */}
          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">
                Projected Total ({horizonDays}d)
              </span>
              <span className="text-base font-extrabold text-emerald-400">
                {formatCurrency(forecastData?.total_forecast_revenue || 0, { compact: true })}
              </span>
            </div>
            <div className="text-right pl-3 border-l border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">
                Avg Daily Projected
              </span>
              <span className="text-sm font-extrabold text-white">
                {formatCurrency(forecastData?.avg_daily_forecast || 0, { compact: true })}
              </span>
            </div>
          </div>
        </div>

        {/* Recharts Area + Line Composed Chart */}
        {loading ? (
          <SkeletonChart height="h-80" />
        ) : (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <defs>
                  {/* Confidence Interval Gradient */}
                  <linearGradient id="confidenceBand" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.03} />
                  </linearGradient>
                </defs>

                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload || !payload.length) return null;
                    const d = payload[0].payload;
                    return (
                      <div className="bg-slate-950/95 border border-slate-800 rounded-xl p-3 shadow-xl text-xs backdrop-blur-md">
                        <p className="font-bold text-slate-200 border-b border-slate-800 pb-1 mb-1.5 flex items-center justify-between gap-4">
                          <span>{d.fullDate}</span>
                          <span
                            className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                              d.isForecast
                                ? "bg-indigo-500/20 text-indigo-300"
                                : "bg-emerald-500/20 text-emerald-300"
                            }`}
                          >
                            {d.isForecast ? "ML Forecast" : "Actual Observed"}
                          </span>
                        </p>
                        {d.actualSales !== undefined && (
                          <div className="flex justify-between gap-4 py-0.5">
                            <span className="text-slate-400">Actual Sales:</span>
                            <span className="font-bold text-white">
                              {formatCurrency(d.actualSales)}
                            </span>
                          </div>
                        )}
                        {d.forecastSales !== undefined && (
                          <div className="flex justify-between gap-4 py-0.5">
                            <span className="text-indigo-400 font-semibold">Forecast (yhat):</span>
                            <span className="font-extrabold text-indigo-300">
                              {formatCurrency(d.forecastSales)}
                            </span>
                          </div>
                        )}
                        {d.lowerBound !== undefined && d.upperBound !== undefined && (
                          <div className="flex justify-between gap-4 py-0.5 text-[11px] text-slate-500 border-t border-slate-800/80 mt-1 pt-1">
                            <span>80% Confidence:</span>
                            <span>
                              {formatCurrency(d.lowerBound, { compact: true })} - {formatCurrency(d.upperBound, { compact: true })}
                            </span>
                          </div>
                        )}
                      </div>
                    );
                  }}
                />
                <Legend
                  verticalAlign="top"
                  height={30}
                  wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }}
                />

                {/* Shaded Confidence Interval Upper Bound */}
                <Area
                  type="monotone"
                  dataKey="upperBound"
                  name="Upper Confidence (80%)"
                  stroke="none"
                  fill="url(#confidenceBand)"
                  connectNulls
                />

                {/* Actual Sales Line (Cyan/Emerald) */}
                <Line
                  type="monotone"
                  dataKey="actualSales"
                  name="Observed Actual Sales"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  dot={false}
                  connectNulls
                />

                {/* Forecast Sales Line (Indigo Dotted/Bold) */}
                <Line
                  type="monotone"
                  dataKey="forecastSales"
                  name="Prophet Forecast Projection"
                  stroke="#818cf8"
                  strokeWidth={2.5}
                  strokeDasharray="5 5"
                  dot={{ r: 3, fill: "#6366f1", strokeWidth: 1 }}
                  connectNulls
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Seasonality & Trend Insights Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Day-of-Week Seasonality (5 cols) */}
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4 text-indigo-400" />
                <span>Day-of-Week Seasonality Decomposition</span>
              </h3>
              <span className="text-[10px] text-slate-400">Mean Revenue / Day</span>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Weekly cycle extracted from historical series showing shopping surge distribution across weekdays vs weekends.
            </p>

            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trendData?.day_of_week_pattern || []} margin={{ top: 0, right: 0, left: -15, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis
                    dataKey="day_name"
                    stroke="#64748b"
                    fontSize={10}
                    tickFormatter={(val) => val.slice(0, 3)}
                  />
                  <YAxis
                    stroke="#64748b"
                    fontSize={10}
                    tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const d = payload[0].payload;
                      return (
                        <div className="bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-white">
                          <p className="font-bold">{d.day_name}</p>
                          <p className="text-indigo-400">Avg Revenue: {formatCurrency(d.avg_revenue)}</p>
                          <p className="text-slate-400">Avg Orders: {d.avg_orders}</p>
                          <p className="text-emerald-400">Share: {d.share_pct}%</p>
                        </div>
                      );
                    }}
                  />
                  <Bar
                    dataKey="avg_revenue"
                    fill="#6366f1"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-3 border-t border-slate-800 mt-3 text-xs">
            <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase block">Historical Peak Day</span>
              <span className="font-bold text-white">{trendData?.peak_day || "N/A"}</span>
              <span className="text-[10px] text-emerald-400 block font-mono">
                {formatCurrency(trendData?.peak_day_revenue || 0, { compact: true })}
              </span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase block">Daily Volatility (Std Dev)</span>
              <span className="font-bold text-white">
                {formatCurrency(trendData?.volatility_std || 0, { compact: true })}
              </span>
              <span className="text-[10px] text-slate-500 block">Daily sales dispersion</span>
            </div>
          </div>
        </div>

        {/* Right: Model Governance & Feature Explanations (6 cols) */}
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Model Governance & Anti-Leakage Protocol</span>
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                Validated
              </span>
            </div>
            <p className="text-xs text-slate-400 mb-3">
              The forecasting pipeline follows enterprise machine learning rules to prevent data leakage and unrealistic accuracy metrics:
            </p>

            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-start gap-2 p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Strict Chronological Split:</strong> Holdout evaluation is performed strictly on the final 30 days without shuffle.
                </span>
              </li>
              <li className="flex items-start gap-2 p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Past-Shifted Regressors:</strong> All lag (T-1, T-7, T-30) and rolling averages are shifted by at least 1 day.
                </span>
              </li>
              <li className="flex items-start gap-2 p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Artifact Persistence:</strong> Pre-trained Prophet models are cached to disk so production API requests take &lt; 50ms.
                </span>
              </li>
            </ul>
          </div>

          {/* Toggle Feature Explanations Accordion */}
          <div className="pt-3 border-t border-slate-800 mt-3">
            <button
              onClick={() => setShowFeatureDrawer(!showFeatureDrawer)}
              className="w-full flex items-center justify-between text-xs font-semibold text-indigo-400 hover:text-indigo-300 cursor-pointer"
            >
              <span className="flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" />
                <span>Inspect All 14 Time-Series Features ({Object.keys(featuresDict).length})</span>
              </span>
              {showFeatureDrawer ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showFeatureDrawer && (
              <div className="mt-3 max-h-48 overflow-y-auto space-y-1.5 pr-1">
                {Object.entries(featuresDict).map(([featName, featDesc]) => (
                  <div key={featName} className="p-2 rounded bg-slate-950 border border-slate-800 text-[11px]">
                    <span className="font-mono text-indigo-300 font-bold">{featName}: </span>
                    <span className="text-slate-400">{featDesc}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
