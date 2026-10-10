import React, { useState, useEffect } from "react";
import { TrendingUp, DollarSign, Layers, ChevronLeft, ChevronRight, ShoppingBag, Filter } from "lucide-react";
import { listSales, getSalesSummary } from "../services/api";
import { formatCurrency, formatDate } from "../utils/formatters";
import MetricCard from "../components/dashboard/MetricCard";
import { SkeletonCard, SkeletonTable } from "../components/common/LoadingSkeleton";
import { ErrorState, EmptyState } from "../components/common/EmptyState";

export default function Sales() {
  const [salesData, setSalesData] = useState({ items: [], total: 0, page: 1, size: 10, pages: 1 });
  const [summary, setSummary] = useState(null);
  const [channel, setChannel] = useState("all");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSales = async () => {
    setLoading(true);
    setError(null);
    try {
      const [salesRes, summaryRes] = await Promise.all([
        listSales({
          page,
          size: 10,
          channel: channel !== "all" ? channel : undefined,
        }),
        getSalesSummary(),
      ]);
      setSalesData(salesRes);
      setSummary(summaryRes);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to load sales ledger.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSales();
  }, [page, channel]);

  const channels = ["all", "In-Store", "Online", "Express Delivery"];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-indigo-400" />
            Financial Sales & Margins Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Itemized transactional revenue, Cost of Goods Sold (COGS), and gross margins
          </p>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full font-mono bg-indigo-950/70 border border-indigo-700/60 text-indigo-300 self-start sm:self-auto">
          {salesData.total} Ledger Entries
        </span>
      </div>

      {/* Financial Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Consolidated Net Revenue"
            value={formatCurrency(summary.total_revenue, { compact: true })}
            subtitle={`Across ${summary.total_orders.toLocaleString()} orders`}
            icon={DollarSign}
            iconColor="text-indigo-400"
            iconBg="bg-indigo-500/10 border-indigo-500/20"
          />
          <MetricCard
            title="Cost of Goods Sold (COGS)"
            value={formatCurrency(summary.total_cogs, { compact: true })}
            subtitle="Wholesale product costs"
            icon={Layers}
            iconColor="text-amber-400"
            iconBg="bg-amber-500/10 border-amber-500/20"
          />
          <MetricCard
            title="Total Gross Profit"
            value={formatCurrency(summary.total_profit, { compact: true })}
            subtitle="Revenue minus COGS"
            icon={TrendingUp}
            iconColor="text-emerald-400"
            iconBg="bg-emerald-500/10 border-emerald-500/20"
          />
          <MetricCard
            title="Average Gross Margin"
            value={`${Number(summary.margin_pct).toFixed(1)}%`}
            subtitle="Profit / Revenue percentage"
            icon={ShoppingBag}
            iconColor="text-purple-400"
            iconBg="bg-purple-500/10 border-purple-500/20"
          />
        </div>
      )}

      {/* Channel Filters */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 shadow-md flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-400 font-medium px-1">Channel:</span>
          {channels.map((ch) => (
            <button
              key={ch}
              onClick={() => {
                setChannel(ch);
                setPage(1);
              }}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                channel === ch
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              {ch === "all" ? "All Channels" : ch}
            </button>
          ))}
        </div>
      </div>

      {error && <ErrorState message={error} onRetry={fetchSales} />}

      {/* Sales Table */}
      {loading ? (
        <SkeletonTable rows={10} />
      ) : salesData.items.length === 0 ? (
        <EmptyState title="No sales records found" description="No sales transactions match the selected channel filter." />
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-semibold">Sale Date</th>
                  <th className="py-3 px-4 font-semibold">Store Location</th>
                  <th className="py-3 px-4 font-semibold">Product SKU</th>
                  <th className="py-3 px-4 font-semibold text-center">Channel</th>
                  <th className="py-3 px-4 font-semibold text-center">Qty</th>
                  <th className="py-3 px-4 font-semibold text-right">Revenue</th>
                  <th className="py-3 px-4 font-semibold text-right">COGS</th>
                  <th className="py-3 px-4 font-semibold text-right">Gross Profit</th>
                  <th className="py-3 px-4 font-semibold text-right">Margin</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {salesData.items.map((sale) => (
                  <tr key={sale.id} className="hover:bg-slate-850/50 transition-colors">
                    <td className="py-3 px-4 text-slate-300 whitespace-nowrap">
                      {formatDate(sale.sale_date)}
                    </td>
                    <td className="py-3 px-4 font-medium text-white max-w-[160px] truncate">
                      {sale.store_name}
                    </td>
                    <td className="py-3 px-4">
                      <div className="text-white truncate max-w-[160px]">{sale.product_name}</div>
                      <div className="font-mono text-[10px] text-indigo-400">{sale.sku_code}</div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                        {sale.channel}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-bold text-slate-200">
                      {sale.quantity}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-white">
                      {formatCurrency(sale.revenue)}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">
                      {formatCurrency(sale.cogs)}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-emerald-400">
                      {formatCurrency(sale.gross_profit)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="px-2 py-0.5 rounded-full font-bold text-[10px] bg-emerald-950/80 border border-emerald-700/60 text-emerald-400">
                        {Number(sale.margin_pct).toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing {salesData.items.length} of {salesData.total} transactions
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-200"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-2 font-medium text-slate-300">
                Page {page} of {salesData.pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(salesData.pages, p + 1))}
                disabled={page >= salesData.pages}
                className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-200"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
