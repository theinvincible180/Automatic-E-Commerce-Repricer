import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getProducts, createProduct, deleteProduct } from "../api";
import { Plus, Trash2, ExternalLink } from "lucide-react";

const emptyForm = {
  name: "", sku: "", our_cost: "", min_margin_percent: "",
  max_price: "", current_price: "",
};

export default function Products() {
  const [products, setProducts] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = () => getProducts().then(r => setProducts(r.data));

  useEffect(() => { load(); }, []);

  const handleSubmit = async () => {
    setSaving(true);
    setError("");
    try {
      await createProduct({
        ...form,
        our_cost: parseFloat(form.our_cost),
        min_margin_percent: parseFloat(form.min_margin_percent),
        max_price: form.max_price ? parseFloat(form.max_price) : null,
        current_price: parseFloat(form.current_price),
      });
      setForm(emptyForm);
      setShowForm(false);
      load();
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to create product.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    await deleteProduct(id);
    load();
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between",
        alignItems: "center", marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700 }}>Products</h1>
          <p style={{ color: "#64748b", marginTop: 4 }}>
            Manage your product catalogue
          </p>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          style={{ background: "#6366f1", color: "#fff",
            display: "flex", alignItems: "center", gap: 6 }}>
          <Plus size={16} /> Add Product
        </button>
      </div>

      {/* Add product form */}
      {showForm && (
        <div style={{
          background: "#fff", border: "1px solid #e2e8f0",
          borderRadius: 12, padding: 24, marginBottom: 24,
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
            New Product
          </h2>
          {error && (
            <p style={{ color: "#ef4444", marginBottom: 12,
              background: "#fef2f2", padding: "8px 12px",
              borderRadius: 6 }}>{error}</p>
          )}
          <div style={{ display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
            {[
              ["Product Name", "name", "text"],
              ["SKU", "sku", "text"],
              ["Our Cost (£)", "our_cost", "number"],
              ["Min Margin %", "min_margin_percent", "number"],
              ["Max Price (£)", "max_price", "number"],
              ["Current Price (£)", "current_price", "number"],
            ].map(([label, key, type]) => (
              <div key={key}>
                <label style={{ display: "block", fontSize: 12,
                  fontWeight: 500, color: "#64748b", marginBottom: 4 }}>
                  {label}
                </label>
                <input type={type} value={form[key]}
                  onChange={e => setForm({ ...form, [key]: e.target.value })}
                  placeholder={label}
                />
              </div>
            ))}
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
            <button onClick={handleSubmit} disabled={saving}
              style={{ background: "#6366f1", color: "#fff" }}>
              {saving ? "Saving..." : "Create Product"}
            </button>
            <button onClick={() => setShowForm(false)}
              style={{ background: "#f1f5f9", color: "#1e293b" }}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Products list */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {products.map(p => (
          <div key={p.id} style={{
            background: "#fff", border: "1px solid #e2e8f0",
            borderRadius: 12, padding: "16px 24px",
            display: "flex", alignItems: "center",
            justifyContent: "space-between",
          }}>
            <div>
              <p style={{ fontWeight: 600, fontSize: 15 }}>{p.name}</p>
              <p style={{ color: "#64748b", fontSize: 12,
                marginTop: 2 }}>SKU: {p.sku}</p>
            </div>
            <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
              <div style={{ textAlign: "center" }}>
                <p style={{ fontSize: 11, color: "#94a3b8" }}>Cost</p>
                <p style={{ fontWeight: 600 }}>£{p.our_cost}</p>
              </div>
              <div style={{ textAlign: "center" }}>
                <p style={{ fontSize: 11, color: "#94a3b8" }}>Price</p>
                <p style={{ fontWeight: 600, color: "#6366f1" }}>
                  £{p.current_price}
                </p>
              </div>
              <div style={{ textAlign: "center" }}>
                <p style={{ fontSize: 11, color: "#94a3b8" }}>Margin</p>
                <p style={{ fontWeight: 600, color: "#22c55e" }}>
                  {(((p.current_price - p.our_cost)
                    / p.current_price) * 100).toFixed(1)}%
                </p>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <Link to={`/products/${p.id}`}>
                  <button style={{ background: "#f1f5f9",
                    color: "#1e293b", padding: "6px 12px",
                    display: "flex", alignItems: "center", gap: 4 }}>
                    <ExternalLink size={14} /> View
                  </button>
                </Link>
                <button onClick={() => handleDelete(p.id, p.name)}
                  style={{ background: "#fef2f2", color: "#ef4444",
                    padding: "6px 12px",
                    display: "flex", alignItems: "center", gap: 4 }}>
                  <Trash2 size={14} /> Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}