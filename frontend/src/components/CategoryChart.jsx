import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function CategoryChart({ data }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">
        Category Performance
      </h2>

      <p className="mb-5 text-sm text-slate-500">
        Revenue by product category
      </p>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
          >
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis type="number" />

            <YAxis
              type="category"
              dataKey="category"
              width={100}
            />

            <Tooltip
              formatter={(value) =>
                `₹${Number(value).toLocaleString()}`
              }
            />

            <Bar
              dataKey="revenue"
              fill="#0f766e"
              radius={[0, 6, 6, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}