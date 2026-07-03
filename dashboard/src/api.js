import axios from "axios";

// Base URL for all API calls — points to your FastAPI server
const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

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

// SSE stream for live pipeline logs — returns an EventSource
// EventSource is the browser's built-in SSE client
export const streamPipeline = (onMessage, onDone, onError) => {
  const source = new EventSource("http://localhost:8000/pipeline/run");
  
  source.onmessage = (e) => {
    if (e.data === "[DONE] Pipeline complete.") {
      onDone();
      source.close();
    } else {
      onMessage(e.data);
    }
  };

  source.onerror = (e) => {
    onError(e);
    source.close();
  };

  return source; // return so caller can close it if needed
};

export default api;
export const getPipelineLogs = () => api.get("/pipeline/logs");