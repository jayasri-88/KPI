import React, { useState, useEffect, useMemo } from "react";
import {
  Store,
  MapPin,
  TrendingUp,
  Award,
  Search,
  Compass,
  Building2,
  SlidersHorizontal,
  RotateCcw,
  Navigation,
  Crosshair,
  DollarSign,
  ShoppingBag,
  Percent,
  Layers,
  ArrowUpRight,
  X,
} from "lucide-react";
import { getStoresSpatial, getRegionalPerformance } from "../services/api";
import { formatCurrency, formatPercent } from "../utils/formatters";
import { SkeletonCard } from "../components/common/LoadingSkeleton";
import { ErrorState, EmptyState } from "../components/common/EmptyState";
import StoreMap from "../components/maps/StoreMap";

// Predefined city coordinates for spatial proximity testing
const CITY_COORDINATES = {
  Bengaluru: { lat: 12.9784, lng: 77.6408 },
  Mumbai: { lat: 19.0596, lng: 72.8295 },
  Delhi: { lat: 28.6315, lng: 77.2167 },
  Hyderabad: { lat: 17.4348, lng: 78.3867 },
  Chennai: { lat: 13.0588, lng: 80.2642 },
  Pune: { lat: 18.5621, lng: 73.9167 },
  Kolkata: { lat: 22.5022, lng: 88.3618 },
};

