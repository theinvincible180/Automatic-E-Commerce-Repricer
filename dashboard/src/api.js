import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export const registerUser = (email, password) =>
  api.post("/auth/register", { email, password });

export const loginUser = (email, password) => {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  return axios.post(`${BASE_URL}/auth/login`, form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
};

export const getProducts = () => api.get("/products/");
export const getProduct = (id) => api.get(`/products/${id}`);
export const createProduct = (data) => api.post("/products/", data);
export const updateProduct = (id, data) => api.patch(`/products/${id}`, data);
export const deleteProduct = (id) => api.delete(`/products/${id}`);

export const addCompetitorUrl = (productId, data) =>
  api.post(`/products/${productId}/competitor-urls`, data);
export const deleteCompetitorUrl = (urlId) =>
  api.delete(`/products/competitor-urls/${urlId}`);

export const getPriceHistory = (productId, limit = 50) =>
  api.get(`/products/${productId}/price-history?limit=${limit}`);
export const getCompetitorPriceHistory = (productId, limit = 100) =>
  api.get(`/products/${productId}/competitor-prices?limit=${limit}`);

export const getAlerts = (threshold = 10) =>
  api.get(`/alerts?threshold_percent=${threshold}`);

export const getPipelineStatus = () => api.get("/pipeline/status");
export const getPipelineLogs = (lines = 200) => api.get(`/pipeline/logs?lines=${lines}`);

export const streamPipeline = (onMessage, onDone, onError) => {
  const token = localStorage.getItem("access_token");
  const source = new EventSource(`${BASE_URL}/pipeline/run?token=${token}`);

  source.onmessage = (e) => {
    if (e.data.startsWith("[DONE]")) {
      onDone();
      source.close();
    } else if (e.data.startsWith("[ERROR]")) {
      onError(e.data);
      source.close();
    } else {
      onMessage(e.data);
    }
  };

  source.onerror = () => {
    onError("Connection error.");
    source.close();
  };

  return source;
};


export const getSchedulerStatus = () => api.get("/scheduler/status");
export const setSchedulerInterval = (hours) => api.post("/scheduler/interval", { hours });
export const pauseScheduler = () => api.post("/scheduler/pause");
export const resumeScheduler = () => api.post("/scheduler/resume");

export default api;