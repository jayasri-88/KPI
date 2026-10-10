import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Loader2 } from "lucide-react";

export default function ProtectedRoute({ children, requiredRole = null }) {
  const { user, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        <p className="text-xs text-slate-400 font-medium">
          Verifying session credentials...
        </p>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect unauthenticated user to /login and preserve destination for seamless return
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user?.role !== requiredRole && !user?.is_superuser) {
    return (
      <div className="max-w-md mx-auto my-12 bg-slate-900 border border-rose-800/40 rounded-2xl p-6 text-center shadow-xl">
        <h2 className="text-lg font-bold text-rose-400 mb-2">Access Restricted</h2>
        <p className="text-xs text-slate-400">
          Your current role (<strong>{user?.role}</strong>) does not have authorization
          to view this administrative section.
        </p>
      </div>
    );
  }

  return children;
}
