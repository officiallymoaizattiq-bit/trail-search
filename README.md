<img width="1280" height="709" alt="image" src="https://github.com/user-attachments/assets/c235f8d4-4d94-4f21-ac26-1a07517cafbb" />
<img width="1280" height="711" alt="image" src="https://github.com/user-attachments/assets/d2da9b44-d18e-4ce4-8dff-cd235757c45a" />

# Trail Report Search

A search engine for hiking trip reports, **built from scratch** — the tokenizer, inverted index, and BM25 ranking are all hand-written, no search libraries. It searches real [Washington Trails Association](https://www.wta.org) trip reports by *trail condition* ("avalanche danger", "no bugs", "snow free"), not just by words in the narrative.

### **[→ Live demo](https://trail-search-pi.vercel.app)**

> First search may take ~40s — the free-tier backend spins down when idle and cold-starts on the first request. Every search after that is instant.

<img width="1280" height="709" alt="image" src="https://github.com/user-attachments/assets/c235f8d4-4d94-4f21-ac26-1a07517cafbb" />
<img width="1280" height="711" alt="image" src="https://github.com/user-attachments/assets/d2da9b44-d18e-4ce4-8dff-cd235757c45a" />
---

## What makes it different

Most "search engine" projects import a library that does the actual searching. This one doesn't. The retrieval core is built by hand, so I understand and can defend every part of it:

- **Hand-written tokenizer + stemmer** — lowercasing, stopword removal, and a rough suffix stemmer so `hiking` / `hiked` / `hikes` all match `hike`. Runs on both indexing and querying so matches are consistent.
- **Hand-built inverted index** — maps each word to the documents containing it, so a search is a *lookup* instead of a *scan*. Benchmarked ~12,000× faster than a linear full-text scan over the same corpus.
- **Hand-implemented BM25 ranking** — full term-frequency saturation (`k1`) and document-length normalization (`b`), tuned by hand rather than copied from a paper.
- **The hiking edge** — WTA reports carry structured condition tags (Snow, Bugs, Road, Trail Conditions...). I fold those tag values into the index, so you can search by *condition* — `road closed`, `avalanche danger` — not just by narrative text.

---

## How it works

```
React (Vercel)  →  FastAPI (Render)  →  hand-built BM25 engine  →  PostgreSQL (Supabase)
```

The engine loads reports from Postgres, builds the inverted index once on startup, and ranks results with BM25 entirely in memory. The index is cached to disk with a **database fingerprint** (row count + max id) so it only rebuilds when the underlying data actually changes — separating slow offline indexing from fast query-time startup.

**Request flow:** a query hits `GET /search?q=...`, gets tokenized and stemmed the same way the corpus was, scored against the in-memory index with BM25, and returned as ranked JSON. The React frontend renders each result as a card linking to the original trip report.

---

## Benchmarked against PostgreSQL full-text search

I ran the hand-built engine head-to-head against Postgres's native full-text search (`tsvector` / `ts_rank` / GIN index) on identical data:

| | My engine | Postgres FTS |
|---|---|---|
| Query latency ("snow on the pass") | **0.21 ms** | 7.54 ms |
| Results for "avalanche danger" | **5** | 2 |

- **~35× faster** at this corpus size — my index lives in RAM, while Postgres hits a GIN index on disk and parses the query. (At millions of documents that tradeoff flips, and I can explain why — this is a scale-aware result, not a blanket claim.)
- **Better recall on condition queries** — I indexed the structured condition tags Postgres never saw, so it found relevant reports the general-purpose baseline missed.

---

## Engineering notes

Things I did on purpose that I can talk about:

- **Tuned BM25 by feel.** Watched `k1` and `b` move the rankings on real queries instead of trusting default values — so I can actually say why `1.5` and `0.75`.
- **Ran my own security/correctness audit.** Found and fixed a scoring bug (a tuning value left maxed out), a silent cache-staleness bug (stale index served without error), and an arbitrary-code-execution risk (swapped `pickle` serialization for JSON).
- **Measured relevance instead of vibing it.** A regression test asserts hand-verified query→result pairs so a ranking change that quietly breaks quality gets caught.
- **Environment-based config.** The database connection reads from `DATABASE_URL`, so the exact same code runs against local Postgres in dev and Supabase in production.

---

## Tech stack

**Python** · **PostgreSQL** · **FastAPI** · **React (Vite)** — deployed on **Vercel** + **Render** + **Supabase**.

---

## Running locally

```bash
# setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# backend (terminal 1) — serves on :8000
python -m uvicorn main:app --reload

# frontend (terminal 2) — serves on :5173
cd frontend && npm install && npm run dev
```

Open `localhost:5173`.

The backend needs a Postgres database with the reports loaded. By default it connects to a local database named `trailsearch`; set the `DATABASE_URL` environment variable to point it anywhere else. Use `scripts/fetch_reports.py` to scrape reports and `scripts/load_db.py` to load them.

Run the tests after any change:

```bash
python test_sanity.py && python test_devil.py && python test_relevance.py
```

---

## Project structure

```
src/
  tokenizer.py     text → clean stemmed words        (by hand)
  index.py         the inverted index                (by hand)
  ranker.py        IDF + BM25 scoring                (by hand)
  engine.py        loads data, builds/caches index, serves search()
main.py            FastAPI server
benchmark.py       the Postgres head-to-head
scripts/
  fetch_reports.py the WTA scraper
  load_db.py       JSON → Postgres loader
frontend/          React + Vite search UI
test_*.py          sanity / bug-regression / relevance tests
```

---

## What I deliberately didn't build

No embeddings, no vector search, no LLM. The whole point was to build the retrieval core by hand — reaching for an off-the-shelf model would defeat it. Same reasoning kept the scope tight: no user accounts, no microservices, no "perfect" stemmer. One codebase, one database, every piece understood.
