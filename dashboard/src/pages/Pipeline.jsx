import { useState, useRef } from "react";
import { Play, Square, Terminal } from "lucide-react";
import { streamPipeline } from "../api";

export default function Pipeline() {
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [done, setDone] = useState(false);
  const sourceRef = useRef(null);
  const logsEndRef = useRef(null);

  const startPipeline = () => {
    setLogs([]);
    setDone(false);
    setRunning(true);

    // streamPipeline (from api.js) builds the EventSource URL with
    // the JWT token attached as a query param, since EventSource
    // can't send Authorization headers.
    const source = streamPipeline(
      // onMessage — called for every normal log line
      (line) => {
        setLogs(prev => [...prev, { text: line, type: "log" }]);
        setTimeout(() => logsEndRef.current?.scrollIntoView(
          { behavior: "smooth" }
        ), 50);
      },
      // onDone — called when the backend sends [DONE]
      () => {
        setDone(true);
        setRunning(false);
      },
      // onError — called for [ERROR] lines or connection failures
      (errMsg) => {
        setLogs(prev => [...prev, { text: errMsg, type: "error" }]);
        setRunning(false);
      }
    );

    sourceRef.current = source;
  };

  const stopPipeline = () => {
    sourceRef.current?.close();
    setRunning(false);
    setLogs(prev => [...prev, {
      text: "Pipeline stopped by user.", type: "error"
    }]);
  };

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
        Pipeline Control
      </h1>
      <p style={{ color: "#64748b", marginBottom: 28 }}>
        Manually trigger the full repricing pipeline
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
          {running ? <><Square size={16} /> Stop</> : <><Play size={16} /> Run Pipeline</>}
        </button>

        {done && (
          <span style={{
            color: "#22c55e", fontWeight: 600,
            display: "flex", alignItems: "center", gap: 6
          }}>
            ✓ Pipeline completed successfully
          </span>
        )}

        {running && (
          <span style={{ color: "#f59e0b", fontWeight: 500 }}>
            ⟳ Running...
          </span>
        )}
      </div>

      {/* Live log terminal */}
      {logs.length > 0 && (
        <div style={{
          background: "#0f172a", borderRadius: 12,
          padding: 24, minHeight: 300,
        }}>
          <div style={{ display: "flex", alignItems: "center",
            gap: 8, marginBottom: 16, color: "#94a3b8" }}>
            <Terminal size={16} />
            <span style={{ fontSize: 13, fontFamily: "monospace" }}>
              Pipeline output
            </span>
          </div>
          <div style={{ fontFamily: "monospace", fontSize: 13,
            lineHeight: 1.7, maxHeight: 480, overflowY: "auto" }}>
            {logs.map((log, i) => (
              <div key={i} style={{
                color: log.type === "error" ? "#f87171"
                  : log.text.includes("✓") || log.text.includes("Saved")
                    ? "#86efac"
                    : "#e2e8f0",
                padding: "1px 0",
              }}>
                {log.text}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      )}
    </div>
  );
}