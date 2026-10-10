import React, { useEffect, useMemo, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  Store as StoreIcon,
  Maximize2,
  Layers,
  MapPin,
  TrendingUp,
  DollarSign,
  ShoppingBag,
  Target,
  ArrowUpRight,
} from "lucide-react";

// Fix default Leaflet icon paths in Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Helper to generate distinct custom DivIcons according to revenue performance
const createStoreDivIcon = (store, isSelected) => {
  const rev = Number(store.total_revenue || 0);

  let bgGradient = "from-indigo-600 to-blue-700";
  let borderColor = "border-indigo-400";
  let ringColor = "ring-indigo-400/40";
  let badgeColor = "bg-indigo-500";

  if (rev >= 6000000) {
    bgGradient = "from-amber-500 to-yellow-600";
    borderColor = "border-amber-300";
    ringColor = "ring-amber-400/50";
    badgeColor = "bg-amber-500";
  } else if (rev >= 4000000) {
    bgGradient = "from-emerald-600 to-teal-700";
    borderColor = "border-emerald-300";
    ringColor = "ring-emerald-400/40";
    badgeColor = "bg-emerald-500";
  }

  const selectedClass = isSelected
    ? "scale-125 z-50 ring-4 " + ringColor
    : "hover:scale-110";

  const html = `
    <div class="relative flex items-center justify-center transition-transform duration-200 ${selectedClass}">
      <div class="w-10 h-10 rounded-2xl bg-gradient-to-br ${bgGradient} text-white shadow-xl flex items-center justify-center border-2 ${borderColor}">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="m2 7 4.41-4.41A2 2 0 0 1 7.83 2h8.34a2 2 0 0 1 1.42.59L22 7"/>
          <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
          <path d="M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4"/>
          <path d="M2 7h20"/>
        </svg>
      </div>
      <div class="absolute -top-1.5 -right-1.5 px-1.5 py-0.5 rounded-full ${badgeColor} text-[10px] font-black text-white shadow-md border border-white/40">
        ₹${(rev / 100000).toFixed(0)}L
      </div>
      <div class="absolute -bottom-1 w-2 h-2 bg-slate-900 rotate-45 border-r border-b ${borderColor}"></div>
    </div>
  `;

  return L.divIcon({
    className: "custom-store-pin",
    html: html,
    iconSize: [40, 40],
    iconAnchor: [20, 36],
    popupAnchor: [0, -36],
  });
};

// Child controller component to fit bounds when stores change or when triggered
const MapViewController = ({ bounds, center, zoom }) => {
  const map = useMap();

  useEffect(() => {
    if (center && zoom) {
      map.flyTo(center, zoom, { duration: 1.2 });
    } else if (bounds && bounds.length > 0) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
    }
  }, [bounds, center, zoom, map]);

  return null;
};

