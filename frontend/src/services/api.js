import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api";

// Create axios instance with auth token
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to add auth token to requests
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

// Dashboard APIs
export const getDashboardOverview = async () => {
  const response = await api.get("/dashboard/overview");
  return response.data;
};

export const getSalesTrend = async () => {
  const response = await api.get("/analytics/sales-trend");
  return response.data;
};

export const getRegionPerformance = async () => {
  const response = await api.get("/analytics/region-performance");
  return response.data;
};

export const getCategoryPerformance = async () => {
  const response = await api.get("/analytics/category-performance");
  return response.data;
};

export const getSkuIntelligence = async () => {
  const response = await api.get("/sku/intelligence");
  return response.data;
};

export const getInventorySummary = async () => {
  const response = await api.get("/inventory/summary");
  return response.data;
};

export const getInventoryAlerts = async () => {
  const response = await api.get("/inventory/alerts");
  return response.data;
};

// Auth APIs
export const loginUser = async (credentials) => {
  const response = await api.post("/auth/login", credentials);
  return response.data;
};

export const registerUser = async (userData) => {
  const response = await api.post("/auth/register", userData);
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get("/auth/me");
  return response.data;
};

// Store APIs
export const listStores = async (params = {}) => {
  const response = await api.get("/stores/", { params });
  return response.data;
};

export const getStore = async (storeId) => {
  const response = await api.get(`/stores/${storeId}`);
  return response.data;
};

// Product APIs
export const listProducts = async (params = {}) => {
  const response = await api.get("/products/", { params });
  return response.data;
};

export const getProduct = async (productId) => {
  const response = await api.get(`/products/${productId}`);
  return response.data;
};

// Customer APIs
export const listCustomers = async (params = {}) => {
  const response = await api.get("/customers/", { params });
  return response.data;
};

// Order APIs
export const listOrders = async (params = {}) => {
  const response = await api.get("/orders/", { params });
  return response.data;
};

// Forecast APIs
export const getForecast = async () => {
  const response = await api.get("/forecast");
  return response.data;
};

// Assistant/AI APIs
export const askQuestion = async (question) => {
  const response = await api.post("/assistant/ask", { question });
  return response.data;
};

export default api;