import { useEffect, useState } from "react";
import { listCustomers } from "../services/api";

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        setLoading(true);
        const data = await listCustomers({ limit: 100 });
        if (!cancelled) setCustomers(Array.isArray(data) ? data : []);
        if (!cancelled) setError(null);
      } catch (err) {
        console.error(err);
        if (!cancelled) setError("Unable to load customers.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-medium text-blue-600">RETAIL INTELLIGENCE</p>
        <h1 className="mt-1 text-3xl font-bold text-slate-900">Customers</h1>
        <p className="mt-2 text-sm text-slate-500">{customers.length} customers</p>
      </div>

      {loading && <p className="text-slate-500">Loading customers…</p>}

      {error && (
        <div className="rounded-xl border border-red-200 bg-white p-8 text-center shadow-sm">
          <h2 className="text-lg font-semibold text-red-700">Customers unavailable</h2>
          <p className="mt-2 text-sm text-slate-500">{error}</p>
        </div>
      )}

      {!loading && !error && customers.length === 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">No customers yet</h2>
          <p className="mt-2 text-sm text-slate-500">
            The source datasets contain no customer dimension, so this table is empty
            until customer data is ingested in a future commit.
          </p>
        </div>
      )}

      {!loading && !error && customers.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-5 py-3">Name</th>
                <th className="px-5 py-3">Email</th>
                <th className="px-5 py-3">City</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {customers.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-medium text-slate-900">
                    {c.first_name} {c.last_name}
                  </td>
                  <td className="px-5 py-3 text-slate-600">{c.email}</td>
                  <td className="px-5 py-3 text-slate-600">{c.city || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
