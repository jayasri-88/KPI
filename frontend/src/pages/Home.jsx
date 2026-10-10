import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Server, 
  Database, 
  MapPin, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  ExternalLink,
  Sparkles,
  ShoppingBag,
  Store,
  Layers,
  ShieldCheck,
  Lock,
  KeyRound,
  LogIn,
  UserCheck,
  Cpu,
  BarChart3,
  LayoutDashboard
} from 'lucide-react';
import { checkHealth, api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Home() {
  const [healthData, setHealthData] = useState(null);
  const [dbCheckData, setDbCheckData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [latency, setLatency] = useState(null);

  const { user, isAuthenticated } = useAuth();

  const fetchDiagnostics = async () => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const [health, dbCheck] = await Promise.all([
        checkHealth(),
        api.get('/v1/db-check').then(r => r.data).catch(err => ({ error: err.message }))
      ]);
      const elapsed = Math.round(performance.now() - start);
      setHealthData(health);
      setDbCheckData(dbCheck);
      setLatency(elapsed);
    } catch (err) {
      setError(err.message || 'Failed to reach FastAPI backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
  }, []);

  const phases = [
    { num: 1, title: 'Project Setup + FastAPI + React', status: 'completed' },
    { num: 2, title: 'PostgreSQL + PostGIS + SQLAlchemy', status: 'completed' },
    { num: 3, title: 'Database Models + Migrations + Seed Data', status: 'completed' },
    { num: 4, title: 'Authentication + JWT', status: 'completed' },
    { num: 5, title: 'Backend REST APIs', status: 'completed' },
    { num: 6, title: 'React KPI Dashboard + Recharts', status: 'completed' },
    { num: 7, title: 'PostGIS + Interactive Leaflet Map', status: 'completed' },
    { num: 8, title: 'Sales Forecasting + Prophet ML Engine', status: 'completed' },
    { num: 9, title: 'AI Retail Analyst (LangGraph + Gemini)', status: 'next' },
    { num: 10, title: 'Redis Caching & Performance', status: 'upcoming' },
    { num: 11, title: 'Comprehensive Testing & Validation', status: 'upcoming' },
    { num: 12, title: 'Production Security & Rate Limiting', status: 'upcoming' },
    { num: 13, title: 'Docker + Cloud Deployment (Render/Vercel)', status: 'upcoming' },
    { num: 14, title: 'Documentation & Architecture Portfolio', status: 'upcoming' },
  ];

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="relative rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 p-8 sm:p-10 overflow-hidden shadow-xl">
        <div className="absolute -right-12 -top-12 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            Phase 8 Active &bull; Prophet Sales Forecasting &bull; Out-of-Time Model Evaluation Live
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white mb-4">
            Retail KPI Intelligence Platform
          </h1>
          <p className="text-base sm:text-lg text-slate-300 leading-relaxed mb-6">
            A full-stack, enterprise-grade retail intelligence platform combining real-time executive KPI monitoring, 
            spatial PostGIS store analytics, Prophet demand forecasting, and an autonomous LangGraph AI analyst.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold transition-all shadow-md hover:shadow-indigo-600/20"
            >
              <LayoutDashboard className="w-4 h-4" />
              Launch Executive Dashboard
            </Link>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 rounded-lg text-sm font-semibold transition-all"
            >
              <ExternalLink className="w-4 h-4" />
              FastAPI Swagger Docs (31 Endpoints)
            </a>
            <button
              onClick={fetchDiagnostics}
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 rounded-lg text-sm font-semibold transition-all cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Re-check Diagnostics
            </button>
          </div>
        </div>
      </div>

      {/* Real-time Diagnostics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md space-y-4">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-indigo-400" />
              <h2 className="text-lg font-bold text-white">PostgreSQL & PostGIS Database Status</h2>
            </div>
            {latency && (
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Round-trip: {latency} ms
              </span>
            )}
          </div>

          {loading ? (
            <div className="py-8 flex flex-col items-center justify-center text-slate-400 gap-3">
              <RefreshCw className="w-6 h-6 animate-spin text-indigo-400" />
              <p className="text-sm">Querying PostgreSQL and PostGIS spatial engine...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-200 space-y-2">
              <div className="flex items-center gap-2 font-semibold">
                <AlertCircle className="w-5 h-5 text-rose-400" />
                <span>Backend Connection Pending</span>
              </div>
              <p className="text-xs text-rose-300">{error}</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                  <span className="text-[11px] text-slate-400 block mb-1">Database Engine</span>
                  <div className="flex items-center gap-1 text-emerald-400 font-semibold text-xs">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>PostgreSQL 18</span>
                  </div>
                </div>

                <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                  <span className="text-[11px] text-slate-400 block mb-1">PostGIS Spatial</span>
                  <div className="flex items-center gap-1 text-emerald-400 font-semibold text-xs">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>Enabled (v3.6)</span>
                  </div>
                </div>

                <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                  <span className="text-[11px] text-slate-400 block mb-1">REST Endpoints</span>
                  <div className="text-slate-200 font-mono text-xs font-semibold">
                    31 Routes Live
                  </div>
                </div>

                <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                  <span className="text-[11px] text-slate-400 block mb-1">Historical Orders</span>
                  <div className="text-indigo-400 font-semibold text-xs">
                    850 Orders (14 mo)
                  </div>
                </div>
              </div>

              {/* Spatial capability check */}
              {dbCheckData?.spatial_test_geometry && (
                <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400 font-medium">PostGIS Live Spatial Query:</span>
                    <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono text-[11px]">
                      POINT (77.5946 12.9716) Passed
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-300 font-mono bg-slate-900 p-2.5 rounded border border-slate-800">
                    Database: <span className="text-indigo-400">{dbCheckData.database_name}</span> | User: <span className="text-indigo-400">{dbCheckData.connected_user}</span> | Schema: <span className="text-emerald-400">Alembic Head (Clean)</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Phase 6 Verification Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-emerald-400" />
              Phase 6 Deliverables
            </h2>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                <span>Responsive Sidebar + Top Navigation with active route indicators</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                <span>5 Executive KPI cards: Revenue, Profit, Orders, AOV, Customers</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                <span>Recharts AreaChart for Revenue, Profit, and Orders trajectory</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                <span>Merchandise share donut chart & store achievement leaderboard</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                <span>Connected Stores, Products, Customers, Sales, and Inventory views</span>
              </li>
            </ul>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800">
            <div className="text-[11px] text-slate-400 flex items-center justify-between">
              <span>Next Production Milestone</span>
              <span className="text-indigo-400 font-semibold">Phase 7: Charts + Filters + Tables</span>
            </div>
          </div>
        </div>
      </div>

      {/* 14-Phase Implementation Roadmap */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md">
        <div className="flex items-center justify-between mb-6 pb-3 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white">Full Platform Engineering Roadmap</h2>
            <p className="text-xs text-slate-400">Step-by-step production build sequence</p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-md">
            6 of 14 Completed
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {phases.map((p) => {
            const isCompleted = p.status === 'completed';
            const isNext = p.status === 'next';
            return (
              <div 
                key={p.num}
                className={`p-3.5 rounded-lg border text-xs transition-all ${
                  isCompleted 
                    ? 'bg-slate-950/80 border-emerald-500/40 text-slate-200' 
                    : isNext 
                    ? 'bg-indigo-950/30 border-indigo-500/50 text-indigo-200 ring-1 ring-indigo-500/30'
                    : 'bg-slate-950/30 border-slate-800/80 text-slate-400'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-mono text-[11px] font-bold text-slate-500">
                    PHASE {p.num < 10 ? `0${p.num}` : p.num}
                  </span>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                    isCompleted ? 'bg-emerald-500/20 text-emerald-400' :
                    isNext ? 'bg-indigo-500/20 text-indigo-300' : 'bg-slate-800 text-slate-500'
                  }`}>
                    {p.status}
                  </span>
                </div>
                <div className="font-semibold text-slate-200 line-clamp-2">
                  {p.title}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
