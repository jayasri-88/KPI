import { useEffect, useState } from "react";
import { listStores } from "../services/api";

export default function Stores() {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [region, setRegion] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        setLoading(true);
        const data = await listStores(region ? { region, limit: 200 } : { limit: 200 });
        if (!cancelled) setStores(Array.isArray(data) ? data : []);
        if (!cancelled) setError(null);
      } catch (err) {
        console.error(err);
        if (!cancelled) setError("Unable to load stores.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [region]);

  const regions = [...new Set(stores.map((s) => s.region).filter(Boolean))].sort();

  return (
    <div>
      <div className="mb-8 flex items-end justify-between">
        <div>
          <p className="text-sm font-medium text-blue-600">RETAIL INTELLIGENCE</p>
          <h1 className="mt-1 text-3xl font-bold text-slate-900">Stores</h1>
          <p className="mt-2 text-sm text-slate-500">{stores.length} retailer locations</p>
        </div>
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
        >
          <option value="">All regions</option>
          {regions.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>

      {loading && <p className="text-slate-500">Loading stores…</p>}

      {error && (
        <div className="rounded-xl border border-red-200 bg-white p-8 text-center shadow-sm">
          <h2 className="text-lg font-semibold text-red-700">Stores unavailable</h2>
          <p className="mt-2 text-sm text-slate-500">{error}</p>
        </div>
      )}

      {!loading && !error && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-5 py-3">ID</th>
                <th className="px-5 py-3">Name</th>
                <th className="px-5 py-3">Type</th>
                <th className="px-5 py-3">City</th>
                <th className="px-5 py-3">Region</th>
                <th className="px-5 py-3 text-right">Size (sq ft)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {stores.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 text-slate-500">{s.retailer_id}</td>
                  <td className="px-5 py-3 font-medium text-slate-900">{s.retailer_name}</td>
                  <td className="px-5 py-3 text-slate-600">{s.store_type}</td>
                  <td className="px-5 py-3 text-slate-600">{s.city}</td>
                  <td className="px-5 py-3 text-slate-600">{s.region}</td>
                  <td className="px-5 py-3 text-right text-slate-600">
                    {Number(s.store_size_sqft).toLocaleString("en-IN")}
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
