export default function SkuIntelligence({
  data,
}) {
  if (!data) {
    return null;
  }

  const {
    summary,
    top_performers,
    underperformers,
  } = data;

  return (
    <div className="space-y-6">

      <div className="grid gap-4 md:grid-cols-3">

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">
            Total SKUs
          </p>

          <p className="mt-2 text-2xl font-bold">
            {summary.total_skus}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">
            Must-Sell SKUs
          </p>

          <p className="mt-2 text-2xl font-bold">
            {summary.must_sell_skus}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">
            Must-Sell Adherence
          </p>

          <p className="mt-2 text-2xl font-bold">
            {summary.must_sell_adherence}%
          </p>
        </div>

      </div>


      <div className="grid gap-6 lg:grid-cols-2">

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <h2 className="text-lg font-semibold">
            Top Performing SKUs
          </h2>

          <div className="mt-4 overflow-x-auto">

            <table className="w-full text-left text-sm">

              <thead>
                <tr className="border-b">
                  <th className="px-3 py-3">
                    Rank
                  </th>

                  <th className="px-3 py-3">
                    SKU
                  </th>

                  <th className="px-3 py-3">
                    Product
                  </th>

                  <th className="px-3 py-3">
                    Revenue
                  </th>
                </tr>
              </thead>

              <tbody>
                {top_performers.map((sku) => (
                  <tr
                    key={sku.product_id}
                    className="border-b border-slate-100"
                  >
                    <td className="px-3 py-3">
                      #{sku.rank}
                    </td>

                    <td className="px-3 py-3">
                      {sku.sku_code}
                    </td>

                    <td className="px-3 py-3">
                      {sku.product_name}
                    </td>

                    <td className="px-3 py-3">
                      ₹
                      {sku.revenue.toLocaleString(
                        "en-IN"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>

            </table>

          </div>
        </div>


        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <h2 className="text-lg font-semibold">
            Underperforming SKUs
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Bottom revenue segment
          </p>

          <div className="mt-4 overflow-x-auto">

            <table className="w-full text-left text-sm">

              <thead>
                <tr className="border-b">
                  <th className="px-3 py-3">
                    SKU
                  </th>

                  <th className="px-3 py-3">
                    Product
                  </th>

                  <th className="px-3 py-3">
                    Revenue
                  </th>

                  <th className="px-3 py-3">
                    Discount
                  </th>
                </tr>
              </thead>

              <tbody>
                {underperformers.map((sku) => (
                  <tr
                    key={sku.product_id}
                    className="border-b border-slate-100"
                  >
                    <td className="px-3 py-3">
                      {sku.sku_code}
                    </td>

                    <td className="px-3 py-3">
                      {sku.product_name}
                    </td>

                    <td className="px-3 py-3">
                      ₹
                      {sku.revenue.toLocaleString(
                        "en-IN"
                      )}
                    </td>

                    <td className="px-3 py-3">
                      {sku.avg_discount}%
                    </td>
                  </tr>
                ))}
              </tbody>

            </table>

          </div>
        </div>

      </div>

    </div>
  );
}