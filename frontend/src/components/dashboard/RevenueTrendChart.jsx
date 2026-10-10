import React, { useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { formatCurrency, formatCompactNumber } from "../../utils/formatters";
import { TrendingUp, BarChart2, DollarSign } from "lucide-react";

export default function RevenueTrendChart({
  data = [],
  interval = "monthly",
  onIntervalChange,
  loading = false,
}) {
  const [metric, setMetric] = useState("revenue"); // revenue, profit, orders_count

  const metricConfig = {
    revenue: {
      label: "Revenue",
      color: "#6366f1", // Indigo
      gradient: "colorRevenue",
      format: (val) => formatCurrency(val, { compact: true }),
      tooltipFormat: (val) => formatCurrency(val),
    },
    profit: {
      label: "Gross Profit",
      color: "#10b981", // Emerald
      gradient: "colorProfit",
      format: (val) => formatCurrency(val, { compact: true }),
      tooltipFormat: (val) => formatCurrency(val),
    },
    orders_count: {
      label: "Orders Volume",
      color: "#38bdf8", // Sky
      gradient: "colorOrders",
      format: (val) => formatCompactNumber(val),
      tooltipFormat: (val) => `${Number(val).toLocaleString()} orders`,
    },
  };

  const activeConfig = metricConfig[metric];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-slate-700/80 rounded-xl p-3 shadow-2xl text-xs space-y-1.5 min-w-[160px]">
          <span className="font-semibold text-slate-300 block pb-1 border-b border-slate-800">
            Period: {label}
          </span>
          <div className="flex items-center justify-between text-indigo-400">
            <span>Revenue:</span>
            <span className="font-bold">{formatCurrency(item.revenue)}</span>
          </div>
          <div className="flex items-center justify-between text-emerald-400">
            <span>Gross Profit:</span>
            <span className="font-bold">{formatCurrency(item.profit)}</span>
          </div>
          <div className="flex items-center justify-between text-sky-400">
            <span>Orders:</span>
            <span className="font-bold">{Number(item.orders_count).toLocaleString()}</span>
          </div>
          <div className="flex items-center justify-between text-amber-400 pt-1 border-t border-slate-800 text-[11px]">
            <span>AOV:</span>
            <span>{formatCurrency(item.average_order_value)}</span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md flex flex-col justify-between">
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-white">Sales & Margin Trajectory</h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Historical timeline of net revenue, gross profit, and customer orders
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Metric Selector Toggle */}
          <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setMetric("revenue")}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                metric === "revenue"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Revenue
            </button>
            <button
              onClick={() => setMetric("profit")}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                metric === "profit"
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Profit
            </button>
            <button
              onClick={() => setMetric("orders_count")}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                metric === "orders_count"
                  ? "bg-sky-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Orders
            </button>
          </div>

          {/* Interval Toggle */}
          {onIntervalChange && (
            <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
              {["monthly", "weekly", "daily"].map((inv) => (
                <button
                  key={inv}
                  onClick={() => onIntervalChange(inv)}
                  className={`px-2 py-0.5 capitalize text-[11px] font-semibold rounded ${
                    interval === inv
                      ? "bg-slate-800 text-slate-200"
                      : "text-slate-500 hover:text-slate-300"
                  }`}
                >
                  {inv[0].toUpperCase() + inv.slice(1, 2)}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-72 w-full mt-4">
        {data.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-slate-500">
            No sales trend records found for active filters.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="colorOrders" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis
                dataKey="period"
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: "#334155" }}
              />
              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: "#334155" }}
                tickFormatter={activeConfig.format}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey={metric}
                stroke={activeConfig.color}
                strokeWidth={2.5}
                fillOpacity={1}
                fill={`url(#${activeConfig.gradient})`}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
