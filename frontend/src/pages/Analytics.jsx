import React, { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  BarChart3,
  TrendingUp,
  Package,
  Layers,
  Award,
  Filter,
  DollarSign,
  ShoppingBag,
} from "lucide-react";
import {
  getDemandAnalytics,
  getProductPerformanceAnalytics,
  getSalesTrendAnalytics,
} from "../services/api";
import { formatCurrency, formatPercent } from "../utils/formatters";
import { SkeletonCard, SkeletonTable } from "../components/common/LoadingSkeleton";
import { ErrorState } from "../components/common/EmptyState";

const PARETO_COLORS = {
  "Class A (Top 80%)": "#10b981", // Emerald
  "Class B (80-95%)": "#6366f1",  // Indigo
  "Class C (Tail 5%)": "#f59e0b",  // Amber
};

export default function Analytics() {
  const [demandData, setDemandData] = useState(null);
  const [productData, setProductData] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [paretoFilter, setParetoFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [demandRes, prodRes, trendRes] = await Promise.all([
        getDemandAnalytics(),
        getProductPerformanceAnalytics({ limit: 100 }),
        getSalesTrendAnalytics({ days: 90 }),
      ]);
      setDemandData(demandRes);
      setProductData(prodRes);
      setTrendData(trendRes);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to load analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredProducts = (productData?.products || []).filter((p) => {
    if (paretoFilter === "all") return true;
    return p.pareto_class.includes(paretoFilter);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center shadow-inner">
              <BarChart3 className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Merchandise Demand & Pareto 80/20 Intelligence
              </h1>
              <p className="text-xs text-slate-400">
                Cross-category demand velocity, SKU concentration curves, and revenue contribution analysis
              </p>
            </div>
          </div>
        </div>

        {/* Global Summary Badge */}
        <div className="flex items-center gap-3">
          <span className="text-xs px-3 py-1.5 rounded-xl font-mono bg-indigo-950/70 border border-indigo-700/60 text-indigo-300">
            {productData?.total_skus_analyzed || 0} SKUs Evaluated
          </span>
        </div>
      </div>

      {error && <ErrorState message={error} onRetry={fetchData} />}

      {/* Demand & Category Volume Velocity */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Category Demand Velocity (7 cols) */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-md">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
              <Package className="w-4 h-4 text-indigo-400" />
              <span>Category Demand Velocity & Revenue Contribution</span>
            </h3>
            <span className="text-[10px] text-slate-400">Units & Gross Sales</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={demandData?.categories || []} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="category_name" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} tickFormatter={(val) => `₹${(val / 100000).toFixed(0)}L`} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const d = payload[0].payload;
                    return (
                      <div className="bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white">
                        <p className="font-bold text-indigo-300">{d.category_name} ({d.category_code})</p>
                        <p className="text-white mt-1">Revenue: {formatCurrency(d.total_revenue)}</p>
                        <p className="text-slate-400">Units Sold: {d.total_units_sold} units</p>
                        <p className="text-emerald-400">Share: {d.revenue_share_pct}% of total</p>
                        <p className="text-slate-400">Avg Selling Price: {formatCurrency(d.avg_selling_price)}</p>
                      </div>
                    );
                  }}
                />
                <Bar dataKey="total_revenue" fill="#6366f1" radius={[6, 6, 0, 0]} name="Total Revenue" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Pareto 80/20 Concentration Ribbon (5 cols) */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                <Award className="w-4 h-4 text-amber-400" />
                <span>Pareto 80/20 ABC SKU Distribution</span>
              </h3>
              <span className="text-[10px] text-slate-400">Concentration Law</span>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Identifies the critical 20% of merchandise lines generating 80% of top-line revenue for inventory priority.
            </p>

            <div className="space-y-3">
              {Object.entries(productData?.pareto_summary || {}).map(([pClass, count]) => {
                const total = productData?.total_skus_analyzed || 1;
                const pct = ((count / total) * 100).toFixed(0);
                const color = PARETO_COLORS[pClass] || "#6366f1";
                return (
                  <div key={pClass} className="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                    <div className="flex justify-between items-center text-xs mb-1">
                      <span className="font-bold text-white flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                        <span>{pClass}</span>
                      </span>
                      <span className="font-mono text-slate-400">
                        {count} SKUs ({pct}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="h-1.5 rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, backgroundColor: color }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="p-3 bg-indigo-950/40 border border-indigo-700/40 rounded-xl mt-4 text-[11px] text-indigo-300">
            <strong>Executive Takeaway:</strong> Protect Class A SKUs from out-of-stock events to safeguard 80% of company revenues.
          </div>
        </div>
      </div>

      {/* SKU Performance Table with Pareto Filter */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-md space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>SKU Revenue, Margin & Cumulative Contribution Ranking</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Ranked descending by revenue with cumulative percentage trajectory
            </p>
          </div>

          {/* Pareto Filter Tabs */}
          <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded-lg p-1 text-xs">
            <button
              onClick={() => setParetoFilter("all")}
              className={`px-2.5 py-1 rounded-md transition ${
                paretoFilter === "all" ? "bg-indigo-600 text-white font-semibold" : "text-slate-400 hover:text-white"
              }`}
            >
              All SKUs
            </button>
            <button
              onClick={() => setParetoFilter("Class A")}
              className={`px-2.5 py-1 rounded-md transition ${
                paretoFilter === "Class A" ? "bg-emerald-600 text-white font-semibold" : "text-slate-400 hover:text-white"
              }`}
            >
              Class A (Top 80%)
            </button>
            <button
              onClick={() => setParetoFilter("Class B")}
              className={`px-2.5 py-1 rounded-md transition ${
                paretoFilter === "Class B" ? "bg-indigo-600 text-white font-semibold" : "text-slate-400 hover:text-white"
              }`}
            >
              Class B (80-95%)
            </button>
            <button
              onClick={() => setParetoFilter("Class C")}
              className={`px-2.5 py-1 rounded-md transition ${
                paretoFilter === "Class C" ? "bg-amber-600 text-white font-semibold" : "text-slate-400 hover:text-white"
              }`}
            >
              Class C (Tail 5%)
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">SKU Code</th>
                <th className="py-2.5 px-3">Product Name</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3 text-right">Units Sold</th>
                <th className="py-2.5 px-3 text-right">Total Revenue</th>
                <th className="py-2.5 px-3 text-right">Gross Profit</th>
                <th className="py-2.5 px-3 text-right">Margin %</th>
                <th className="py-2.5 px-3 text-right">Cumulative %</th>
                <th className="py-2.5 px-3 text-center">Pareto Class</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {filteredProducts.map((p) => (
                <tr key={p.product_id} className="hover:bg-slate-850/60 transition">
                  <td className="py-2.5 px-3 font-mono font-bold text-indigo-400">{p.sku_code}</td>
                  <td className="py-2.5 px-3 font-semibold text-white truncate max-w-[200px]">{p.product_name}</td>
                  <td className="py-2.5 px-3 text-slate-400">{p.category_name}</td>
                  <td className="py-2.5 px-3 text-right font-medium">{p.units_sold.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-right font-extrabold text-white">{formatCurrency(p.total_revenue)}</td>
                  <td className="py-2.5 px-3 text-right font-bold text-emerald-400">{formatCurrency(p.total_profit)}</td>
                  <td className="py-2.5 px-3 text-right text-emerald-400 font-semibold">{p.margin_pct.toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-400">{p.cumulative_revenue_pct.toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-center">
                    <span
                      className="px-2 py-0.5 rounded-full text-[10px] font-bold"
                      style={{
                        backgroundColor: `${PARETO_COLORS[p.pareto_class] || "#6366f1"}20`,
                        color: PARETO_COLORS[p.pareto_class] || "#6366f1",
                        border: `1px solid ${PARETO_COLORS[p.pareto_class] || "#6366f1"}40`,
                      }}
                    >
                      {p.pareto_class}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
