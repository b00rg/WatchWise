import React, { useState } from "react";
import { ScoreCard } from "../components/ScoreCard";

const API = "http://localhost:8000";

export default function VideoScore() {
  const [url, setUrl] = useState("");
  const [age, setAge] = useState(8);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [stage, setStage] = useState("");
  const [agents, setAgents] = useState([]);

  function handleEvent(event) {
    if (event.type === "pipeline_start") {
      setStage("Downloading & analysing video…");
    } else if (event.type === "error") {
      setError(event.detail || "Pipeline failed");
      setLoading(false);
    } else if (event.type === "meta") {
      setStage("Running AI specialists…");
    } else if (event.type === "agent_start") {
      setAgents(prev => [...prev, { id: event.agent, label: event.label, status: "running" }]);
    } else if (event.type === "agent_done") {
      setAgents(prev => prev.map(a =>
        a.id === event.agent ? { ...a, status: "done", score: event.score } : a
      ));
    } else if (event.type === "final") {
      setResult(event);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(""); setResult(null); setAgents([]);
    setStage("Downloading & analysing video…");
    setLoading(true);

    try {
      const res = await fetch(`${API}/score/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, age: Number(age) }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try { handleEvent(JSON.parse(line.slice(6))); } catch {}
        }
      }
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
      setStage("");
    }
  }

  return (
    <>
      <div className="card">
        <div className="section-title">Score a YouTube Video</div>
        <form onSubmit={handleSubmit}>
          <div className="row">
            <input
              type="text" placeholder="https://youtube.com/watch?v=..."
              value={url} onChange={e => setUrl(e.target.value)} required
            />
            <span className="age-label">Age</span>
            <input type="number" min={2} max={17} value={age} onChange={e => setAge(e.target.value)} />
            <button type="submit" disabled={loading}>{loading ? "Analysing…" : "Score"}</button>
          </div>
        </form>
        {error && <div className="error">{error}</div>}

        {loading && (
          <div className="loader-wrap">
            <div className="loader-stage">
              <span className="loader-spinner" /> {stage}
            </div>
            {agents.map(a => (
              <div key={a.id} className={`agent-row agent-${a.status}`}>
                <span className={`agent-dot ${a.status === "running" ? "agent-dot-pulse" : ""}`} />
                <span className="agent-label">{a.label}</span>
                {a.status === "done" && (
                  <span className="agent-score" style={{ color: a.score > 65 ? "#f87171" : a.score > 40 ? "#fbbf24" : "#34d399" }}>
                    {a.score}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      {result && <ScoreCard result={result} />}
    </>
  );
}
