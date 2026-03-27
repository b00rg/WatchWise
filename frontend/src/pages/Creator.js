import React, { useState } from "react";
import axios from "axios";
import { ScoreCard } from "../components/ScoreCard";

const API = "http://localhost:8000";

export default function Creator() {
  const [channelUrl, setChannelUrl] = useState("");
  const [age, setAge] = useState(8);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError(""); setResult(null); setLoading(true);
    try {
      const { data } = await axios.post(`${API}/creator`, { channel_url: channelUrl, age: Number(age) });
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
        <div className="section-title">Creator Lookup</div>
        <form onSubmit={handleSubmit}>
          <div className="row">
            <input
              type="text" placeholder="https://youtube.com/@ChannelName"
              value={channelUrl} onChange={e => setChannelUrl(e.target.value)} required
            />
            <span className="age-label">Age</span>
            <input type="number" min={2} max={17} value={age} onChange={e => setAge(e.target.value)} />
            <button type="submit" disabled={loading}>{loading ? "Sampling…" : "Look Up"}</button>
          </div>
        </form>
        {error && <div className="error">{error}</div>}
        {loading && <div className="loading">Sampling 5 recent videos — ~2 minutes…</div>}
      </div>

      {result && (
        <>
          <div className="card">
            <div className="section-title">Channel Average</div>
            <div style={{ fontSize: "2.5rem", fontWeight: 900, color: "#6248d4" }}>
              {result.average_brainrot_score}
              <span style={{ fontSize: "1rem", color: "#a098cc", marginLeft: "0.5rem", fontWeight: 700 }}>
                BrainRot score ({result.videos_sampled} videos sampled)
              </span>
            </div>
          </div>
          {result.videos.map((v, i) => <ScoreCard key={i} result={v} />)}
        </>
      )}
    </>
  );
}
