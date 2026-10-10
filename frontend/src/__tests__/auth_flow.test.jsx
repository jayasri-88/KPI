import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "../context/AuthContext";
import * as api from "../services/api";

// Mock API functions
vi.mock("../services/api", async () => {
  const actual = await vi.importActual("../services/api");
  return {
    ...actual,
    loginUser: vi.fn(),
    registerUser: vi.fn(),
    getCurrentUser: vi.fn(),
    logoutUser: vi.fn(),
  };
});

// Test component to consume AuthContext
function AuthConsumer() {
  const { user, isAuthenticated, login, logout, authError } = useAuth();
  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? "AUTHENTICATED" : "GUEST"}</div>
      <div data-testid="user-email">{user?.email || "none"}</div>
      {authError && <div data-testid="auth-error">{authError}</div>}
      <button
        onClick={() => login("admin@retailkpi.com", "Admin@2026")}
        data-testid="login-btn"
      >
        Login
      </button>
      <button onClick={() => logout()} data-testid="logout-btn">
        Logout
      </button>
    </div>
  );
}

describe("Authentication Flow and AuthContext", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("starts in guest mode when localStorage contains no token", async () => {
    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    expect(screen.getByTestId("auth-status")).toHaveTextContent("GUEST");
    expect(screen.getByTestId("user-email")).toHaveTextContent("none");
  });

  it("hydrates user profile when a valid token exists in localStorage", async () => {
    localStorage.setItem("access_token", "fake-jwt-token-123");
    api.getCurrentUser.mockResolvedValueOnce({
      id: "user-1",
      email: "hydrated@retailkpi.com",
      role: "analyst",
    });

    await act(async () => {
      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      );
    });

    expect(screen.getByTestId("auth-status")).toHaveTextContent("AUTHENTICATED");
    expect(screen.getByTestId("user-email")).toHaveTextContent("hydrated@retailkpi.com");
  });

  it("successfully logs in, saves token to localStorage, and updates state", async () => {
    api.loginUser.mockResolvedValueOnce({
      access_token: "new-access-token-999",
      user: {
        id: "user-999",
        email: "admin@retailkpi.com",
        role: "admin",
      },
    });

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    const loginButton = screen.getByTestId("login-btn");
    await act(async () => {
      loginButton.click();
    });

    expect(localStorage.getItem("access_token")).toBe("new-access-token-999");
    expect(screen.getByTestId("auth-status")).toHaveTextContent("AUTHENTICATED");
    expect(screen.getByTestId("user-email")).toHaveTextContent("admin@retailkpi.com");
  });

  it("clears token and user state on logout", async () => {
    localStorage.setItem("access_token", "active-token");
    api.getCurrentUser.mockResolvedValueOnce({
      id: "user-1",
      email: "active@retailkpi.com",
      role: "analyst",
    });
    api.logoutUser.mockResolvedValueOnce({ status: "success" });

    await act(async () => {
      render(
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      );
    });

    expect(screen.getByTestId("auth-status")).toHaveTextContent("AUTHENTICATED");

    const logoutButton = screen.getByTestId("logout-btn");
    await act(async () => {
      logoutButton.click();
    });

    expect(localStorage.getItem("access_token")).toBeNull();
    expect(screen.getByTestId("auth-status")).toHaveTextContent("GUEST");
    expect(screen.getByTestId("user-email")).toHaveTextContent("none");
  });
});
