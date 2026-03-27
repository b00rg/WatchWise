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
        <p style={{ fontSize: "0.85rem", color: "#a098cc", marginBottom: "1rem", fontWeight: 600 }}>
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
            <div style={{ fontSize: "2.5rem", fontWeight: 900, color: "#6248d4" }}>
              {result.average_brainrot_score}
              <span style={{ fontSize: "1rem", color: "#a098cc", marginLeft: "0.5rem", fontWeight: 700 }}>avg BrainRot score</span>
            </div>
            <div style={{ fontSize: "0.85rem", color: "#a098cc", marginTop: "0.25rem", fontWeight: 600 }}>
              Based on {result.total_scored} videos
            </div>
          </div>

          <div className="card">
            <div className="section-title">Score Over Time</div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid stroke="#ede9ff" />
                <XAxis dataKey="i" tick={{ fill: "#a098cc", fontSize: 11, fontWeight: 700 }} />
                <YAxis domain={[0, 100]} tick={{ fill: "#a098cc", fontSize: 11, fontWeight: 700 }} />
                <Tooltip
                  contentStyle={{ background: "#fff", border: "2px solid #e8e2ff", borderRadius: 12, fontSize: "0.8rem", fontWeight: 700 }}
                  formatter={(v, _, p) => [v, p.payload.title]}
                />
                <Line type="monotone" dataKey="score" stroke="#6248d4" dot={false} strokeWidth={2.5} />
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
                    <td style={{ color: score > 65 ? "#d83030" : score > 40 ? "#c98a00" : "#1fa870", fontWeight: 800 }}>
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
