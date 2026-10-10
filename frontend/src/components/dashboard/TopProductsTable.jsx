import React from "react";
import { Link } from "react-router-dom";
import { Package, ArrowUpRight } from "lucide-react";
import { formatCurrency } from "../../utils/formatters";

export default function TopProductsTable({ products = [] }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-bold text-white">Top Revenue SKUs</h3>
        </div>
        <Link
          to="/products"
          className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 hover:underline"
        >
          <span>Catalog</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {products.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500">
          No top product records found.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="pb-2.5 font-semibold">SKU & Product</th>
                <th className="pb-2.5 font-semibold text-center">Units Sold</th>
                <th className="pb-2.5 font-semibold text-right">Revenue</th>
                <th className="pb-2.5 font-semibold text-right">Margin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {products.map((prod, idx) => (
                <tr key={prod.product_id} className="hover:bg-slate-850/50 transition-colors">
                  <td className="py-3 pr-2">
                    <div className="font-semibold text-white truncate max-w-[200px] sm:max-w-xs">
                      {prod.product_name}
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                      <span className="font-mono text-indigo-400">{prod.sku_code}</span>
                      <span>&bull;</span>
                      <span>{prod.brand}</span>
                      <span>&bull;</span>
                      <span className="text-slate-500">{prod.category_name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-center text-slate-300 font-medium">
                    {prod.units_sold.toLocaleString()}
                  </td>
                  <td className="py-3 px-2 text-right font-bold text-white">
                    {formatCurrency(prod.revenue, { compact: true })}
                  </td>
                  <td className="py-3 pl-2 text-right">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950/80 border border-emerald-700/60 text-emerald-400">
                      {Number(prod.margin_pct).toFixed(1)}%
                    </span>
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
