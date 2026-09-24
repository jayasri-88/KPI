import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  getSalesTrend,
  getCategoryPerformance,
  getRegionPerformance,
  getSkuPerformance,
} from "../services/api";

function inr(value) {
  return `₹${Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export default function Analytics() {
  const [trend, setTrend] = useState([]);
  const [categories, setCategories] = useState([]);
  const [regions, setRegions] = useState([]);
  const [skus, setSkus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        setLoading(true);
        const [t, c, r, s] = await Promise.all([
          getSalesTrend(),
          getCategoryPerformance(),
          getRegionPerformance(),
          getSkuPerformance(),
        ]);
        if (cancelled) return;
        setTrend(t.data || []);
        setCategories(c.data || []);
        setRegions(r.data || []);
        setSkus(s.data || []);
        setError(null);
      } catch (err) {
        console.error(err);
        if (!cancelled) setError("Unable to load analytics data.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <p className="text-slate-500">Loading analytics…</p>;
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-white p-8 text-center shadow-sm">
        <h2 className="text-lg font-semibold text-red-700">Analytics unavailable</h2>
        <p className="mt-2 text-sm text-slate-500">{error}</p>
      </div>
    );
  }

  const totalRevenue = trend.reduce((sum, m) => sum + Number(m.revenue || 0), 0);

  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-medium text-blue-600">RETAIL INTELLIGENCE</p>
        <h1 className="mt-1 text-3xl font-bold text-slate-900">Analytics</h1>
        <p className="mt-2 text-sm text-slate-500">
          Monthly, category, regional and SKU-level performance
        </p>
      </div>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Months covered</p>
          <p className="mt-2 text-2xl font-bold text-slate-900">{trend.length}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Total revenue</p>
          <p className="mt-2 text-2xl font-bold text-slate-900">{inr(totalRevenue)}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Products tracked</p>
          <p className="mt-2 text-2xl font-bold text-slate-900">{skus.length}</p>
        </div>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Monthly Revenue</h2>
          <p className="mb-5 text-sm text-slate-500">Fact table aggregates by month</p>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(v) => inr(v)} />
                <Line type="monotone" dataKey="revenue" stroke="#2563eb" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Category Performance</h2>
          <p className="mb-5 text-sm text-slate-500">Revenue by product category</p>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categories}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip formatter={(v) => inr(v)} />
                <Bar dataKey="revenue" fill="#0f766e" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="mt-6">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Region Performance</h2>
          <p className="mb-5 text-sm text-slate-500">Revenue by region</p>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={regions}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="region" />
                <YAxis />
                <Tooltip formatter={(v) => inr(v)} />
                <Bar dataKey="revenue" fill="#2563eb" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="mt-6 rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="p-5">
          <h2 className="text-lg font-semibold text-slate-900">SKU Performance</h2>
          <p className="text-sm text-slate-500">All {skus.length} products, ranked by revenue</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-5 py-3">SKU</th>
                <th className="px-5 py-3">Product</th>
                <th className="px-5 py-3">Category</th>
                <th className="px-5 py-3 text-right">Revenue</th>
                <th className="px-5 py-3 text-right">Units</th>
                <th className="px-5 py-3 text-right">Profit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {skus.map((s) => (
                <tr key={s.product_id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-mono text-xs text-slate-600">{s.sku_code}</td>
                  <td className="px-5 py-3 text-slate-900">{s.product_name}</td>
                  <td className="px-5 py-3 text-slate-600">{s.category}</td>
                  <td className="px-5 py-3 text-right text-slate-900">{inr(s.revenue)}</td>
                  <td className="px-5 py-3 text-right text-slate-600">
                    {Number(s.units).toLocaleString("en-IN")}
                  </td>
                  <td className="px-5 py-3 text-right text-slate-900">{inr(s.profit)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
