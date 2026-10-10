import React, { useState, useEffect } from "react";
import { NavLink, Link, useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3,
  TrendingUp,
  Store,
  Package,
  Users,
  Archive,
  Bot,
  Activity,
  LogOut,
  ExternalLink,
  Menu,
  X,
  ChevronRight,
  ShieldCheck,
  Sparkles,
  SlidersHorizontal,
} from "lucide-react";
import { checkHealth } from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function DashboardLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState("checking");
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    const verifyApi = async () => {
      try {
        const data = await checkHealth();
        if (isMounted) {
          setBackendStatus(data.status === "healthy" ? "online" : "error");
        }
      } catch (err) {
        if (isMounted) {
          setBackendStatus("offline");
        }
      }
    };

    verifyApi();
    const interval = setInterval(verifyApi, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const navGroups = [
    {
      group: "Core Analytics",
      items: [
        { to: "/dashboard", label: "Executive Dashboard", icon: BarChart3 },
        { to: "/analytics", label: "Demand & Pareto", icon: SlidersHorizontal, badge: "80/20" },
        { to: "/sales", label: "Sales & Margins", icon: TrendingUp },
        { to: "/forecast", label: "Sales Forecasting", icon: Activity, badge: "Prophet" },
      ],
    },
    {
      group: "Retail Management",
      items: [
        { to: "/stores", label: "Stores & Geography", icon: Store, badge: "PostGIS" },
        { to: "/products", label: "Product Catalog", icon: Package },
        { to: "/customers", label: "Customer Cohorts", icon: Users },
        { to: "/inventory", label: "Inventory & Alerts", icon: Archive },
      ],
    },
    {
      group: "Intelligence Agent",
      items: [
        { to: "/assistant", label: "AI Retail Analyst", icon: Bot, badge: "LangGraph" },
      ],
    },
  ];

  // Helper to extract page title from path
  const getPageTitle = (path) => {
    switch (path) {
      case "/dashboard":
        return "Executive KPI Dashboard";
      case "/analytics":
        return "Merchandise Demand & Pareto 80/20 Intelligence";
      case "/sales":
        return "Sales Financials & Margins";
      case "/stores":
        return "Store Network & Spatial Performance";
      case "/products":
        return "Product Merchandising Catalog";
      case "/customers":
        return "Customer Demographic & Cohort Intelligence";
      case "/inventory":
        return "Multi-Store Inventory & Stock Replenishment";
      case "/forecast":
        return "Prophet Machine Learning Demand Forecast";
      case "/assistant":
        return "Autonomous AI Retail Analyst";
      default:
        return "Retail KPI Intelligence Platform";
    }
  };

  const getRoleBadgeClass = (role) => {
    switch (role) {
      case "admin":
        return "bg-emerald-950/80 border-emerald-600/60 text-emerald-400";
      case "manager":
        return "bg-amber-950/80 border-amber-600/60 text-amber-400";
      default:
        return "bg-indigo-950/80 border-indigo-600/60 text-indigo-400";
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans antialiased">
      {/* ------------------------------------------------------------------ */}
      {/* 1. SIDEBAR (Desktop & Mobile Drawer)                                */}
      {/* ------------------------------------------------------------------ */}
      {/* Mobile Backdrop */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden transition-opacity"
        />
      )}

      <aside
        className={`fixed lg:sticky top-0 h-screen z-50 flex flex-col justify-between w-64 bg-slate-900 border-r border-slate-800 transition-transform duration-300 ease-in-out ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="flex flex-col flex-1 overflow-y-auto">
          {/* Brand Header */}
          <div className="h-16 flex items-center justify-between px-5 border-b border-slate-800">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="p-2 bg-indigo-600 rounded-lg group-hover:bg-indigo-500 transition-colors shadow-sm">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-sm font-bold text-white flex items-center gap-1">
                  Retail KPI
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                    Pro
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 font-medium">
                  Intelligence Engine
                </div>
              </div>
            </Link>

            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Items */}
          <nav className="p-4 space-y-6">
            {navGroups.map((group) => (
              <div key={group.group}>
                <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  {group.group}
                </div>
                <div className="space-y-1">
                  {group.items.map((item) => {
                    const Icon = item.icon;
                    return (
                      <NavLink
                        key={item.to}
                        to={item.to}
                        onClick={() => setSidebarOpen(false)}
                        className={({ isActive }) =>
                          `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                            isActive
                              ? "bg-indigo-600 text-white font-semibold shadow-sm"
                              : "text-slate-300 hover:text-white hover:bg-slate-800/80"
                          }`
                        }
                      >
                        <div className="flex items-center gap-2.5">
                          <Icon className="w-4 h-4 flex-shrink-0" />
                          <span>{item.label}</span>
                        </div>
                        {item.badge && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-tight bg-slate-800/90 text-slate-300 border border-slate-700/60">
                            {item.badge}
                          </span>
                        )}
                      </NavLink>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>
        </div>

        {/* User Card & Logout Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60">
          {isAuthenticated ? (
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <div className="text-xs font-semibold text-white truncate">
                  {user?.full_name || user?.username}
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span
                    className={`text-[9px] font-bold px-1.5 py-0.2 rounded border uppercase ${getRoleBadgeClass(
                      user?.role
                    )}`}
                  >
                    {user?.role}
                  </span>
                  <span className="text-[10px] text-slate-400 truncate max-w-[100px]">
                    {user?.email}
                  </span>
                </div>
              </div>
              <button
                onClick={handleLogout}
                title="Logout"
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              <Link
                to="/login"
                className="py-1.5 text-center text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-md"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="py-1.5 text-center text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-md"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      </aside>

      {/* ------------------------------------------------------------------ */}
      {/* 2. MAIN CONTAINER & TOP NAVIGATION                                 */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navbar */}
        <header className="sticky top-0 z-30 h-16 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 focus:outline-none"
              aria-label="Open sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div>
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <Link to="/" className="hover:text-indigo-400 transition-colors">
                  Platform
                </Link>
                <ChevronRight className="w-3 h-3 text-slate-600" />
                <span className="text-slate-200 font-medium">Analytics</span>
              </div>
              <h1 className="text-sm sm:text-base font-bold text-white tracking-tight">
                {getPageTitle(location.pathname)}
              </h1>
            </div>
          </div>

          {/* Right Status Actions */}
          <div className="flex items-center gap-3">
            {/* Backend status badge */}
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                backendStatus === "online"
                  ? "bg-emerald-950/60 border-emerald-700/50 text-emerald-400"
                  : backendStatus === "checking"
                  ? "bg-amber-950/60 border-amber-700/50 text-amber-400"
                  : "bg-rose-950/60 border-rose-700/50 text-rose-400"
              }`}
              title={`FastAPI Service Status: ${backendStatus}`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  backendStatus === "online"
                    ? "bg-emerald-400 animate-pulse"
                    : backendStatus === "checking"
                    ? "bg-amber-400 animate-pulse"
                    : "bg-rose-400"
                }`}
              />
              <span className="hidden sm:inline">FastAPI {backendStatus}</span>
            </div>

            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="hidden md:flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-md transition-colors"
            >
              <span>Swagger Docs</span>
              <ExternalLink className="w-3 h-3" />
            </a>

            <Link
              to="/"
              className="px-2.5 py-1.5 text-xs font-medium text-indigo-300 bg-indigo-950/70 hover:bg-indigo-900 border border-indigo-800/60 rounded-md transition-colors"
            >
              Roadmap
            </Link>
          </div>
        </header>

        {/* ------------------------------------------------------------------ */}
        {/* 3. MAIN CONTENT VIEW                                               */}
        {/* ------------------------------------------------------------------ */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-6">
          {children}
        </main>

        {/* Platform Footer */}
        <footer className="border-t border-slate-900 py-4 px-6 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Retail KPI Intelligence Platform &copy; {new Date().getFullYear()}</span>
          <span>FastAPI 0.141 &bull; PostgreSQL 18 &bull; PostGIS 3.6 &bull; React 19 &bull; Recharts</span>
        </footer>
      </div>
    </div>
  );
}
