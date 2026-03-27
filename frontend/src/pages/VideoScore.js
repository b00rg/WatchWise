import React, { useState } from "react";
import axios from "axios";
import { ScoreCard } from "../components/ScoreCard";

const API = "http://localhost:8000";

export default function VideoScore() {
  const [url, setUrl] = useState("");
  const [age, setAge] = useState(8);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError(""); setResult(null); setLoading(true);
    try {
      const { data } = await axios.post(`${API}/score`, { url, age: Number(age) });
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
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
            <button type="submit" disabled={loading}>{loading ? "Analyzing…" : "Score"}</button>
          </div>
        </form>
        {error && <div className="error">{error}</div>}
        {loading && <div className="loading">Downloading & analyzing video — this takes ~30s…</div>}
      </div>
      {result && <ScoreCard result={result} />}
    </>
  );
}
