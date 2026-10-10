import React, { useState, useEffect } from "react";
import { Archive, AlertTriangle, CheckCircle2, XCircle, Search, RefreshCw, ChevronLeft, ChevronRight, PlusCircle } from "lucide-react";
import { listInventory, getInventoryAlerts, restockInventoryItem } from "../services/api";
import { formatDate } from "../utils/formatters";
import { SkeletonTable } from "../components/common/LoadingSkeleton";
import { ErrorState, EmptyState } from "../components/common/EmptyState";

export default function Inventory() {
  const [inventoryData, setInventoryData] = useState({ items: [], total: 0, page: 1, size: 10, pages: 1 });
  const [alerts, setAlerts] = useState([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [restockingId, setRestockingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchInventory = async () => {
    setLoading(true);
    setError(null);
    try {
      const [invRes, alertRes] = await Promise.all([
        listInventory({
          page,
          size: 10,
          stock_status: statusFilter !== "all" ? statusFilter : undefined,
          search: search.trim() || undefined,
        }),
        getInventoryAlerts(),
      ]);
      setInventoryData(invRes);
      setAlerts(alertRes || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to load inventory.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, [page, statusFilter]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchInventory();
  };

  const handleQuickRestock = async (inventoryId, reorderQty = 50) => {
    setRestockingId(inventoryId);
    try {
      await restockInventoryItem(inventoryId, reorderQty);
      await fetchInventory();
    } catch (err) {
      alert("Failed to restock inventory item: " + (err.response?.data?.detail || err.message));
    } finally {
      setRestockingId(null);
    }
  };

  const statuses = [
    { id: "all", label: "All Items" },
    { id: "Low Stock", label: "Low Stock Alert" },
    { id: "In Stock", label: "Adequate Stock" },
    { id: "Out of Stock", label: "Depleted (0)" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Archive className="w-6 h-6 text-indigo-400" />
            Multi-Store Inventory & Replenishment
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Store-level stock buffers, on-hand counts, and automated reorder threshold monitoring
          </p>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full font-mono bg-indigo-950/70 border border-indigo-700/60 text-indigo-300 self-start sm:self-auto">
          {inventoryData.total} Stock Keeping Points
        </span>
      </div>

      {/* Critical Stock Replenishment Alerts Banner */}
      {alerts.length > 0 && (
        <div className="bg-amber-950/40 border border-amber-600/60 rounded-xl p-4 shadow-md">
          <div className="flex items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 animate-pulse" />
              <h3 className="text-xs font-bold text-amber-300 uppercase tracking-wider">
                {alerts.length} Low-Stock Replenishment Triggers Detected
              </h3>
            </div>
            <span className="text-[11px] text-amber-400 font-medium">
              Immediate Reorder Recommended
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 mt-3">
            {alerts.slice(0, 3).map((al) => (
              <div
                key={al.inventory_id}
                className="p-3 bg-slate-900/90 rounded-lg border border-amber-600/40 flex items-center justify-between gap-2 text-xs"
              >
                <div className="min-w-0">
                  <div className="font-semibold text-white truncate max-w-[150px]">
                    {al.product_name}
                  </div>
                  <div className="text-[11px] text-slate-400 truncate max-w-[150px]">
                    {al.store_name}
                  </div>
                  <div className="text-[10px] text-amber-400 font-medium mt-0.5">
                    Available: {al.quantity_available} / Reorder Point: {al.reorder_point}
                  </div>
                </div>

                <button
                  onClick={() => handleQuickRestock(al.inventory_id, al.reorder_quantity)}
                  disabled={restockingId === al.inventory_id}
                  className="px-2.5 py-1 bg-amber-500/20 hover:bg-amber-500 text-amber-300 hover:text-slate-950 font-bold rounded text-[11px] border border-amber-500/40 transition-all flex-shrink-0 cursor-pointer disabled:opacity-50"
                >
                  {restockingId === al.inventory_id ? "Adding..." : `+${al.reorder_quantity}`}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 shadow-md flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 flex-wrap">
          {statuses.map((st) => (
            <button
              key={st.id}
              onClick={() => {
                setStatusFilter(st.id);
                setPage(1);
              }}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                statusFilter === st.id
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              {st.label}
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
              placeholder="Search product SKU or store..."
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

      {error && <ErrorState message={error} onRetry={fetchInventory} />}

      {/* Inventory Table */}
      {loading ? (
        <SkeletonTable rows={10} />
      ) : inventoryData.items.length === 0 ? (
        <EmptyState title="No inventory positions found" description="Try selecting a different stock filter or clearing search." />
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-semibold">Store Location</th>
                  <th className="py-3 px-4 font-semibold">SKU & Product</th>
                  <th className="py-3 px-4 font-semibold text-center">Available Stock</th>
                  <th className="py-3 px-4 font-semibold text-center">Reserved</th>
                  <th className="py-3 px-4 font-semibold text-center">On Hand</th>
                  <th className="py-3 px-4 font-semibold text-center">Reorder Point</th>
                  <th className="py-3 px-4 font-semibold text-center">Status</th>
                  <th className="py-3 px-4 font-semibold text-right">Quick Restock</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {inventoryData.items.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-850/50 transition-colors">
                    <td className="py-3 px-4 font-medium text-white max-w-[160px] truncate">
                      {inv.store_name}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-200 truncate max-w-[180px]">
                        {inv.product_name}
                      </div>
                      <div className="font-mono text-[10px] text-indigo-400">
                        {inv.sku_code}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center font-extrabold text-sm text-white">
                      {inv.quantity_available}
                    </td>
                    <td className="py-3 px-4 text-center text-slate-400">
                      {inv.quantity_reserved}
                    </td>
                    <td className="py-3 px-4 text-center text-slate-300">
                      {inv.quantity_on_hand}
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-slate-400">
                      {inv.reorder_point}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          inv.stock_status === "In Stock"
                            ? "bg-emerald-950/70 border-emerald-700/60 text-emerald-400"
                            : inv.stock_status === "Low Stock"
                            ? "bg-amber-950/70 border-amber-700/60 text-amber-400"
                            : "bg-rose-950/70 border-rose-700/60 text-rose-400"
                        }`}
                      >
                        {inv.stock_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleQuickRestock(inv.id, inv.reorder_quantity)}
                        disabled={restockingId === inv.id}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-indigo-600 text-slate-300 hover:text-white border border-slate-700 text-[11px] font-semibold transition-all cursor-pointer disabled:opacity-50"
                      >
                        {restockingId === inv.id ? "Adding..." : `+${inv.reorder_quantity}`}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing {inventoryData.items.length} of {inventoryData.total} positions
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
                Page {page} of {inventoryData.pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(inventoryData.pages, p + 1))}
                disabled={page >= inventoryData.pages}
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
