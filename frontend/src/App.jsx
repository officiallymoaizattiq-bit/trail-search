import { useState } from "react";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
        `${API}/search?q=${encodeURIComponent(query)}`
      );
      const data = await res.json();
      setResults(data.results || []);
    } catch (err) {
      setResults([]);
    }
    setLoading(false);
  }

  // render-only derived values (does not touch state flow)
  const maxScore = results[0]?.score || 1;

  return (
    <div className="station">
      <main className="frame">
        <header className="masthead">
          <p className="eyebrow">WTA TRIP REPORTS · FIELD JOURNAL</p>
          <h1 className="title">Trail Report Search</h1>
          <p className="lede">
            Real hiking trip reports, read by trail conditions — snow, water,
            bugs, bloom. Ranked by relevance.
          </p>
        </header>

        <section className="console">
          <label className="field-label" htmlFor="q">
            Enter conditions
          </label>
          <div className="field">
            <input
              id="q"
              className="field-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runSearch()}
              placeholder="snow on the pass"
              autoComplete="off"
              spellCheck="false"
            />
            <button className="field-go" onClick={runSearch}>
              Search
            </button>
          </div>
        </section>

        <section className="results" aria-live="polite" aria-busy={loading}>
          {loading &&
            [0, 1, 2, 3, 4].map((n) => (
              <div className="skel-row" key={`skel-${n}`} aria-hidden="true">
                <div className="skel-rank" />
                <div className="skel-body">
                  <div className="skel-line" />
                  <div className="skel-line skel-line-sm" />
                </div>
                <div className="skel-signal" />
              </div>
            ))}

          {!loading && searched && results.length === 0 && (
            <p className="status-empty">
              no entries — try a broader condition: snow, water, bugs
            </p>
          )}

          {!loading &&
            results.map((r, i) => {
              const rel = r.score / maxScore;
              const pct = Math.round(rel * 100);
              return (
                <a
                  className="entry"
                  key={r.id}
                  href={r.url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ "--i": i }}
                  aria-label={`${r.trail_name}, ${r.region} — opens WTA trip report`}
                >
                  <span className="rank">{String(i + 1).padStart(2, "0")}</span>

                  <span className="entry-info">
                    <span className="entry-name">{r.trail_name}</span>
                    <span className="entry-meta">
                      <span className="meta-pin" aria-hidden="true">◇</span>
                      <span className="region">{r.region}</span>
                    </span>
                  </span>

                  <span className="entry-score">
                    <span className="score-label">{pct}% match</span>
                    <span className="score-track" aria-hidden="true">
                      <span className="score-fill" style={{ width: `${pct}%` }} />
                    </span>
                  </span>
                </a>
              );
            })}
        </section>
      </main>
    </div>
  );
}

export default App;
