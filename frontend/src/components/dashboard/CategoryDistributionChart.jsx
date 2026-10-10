import React from "react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";
import { formatCurrency, formatPercent } from "../../utils/formatters";
import { PieChart as PieIcon } from "lucide-react";

const CATEGORY_COLORS = [
  "#6366f1", // Indigo
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#ec4899", // Pink
  "#8b5cf6", // Purple
  "#06b6d4", // Cyan
  "#f97316", // Orange
];

export default function CategoryDistributionChart({ data = [] }) {
  const chartData = data.map((item, idx) => ({
    name: item.category_name,
    value: Number(item.revenue),
    share: Number(item.share_pct),
    units: item.units_sold,
    color: CATEGORY_COLORS[idx % CATEGORY_COLORS.length],
  }));

  const totalRevenue = chartData.reduce((acc, curr) => acc + curr.value, 0);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-slate-700/80 rounded-xl p-3 shadow-2xl text-xs space-y-1 min-w-[140px]">
          <div className="flex items-center gap-1.5 font-semibold text-white">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: item.color }}
            />
            <span>{item.name}</span>
          </div>
          <div className="flex items-center justify-between text-slate-300">
            <span>Revenue:</span>
            <span className="font-bold">{formatCurrency(item.value)}</span>
          </div>
          <div className="flex items-center justify-between text-slate-400 text-[11px]">
            <span>Share:</span>
            <span className="text-emerald-400 font-semibold">{item.share}%</span>
          </div>
          <div className="flex items-center justify-between text-slate-400 text-[11px]">
            <span>Volume:</span>
            <span>{item.units.toLocaleString()} units</span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md flex flex-col justify-between">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <PieIcon className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-bold text-white">Merchandise Share</h3>
        </div>
        <span className="text-xs text-slate-400">
          {data.length} Departments
        </span>
      </div>

      {data.length === 0 ? (
        <div className="h-60 flex items-center justify-center text-xs text-slate-500">
          No category sales recorded.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center mt-3">
          {/* Donut Chart */}
          <div className="sm:col-span-6 h-52 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Tooltip content={<CustomTooltip />} />
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                Total
              </span>
              <span className="text-xs font-extrabold text-white">
                {formatCurrency(totalRevenue, { compact: true })}
              </span>
            </div>
          </div>

          {/* Legend Table */}
          <div className="sm:col-span-6 space-y-2">
            {chartData.map((item) => (
              <div
                key={item.name}
                className="flex items-center justify-between text-xs p-1.5 rounded-lg hover:bg-slate-850/60 transition-colors"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="truncate text-slate-300 font-medium text-xs">
                    {item.name}
                  </span>
                </div>
                <div className="text-right flex-shrink-0 pl-2">
                  <span className="text-white font-semibold block text-xs">
                    {formatCurrency(item.value, { compact: true })}
                  </span>
                  <span className="text-[10px] text-slate-400">{item.share}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
