import React from "react";

export function SkeletonCard() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 animate-pulse space-y-3">
      <div className="flex items-center justify-between">
        <div className="h-4 w-24 bg-slate-800 rounded"></div>
        <div className="h-8 w-8 bg-slate-800 rounded-lg"></div>
      </div>
      <div className="h-7 w-36 bg-slate-800 rounded"></div>
      <div className="flex items-center gap-2">
        <div className="h-4 w-12 bg-slate-800 rounded"></div>
        <div className="h-3 w-20 bg-slate-800 rounded"></div>
      </div>
    </div>
  );
}

export function SkeletonChart({ height = "h-72" }) {
  return (
    <div className={`bg-slate-900 border border-slate-800 rounded-xl p-6 animate-pulse flex flex-col justify-between ${height}`}>
      <div className="flex items-center justify-between">
        <div className="h-5 w-40 bg-slate-800 rounded"></div>
        <div className="h-4 w-24 bg-slate-800 rounded"></div>
      </div>
      <div className="h-44 w-full bg-slate-800/60 rounded flex items-end gap-3 p-4">
        {[40, 65, 30, 80, 55, 90, 70, 85, 60, 95, 75, 50].map((h, i) => (
          <div key={i} className="flex-1 bg-slate-800 rounded-t" style={{ height: `${h}%` }}></div>
        ))}
      </div>
    </div>
  );
}

export function SkeletonTable({ rows = 5 }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 animate-pulse space-y-4">
      <div className="h-5 w-36 bg-slate-800 rounded"></div>
      <div className="space-y-2.5">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="h-10 w-full bg-slate-850 bg-slate-800/50 rounded flex items-center px-4 gap-4">
            <div className="h-3 w-1/4 bg-slate-800 rounded"></div>
            <div className="h-3 w-1/4 bg-slate-800 rounded"></div>
            <div className="h-3 w-1/4 bg-slate-800 rounded"></div>
            <div className="h-3 w-1/4 bg-slate-800 rounded"></div>
          </div>
        ))}
      </div>
    </div>
  );
}
