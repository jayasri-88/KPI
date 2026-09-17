import { useEffect, useState } from "react";
import SkuIntelligence from "../components/SkuIntelligence";
import MetricCard from "../components/MetricCard";
import SalesChart from "../components/SalesChart";
import RegionChart from "../components/RegionChart";
import CategoryChart from "../components/CategoryChart";
import InventoryAlerts from "../components/InventoryAlerts";

import {
  getDashboardOverview,
  getSalesTrend,
  getRegionPerformance,
  getCategoryPerformance,
  getInventorySummary,
  getSkuIntelligence,
  getInventoryAlerts,
} from "../services/api";


function formatCurrency(value) {
  return `₹${Number(value || 0).toLocaleString(
    "en-IN",
    {
      maximumFractionDigits: 0,
    }
  )}`;
}


export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [salesTrend, setSalesTrend] = useState([]);
  const [regions, setRegions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [inventorySummary, setInventorySummary] =
    useState(null);
  const [inventoryAlerts, setInventoryAlerts] =
    useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [skuIntelligence, setSkuIntelligence] =
  useState(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);

        const [
          overviewResponse,
          salesResponse,
          regionResponse,
          categoryResponse,
          inventorySummaryResponse,
          inventoryAlertsResponse,
        ] = await Promise.all([
          getDashboardOverview(),
          getSalesTrend(),
          getRegionPerformance(),
          getCategoryPerformance(),
          getInventorySummary(),
          getInventoryAlerts(),
        ]);

        setOverview(overviewResponse);

        setSalesTrend(
          salesResponse.data || []
        );

        setRegions(
          regionResponse.data || []
        );

        setCategories(
          categoryResponse.data || []
        );

        setInventorySummary(
          inventorySummaryResponse
        );

        setInventoryAlerts(
          inventoryAlertsResponse.data || []
        );

        setError(null);
      } catch (err) {
        console.error(err);

        setError(
          "Unable to connect to the Retail Intelligence API."
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);


  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-500">
          Loading retail intelligence...
        </p>
      </div>
    );
  }


  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="rounded-xl border border-red-200 bg-white p-8 text-center shadow-sm">
          <h1 className="text-lg font-semibold text-red-700">
            Backend connection failed
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            {error}
          </p>
        </div>
      </div>
    );
  }


  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-6 py-8">

        <div className="mb-8">
          <p className="text-sm font-medium text-blue-600">
            RETAIL INTELLIGENCE
          </p>

          <h1 className="mt-1 text-3xl font-bold text-slate-900">
            Executive Dashboard
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Sales, inventory, regional and category
            intelligence
          </p>
        </div>


        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">

          <MetricCard
            title="Total Revenue"
            value={formatCurrency(
              overview?.total_revenue
            )}
            subtitle="All recorded transactions"
          />

          <MetricCard
            title="Units Sold"
            value={Number(
              overview?.total_units || 0
            ).toLocaleString("en-IN")}
            subtitle="Total quantity sold"
          />

          <MetricCard
            title="Transactions"
            value={Number(
              overview?.total_transactions || 0
            ).toLocaleString("en-IN")}
            subtitle="Recorded sales"
          />

          <MetricCard
            title="Average Discount"
            value={`${overview?.avg_discount || 0}%`}
            subtitle="Across transactions"
          />

        </section>


        <section className="mt-6 grid gap-6 lg:grid-cols-2">

          <SalesChart
            data={salesTrend}
          />

          <RegionChart
            data={regions}
          />

        </section>


        <section className="mt-6 grid gap-6 lg:grid-cols-2">

          <CategoryChart
            data={categories}
          />

          <InventoryAlerts
            alerts={inventoryAlerts}
            summary={inventorySummary}
          />

        </section>


        <section className="mt-6 grid gap-4 md:grid-cols-2">

          <MetricCard
            title="Top Category"
            value={
              overview?.top_category || "N/A"
            }
            subtitle={
              overview?.top_category_revenue
                ? formatCurrency(
                    overview.top_category_revenue
                  )
                : undefined
            }
          />

          <MetricCard
            title="Top Region"
            value={
              overview?.top_region || "N/A"
            }
            subtitle={
              overview?.top_region_revenue
                ? formatCurrency(
                    overview.top_region_revenue
                  )
                : undefined
            }
          />

        </section>

      </div>
    </main>
  );
}