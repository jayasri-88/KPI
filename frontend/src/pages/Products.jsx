import { useEffect, useState } from "react";
import { listProducts } from "../services/api";

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(() => {
      async function load() {
        try {
          setLoading(true);
          const params = { limit: 200 };
          if (search) params.search = search;
          const data = await listProducts(params);
          if (!cancelled) setProducts(Array.isArray(data) ? data : []);
          if (!cancelled) setError(null);
        } catch (err) {
          console.error(err);
          if (!cancelled) setError("Unable to load products.");
        } finally {
          if (!cancelled) setLoading(false);
        }
      }
      load();
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [search]);

  return (
    <div>
      <div className="mb-8 flex items-end justify-between">
        <div>
          <p className="text-sm font-medium text-blue-600">RETAIL INTELLIGENCE</p>
          <h1 className="mt-1 text-3xl font-bold text-slate-900">Products</h1>
          <p className="mt-2 text-sm text-slate-500">{products.length} SKUs</p>
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search name or SKU…"
          className="w-64 rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
      </div>

      {loading && <p className="text-slate-500">Loading products…</p>}

      {error && (
        <div className="rounded-xl border border-red-200 bg-white p-8 text-center shadow-sm">
          <h2 className="text-lg font-semibold text-red-700">Products unavailable</h2>
          <p className="mt-2 text-sm text-slate-500">{error}</p>
        </div>
      )}

      {!loading && !error && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-5 py-3">SKU</th>
                <th className="px-5 py-3">Name</th>
                <th className="px-5 py-3">Brand</th>
                <th className="px-5 py-3 text-right">Unit price</th>
                <th className="px-5 py-3 text-right">Cost price</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {products.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-mono text-xs text-slate-600">{p.sku_code}</td>
                  <td className="px-5 py-3 font-medium text-slate-900">{p.product_name}</td>
                  <td className="px-5 py-3 text-slate-600">{p.brand || "—"}</td>
                  <td className="px-5 py-3 text-right text-slate-900">
                    ₹{Number(p.unit_price).toLocaleString("en-IN")}
                  </td>
                  <td className="px-5 py-3 text-right text-slate-600">
                    ₹{Number(p.cost_price).toLocaleString("en-IN")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
