import React, { useState } from "react";
import axios from "axios";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from "recharts";

const API = "http://localhost:8000";

export default function History() {
  const [age, setAge] = useState(8);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    setError(""); setResult(null); setLoading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const { data } = await axios.post(`${API}/history?age=${age}`, form);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const chartData = result?.videos
    ?.slice()
    .reverse()
    .map((v, i) => ({ i: i + 1, score: v.brainrot_score, title: v.meta?.title?.slice(0, 30) }));

  return (
    <>
      <div className="card">
        <div className="section-title">Upload YouTube Watch History</div>
        <p style={{ fontSize: "0.85rem", color: "#9090b0", marginBottom: "1rem" }}>
          Export from Google Takeout → YouTube → watch-history.json
        </p>
        <div className="row">
          <span className="age-label">Child's age</span>
          <input type="number" min={2} max={17} value={age} onChange={e => setAge(e.target.value)} />
          <input type="file" accept=".json" onChange={handleFile} style={{ color: "#e8e8f0" }} />
        </div>
        {error && <div className="error">{error}</div>}
        {loading && <div className="loading">Scoring up to 20 recent videos — this may take a few minutes…</div>}
      </div>

      {result && (
        <>
          <div className="card">
            <div className="section-title">Overview</div>
            <div style={{ fontSize: "2.5rem", fontWeight: 800, color: "#c084fc" }}>
              {result.average_brainrot_score}
              <span style={{ fontSize: "1rem", color: "#9090b0", marginLeft: "0.5rem" }}>avg BrainRot score</span>
            </div>
            <div style={{ fontSize: "0.85rem", color: "#9090b0", marginTop: "0.25rem" }}>
              Based on {result.total_scored} videos
            </div>
          </div>

          <div className="card">
            <div className="section-title">Score Over Time</div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid stroke="#2a2a3a" />
                <XAxis dataKey="i" tick={{ fill: "#6060a0", fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fill: "#6060a0", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "#18181f", border: "1px solid #2a2a3a", fontSize: "0.8rem" }}
                  formatter={(v, _, p) => [v, p.payload.title]}
                />
                <Line type="monotone" dataKey="score" stroke="#c084fc" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div className="section-title">Creator Breakdown</div>
            <table className="creator-table">
              <thead>
                <tr><th>Creator</th><th>Avg BrainRot Score</th></tr>
              </thead>
              <tbody>
                {Object.entries(result.creator_scores).map(([ch, score]) => (
                  <tr key={ch}>
                    <td>{ch}</td>
                    <td style={{ color: score > 65 ? "#f87171" : score > 40 ? "#fbbf24" : "#34d399" }}>
                      {score}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}
