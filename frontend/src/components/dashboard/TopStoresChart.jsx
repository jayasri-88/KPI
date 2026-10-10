import React from "react";
import { Link } from "react-router-dom";
import { Store, ArrowUpRight, MapPin } from "lucide-react";
import { formatCurrency } from "../../utils/formatters";

export default function TopStoresChart({ stores = [] }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md flex flex-col justify-between">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Store className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-bold text-white">Store Leaderboard</h3>
        </div>
        <Link
          to="/stores"
          className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 hover:underline"
        >
          <span>All Stores</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {stores.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500">
          No store performance data available.
        </div>
      ) : (
        <div className="divide-y divide-slate-800/80 mt-2">
          {stores.map((st, idx) => {
            const achieve = Number(st.target_achievement_pct) || 0;
            return (
              <div key={st.store_id} className="py-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <span className="w-6 h-6 rounded-md bg-slate-800 text-slate-400 text-xs font-bold flex items-center justify-center flex-shrink-0">
                    {idx + 1}
                  </span>
                  <div className="min-w-0">
                    <div className="font-semibold text-white text-xs truncate">
                      {st.name}
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                      <MapPin className="w-3 h-3 text-slate-500" />
                      <span>{st.city} &bull; {st.region}</span>
                    </div>
                  </div>
                </div>

                <div className="text-right flex-shrink-0">
                  <div className="text-xs font-bold text-white">
                    {formatCurrency(st.revenue, { compact: true })}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="w-20 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          achieve >= 80 ? "bg-emerald-500" : achieve >= 50 ? "bg-indigo-500" : "bg-amber-500"
                        }`}
                        style={{ width: `${Math.min(100, achieve)}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-slate-400 font-semibold">
                      {achieve.toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
