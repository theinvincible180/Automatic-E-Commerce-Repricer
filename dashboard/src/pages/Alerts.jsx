import { useEffect, useState } from "react";
import { getAlerts } from "../api";
import { AlertTriangle, TrendingUp } from "lucide-react";

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [threshold, setThreshold] = useState(10);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    getAlerts(threshold)
      .then(r => setAlerts(r.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [threshold]);

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
        Alerts
      </h1>
      <p style={{ color: "#64748b", marginBottom: 24 }}>
        Products with significant recent price changes
      </p>

      {/* Threshold control */}
      <div style={{
        background: "#fff", border: "1px solid #e2e8f0",
        borderRadius: 12, padding: "16px 24px",
        display: "flex", alignItems: "center",
        gap: 16, marginBottom: 24,
      }}>
        <label style={{ fontWeight: 500, whiteSpace: "nowrap" }}>
          Alert threshold:
        </label>
        <input type="range" min="1" max="50" value={threshold}
          onChange={e => setThreshold(Number(e.target.value))}
          style={{ width: 160 }}
        />
        <span style={{ fontWeight: 700, color: "#6366f1",
          minWidth: 40 }}>{threshold}%</span>
        <p style={{ color: "#64748b", fontSize: 13 }}>
          Showing products where price changed by ≥{threshold}%
        </p>
      </div>

      {loading ? (
        <p style={{ color: "#64748b" }}>Loading...</p>
      ) : alerts.length === 0 ? (
        <div style={{
          background: "#fff", border: "1px solid #e2e8f0",
          borderRadius: 12, padding: 48, textAlign: "center",
        }}>
          <AlertTriangle size={32} style={{ color: "#94a3b8",
            margin: "0 auto 12px" }} />
          <p style={{ color: "#64748b" }}>
            No alerts at {threshold}% threshold.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {alerts.map(a => (
            <div key={a.product_id} style={{
              background: "#fff", border: "1px solid #fca5a5",
              borderLeft: "4px solid #ef4444",
              borderRadius: 12, padding: "16px 24px",
              display: "flex", justifyContent: "space-between",
              alignItems: "center",
            }}>
              <div>
                <p style={{ fontWeight: 600, fontSize: 15 }}>{a.name}</p>
                <p style={{ color: "#64748b", fontSize: 13, marginTop: 4 }}>
                  {a.reason}
                </p>
                <p style={{ color: "#94a3b8", fontSize: 12, marginTop: 2 }}>
                  {new Date(a.changed_at).toLocaleString()}
                </p>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ display: "flex", alignItems: "center",
                  gap: 8, justifyContent: "flex-end" }}>
                  <span style={{ color: "#94a3b8",
                    textDecoration: "line-through" }}>
                    £{a.old_price}
                  </span>
                  <span>→</span>
                  <span style={{ fontWeight: 700, fontSize: 18,
                    color: "#ef4444" }}>£{a.new_price}</span>
                </div>
                <span style={{
                  display: "inline-flex", alignItems: "center",
                  gap: 4, marginTop: 6, fontSize: 12, fontWeight: 600,
                  color: "#ef4444", background: "#fef2f2",
                  padding: "2px 10px", borderRadius: 20,
                }}>
                  <TrendingUp size={12} />
                  {parseFloat(a.change_percent).toFixed(1)}% change
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}