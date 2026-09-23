import { Link } from "react-router-dom";

export default function Forecast() {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
      <p className="text-sm font-medium text-blue-600">RETAIL INTELLIGENCE</p>
      <h1 className="mt-1 text-3xl font-bold text-slate-900">Forecast</h1>
      <p className="mt-3 text-sm text-slate-500">
        This page is a placeholder. Forecasting functionality will be
        implemented in a later commit.
      </p>
      <Link
        to="/dashboard"
        className="mt-6 inline-block rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-600 transition-colors hover:bg-slate-100"
      >
        Back to Dashboard
      </Link>
    </section>
  );
}
