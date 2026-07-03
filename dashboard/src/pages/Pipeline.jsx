import { useState, useRef, useEffect } from "react";
import { Play, Square, Terminal } from "lucide-react";
import { getPipelineLogs } from "../api"; // <-- Import the new API call

export default function Pipeline() {
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [done, setDone] = useState(false);
  const sourceRef = useRef(null);
  const logsEndRef = useRef(null);

  // Fetch log history when the page loads
  useEffect(() => {
    getPipelineLogs().then(r => {
      setLogs(r.data.logs);
      // Scroll to bottom after loading history
      setTimeout(() => logsEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    });
  }, []);

  const startPipeline = () => {
    setDone(false);
    setRunning(true);
    
    // Notice we removed setLogs([]) here so it doesn't erase history!
    
    const source = new EventSource("http://localhost:8000/pipeline/run");
    sourceRef.current = source;

    source.onmessage = (e) => {
      if (e.data.startsWith("[DONE]")) {
        setDone(true);
        setRunning(false);
        source.close();
      } else if (e.data.startsWith("[ERROR]")) {
        setLogs(prev => [...prev, { text: e.data, type: "error" }]);
        setRunning(false);
        source.close();
      } else {
        setLogs(prev => [...prev, { text: e.data, type: "log" }]);
        setTimeout(() => logsEndRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
      }
    };

    source.onerror = () => {
      setLogs(prev => [...prev, { text: "Connection error.", type: "error" }]);
      setRunning(false);
      source.close();
    };
  };

  const stopPipeline = () => {
    sourceRef.current?.close();
    setRunning(false);
    setLogs(prev => [...prev, { text: "Pipeline stopped by user.", type: "error" }]);
  };

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
        Pipeline Control
      </h1>
      <p style={{ color: "#64748b", marginBottom: 28 }}>
        Monitor automated background runs or manually trigger the pipeline
      </p>

      {/* Control panel */}
      <div style={{
        background: "#fff", border: "1px solid #e2e8f0",
        borderRadius: 12, padding: 24, marginBottom: 24,
        display: "flex", alignItems: "center", gap: 16,
      }}>
        <button
          onClick={running ? stopPipeline : startPipeline}
          style={{
            background: running ? "#ef4444" : "#6366f1",
            color: "#fff", padding: "10px 20px",
            display: "flex", alignItems: "center", gap: 8,
            fontSize: 15,
          }}>
          {running ? <><Square size={16} /> Stop</> : <><Play size={16} /> Run Manual Override</>}
        </button>

        {done && (
          <span style={{ color: "#22c55e", fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}>
            ✓ Last run completed successfully
          </span>
        )}
        {running && (
          <span style={{ color: "#f59e0b", fontWeight: 500 }}>
            ⟳ Running...
          </span>
        )}
      </div>

      {/* Live log terminal */}
      <div style={{
        background: "#0f172a", borderRadius: 12,
        padding: 24, minHeight: 400,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16, color: "#94a3b8" }}>
          <Terminal size={16} />
          <span style={{ fontSize: 13, fontFamily: "monospace" }}>
            System Event Log (History & Live)
          </span>
        </div>

        <div style={{ fontFamily: "monospace", fontSize: 13, lineHeight: 1.7, maxHeight: 500, overflowY: "auto" }}>
          {logs.map((log, i) => (
            <div key={i} style={{
              color: log.type === "error" || log.text.includes("❌") ? "#f87171"
                : log.text.includes("✅") || log.text.includes("Saved") ? "#86efac"
                : log.text.includes("⏰") || log.text.includes("🚀") ? "#60a5fa"
                : "#e2e8f0",
              padding: "2px 0",
            }}>
              {log.text}
            </div>
          ))}
          <div ref={logsEndRef} />
        </div>
      </div>
    </div>
  );
}