export default function StoreMap({
  stores = [],
  selectedStore = null,
  onSelectStore,
  radiusCenter = null,
  radiusKm = null,
}) {
  const [mapStyle, setMapStyle] = useState("voyager"); // 'voyager' | 'dark' | 'osm'

  // Map Tile Providers
  const tileLayers = {
    voyager: {
      url: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    },
    dark: {
      url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    },
    osm: {
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
  };

  // Compute bounding box around all valid coordinates
  const bounds = useMemo(() => {
    const validCoords = stores
      .filter((s) => s.latitude && s.longitude)
      .map((s) => [Number(s.latitude), Number(s.longitude)]);
    return validCoords.length > 0 ? validCoords : null;
  }, [stores]);

  // Center on selected store if available, else center of India
  const [focusTarget, setFocusTarget] = useState(null);

  useEffect(() => {
    if (selectedStore && selectedStore.latitude && selectedStore.longitude) {
      setFocusTarget({
        center: [Number(selectedStore.latitude), Number(selectedStore.longitude)],
        zoom: 11,
      });
    }
  }, [selectedStore]);

  const handleFitAll = () => {
    if (bounds) {
      setFocusTarget({
        bounds: bounds,
      });
    }
  };

  return (
    <div className="relative w-full h-full min-h-[520px] rounded-2xl overflow-hidden border border-slate-200/80 dark:border-slate-800 shadow-sm bg-slate-900">
      {/* Top Map Controls Floating Bar */}
      <div className="absolute top-4 right-4 z-[1000] flex items-center gap-2">
        {/* Fit All button */}
        <button
          onClick={handleFitAll}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-white/90 dark:bg-slate-900/90 text-slate-700 dark:text-slate-200 backdrop-blur-md border border-slate-200 dark:border-slate-700 shadow-md hover:bg-white dark:hover:bg-slate-800 transition"
          title="Fit all stores in view"
        >
          <Maximize2 className="w-3.5 h-3.5" />
          <span>Fit All ({stores.length})</span>
        </button>

        {/* Tile style switcher */}
        <div className="flex items-center bg-white/90 dark:bg-slate-900/90 backdrop-blur-md rounded-xl p-0.5 border border-slate-200 dark:border-slate-700 shadow-md">
          <button
            onClick={() => setMapStyle("voyager")}
            className={`px-2.5 py-1 text-xs font-medium rounded-lg transition ${
              mapStyle === "voyager"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            Voyager
          </button>
          <button
            onClick={() => setMapStyle("dark")}
            className={`px-2.5 py-1 text-xs font-medium rounded-lg transition ${
              mapStyle === "dark"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            Dark
          </button>
          <button
            onClick={() => setMapStyle("osm")}
            className={`px-2.5 py-1 text-xs font-medium rounded-lg transition ${
              mapStyle === "osm"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            OSM
          </button>
        </div>
      </div>

      {/* Map Legend Overlay */}
      <div className="absolute bottom-4 left-4 z-[1000] hidden sm:flex items-center gap-4 px-3.5 py-2 rounded-xl bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border border-slate-200 dark:border-slate-800 shadow-md text-xs font-medium text-slate-600 dark:text-slate-300">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-amber-500 ring-2 ring-amber-400/40" />
          <span>&gt; ₹60L Rev</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-emerald-500 ring-2 ring-emerald-400/40" />
          <span>&gt; ₹40L Rev</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-indigo-500 ring-2 ring-indigo-400/40" />
          <span>Standard</span>
        </div>
        {radiusKm && radiusCenter && (
          <div className="flex items-center gap-1.5 text-cyan-600 dark:text-cyan-400 border-l border-slate-200 dark:border-slate-700 pl-3">
            <span className="w-2.5 h-2.5 rounded-full border-2 border-dashed border-cyan-500" />
            <span>{radiusKm}km PostGIS Radius</span>
          </div>
        )}
      </div>

      {/* React Leaflet Map */}
      <MapContainer
        center={[20.5937, 78.9629]}
        zoom={5}
        scrollWheelZoom={true}
        className="w-full h-full z-0"
        style={{ height: "100%", width: "100%", minHeight: "520px" }}
      >
        <TileLayer
          url={tileLayers[mapStyle].url}
          attribution={tileLayers[mapStyle].attribution}
        />

        {focusTarget && (
          <MapViewController
            bounds={focusTarget.bounds}
            center={focusTarget.center}
            zoom={focusTarget.zoom}
          />
        )}

        {/* Spatial Radius Circle Visualization if radius filter is active */}
        {radiusKm && radiusCenter && (
          <Circle
            center={radiusCenter}
            radius={radiusKm * 1000}
            pathOptions={{
              color: "#06b6d4",
              fillColor: "#06b6d4",
              fillOpacity: 0.12,
              weight: 2,
              dashArray: "6, 6",
            }}
          />
        )}

        {/* Store Markers */}
        {stores.map((store) => {
          if (!store.latitude || !store.longitude) return null;
          const pos = [Number(store.latitude), Number(store.longitude)];
          const isSelected = selectedStore?.store_id === store.store_id;

          return (
            <Marker
              key={store.store_id}
              position={pos}
              icon={createStoreDivIcon(store, isSelected)}
              eventHandlers={{
                click: () => {
                  if (onSelectStore) onSelectStore(store);
                },
              }}
            >
              <Popup className="custom-leaflet-popup" minWidth={260} maxWidth={320}>
                <div className="p-1 text-slate-900 dark:text-slate-100 font-sans">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-2 border-b border-slate-200 dark:border-slate-700 pb-2 mb-2">
                    <div>
                      <span className="text-[10px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300">
                        {store.store_code}
                      </span>
                      <h4 className="font-bold text-sm text-slate-900 dark:text-white mt-1 leading-snug">
                        {store.name}
                      </h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {store.city}, {store.region} Region
                      </p>
                    </div>
                  </div>

                  {/* KPIs Grid */}
                  <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-100 dark:border-slate-700/60">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">
                        Revenue
                      </span>
                      <p className="font-extrabold text-slate-900 dark:text-white text-sm">
                        ₹{Number(store.total_revenue || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                      </p>
                    </div>

                    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-100 dark:border-slate-700/60">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">
                        Gross Profit
                      </span>
                      <p className="font-extrabold text-emerald-600 dark:text-emerald-400 text-sm">
                        ₹{Number(store.total_profit || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                      </p>
                    </div>

                    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-100 dark:border-slate-700/60">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">
                        Orders
                      </span>
                      <p className="font-bold text-slate-800 dark:text-slate-200">
                        {store.total_orders || 0}
                      </p>
                    </div>

                    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-100 dark:border-slate-700/60">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">
                        Avg Order
                      </span>
                      <p className="font-bold text-slate-800 dark:text-slate-200">
                        ₹{Number(store.average_order_value || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                      </p>
                    </div>
                  </div>

                  {/* Target Achievement */}
                  <div className="mb-3">
                    <div className="flex justify-between text-[11px] font-medium text-slate-600 dark:text-slate-300 mb-1">
                      <span>Target Achievement</span>
                      <span className="font-bold text-indigo-600 dark:text-indigo-400">
                        {Number(store.target_achievement_pct || 0).toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-indigo-600 h-1.5 rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.min(100, Number(store.target_achievement_pct || 0))}%`,
                        }}
                      />
                    </div>
                  </div>

                  {store.distance_km !== null && store.distance_km !== undefined && (
                    <div className="text-[11px] text-cyan-600 dark:text-cyan-400 font-medium mb-2 flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      <span>{store.distance_km} km from search origin</span>
                    </div>
                  )}

                  {/* Action */}
                  <button
                    onClick={() => {
                      if (onSelectStore) onSelectStore(store);
                    }}
                    className="w-full py-1.5 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs transition flex items-center justify-center gap-1 shadow-sm"
                  >
                    <span>Inspect Analytics</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
