import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import Analytics from "./pages/Analytics";
import Stores from "./pages/Stores";
import Products from "./pages/Products";
import Customers from "./pages/Customers";
import Inventory from "./pages/Inventory";
import Forecast from "./pages/Forecast";
import Assistant from "./pages/Assistant";
import Login from "./pages/Auth/Login";
import Register from "./pages/Auth/Register";

const PUBLIC_PATHS = ["/login", "/register"];

const NAV_LINKS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/analytics", label: "Analytics" },
  { to: "/stores", label: "Stores" },
  { to: "/products", label: "Products" },
  { to: "/inventory", label: "Inventory" },
  { to: "/customers", label: "Customers" },
  { to: "/forecast", label: "Forecast" },
];

function AppShell() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token && !PUBLIC_PATHS.includes(location.pathname)) {
      navigate("/login");
    }
  }, [navigate, location.pathname]);

  return (
    <div className="min-h-screen">
      <nav className="border-b border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold text-slate-900">RETAIL KPI</span>
          </div>

          <div className="hidden md:flex items-center gap-6">
            {NAV_LINKS.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={
                  location.pathname === to
                    ? "text-slate-900 font-medium transition-colors"
                    : "text-slate-600 hover:text-slate-900 transition-colors"
                }
              >
                {label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                localStorage.removeItem("access_token");
                navigate("/login");
              }}
              className="hidden md:flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-md text-sm text-slate-600 hover:bg-slate-100"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <main>
        <div className="max-w-7xl mx-auto px-6 py-8">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/stores" element={<Stores />} />
            <Route path="/products" element={<Products />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/assistant" element={<Assistant />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AppShell />
    </Router>
  );
}
