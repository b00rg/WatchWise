import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import VideoScore from "./pages/VideoScore";
import History from "./pages/History";
import Creator from "./pages/Creator";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <nav className="nav">
      <span className="logo">🧠 RotCheck</span>
      <NavLink to="/">Score Video</NavLink>
      <NavLink to="/history">Watch History</NavLink>
      <NavLink to="/creator">Creator Lookup</NavLink>
    </nav>
    <main className="container">
      <Routes>
        <Route path="/" element={<VideoScore />} />
        <Route path="/history" element={<History />} />
        <Route path="/creator" element={<Creator />} />
      </Routes>
    </main>
  </BrowserRouter>
);
