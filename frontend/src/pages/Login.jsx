import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { 
  Lock, 
  Mail, 
  ArrowRight, 
  ShieldCheck, 
  AlertCircle, 
  Eye, 
  EyeOff, 
  Loader2,
  Sparkles,
  UserCheck
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState("");

  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // If already logged in, navigate directly
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError("");
    setSubmitting(true);

    try {
      await login(username, password);
      const destination = location.state?.from?.pathname || "/dashboard";
      navigate(destination, { replace: true });
    } catch (err) {
      setLocalError(err.message || "Invalid credentials. Please verify your email/password.");
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemoAccount = (demoUser, demoPass) => {
    setUsername(demoUser);
    setPassword(demoPass);
    setLocalError("");
  };

  return (
    <div className="max-w-md mx-auto my-8 bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex p-3 bg-indigo-600/20 text-indigo-400 rounded-xl mb-3 border border-indigo-500/30">
          <Lock className="w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Executive Sign In</h1>
        <p className="text-xs text-slate-400 mt-1">
          Access your real-time retail KPIs, spatial analytics, and AI analyst
        </p>
      </div>

      {/* Error Alert */}
      {localError && (
        <div className="mb-5 p-3 rounded-lg bg-rose-950/70 border border-rose-700/60 text-rose-300 text-xs flex items-start gap-2.5 animate-fadeIn">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-rose-400" />
          <span className="leading-relaxed">{localError}</span>
        </div>
      )}

      {/* Login Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
            Email or Username
          </label>
          <div className="relative">
            <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="analyst@retailkpi.com or username"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-3 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
            Password
          </label>
          <div className="relative">
            <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            <input
              type={showPassword ? "text" : "password"}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-10 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-3 text-slate-500 hover:text-slate-300 focus:outline-none"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg text-sm transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer mt-2"
        >
          {submitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Authenticating...</span>
            </>
          ) : (
            <>
              <span>Sign In to Platform</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      {/* Demo Credentials Section */}
      <div className="mt-6 pt-5 border-t border-slate-800">
        <div className="flex items-center gap-1.5 text-xs text-indigo-400 font-semibold mb-2.5">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Quick Demo One-Click Login:</span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() => fillDemoAccount("analyst@retailkpi.com", "Analyst@2026")}
            className="px-2 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-md text-[11px] text-slate-300 hover:text-white transition-all text-center"
          >
            <div className="font-semibold text-indigo-400">Analyst</div>
            <div className="text-[10px] text-slate-500">Read-Write</div>
          </button>
          <button
            type="button"
            onClick={() => fillDemoAccount("admin@retailkpi.com", "Admin@2026")}
            className="px-2 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-md text-[11px] text-slate-300 hover:text-white transition-all text-center"
          >
            <div className="font-semibold text-emerald-400">Admin</div>
            <div className="text-[10px] text-slate-500">Full Access</div>
          </button>
          <button
            type="button"
            onClick={() => fillDemoAccount("manager@retailkpi.com", "Manager@2026")}
            className="px-2 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-md text-[11px] text-slate-300 hover:text-white transition-all text-center"
          >
            <div className="font-semibold text-amber-400">Manager</div>
            <div className="text-[10px] text-slate-500">Store Ops</div>
          </button>
        </div>
      </div>

      {/* Footer Navigation */}
      <div className="mt-6 pt-4 border-t border-slate-800 text-center text-xs text-slate-400 space-y-2">
        <p>
          Don't have an account yet?{" "}
          <Link to="/register" className="text-indigo-400 font-semibold hover:underline">
            Register here
          </Link>
        </p>
        <Link to="/" className="text-slate-500 hover:text-slate-300 inline-block text-[11px]">
          &larr; Back to Platform Architecture
        </Link>
      </div>
    </div>
  );
}
