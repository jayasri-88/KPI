import { useEffect, useState } from "react";
import { getInventorySummary, getInventoryAlerts } from "../services/api";

export default function Inventory() {
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        setLoading(true);
        const [s, a] = await Promise.all([getInventorySummary(), getInventoryAlerts()]);
        if (cancelled) return;
        setSummary(s);
        setAlerts(a.data || []);
        setError(null);
      } catch (err) {
        console.error(err);
        if (!cancelled) setError("Unable to load inventory data.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <p className="text-slate-500">Loading inventory…</p>;

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-white p-8 text-center shadow-sm">
        <h2 className="text-lg font-semibold text-red-700">Inventory unavailable</h2>
        <p className="mt-2 text-sm text-slate-500">{error}</p>
      </div>
    );
  }

  const stats = [
    { label: "Tracked records", value: Number(summary?.total_records || 0).toLocaleString("en-IN") },
    { label: "Critical (out of stock)", value: summary?.critical_alerts ?? 0 },
    { label: "High (≤50% reorder point)", value: summary?.high_alerts ?? 0 },
    { label: "Warning (≤100% reorder point)", value: summary?.warning_alerts ?? 0 },
  ];

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-medium text-blue-600">RETAIL INTELLIGENCE</p>
        <h1 className="mt-1 text-3xl font-bold text-slate-900">Inventory</h1>
        <p className="mt-2 text-sm text-slate-500">
          Current stock position across all retailers
        </p>
      </div>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map(({ label, value }) => (
          <div key={label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">{label}</p>
            <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
          </div>
        ))}
      </section>

      <section className="mt-6 rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="p-5">
          <h2 className="text-lg font-semibold text-slate-900">Stock Alerts</h2>
          <p className="text-sm text-slate-500">
            {alerts.length === 0
              ? "No items below reorder point in the latest snapshots"
              : `${alerts.length} items need attention`}
          </p>
        </div>
        {alerts.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-5 py-3">Product</th>
                  <th className="px-5 py-3">Store</th>
                  <th className="px-5 py-3 text-right">On hand</th>
                  <th className="px-5 py-3 text-right">Reorder point</th>
                  <th className="px-5 py-3">Severity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {alerts.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50">
                    <td className="px-5 py-3 text-slate-900">{a.product_name || a.sku_code || a.product_id}</td>
                    <td className="px-5 py-3 text-slate-600">{a.retailer_name || a.retailer_id}</td>
                    <td className="px-5 py-3 text-right text-slate-900">{a.quantity_on_hand}</td>
                    <td className="px-5 py-3 text-right text-slate-600">{a.reorder_point}</td>
                    <td className="px-5 py-3">
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                        {a.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
