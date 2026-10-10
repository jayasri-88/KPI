import React, { useState, useEffect, useCallback } from "react";
import { 
  DollarSign, 
  TrendingUp, 
  ShoppingCart, 
  Users, 
  Package, 
  Store, 
  Layers, 
  AlertCircle,
  Sparkles,
  ArrowUpRight
} from "lucide-react";
import MetricCard from "../components/dashboard/MetricCard";
import FilterBar from "../components/dashboard/FilterBar";
import RevenueTrendChart from "../components/dashboard/RevenueTrendChart";
import CategoryDistributionChart from "../components/dashboard/CategoryDistributionChart";
import TopStoresChart from "../components/dashboard/TopStoresChart";
import TopProductsTable from "../components/dashboard/TopProductsTable";
import RecentOrdersTable from "../components/dashboard/RecentOrdersTable";
import { SkeletonCard, SkeletonChart, SkeletonTable } from "../components/common/LoadingSkeleton";
import { ErrorState } from "../components/common/EmptyState";

import { 
  getDashboardOverview, 
  getSalesTrend, 
  listStores, 
  listCategories 
} from "../services/api";
import { formatCurrency, formatPercent } from "../utils/formatters";

export default function Dashboard() {
  // Filter States
  const [dateRange, setDateRange] = useState("all");
  const [selectedStore, setSelectedStore] = useState("all");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [trendInterval, setTrendInterval] = useState("monthly");

  // Data States
  const [overview, setOverview] = useState(null);
  const [salesTrend, setSalesTrend] = useState(null);
  const [storesList, setStoresList] = useState([]);
  const [categoriesList, setCategoriesList] = useState([]);

  // UI States
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Compute ISO dates for dateRange filter
  const getDateBounds = (rangeKey) => {
    if (rangeKey === "all") return { start_date: undefined, end_date: undefined };
    const now = new Date();
    let past = new Date();
    if (rangeKey === "7d") past.setDate(now.getDate() - 7);
    else if (rangeKey === "30d") past.setDate(now.getDate() - 30);
    else if (rangeKey === "90d") past.setDate(now.getDate() - 90);
    else if (rangeKey === "1y") past.setFullYear(now.getFullYear() - 1);
    return {
      start_date: past.toISOString(),
      end_date: now.toISOString(),
    };
  };

  // Fetch all dashboard data concurrently
  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { start_date, end_date } = getDateBounds(dateRange);

      const [overviewData, trendData, storesData, categoriesData] = await Promise.all([
        getDashboardOverview({ start_date, end_date }),
        getSalesTrend({ interval: trendInterval, start_date, end_date }),
        listStores({ size: 100 }),
        listCategories(),
      ]);

      setOverview(overviewData);
      setSalesTrend(trendData);
      setStoresList(storesData.items || []);
      setCategoriesList(categoriesData || []);
    } catch (err) {
      console.error("Dashboard fetch failure:", err);
      setError(err.response?.data?.detail || err.message || "Failed to load executive KPI metrics.");
    } finally {
      setLoading(false);
    }
  }, [dateRange, trendInterval]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  return (
    <div className="space-y-6">
      {/* ------------------------------------------------------------------ */}
      {/* 1. TOP HEADER & METADATA BAR                                        */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold tracking-tight text-white">
              Executive KPI Intelligence
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              Live DB
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time multi-store retail performance, gross margins, and customer analytics
          </p>
        </div>

        {overview && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">Target Gross Margin:</span>
            <span className="px-2 py-0.5 rounded font-mono font-bold bg-slate-800 text-slate-200 border border-slate-700">
              {Number(overview.gross_margin_pct).toFixed(1)}% Active
            </span>
          </div>
        )}
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* 2. MULTI-DIMENSIONAL FILTER CONTROLS                               */}
      {/* ------------------------------------------------------------------ */}
      <FilterBar
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        selectedStore={selectedStore}
        onStoreChange={setSelectedStore}
        stores={storesList}
        selectedCategory={selectedCategory}
        onCategoryChange={setSelectedCategory}
        categories={categoriesList}
        onRefresh={loadDashboardData}
        loading={loading}
      />

      {/* ------------------------------------------------------------------ */}
      {/* 3. ERROR BANNER (IF ANY)                                           */}
      {/* ------------------------------------------------------------------ */}
      {error && (
        <ErrorState
          title="Could Not Connect to Analytics Pipeline"
          message={error}
          onRetry={loadDashboardData}
        />
      )}

      {/* ------------------------------------------------------------------ */}
      {/* 4. EXECUTIVE KPI METRIC CARDS GRID (5 CARDS)                       */}
      {/* ------------------------------------------------------------------ */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : overview ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {/* Card 1: Total Revenue */}
          <MetricCard
            title="Total Revenue"
            value={formatCurrency(overview.total_revenue, { compact: true })}
            change={Number(overview.revenue_growth_pct)}
            subtitle="vs prior period"
            icon={DollarSign}
            iconColor="text-indigo-400"
            iconBg="bg-indigo-500/10 border-indigo-500/20"
            accentColor="from-indigo-600/20 via-transparent to-transparent"
          />

          {/* Card 2: Total Gross Profit */}
          <MetricCard
            title="Gross Profit"
            value={formatCurrency(overview.total_profit, { compact: true })}
            change={Number(overview.profit_growth_pct)}
            subtitle={`${Number(overview.gross_margin_pct).toFixed(1)}% gross margin`}
            icon={TrendingUp}
            iconColor="text-emerald-400"
            iconBg="bg-emerald-500/10 border-emerald-500/20"
            accentColor="from-emerald-600/20 via-transparent to-transparent"
          />

          {/* Card 3: Total Orders */}
          <MetricCard
            title="Total Orders"
            value={Number(overview.total_orders).toLocaleString()}
            change={Number(overview.orders_growth_pct)}
            subtitle="Historical transactions"
            icon={ShoppingCart}
            iconColor="text-sky-400"
            iconBg="bg-sky-500/10 border-sky-500/20"
            accentColor="from-sky-600/20 via-transparent to-transparent"
          />

          {/* Card 4: Average Order Value */}
          <MetricCard
            title="Average Order Value"
            value={formatCurrency(overview.average_order_value)}
            subtitle="Revenue / orders"
            icon={Package}
            iconColor="text-amber-400"
            iconBg="bg-amber-500/10 border-amber-500/20"
            accentColor="from-amber-600/20 via-transparent to-transparent"
          />

          {/* Card 5: Unique Customers */}
          <MetricCard
            title="Active Customers"
            value={Number(overview.total_customers).toLocaleString()}
            subtitle="VIP, Regular, & New"
            icon={Users}
            iconColor="text-purple-400"
            iconBg="bg-purple-500/10 border-purple-500/20"
            accentColor="from-purple-600/20 via-transparent to-transparent"
          />
        </div>
      ) : null}

      {/* ------------------------------------------------------------------ */}
      {/* 5. VISUALIZATION ROW 1: REVENUE TREND + CATEGORY DONUT             */}
      {/* ------------------------------------------------------------------ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8">
          {loading ? (
            <SkeletonChart height="h-80" />
          ) : (
            <RevenueTrendChart
              data={salesTrend?.points || []}
              interval={trendInterval}
              onIntervalChange={setTrendInterval}
            />
          )}
        </div>

        <div className="lg:col-span-4">
          {loading ? (
            <SkeletonChart height="h-80" />
          ) : (
            <CategoryDistributionChart
              data={overview?.category_distribution || []}
            />
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* 6. VISUALIZATION ROW 2: STORE LEADERBOARD + TOP SKUs               */}
      {/* ------------------------------------------------------------------ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5">
          {loading ? (
            <SkeletonTable rows={5} />
          ) : (
            <TopStoresChart stores={overview?.top_stores || []} />
          )}
        </div>

        <div className="lg:col-span-7">
          {loading ? (
            <SkeletonTable rows={5} />
          ) : (
            <TopProductsTable products={overview?.top_products || []} />
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* 7. VISUALIZATION ROW 3: LIVE RECENT ORDERS STREAM                  */}
      {/* ------------------------------------------------------------------ */}
      <div>
        {loading ? (
          <SkeletonTable rows={5} />
        ) : (
          <RecentOrdersTable orders={overview?.recent_orders || []} />
        )}
      </div>
    </div>
  );
}