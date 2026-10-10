import React, { useState, useEffect } from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import { 
  BarChart3, 
  Store, 
  Package, 
  Users, 
  TrendingUp, 
  Bot, 
  Activity, 
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Menu,
  X,
  LogOut,
  UserCircle,
  LogIn,
  UserPlus
} from 'lucide-react';
import { checkHealth } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

export default function Navbar() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    const verifyApi = async () => {
      try {
        const data = await checkHealth();
        if (isMounted) {
          setBackendStatus(data.status === 'healthy' ? 'online' : 'error');
        }
      } catch (err) {
        if (isMounted) {
          setBackendStatus('offline');
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
    navigate('/login');
  };

  const navLinks = [
    { to: '/', label: 'Overview', icon: Activity },
    { to: '/dashboard', label: 'Dashboard', icon: BarChart3 },
    { to: '/sales', label: 'Sales', icon: TrendingUp },
    { to: '/stores', label: 'Stores', icon: Store },
    { to: '/products', label: 'Products', icon: Package },
    { to: '/customers', label: 'Customers', icon: Users },
    { to: '/forecast', label: 'Forecast', icon: TrendingUp },
    { to: '/assistant', label: 'AI Analyst', icon: Bot },
  ];

  const getRoleBadgeClass = (role) => {
    switch (role) {
      case 'admin':
        return 'bg-emerald-950/80 border-emerald-600/60 text-emerald-400';
      case 'manager':
        return 'bg-amber-950/80 border-amber-600/60 text-amber-400';
      default:
        return 'bg-indigo-950/80 border-indigo-600/60 text-indigo-400';
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-slate-900 text-slate-100 border-b border-slate-800 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="p-2 bg-indigo-600 rounded-lg group-hover:bg-indigo-500 transition-colors shadow-sm">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
                Retail KPI
                <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-semibold border border-indigo-500/30">
                  Platform
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Intelligence & Forecasting</p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-1">
            {navLinks.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                      isActive
                        ? 'bg-indigo-600 text-white shadow-sm'
                        : 'text-slate-300 hover:text-white hover:bg-slate-800'
                    }`
                  }
                >
                  <Icon className="w-3.5 h-3.5" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>

          {/* Right status & actions */}
          <div className="flex items-center gap-2.5 sm:gap-3">
            {/* Backend status badge */}
            <div 
              className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                backendStatus === 'online'
                  ? 'bg-emerald-950/60 border-emerald-700/50 text-emerald-400'
                  : backendStatus === 'checking'
                  ? 'bg-amber-950/60 border-amber-700/50 text-amber-400'
                  : 'bg-rose-950/60 border-rose-700/50 text-rose-400'
              }`}
              title={`FastAPI Backend: ${backendStatus}`}
            >
              <span className={`w-2 h-2 rounded-full ${
                backendStatus === 'online' ? 'bg-emerald-400 animate-pulse' :
                backendStatus === 'checking' ? 'bg-amber-400 animate-pulse' : 'bg-rose-400'
              }`} />
              <span>FastAPI {backendStatus}</span>
            </div>

            {/* Auth Session State Controls */}
            {isAuthenticated ? (
              <div className="flex items-center gap-2 pl-1 border-l border-slate-800">
                <div className="hidden md:flex flex-col items-end">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-semibold text-slate-200">
                      {user?.full_name || user?.username}
                    </span>
                    <span className={`text-[10px] uppercase font-bold px-1.5 py-0.2 rounded border ${getRoleBadgeClass(user?.role)}`}>
                      {user?.role}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400">{user?.email}</span>
                </div>

                <button
                  onClick={handleLogout}
                  title="Sign out of Retail KPI Platform"
                  className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-rose-900/60 hover:border-rose-700/60 border border-slate-700 rounded-md transition-colors cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2 pl-1 border-l border-slate-800">
                <Link
                  to="/login"
                  className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-md transition-colors"
                >
                  <LogIn className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Sign In</span>
                </Link>
                <Link
                  to="/register"
                  className="hidden sm:flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-md transition-colors shadow-sm"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Register</span>
                </Link>
              </div>
            )}

            {/* Mobile menu trigger */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-1.5 text-slate-300 hover:text-white rounded-md hover:bg-slate-800 focus:outline-none"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu dropdown */}
        {mobileMenuOpen && (
          <div className="lg:hidden py-3 border-t border-slate-800 space-y-1">
            {navLinks.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md ${
                      isActive
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-300 hover:text-white hover:bg-slate-800'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </NavLink>
              );
            })}

            <div className="pt-3 border-t border-slate-800 px-3 space-y-2">
              {isAuthenticated ? (
                <div className="flex items-center justify-between text-xs text-slate-300">
                  <div>
                    <span className="font-semibold text-white">{user?.username}</span>
                    <span className="text-slate-500 text-[11px] block">{user?.email}</span>
                  </div>
                  <button
                    onClick={() => {
                      setMobileMenuOpen(false);
                      handleLogout();
                    }}
                    className="px-3 py-1.5 rounded bg-rose-950/80 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-1"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Logout</span>
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-2 text-center">
                  <Link
                    to="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="py-1.5 px-3 rounded bg-slate-800 text-slate-200 text-xs font-medium"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/register"
                    onClick={() => setMobileMenuOpen(false)}
                    className="py-1.5 px-3 rounded bg-indigo-600 text-white text-xs font-medium"
                  >
                    Register
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
