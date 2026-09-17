export default function InventoryAlerts({
  alerts,
  summary,
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Inventory Health
          </h2>

          <p className="text-sm text-slate-500">
            Latest inventory snapshot
          </p>
        </div>

        <div className="text-right">
          <p className="text-2xl font-bold text-slate-900">
            {summary?.total_alerts ?? 0}
          </p>

          <p className="text-xs text-slate-500">
            reorder alerts
          </p>
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="mt-6 rounded-lg bg-slate-50 p-6 text-center">
          <p className="font-medium text-slate-700">
            No reorder alerts
          </p>

          <p className="mt-1 text-sm text-slate-500">
            All monitored inventory positions are above
            their reorder points.
          </p>

          <p className="mt-3 text-xs text-slate-400">
            {summary?.total_records ?? 0} positions monitored
          </p>
        </div>
      ) : (
        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="px-3 py-3">SKU</th>
                <th className="px-3 py-3">Retailer</th>
                <th className="px-3 py-3">Stock</th>
                <th className="px-3 py-3">Reorder</th>
                <th className="px-3 py-3">Severity</th>
              </tr>
            </thead>

            <tbody>
              {alerts.map((alert) => (
                <tr
                  key={alert.inventory_id}
                  className="border-b border-slate-100"
                >
                  <td className="px-3 py-3">
                    {alert.sku_code}
                  </td>

                  <td className="px-3 py-3">
                    {alert.retailer_name}
                  </td>

                  <td className="px-3 py-3">
                    {alert.stock_level}
                  </td>

                  <td className="px-3 py-3">
                    {alert.reorder_point}
                  </td>

                  <td className="px-3 py-3 capitalize">
                    {alert.severity}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}