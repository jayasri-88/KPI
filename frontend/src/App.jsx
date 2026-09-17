import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Analytics from "./pages/Analytics";
import Sales from "./pages/Sales";
import Stores from "./pages/Stores";
import Products from "./pages/Products";
import Customers from "./pages/Customers";
import Forecast from "./pages/Forecast";
import Assistant from "./pages/Assistant";
import Login from "./pages/Auth/Login";
import Register from "./pages/Auth/Register";
import { useEffect } from "react";
import { useLocation } from "react-router-dom";

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Check auth on mount
    const token = localStorage.getItem("access_token");
    if (!token && location.pathname !== "/login" && location.pathname !== "/register") {
      navigate("/login");
    }
  }, [navigate, location.pathname]);

  return (
    <Router>
      <nav className="border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold text-slate-900">RETAIL KPI</span>
          </div>
          
          <div className="hidden md:flex items-center gap-6">
            <Link to="/dashboard" className="text-slate-600 hover:text-slate-900 transition-colors">
              Dashboard
            </Link>
            <Link to="/analytics" className="text-slate-600 hover:text-slate-900 transition-colors">
              Analytics
            </Link>
            <Link to="/stores" className="text-slate-600 hover:text-slate-900 transition-colors">
              Stores
            </Link>
            <Link to="/products" className="text-slate-600 hover:text-slate-900 transition-colors">
              Products
            </Link>
            <Link to="/customers" className="text-slate-600 hover:text-slate-900 transition-colors">
              Customers
            </Link>
            <Link to="/forecast" className="text-slate-600 hover:text-slate-900 transition-colors">
              Forecast
            </Link>
          </div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={() => localStorage.removeItem("access_token")}
              className="hidden md:flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-md text-sm text-slate-600 hover:bg-slate-100"
            >
              Logout
            </button>
            <button 
              onClick={() => navigate("/login")}
              className="hidden md:flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-md text-sm text-slate-600 hover:bg-slate-100"
            >
              Login
            </button>
          </div>
        </div>
      </nav>

      <main className="min-h-screen bg-slate-50">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            <Route path="/dashboard" element={
              <div className="min-h-screen">
                <Dashboard />
              </div>
            } />
            
            <Route path="/analytics" element={
              <div className="min-h-screen">
                <Analytics />
              </div>
            } />
            
            <Route path="/sales" element={
              <div className="min-h-screen">
                <Sales />
              </div>
            } />
            
            <Route path="/stores" element={
              <div className="min-h-screen">
                <Stores />
              </div>
            } />
            
            <Route path="/products" element={
              <div className="min-h-screen">
                <Products />
              </div>
            } />
            
            <Route path="/customers" element={
              <div className="min-h-screen">
                <Customers />
              </div>
            } />
            
            <Route path="/forecast" element={
              <div className="min-h-screen">
                <Forecast />
              </div>
            } />
            
            <Route path="/assistant" element={
              <div className="min-h-screen">
                <Assistant />
              </div>
            } />
          </Routes>
        </div>
      </main>
    </Router>
  );
}