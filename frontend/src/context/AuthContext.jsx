import React, { createContext, useContext, useState, useEffect } from "react";
import { loginUser, registerUser, getCurrentUser, logoutUser, extractErrorMessage } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem("access_token") || null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Hydrate user profile on application boot if a token exists
  useEffect(() => {
    let isMounted = true;

    const bootstrapAuth = async () => {
      const storedToken = localStorage.getItem("access_token");
      if (!storedToken) {
        if (isMounted) {
          setUser(null);
          setLoading(false);
        }
        return;
      }

      try {
        const userData = await getCurrentUser();
        if (isMounted) {
          setUser(userData);
          setToken(storedToken);
          setAuthError(null);
        }
      } catch (err) {
        console.warn("Stored JWT invalid or session expired:", err.message);
        if (isMounted) {
          localStorage.removeItem("access_token");
          setUser(null);
          setToken(null);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    bootstrapAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = async (username, password) => {
    setLoading(true);
    setAuthError(null);
    try {
      const data = await loginUser({ username, password });
      const { access_token, user: profile } = data;
      localStorage.setItem("access_token", access_token);
      setToken(access_token);
      setUser(profile);
      return profile;
    } catch (err) {
      const msg = extractErrorMessage(err) || "Invalid username or password. Please try again.";
      setAuthError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    setLoading(true);
    setAuthError(null);
    try {
      const data = await registerUser(userData);
      const { access_token, user: profile } = data;
      localStorage.setItem("access_token", access_token);
      setToken(access_token);
      setUser(profile);
      return profile;
    } catch (err) {
      const msg = extractErrorMessage(err) || "Registration failed. Please check inputs and try again.";
      setAuthError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await logoutUser();
      }
    } catch (err) {
      console.warn("Backend logout notification warning:", err.message);
    } finally {
      localStorage.removeItem("access_token");
      setUser(null);
      setToken(null);
      setAuthError(null);
    }
  };

  const clearError = () => setAuthError(null);

  const value = {
    user,
    token,
    loading,
    authError,
    isAuthenticated: Boolean(user && token),
    login,
    register,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
