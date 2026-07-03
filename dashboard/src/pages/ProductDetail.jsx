import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from "recharts";
import {
  getProduct, getPriceHistory,
  getCompetitorPriceHistory, addCompetitorUrl, deleteCompetitorUrl
} from "../api";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [competitorHistory, setCompetitorHistory] = useState([]);
  const [urlForm, setUrlForm] = useState({ competitor_name: "", url: "" });
  const [showUrlForm, setShowUrlForm] = useState(false);

  const load = () => {
    getProduct(id).then(r => setProduct(r.data));
    getPriceHistory(id).then(r => setPriceHistory(r.data));
    getCompetitorPriceHistory(id).then(r => setCompetitorHistory(r.data));
  };

  useEffect(() => { load(); }, [id]);

  const handleAddUrl = async () => {
    await addCompetitorUrl(id, urlForm);
    setUrlForm({ competitor_name: "", url: "" });
    setShowUrlForm(false);
    load();
  };

  const handleDeleteUrl = async (urlId) => {
    await deleteCompetitorUrl(urlId);
    load();
  };

  // Build chart data — merge our price history with competitor prices by date
  const chartData = priceHistory.map(h => ({
    date: new Date(h.changed_at).toLocaleDateString(),
    "Our Price": parseFloat(h.new_price),
  }));

  // Get unique competitor names for chart lines
  const competitorNames = [
    ...new Set(competitorHistory.map(r => r.competitor_name))
  ];

  const COLORS = ["#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

  if (!product) return <p style={{ color: "#64748b" }}>Loading...</p>;

  return (
    <div>
      <button onClick={() => navigate("/products")}
        style={{ background: "transparent", color: "#64748b", padding: 0,
          display: "flex", alignItems: "center", gap: 6, marginBottom: 20 }}>
        <ArrowLeft size={16} /> Back to Products
      </button>

      <h1 style={{ fontSize: 24, fontWeight: 700 }}>{product.name}</h1>
      <p style={{ color: "#64748b", marginTop: 4, marginBottom: 28 }}>
        SKU: {product.sku}
      </p>

      {/* Stats row */}
      <div style={{ display: "flex", gap: 16, marginBottom: 28 }}>
        {[
          ["Our Cost", `£${product.our_cost}`, "#1e293b"],
          ["Current Price", `£${product.current_price}`, "#6366f1"],
          ["Min Margin", `${product.min_margin_percent}%`, "#22c55e"],
          ["Max Price", product.max_price ? `£${product.max_price}` : "None",
            "#f59e0b"],
        ].map(([label, value, color]) => (
          <div key={label} style={{
            background: "#fff", border: "1px solid #e2e8f0",
            borderRadius: 12, padding: "16px 20px", flex: 1,
          }}>
            <p style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>
              {label}
            </p>
            <p style={{ fontSize: 22, fontWeight: 700, color }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Price history chart */}
      {priceHistory.length > 0 && (
        <div style={{
          background: "#fff", border: "1px solid #e2e8f0",
          borderRadius: 12, padding: 24, marginBottom: 24,
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>
            Price History
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }}
                tickFormatter={v => `£${v}`} />
              <Tooltip formatter={v => `£${v}`} />
              <Legend />
              <Line type="monotone" dataKey="Our Price"
                stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Competitor prices chart */}
      {competitorHistory.length > 0 && (
        <div style={{
          background: "#fff", border: "1px solid #e2e8f0",
          borderRadius: 12, padding: 24, marginBottom: 24,
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>
            Competitor Price History
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={competitorHistory.map(r => ({
              date: new Date(r.scraped_at).toLocaleDateString(),
              [r.competitor_name]: parseFloat(r.scraped_price),
            }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }}
                tickFormatter={v => `£${v}`} />
              <Tooltip formatter={v => `£${v}`} />
              <Legend />
              {competitorNames.map((name, i) => (
                <Line key={name} type="monotone" dataKey={name}
                  stroke={COLORS[i % COLORS.length]}
                  strokeWidth={2} dot={{ r: 3 }} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Competitor URLs */}
      <div style={{
        background: "#fff", border: "1px solid #e2e8f0",
        borderRadius: 12, padding: 24,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between",
          alignItems: "center", marginBottom: 16 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600 }}>Competitor URLs</h2>
          <button onClick={() => setShowUrlForm(!showUrlForm)}
            style={{ background: "#6366f1", color: "#fff",
              display: "flex", alignItems: "center", gap: 6,
              padding: "6px 14px", fontSize: 13 }}>
            <Plus size={14} /> Add URL
          </button>
        </div>

        {showUrlForm && (
          <div style={{ display: "flex", gap: 8,
            marginBottom: 16, alignItems: "flex-end" }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 12, color: "#64748b",
                display: "block", marginBottom: 4 }}>
                Competitor Name
              </label>
              <input value={urlForm.competitor_name}
                onChange={e => setUrlForm({
                  ...urlForm, competitor_name: e.target.value
                })}
                placeholder="e.g. amazon" />
            </div>
            <div style={{ flex: 2 }}>
              <label style={{ fontSize: 12, color: "#64748b",
                display: "block", marginBottom: 4 }}>
                URL
              </label>
              <input value={urlForm.url}
                onChange={e => setUrlForm({ ...urlForm, url: e.target.value })}
                placeholder="https://..." />
            </div>
            <button onClick={handleAddUrl}
              style={{ background: "#22c55e", color: "#fff",
                padding: "8px 16px", flexShrink: 0 }}>
              Add
            </button>
          </div>
        )}

        {product.competitor_urls?.length === 0 ? (
          <p style={{ color: "#94a3b8" }}>No competitor URLs yet.</p>
        ) : (
          product.competitor_urls?.map(u => (
            <div key={u.id} style={{
              display: "flex", justifyContent: "space-between",
              alignItems: "center", padding: "10px 0",
              borderBottom: "1px solid #f1f5f9",
            }}>
              <div>
                <p style={{ fontWeight: 500 }}>{u.competitor_name}</p>
                <a href={u.url} target="_blank" rel="noreferrer"
                  style={{ color: "#6366f1", fontSize: 12 }}>
                  {u.url.slice(0, 60)}...
                </a>
              </div>
              <button onClick={() => handleDeleteUrl(u.id)}
                style={{ background: "#fef2f2", color: "#ef4444",
                  padding: "6px 10px",
                  display: "flex", alignItems: "center", gap: 4 }}>
                <Trash2 size={13} /> Remove
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}