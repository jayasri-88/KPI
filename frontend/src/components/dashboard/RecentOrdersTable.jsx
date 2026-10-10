import React from "react";
import { Link } from "react-router-dom";
import { ShoppingBag, ArrowUpRight } from "lucide-react";
import { formatCurrency, formatDate } from "../../utils/formatters";

export default function RecentOrdersTable({ orders = [] }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <ShoppingBag className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-bold text-white">Live Transactions</h3>
        </div>
        <Link
          to="/sales"
          className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 hover:underline"
        >
          <span>Sales Ledger</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {orders.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500">
          No recent order transactions.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="pb-2.5 font-semibold">Order</th>
                <th className="pb-2.5 font-semibold">Store & Customer</th>
                <th className="pb-2.5 font-semibold">Date</th>
                <th className="pb-2.5 font-semibold text-right">Amount</th>
                <th className="pb-2.5 font-semibold text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {orders.map((ord) => (
                <tr key={ord.order_id} className="hover:bg-slate-850/50 transition-colors">
                  <td className="py-3 pr-2">
                    <span className="font-mono font-semibold text-indigo-300">
                      {ord.order_number}
                    </span>
                  </td>
                  <td className="py-3 px-2">
                    <div className="text-white font-medium truncate max-w-[160px]">
                      {ord.store_name}
                    </div>
                    <div className="text-[11px] text-slate-400 truncate max-w-[160px]">
                      {ord.customer_name || "Guest Customer"}
                    </div>
                  </td>
                  <td className="py-3 px-2 text-slate-400 text-[11px] whitespace-nowrap">
                    {formatDate(ord.order_date)}
                  </td>
                  <td className="py-3 px-2 text-right font-bold text-white">
                    {formatCurrency(ord.total_amount)}
                  </td>
                  <td className="py-3 pl-2 text-right">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase ${
                        ord.status === "completed"
                          ? "bg-emerald-950/70 border-emerald-700/60 text-emerald-400"
                          : ord.status === "returned"
                          ? "bg-amber-950/70 border-amber-700/60 text-amber-400"
                          : "bg-rose-950/70 border-rose-700/60 text-rose-400"
                      }`}
                    >
                      {ord.status}
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