export default function Stores() {
  const [stores, setStores] = useState([]);
  const [regionsData, setRegionsData] = useState([]);
  const [selectedStore, setSelectedStore] = useState(null);

  // Filters
  const [regionFilter, setRegionFilter] = useState("all");
  const [storeTypeFilter, setStoreTypeFilter] = useState("all");
  const [originCity, setOriginCity] = useState("none");
  const [radiusKm, setRadiusKm] = useState(100);
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load stores with spatial queries
  const fetchSpatialData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (regionFilter !== "all") params.region = regionFilter;
      if (storeTypeFilter !== "all") params.store_type = storeTypeFilter;
      if (search.trim()) params.city = search.trim();

      // Proximity search using PostGIS
      if (originCity !== "none" && CITY_COORDINATES[originCity]) {
        params.lat = CITY_COORDINATES[originCity].lat;
        params.lng = CITY_COORDINATES[originCity].lng;
        params.radius_km = radiusKm;
      }

      const [spatialStores, regPerf] = await Promise.all([
        getStoresSpatial(params),
        getRegionalPerformance(),
      ]);

      setStores(spatialStores || []);
      setRegionsData(regPerf || []);

      // If previously selected store is not in filtered list, reset or keep
      if (selectedStore) {
        const found = spatialStores.find((s) => s.store_id === selectedStore.store_id);
        if (!found && spatialStores.length > 0) {
          setSelectedStore(spatialStores[0]);
        }
      } else if (spatialStores.length > 0) {
        setSelectedStore(spatialStores[0]);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to load geographic data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSpatialData();
  }, [regionFilter, storeTypeFilter, originCity, radiusKm]);

  const handleResetFilters = () => {
    setRegionFilter("all");
    setStoreTypeFilter("all");
    setOriginCity("none");
    setRadiusKm(100);
    setSearch("");
  };

  // Radius center coordinates for Map circle overlay
  const activeRadiusCenter = useMemo(() => {
    if (originCity !== "none" && CITY_COORDINATES[originCity]) {
      return [CITY_COORDINATES[originCity].lat, CITY_COORDINATES[originCity].lng];
    }
    return null;
  }, [originCity]);

  // Aggregate stats from current view
  const currentTotalRevenue = useMemo(() => {
    return stores.reduce((acc, s) => acc + Number(s.total_revenue || 0), 0);
  }, [stores]);

  const currentTotalOrders = useMemo(() => {
    return stores.reduce((acc, s) => acc + Number(s.total_orders || 0), 0);
  }, [stores]);

  const regions = ["all", "South", "West", "North", "East"];
  const storeTypes = ["all", "Flagship", "Mall Outlet", "Express", "Hypermarket"];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center shadow-inner">
              <Compass className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Geographic Retail Network & PostGIS Spatial Analytics
              </h1>
              <p className="text-xs text-slate-400">
                Interactive spatial visualization, radius distance calculations, and location-based revenue distribution
              </p>
            </div>
          </div>
        </div>

        {/* Global Summary Badge */}
        <div className="flex items-center gap-3">
          <div className="px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-slate-400">Filtered Revenue:</span>
            <span className="font-bold text-white">
              {formatCurrency(currentTotalRevenue, { compact: true })}
            </span>
          </div>
          <span className="text-xs px-3 py-1.5 rounded-xl font-mono bg-indigo-950/70 border border-indigo-700/60 text-indigo-300">
            {stores.length} / 10 Stores
          </span>
        </div>
      </div>

      {/* Regional Performance Cards Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {regionsData.map((reg) => {
          const isSelected = regionFilter.toLowerCase() === reg.region.toLowerCase();
          return (
            <div
              key={reg.region}
              onClick={() =>
                setRegionFilter(isSelected ? "all" : reg.region)
              }
              className={`p-4 rounded-xl border transition-all cursor-pointer shadow-md ${
                isSelected
                  ? "bg-indigo-950/50 border-indigo-500/80 ring-2 ring-indigo-500/30"
                  : "bg-slate-900 border-slate-800 hover:border-slate-700 hover:bg-slate-850"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-white uppercase tracking-wider">
                    {reg.region} Region
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                    {reg.store_count} {reg.store_count === 1 ? "store" : "stores"}
                  </span>
                </div>
                <span className="text-xs text-indigo-400 font-semibold">
                  {formatPercent(reg.profit_margin_pct)} margin
                </span>
              </div>

              <div className="text-xl font-extrabold text-white tracking-tight">
                {formatCurrency(reg.total_revenue, { compact: true })}
              </div>

              <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                <span className="truncate max-w-[150px]">
                  Top: <span className="text-slate-200 font-medium">{reg.top_store_name}</span>
                </span>
                <span className="font-mono text-slate-500">
                  {reg.centroid_lat?.toFixed(1)}°, {reg.centroid_lng?.toFixed(1)}°
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Spatial Controls & Multi-Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-md space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Region Tabs */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs text-slate-400 font-medium px-1 flex items-center gap-1">
              <Compass className="w-3.5 h-3.5 text-indigo-400" />
              <span>Region:</span>
            </span>
            {regions.map((reg) => (
              <button
                key={reg}
                onClick={() => setRegionFilter(reg)}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                  regionFilter === reg
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
                }`}
              >
                {reg === "all" ? "All Regions" : reg}
              </button>
            ))}
          </div>

          {/* Reset Filters */}
          <button
            onClick={handleResetFilters}
            className="flex items-center gap-1 px-2.5 py-1 text-xs text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 rounded-lg border border-slate-700/60 transition cursor-pointer"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Reset Filters</span>
          </button>
        </div>

        {/* Secondary Proximity & Type Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 border-t border-slate-800/80">
          {/* Store Type Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 whitespace-nowrap">Format:</span>
            <select
              value={storeTypeFilter}
              onChange={(e) => setStoreTypeFilter(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              {storeTypes.map((st) => (
                <option key={st} value={st}>
                  {st === "all" ? "All Formats (Flagship, Outlet, Express)" : st}
                </option>
              ))}
            </select>
          </div>

          {/* PostGIS Origin City Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 whitespace-nowrap flex items-center gap-1">
              <Crosshair className="w-3.5 h-3.5 text-indigo-400" />
              <span>Origin:</span>
            </span>
            <select
              value={originCity}
              onChange={(e) => setOriginCity(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="none">No Proximity Filter (All Cities)</option>
              {Object.keys(CITY_COORDINATES).map((c) => (
                <option key={c} value={c}>
                  Around {c}
                </option>
              ))}
            </select>
          </div>

          {/* PostGIS Radius Slider */}
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 whitespace-nowrap">
              Radius: <span className="text-indigo-400 font-bold">{radiusKm} km</span>
            </span>
            <input
              type="range"
              min="20"
              max="500"
              step="10"
              value={radiusKm}
              disabled={originCity === "none"}
              onChange={(e) => setRadiusKm(Number(e.target.value))}
              className="w-full accent-indigo-500 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
            />
          </div>
        </div>
      </div>

      {error && <ErrorState message={error} onRetry={fetchSpatialData} />}

      {/* Main Geographic Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Side: Interactive Leaflet Map (7 cols) */}
        <div className="lg:col-span-7 xl:col-span-8 flex flex-col gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-3 shadow-md flex-1">
            <div className="flex items-center justify-between px-2 py-1 mb-2">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Interactive PostGIS Store Map
                </span>
              </div>
              <span className="text-[11px] text-slate-400">
                Click pin to inspect KPIs or switch basemaps
              </span>
            </div>

            <StoreMap
              stores={stores}
              selectedStore={selectedStore}
              onSelectStore={(st) => setSelectedStore(st)}
              radiusCenter={activeRadiusCenter}
              radiusKm={originCity !== "none" ? radiusKm : null}
            />
          </div>
        </div>

        {/* Right Side: Active Store Inspector & Leaderboard (5 cols) */}
        <div className="lg:col-span-5 xl:col-span-4 space-y-4">
          {/* Active Store Inspection Card */}
          {selectedStore ? (
            <div className="bg-slate-900 border border-indigo-500/40 rounded-2xl p-5 shadow-lg relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-2xl pointer-events-none" />

              <div className="flex items-start justify-between gap-2 mb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-600/30 text-indigo-300 border border-indigo-500/40">
                      {selectedStore.store_code}
                    </span>
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {selectedStore.store_type}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white mt-1.5">
                    {selectedStore.name}
                  </h3>
                  <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-0.5">
                    <MapPin className="w-3.5 h-3.5 text-slate-500" />
                    <span>
                      {selectedStore.city}, {selectedStore.state} ({selectedStore.region})
                    </span>
                  </div>
                </div>
              </div>

              {/* Distance badge if proximity search is active */}
              {selectedStore.distance_km !== null && selectedStore.distance_km !== undefined && (
                <div className="mb-3 px-3 py-1.5 rounded-lg bg-cyan-950/60 border border-cyan-800/60 text-xs text-cyan-300 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Navigation className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Distance from {originCity}:</span>
                  </span>
                  <span className="font-mono font-bold">{selectedStore.distance_km} km</span>
                </div>
              )}

              {/* Store KPIs Grid */}
              <div className="grid grid-cols-2 gap-2 text-xs mb-4">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase block font-medium">
                    Total Revenue
                  </span>
                  <span className="font-extrabold text-white text-sm">
                    {formatCurrency(selectedStore.total_revenue, { compact: true })}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase block font-medium">
                    Gross Profit
                  </span>
                  <span className="font-extrabold text-emerald-400 text-sm">
                    {formatCurrency(selectedStore.total_profit, { compact: true })}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase block font-medium">
                    Orders / Volume
                  </span>
                  <span className="font-bold text-slate-200">
                    {selectedStore.total_orders?.toLocaleString()} orders
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase block font-medium">
                    Sales / Sq.Ft
                  </span>
                  <span className="font-bold text-slate-200">
                    ₹{Number(selectedStore.sales_per_sqft || 0).toFixed(0)}/sqft
                  </span>
                </div>
              </div>

              {/* Target Achievement Bar */}
              <div>
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="text-slate-400">Revenue Target Progress</span>
                  <span className="font-bold text-white">
                    {Number(selectedStore.target_achievement_pct || 0).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      Number(selectedStore.target_achievement_pct) >= 80
                        ? "bg-emerald-500"
                        : Number(selectedStore.target_achievement_pct) >= 50
                        ? "bg-indigo-500"
                        : "bg-amber-500"
                    }`}
                    style={{
                      width: `${Math.min(100, Number(selectedStore.target_achievement_pct || 0))}%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                  <span>Actual: {formatCurrency(selectedStore.total_revenue, { compact: true })}</span>
                  <span>Target: {formatCurrency(selectedStore.target_monthly_sales, { compact: true })}</span>
                </div>
              </div>

              {/* Address details */}
              {selectedStore.address && (
                <div className="mt-3 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400">
                  <span className="font-semibold text-slate-300">Address: </span>
                  <span>{selectedStore.address}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center text-slate-500 text-xs">
              Select a store pin on the map to inspect location analytics
            </div>
          )}

          {/* Store Network Leaderboard List */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-md">
            <div className="flex items-center justify-between mb-3 px-1">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-amber-400" />
                <span>Store Leaderboard ({stores.length})</span>
              </h3>
              <span className="text-[10px] text-slate-500">Ranked by revenue</span>
            </div>

            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
              {stores.length === 0 ? (
                <div className="text-center py-6 text-slate-500 text-xs">
                  No stores match the current spatial filter.
                </div>
              ) : (
                stores.map((st, idx) => {
                  const isSelected = selectedStore?.store_id === st.store_id;
                  return (
                    <div
                      key={st.store_id}
                      onClick={() => setSelectedStore(st)}
                      className={`p-2.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-2 ${
                        isSelected
                          ? "bg-indigo-950/60 border-indigo-500 text-white"
                          : "bg-slate-950/70 border-slate-800/80 hover:border-slate-700 text-slate-300"
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <span
                          className={`w-5 h-5 rounded-md text-[10px] font-bold flex items-center justify-center shrink-0 ${
                            idx === 0
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                              : idx === 1
                              ? "bg-slate-300/20 text-slate-200 border border-slate-400/40"
                              : idx === 2
                              ? "bg-amber-700/20 text-amber-400 border border-amber-600/40"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {idx + 1}
                        </span>
                        <div className="min-w-0">
                          <p className="text-xs font-bold truncate leading-tight">
                            {st.name}
                          </p>
                          <p className="text-[10px] text-slate-400">
                            {st.city} &bull; {st.store_type}
                          </p>
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        <span className="text-xs font-extrabold text-white block">
                          {formatCurrency(st.total_revenue, { compact: true })}
                        </span>
                        {st.distance_km !== null && st.distance_km !== undefined ? (
                          <span className="text-[10px] text-cyan-400 font-mono">
                            {st.distance_km} km
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-500">
                            {Number(st.target_achievement_pct || 0).toFixed(0)}% target
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
