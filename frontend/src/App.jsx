import { useState } from "react";

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function runSearch() {
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const res = await fetch(
        `http://localhost:8000/search?q=${encodeURIComponent(query)}`
      );
      const data = await res.json();
      setResults(data.results || []);
    } catch (err) {
      setResults([]);
    }
    setLoading(false);
  }

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", padding: "0 20px", fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ color: "#1b5e3f" }}>Trail Report Search</h1>
      <p style={{ color: "#666" }}>Search real hiking trip reports by trail conditions.</p>

      <div style={{ display: "flex", gap: 8, marginTop: 20 }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runSearch()}
          placeholder="try: snow on the pass"
          style={{ flex: 1, padding: "10px 12px", fontSize: 16, border: "1px solid #ccc", borderRadius: 6 }}
        />
        <button
          onClick={runSearch}
          style={{ padding: "10px 20px", fontSize: 16, background: "#1b5e3f", color: "white", border: "none", borderRadius: 6, cursor: "pointer" }}
        >
          Search
        </button>
      </div>

      {loading && <p style={{ marginTop: 20 }}>searching...</p>}
      {!loading && searched && results.length === 0 && (
        <p style={{ marginTop: 20, color: "#999" }}>no results found</p>
      )}

      <div style={{ marginTop: 20 }}>
        {results.map((r) => (
          <a
            key={r.id}
            href={r.url}
            target="_blank"
            rel="noreferrer"
            style={{ display: "block", padding: "14px 16px", marginBottom: 10, border: "1px solid #e0e0e0", borderRadius: 8, textDecoration: "none", color: "inherit" }}
          >
            <div style={{ fontWeight: 600, color: "#1b5e3f" }}>{r.trail_name}</div>
            <div style={{ fontSize: 13, color: "#888" }}>{r.region}</div>
          </a>
        ))}
      </div>
    </div>
  );
}

export default App;
