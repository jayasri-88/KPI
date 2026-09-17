import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await axios.post("/api/auth/login", {
        username: email,
        password: password,
      });
      localStorage.setItem("access_token", response.data.access_token);
      navigate("/dashboard");
    } catch (err) {
      setError("Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 p-6">
      <div className="bg-white rounded-xl p-8 max-w-md w-full shadow-2xl">
        <h2 className="text-2xl font-bold text-slate-900 mb-6 text-center">Welcome Back</h2>
        
        {error && (
          <div className="mb-4 p-3 rounded bg-red-100 text-red-800 text-sm">
            {error}
          </div>
        )}
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-600 mb-2">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:border-slate-500"
            />
          </div>
          
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-600 mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:border-slate-500"
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 bg-slate-900 text-white rounded-md font-medium hover:bg-slate-800 transition-colors disabled:opacity-50"
          >
            {loading ? "Logging in..." : "Sign In"}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-sm text-slate-500">
            Don't have an account? <span onClick={() => navigate("/register")} className="text-slate-600 hover-underline">Sign Up</span>
          </p>
        </div>
      </div>
    </div>
  );
}