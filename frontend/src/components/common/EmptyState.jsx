import React from "react";
import { Inbox, AlertCircle, RefreshCw } from "lucide-react";

export function EmptyState({
  title = "No data available",
  description = "No records matched your active filter criteria.",
  icon: Icon = Inbox,
  actionText = null,
  onAction = null,
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-slate-900/60 border border-dashed border-slate-800 rounded-xl my-4">
      <div className="p-3 bg-slate-800 text-slate-400 rounded-full mb-3">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
      <p className="text-xs text-slate-400 max-w-sm mt-1">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="mt-4 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-medium transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}

export function ErrorState({
  title = "Failed to load analytics",
  message = "An error occurred while fetching real-time data from the backend.",
  onRetry = null,
}) {
  return (
    <div className="p-5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-semibold text-rose-300">{title}</h4>
          <p className="text-xs text-rose-200/80 mt-0.5">{message}</p>
        </div>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-900/80 hover:bg-rose-800 border border-rose-700/60 text-xs font-semibold text-white transition-all self-start sm:self-auto cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Query</span>
        </button>
      )}
    </div>
  );
}
