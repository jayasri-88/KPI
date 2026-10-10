import React, { useState, useEffect } from "react";
import { Users, Search, Award, Crown, Clock, ArrowUpDown, ChevronLeft, ChevronRight, Mail, Phone } from "lucide-react";
import { listCustomers } from "../services/api";
import { formatCurrency, formatDate } from "../utils/formatters";
import { SkeletonTable } from "../components/common/LoadingSkeleton";
import { ErrorState, EmptyState } from "../components/common/EmptyState";

export default function Customers() {
  const [customersData, setCustomersData] = useState({ items: [], total: 0, page: 1, size: 10, pages: 1 });
  const [segmentFilter, setSegmentFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState("total_spend");
  const [sortDesc, setSortDesc] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCustomers = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listCustomers({
        page,
        size: 10,
        segment: segmentFilter !== "all" ? segmentFilter : undefined,
        search: search.trim() || undefined,
        sort_by: sortBy,
        sort_desc: sortDesc,
      });
      setCustomersData(res);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to load customer profiles.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [page, segmentFilter, sortBy, sortDesc]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchCustomers();
  };

  const segments = ["all", "VIP", "Regular", "New", "At-Risk"];

  const getSegmentBadge = (segment) => {
    switch (segment) {
      case "VIP":
        return "bg-amber-950/80 border-amber-600/70 text-amber-300 font-extrabold";
      case "Regular":
        return "bg-indigo-950/80 border-indigo-600/60 text-indigo-300";
      case "New":
        return "bg-emerald-950/80 border-emerald-600/60 text-emerald-300";
      case "At-Risk":
        return "bg-rose-950/80 border-rose-600/60 text-rose-300";
      default:
        return "bg-slate-800 text-slate-300";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-indigo-400" />
            Customer Demographics & Cohorts
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Shopper lifetime value (LTV), transaction counts, and behavioral segmentation
          </p>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full font-mono bg-indigo-950/70 border border-indigo-700/60 text-indigo-300 self-start sm:self-auto">
          {customersData.total} Profiles Active
        </span>
      </div>

      {/* Cohort Tabs and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 shadow-md flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-400 font-medium px-1">Cohort:</span>
          {segments.map((seg) => (
            <button
              key={seg}
              onClick={() => {
                setSegmentFilter(seg);
                setPage(1);
              }}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                segmentFilter === seg
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              {seg === "all" ? "All Shoppers" : seg}
            </button>
          ))}
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search customer name or email..."
              className="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer"
          >
            Filter
          </button>
        </form>
      </div>

      {error && <ErrorState message={error} onRetry={fetchCustomers} />}

      {/* Customers Table */}
      {loading ? (
        <SkeletonTable rows={10} />
      ) : customersData.items.length === 0 ? (
        <EmptyState title="No customer profiles found" description="Try selecting a different cohort or resetting search." />
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-semibold">Customer</th>
                  <th className="py-3 px-4 font-semibold">Contact & Location</th>
                  <th className="py-3 px-4 font-semibold text-center">Segment</th>
                  <th className="py-3 px-4 font-semibold text-center">Orders</th>
                  <th className="py-3 px-4 font-semibold text-right">Lifetime Spend</th>
                  <th className="py-3 px-4 font-semibold text-right">Last Purchase</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {customersData.items.map((cust) => (
                  <tr key={cust.id} className="hover:bg-slate-850/50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-white">
                        {cust.first_name} {cust.last_name}
                      </div>
                      <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                        <Mail className="w-3 h-3 text-slate-500" />
                        <span>{cust.email}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      <div>{cust.city || "Urban Metro"}, {cust.state || "India"}</div>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                        <Phone className="w-3 h-3" />
                        <span>{cust.phone || "Verified"}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] uppercase font-bold border ${getSegmentBadge(
                          cust.segment
                        )}`}
                      >
                        {cust.segment}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-bold text-slate-200">
                      {cust.total_orders_count}
                    </td>
                    <td className="py-3 px-4 text-right font-extrabold text-emerald-400">
                      {formatCurrency(cust.total_spend)}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">
                      {formatDate(cust.last_order_date)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing {customersData.items.length} of {customersData.total} customers
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
                Page {page} of {customersData.pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(customersData.pages, p + 1))}
                disabled={page >= customersData.pages}
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
