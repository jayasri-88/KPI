import axios from "axios";

// Automatically resolve API URL in production (e.g. Render/Vercel) or development proxy
const rawApiUrl = (import.meta.env.VITE_API_URL || "").trim().replace(/\/+$/, "");
const API_BASE_URL = rawApiUrl
  ? (rawApiUrl.endsWith("/api") ? rawApiUrl : `${rawApiUrl}/api`)
  : "/api";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

// Interceptor to attach JWT token to every outgoing request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor to handle common response errors & stale session revocation
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const requestUrl = error.config?.url || "";
      // Do not clear credentials or force redirect on initial login/register attempt failures
      if (!requestUrl.includes("/auth/login") && !requestUrl.includes("/auth/register")) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
          window.location.href = "/login?session_expired=true";
        }
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Standardizes backend error messages from either structured { error: { message } }
 * or FastAPI { detail: "..." } schemas.
 */
export const extractErrorMessage = (error) => {
  if (!error) return "An unexpected error occurred.";
  if (error.response?.data) {
    const data = error.response.data;
    if (data.error?.message) return data.error.message;
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail) && data.detail.length > 0) {
      return data.detail.map((d) => d.msg || JSON.stringify(d)).join(", ");
    }
  }
  return error.message || "Network request failed.";
};

// Health check
export const checkHealth = async () => {
  const response = await api.get("/v1/health");
  return response.data;
};

// ----------------------------------------------------------------------------
// 1. Authentication APIs
// ----------------------------------------------------------------------------
export const loginUser = async (credentials) => {
  const response = await api.post("/v1/auth/login", credentials);
  return response.data;
};

export const registerUser = async (userData) => {
  const response = await api.post("/v1/auth/register", userData);
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get("/v1/auth/me");
  return response.data;
};

export const logoutUser = async () => {
  const response = await api.post("/v1/auth/logout");
  return response.data;
};

// ----------------------------------------------------------------------------
// 2. Executive Dashboard APIs
// ----------------------------------------------------------------------------
export const getDashboardOverview = async (params = {}) => {
  const response = await api.get("/v1/dashboard/overview", { params });
  return response.data;
};

export const getSalesTrend = async (params = {}) => {
  const response = await api.get("/v1/dashboard/sales-trend", { params });
  return response.data;
};

export const getTopProducts = async (params = {}) => {
  const response = await api.get("/v1/dashboard/top-products", { params });
  return response.data;
};

export const getTopStores = async (params = {}) => {
  const response = await api.get("/v1/dashboard/top-stores", { params });
  return response.data;
};

// ----------------------------------------------------------------------------
// 3. Store APIs
// ----------------------------------------------------------------------------
export const listStores = async (params = {}) => {
  const response = await api.get("/v1/stores", { params });
  return response.data;
};

export const getStorePerformance = async (params = {}) => {
  const response = await api.get("/v1/stores/performance", { params });
  return response.data;
};

export const getStoresSpatial = async (params = {}) => {
  const response = await api.get("/v1/stores/spatial", { params });
  return response.data;
};

export const getRegionalPerformance = async (params = {}) => {
  const response = await api.get("/v1/stores/geographic/regions", { params });
  return response.data;
};

export const getStore = async (storeId) => {
  const response = await api.get(`/v1/stores/${storeId}`);
  return response.data;
};

// ----------------------------------------------------------------------------
// 4. Product APIs
// ----------------------------------------------------------------------------
export const listProducts = async (params = {}) => {
  const response = await api.get("/v1/products", { params });
  return response.data;
};

export const getProduct = async (productId) => {
  const response = await api.get(`/v1/products/${productId}`);
  return response.data;
};

// ----------------------------------------------------------------------------
// 5. Category APIs
// ----------------------------------------------------------------------------
export const listCategories = async (params = {}) => {
  const response = await api.get("/v1/categories", { params });
  return response.data;
};

export const getCategory = async (categoryId) => {
  const response = await api.get(`/v1/categories/${categoryId}`);
  return response.data;
};

// ----------------------------------------------------------------------------
// 6. Customer APIs
// ----------------------------------------------------------------------------
export const listCustomers = async (params = {}) => {
  const response = await api.get("/v1/customers", { params });
  return response.data;
};

export const getCustomer = async (customerId) => {
  const response = await api.get(`/v1/customers/${customerId}`);
  return response.data;
};

// ----------------------------------------------------------------------------
// 7. Order APIs
// ----------------------------------------------------------------------------
export const listOrders = async (params = {}) => {
  const response = await api.get("/v1/orders", { params });
  return response.data;
};

export const getOrder = async (orderId) => {
  const response = await api.get(`/v1/orders/${orderId}`);
  return response.data;
};

export const createOrder = async (orderData) => {
  const response = await api.post("/v1/orders", orderData);
  return response.data;
};

// ----------------------------------------------------------------------------
// 8. Sales APIs
// ----------------------------------------------------------------------------
export const listSales = async (params = {}) => {
  const response = await api.get("/v1/sales", { params });
  return response.data;
};

export const getSalesSummary = async (params = {}) => {
  const response = await api.get("/v1/sales/summary", { params });
  return response.data;
};

// ----------------------------------------------------------------------------
// 9. Inventory APIs
// ----------------------------------------------------------------------------
export const listInventory = async (params = {}) => {
  const response = await api.get("/v1/inventory", { params });
  return response.data;
};

export const getInventoryAlerts = async (params = {}) => {
  const response = await api.get("/v1/inventory/alerts", { params });
  return response.data;
};

export const updateInventoryItem = async (inventoryId, updateData) => {
  const response = await api.put(`/v1/inventory/${inventoryId}`, updateData);
  return response.data;
};

export const restockInventoryItem = async (inventoryId, quantity) => {
  const response = await api.post(`/v1/inventory/${inventoryId}/restock`, { quantity });
  return response.data;
};

// ----------------------------------------------------------------------------
// 10. ML Analytics & Forecasting APIs (Phase 8)
// ----------------------------------------------------------------------------
export const getSalesTrendAnalytics = async (params = {}) => {
  const response = await api.get("/v1/analytics/sales-trend", { params });
  return response.data;
};

export const getDemandAnalytics = async () => {
  const response = await api.get("/v1/analytics/demand");
  return response.data;
};

export const getProductPerformanceAnalytics = async (params = {}) => {
  const response = await api.get("/v1/analytics/product-performance", { params });
  return response.data;
};

export const getSalesForecast = async (params = {}) => {
  const response = await api.get("/v1/forecast/sales", { params });
  return response.data;
};

export const retrainForecast = async (params = {}) => {
  const response = await api.post("/v1/forecast/train", null, { params });
  return response.data;
};

export const getForecastFeatures = async () => {
  const response = await api.get("/v1/forecast/features");
  return response.data;
};

// Backwards compatibility alias
// ----------------------------------------------------------------------------
// 11. AI Retail Analyst Agent APIs (Phase 9)
// ----------------------------------------------------------------------------
export const sendAgentChat = async (message, conversationId = null) => {
  const payload = { message };
  if (conversationId) {
    payload.conversation_id = conversationId;
  }
  const response = await api.post("/v1/agent/chat", payload);
  return response.data;
};

export const clearAgentConversation = async (conversationId) => {
  const response = await api.delete(`/v1/agent/conversations/${conversationId}`);
  return response.data;
};

export const askQuestion = async (question) => {
  return sendAgentChat(question);
};

export default api;