import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getProducts } from "../api";
import { TrendingUp, TrendingDown, Package, AlertCircle } from "lucide-react";

function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: "#fff", borderRadius: 12, padding: "20px 24px",
      border: "1px solid #e2e8f0", flex: 1,
    }}>
      <p style={{ color: "#64748b", fontSize: 13, marginBottom: 8 }}>{label}</p>
      <p style={{ fontSize: 28, fontWeight: 700, color: color || "#1e293b" }}>
        {value}
      </p>
    </div>
  );
}

export default function Overview() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProducts()
      .then(r => setProducts(r.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ color: "#64748b" }}>Loading...</p>;

  const totalProducts = products.length;
  const withCompetitors = products.filter(
    p => p.competitor_prices?.length > 0
  ).length;

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
        Overview
      </h1>
      <p style={{ color: "#64748b", marginBottom: 28 }}>
        Live pricing dashboard
      </p>

      {/* Stat cards */}
      <div style={{ display: "flex", gap: 16, marginBottom: 32 }}>
        <StatCard label="Total Products" value={totalProducts} />
        <StatCard label="With Competitor Data" value={withCompetitors}
          color="#6366f1" />
        <StatCard label="Needs Repricing"
          value={products.filter(p => {
            const low = p.lowest_competitor_price;
            return low && Math.abs(low - p.current_price) / p.current_price > 0.05;
          }).length}
          color="#f59e0b"
        />
      </div>

      {/* Products table */}
      <div style={{
        background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0",
        overflow: "hidden",
      }}>
        <div style={{ padding: "16px 24px", borderBottom: "1px solid #e2e8f0",
          display: "flex", justifyContent: "space-between", alignItems: "center"
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 600 }}>Products</h2>
          <Link to="/products">
            <button style={{ background: "#6366f1", color: "#fff",
              fontSize: 13, padding: "6px 14px" }}>
              Manage
            </button>
          </Link>
        </div>

        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#f8fafc" }}>
              {["Product", "Our Cost", "Current Price",
                "Lowest Competitor", "Status"].map(h => (
                <th key={h} style={{
                  padding: "12px 24px", textAlign: "left",
                  fontSize: 12, fontWeight: 600, color: "#64748b",
                  textTransform: "uppercase", letterSpacing: "0.05em"
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {products.map((p, i) => {
              const low = p.lowest_competitor_price;
              const diff = low
                ? ((p.current_price - low) / low * 100).toFixed(1)
                : null;
              const isAbove = diff > 0;

              return (
                <tr key={p.id} style={{
                  borderTop: "1px solid #f1f5f9",
                  background: i % 2 === 0 ? "#fff" : "#fafafa"
                }}>
                  <td style={{ padding: "14px 24px" }}>
                    <Link to={`/products/${p.id}`}
                      style={{ color: "#6366f1", fontWeight: 500 }}>
                      {p.name}
                    </Link>
                    <p style={{ color: "#94a3b8", fontSize: 12,
                      marginTop: 2 }}>{p.sku}</p>
                  </td>
                  <td style={{ padding: "14px 24px" }}>£{p.our_cost}</td>
                  <td style={{ padding: "14px 24px", fontWeight: 600 }}>
                    £{p.current_price}
                  </td>
                  <td style={{ padding: "14px 24px" }}>
                    {low ? `£${low}` : "—"}
                  </td>
                  <td style={{ padding: "14px 24px" }}>
                    {diff !== null ? (
                      <span style={{
                        display: "inline-flex", alignItems: "center",
                        gap: 4, fontSize: 12, fontWeight: 500,
                        color: isAbove ? "#ef4444" : "#22c55e",
                        background: isAbove ? "#fef2f2" : "#f0fdf4",
                        padding: "3px 10px", borderRadius: 20,
                      }}>
                        {isAbove
                          ? <TrendingUp size={12} />
                          : <TrendingDown size={12} />}
                        {Math.abs(diff)}% {isAbove ? "above" : "below"}
                      </span>
                    ) : (
                      <span style={{ color: "#94a3b8" }}>No data</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}