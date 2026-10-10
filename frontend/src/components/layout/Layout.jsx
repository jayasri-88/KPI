import React from 'react';
import Navbar from './Navbar';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Retail KPI Intelligence Platform &copy; {new Date().getFullYear()}</span>
          <span>Engineered with FastAPI &bull; React &bull; PostgreSQL &bull; PostGIS &bull; LangGraph</span>
        </div>
      </footer>
    </div>
  );
}
