import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// Attach the token to every outgoing request automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If any request comes back 401, the token is invalid/expired — log the user out
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

// ── Auth ────────────────────────────────────────────────────
export const registerUser = (email, password) =>
  api.post("/auth/register", { email, password });

export const loginUser = (email, password) => {
  // Backend expects form data, not JSON, for OAuth2PasswordRequestForm
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  return axios.post("http://localhost:8000/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
};

// ── Products ────────────────────────────────────────────────
export const getProducts = () => api.get("/products/");
export const getProduct = (id) => api.get(`/products/${id}`);
export const createProduct = (data) => api.post("/products/", data);
export const updateProduct = (id, data) => api.patch(`/products/${id}`, data);
export const deleteProduct = (id) => api.delete(`/products/${id}`);

// ── Competitor URLs ─────────────────────────────────────────
export const addCompetitorUrl = (productId, data) =>
  api.post(`/products/${productId}/competitor-urls`, data);
export const deleteCompetitorUrl = (urlId) =>
  api.delete(`/products/competitor-urls/${urlId}`);

// ── Prices ──────────────────────────────────────────────────
export const getPriceHistory = (productId, limit = 50) =>
  api.get(`/products/${productId}/price-history?limit=${limit}`);
export const getCompetitorPriceHistory = (productId, limit = 100) =>
  api.get(`/products/${productId}/competitor-prices?limit=${limit}`);

// ── Alerts ──────────────────────────────────────────────────
export const getAlerts = (threshold = 10) =>
  api.get(`/alerts?threshold_percent=${threshold}`);

// ── Pipeline ────────────────────────────────────────────────
export const getPipelineStatus = () => api.get("/pipeline/status");
export const getPipelineLogs = (lines = 200) => api.get(`/pipeline/logs?lines=${lines}`);

// SSE can't send headers, so the token goes in the query string instead
export const streamPipeline = (onMessage, onDone, onError) => {
  const token = localStorage.getItem("access_token");
  const source = new EventSource(`http://localhost:8000/pipeline/run?token=${token}`);

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

  source.onerror = (e) => {
    onError("Connection error.");
    source.close();
  };

  return source;
};

export default api;