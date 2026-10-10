import React from "react";
import { Filter, Calendar, Store, Layers, RotateCcw, RefreshCw } from "lucide-react";

export default function FilterBar({
  dateRange,
  onDateRangeChange,
  selectedStore,
  onStoreChange,
  stores = [],
  selectedCategory,
  onCategoryChange,
  categories = [],
  onRefresh,
  loading = false,
}) {
  const dateRanges = [
    { id: "7d", label: "Last 7 Days" },
    { id: "30d", label: "Last 30 Days" },
    { id: "90d", label: "Last 90 Days" },
    { id: "1y", label: "Last 12 Months" },
    { id: "all", label: "All Time" },
  ];

  const hasActiveFilters =
    dateRange !== "all" || selectedStore !== "all" || selectedCategory !== "all";

  const handleReset = () => {
    onDateRangeChange("all");
    onStoreChange("all");
    onCategoryChange("all");
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 shadow-md flex flex-wrap items-center justify-between gap-3">
      {/* Date Range Quick Selector */}
      <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800/80">
        <div className="px-2 py-1 text-slate-500 hidden sm:flex items-center gap-1.5 text-xs font-medium">
          <Calendar className="w-3.5 h-3.5 text-indigo-400" />
          <span>Period:</span>
        </div>
        {dateRanges.map((r) => (
          <button
            key={r.id}
            type="button"
            onClick={() => onDateRangeChange(r.id)}
            className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
              dateRange === r.id
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white hover:bg-slate-850"
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      {/* Filter Dropdowns & Refresh Controls */}
      <div className="flex items-center flex-wrap gap-2.5">
        {/* Store Dropdown */}
        <div className="relative">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs">
            <Store className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedStore}
              onChange={(e) => onStoreChange(e.target.value)}
              className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer pr-2"
            >
              <option value="all" className="bg-slate-900 text-slate-200">
                All Stores ({stores.length})
              </option>
              {stores.map((s) => (
                <option key={s.id} value={s.id} className="bg-slate-900 text-slate-200">
                  {s.name} ({s.city})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Category Dropdown */}
        <div className="relative">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs">
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedCategory}
              onChange={(e) => onCategoryChange(e.target.value)}
              className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer pr-2"
            >
              <option value="all" className="bg-slate-900 text-slate-200">
                All Departments ({categories.length})
              </option>
              {categories.map((c) => (
                <option key={c.id} value={c.id} className="bg-slate-900 text-slate-200">
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Reset Filters */}
        {hasActiveFilters && (
          <button
            onClick={handleReset}
            title="Reset active filters"
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3 h-3" />
            <span className="hidden sm:inline">Reset</span>
          </button>
        )}

        {/* Refresh Action */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={loading}
            title="Refresh analytics data"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 rounded-lg text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        )}
      </div>
    </div>
  );
}
