import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser, registerUser } from "../api";
import { useAuth } from "../context/AuthContext";
import { Lock } from "lucide-react";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState("login"); // "login" or "register"
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "register") {
        await registerUser(email, password);
        // auto-login right after successful registration
      }
      const res = await loginUser(email, password);
      login(res.data.access_token);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex",
      alignItems: "center", justifyContent: "center",
      background: "#f8fafc",
    }}>
      <div style={{
        background: "#fff", padding: 40, borderRadius: 12,
        border: "1px solid #e2e8f0", width: 360,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10,
          marginBottom: 24 }}>
          <div style={{
            background: "#6366f1", borderRadius: 8, padding: 8,
            display: "flex",
          }}>
            <Lock size={18} color="#fff" />
          </div>
          <div>
            <p style={{ fontWeight: 700, fontSize: 16 }}>Repricer Agent</p>
            <p style={{ color: "#64748b", fontSize: 12 }}>
              {mode === "login" ? "Sign in to continue" : "Create an account"}
            </p>
          </div>
        </div>

        {error && (
          <p style={{ color: "#ef4444", background: "#fef2f2",
            padding: "8px 12px", borderRadius: 6, fontSize: 13,
            marginBottom: 16 }}>{error}</p>
        )}

        <form onSubmit={handleSubmit}>
          <label style={{ display: "block", fontSize: 12, fontWeight: 500,
            color: "#64748b", marginBottom: 4 }}>Email</label>
          <input type="email" value={email} required
            onChange={e => setEmail(e.target.value)}
            placeholder="you@example.com"
            style={{ marginBottom: 14 }} />

          <label style={{ display: "block", fontSize: 12, fontWeight: 500,
            color: "#64748b", marginBottom: 4 }}>Password</label>
          <input type="password" value={password} required
            onChange={e => setPassword(e.target.value)}
            placeholder="••••••••"
            style={{ marginBottom: 20 }} />

          <button type="submit" disabled={loading}
            style={{ background: "#6366f1", color: "#fff",
              width: "100%", padding: "10px 0", fontSize: 14 }}>
            {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Register"}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: 16, fontSize: 13,
          color: "#64748b" }}>
          {mode === "login" ? "No account?" : "Already have an account?"}{" "}
          <span onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
            style={{ color: "#6366f1", cursor: "pointer", fontWeight: 500 }}>
            {mode === "login" ? "Register" : "Sign in"}
          </span>
        </p>
      </div>
    </div>
  );
}