import React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export default function MetricCard({
  title,
  value,
  change,
  changeType = "percent", // percent or label
  trend = "up", // up, down, neutral
  subtitle,
  icon: Icon,
  iconColor = "text-indigo-400",
  iconBg = "bg-indigo-500/10 border-indigo-500/20",
  accentColor = "from-indigo-500/10 via-transparent to-transparent",
}) {
  const isPositive = trend === "up" || (typeof change === "number" && change > 0);
  const isNegative = trend === "down" || (typeof change === "number" && change < 0);

  return (
    <div className="relative overflow-hidden rounded-xl bg-slate-900 border border-slate-800 p-5 shadow-md hover:border-slate-700/80 hover:shadow-lg transition-all group">
      {/* Subtle Ambient Radial Highlight */}
      <div
        className={`absolute -right-6 -top-6 w-24 h-24 bg-gradient-to-br ${accentColor} rounded-full blur-2xl pointer-events-none group-hover:scale-125 transition-transform duration-500`}
      />

      <div className="relative z-10 flex items-start justify-between">
        <div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            {title}
          </span>
          <div className="mt-2 text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            {value}
          </div>
        </div>

        {Icon && (
          <div className={`p-2.5 rounded-xl border ${iconBg} ${iconColor} shadow-inner`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="relative z-10 mt-4 flex items-center justify-between text-xs">
        {change !== undefined && change !== null ? (
          <div
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-semibold text-[11px] border ${
              isPositive
                ? "bg-emerald-950/70 border-emerald-700/50 text-emerald-400"
                : isNegative
                ? "bg-rose-950/70 border-rose-700/50 text-rose-400"
                : "bg-slate-800 border-slate-700 text-slate-300"
            }`}
          >
            {isPositive ? (
              <TrendingUp className="w-3 h-3" />
            ) : isNegative ? (
              <TrendingDown className="w-3 h-3" />
            ) : (
              <Minus className="w-3 h-3" />
            )}
            <span>
              {typeof change === "number"
                ? `${change > 0 ? "+" : ""}${change.toFixed(1)}%`
                : change}
            </span>
          </div>
        ) : (
          <div />
        )}

        {subtitle && (
          <span className="text-[11px] text-slate-400 font-medium">
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
}
