import React, { useState, useEffect } from "react";
import { Package, Search, Filter, Layers, DollarSign, ChevronLeft, ChevronRight, Tag } from "lucide-react";
import { listProducts, listCategories } from "../services/api";
import { formatCurrency } from "../utils/formatters";
import { SkeletonTable } from "../components/common/LoadingSkeleton";
import { ErrorState, EmptyState } from "../components/common/EmptyState";

export default function Products() {
  const [productsData, setProductsData] = useState({ items: [], total: 0, page: 1, size: 10, pages: 1 });
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCatalog = async () => {
    setLoading(true);
    setError(null);
    try {
      const [prodRes, catRes] = await Promise.all([
        listProducts({
          page,
          size: 10,
          category_id: selectedCategory !== "all" ? selectedCategory : undefined,
          search: search.trim() || undefined,
        }),
        listCategories(),
      ]);
      setProductsData(prodRes);
      setCategories(catRes || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to load product catalog.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalog();
  }, [page, selectedCategory]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchCatalog();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Package className="w-6 h-6 text-indigo-400" />
            Product Catalog & Merchandising
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Retail inventory SKUs, cost prices, selling margins, and merchandise hierarchy
          </p>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full font-mono bg-indigo-950/70 border border-indigo-700/60 text-indigo-300 self-start sm:self-auto">
          {productsData.total} Total SKUs
        </span>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 shadow-md flex flex-wrap items-center justify-between gap-3">
        {/* Category Dropdown */}
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-slate-400" />
          <select
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="all">All Departments ({categories.length})</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({Number(c.target_margin_pct)}% target)
              </option>
            ))}
          </select>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search product name or SKU..."
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

      {error && <ErrorState message={error} onRetry={fetchCatalog} />}

      {/* Catalog Table */}
      {loading ? (
        <SkeletonTable rows={10} />
      ) : productsData.items.length === 0 ? (
        <EmptyState title="No products found" description="Try selecting a different department or clearing the search text." />
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-semibold">SKU Code</th>
                  <th className="py-3 px-4 font-semibold">Product Name</th>
                  <th className="py-3 px-4 font-semibold">Department</th>
                  <th className="py-3 px-4 font-semibold">Brand</th>
                  <th className="py-3 px-4 font-semibold text-right">Selling Price</th>
                  <th className="py-3 px-4 font-semibold text-right">COGS</th>
                  <th className="py-3 px-4 font-semibold text-right">Gross Margin</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {productsData.items.map((prod) => {
                  const price = Number(prod.unit_price) || 0;
                  const cost = Number(prod.cost_price) || 0;
                  const marginPct = price > 0 ? ((price - cost) / price) * 100 : 0;
                  return (
                    <tr key={prod.id} className="hover:bg-slate-850/50 transition-colors">
                      <td className="py-3 px-4 font-mono font-semibold text-indigo-400">
                        {prod.sku_code}
                      </td>
                      <td className="py-3 px-4 font-medium text-white max-w-xs truncate">
                        {prod.product_name}
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {prod.category_name || "General"}
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-medium">
                        {prod.brand}
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-white">
                        {formatCurrency(prod.unit_price)}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-400">
                        {formatCurrency(prod.cost_price)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className="px-2 py-0.5 rounded-full font-bold text-[10px] bg-emerald-950/80 border border-emerald-700/60 text-emerald-400">
                          {marginPct.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing {productsData.items.length} of {productsData.total} products
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
                Page {page} of {productsData.pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(productsData.pages, p + 1))}
                disabled={page >= productsData.pages}
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
