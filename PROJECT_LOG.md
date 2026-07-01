# Trail Search — Project Log

Running log of decisions and progress. Update this as you go. If starting a new chat, paste this whole file in first so Claude has context.

Repo: https://github.com/officiallymoaizattiq-bit/trail-search

---

## Status: Week 1, Setup complete — about to start Task 1.1 (data fetching)

---

## Environment
- macOS, Homebrew installed
- Python 3.13 (venv built off system python3, not the homebrew 3.12 — fine, no issue)
- venv: `.venv` in `trail-search/` — activate with `source .venv/bin/activate`
- Git configured, first commit pushed to GitHub (`d00a633`)
- Project skeleton created: `src/{__init__,tokenizer,index,ranker,search}.py`, `scripts/fetch_reports.py`, `requirements.txt`, `README.md`, `.gitignore`
- `.gitignore` set up correctly (`.venv/`, `__pycache__/`, `data/`, `*.pkl`, `.env`, `.DS_Store`)
- Postgres NOT yet installed (`brew install postgresql@16` — pending)

## Key decision: data sources changed from the original plan
- **Reddit API is a dead end.** As of Nov 2025, Reddit closed self-serve OAuth app creation (the "Responsible Builder Policy"). The create-app form now silently fails / just submits an approval request that can take weeks or never resolve. Do not waste more time on reddit.com/prefs/apps.
- **New plan: scrape public trip-report sites instead of using an API.**
  - **WTA (Washington Trails Association)** — primary source. ~280k public trip reports, no login needed, purpose-built for trail condition reporting (great fit for the "hiking edge" condition-tagging feature in week 3).
  - **Oregon Hikers forum** — secondary source, PNW-focused trip report threads, different writing style for ranking diversity.
  - **SummitPost** — tertiary source, more summit/mountaineering-focused trip reports.
  - **Explicitly skipping AllTrails** — aggressive anti-scraping ToS, data ownership terms are hostile, not worth the legal/technical hassle for this project.
- This is arguably a *better* fit than reddit would've been — WTA reports are pre-filtered to be exactly the condition-focused text the project's "hiking edge" wedge needs, vs reddit's noisier mixed content.
- Tradeoff: no clean JSON API, need to write HTML scrapers (BeautifulSoup/requests) per site instead of one `praw` call. More parsing code, but same core skill, and arguably closer to how real search engines ingest data.

## Next step (pick up here)
Look at WTA's actual trip report page structure (URL patterns, HTML layout) to start writing `scripts/fetch_reports.py` against it.

## Not started yet
- Postgres install + `documents` table (Task 1.2)
- Tokenizer (Task 1.3)
- Inverted index (Task 1.4)
- Everything from Week 2 onward (BM25 ranking)

## Reminders / rules established
- No search libraries, ever — tokenizer, index, ranker all hand-written per the project's whole premise.
- Secrets go in `.env`, never committed (already gitignored).
- Cache raw scraped data to disk immediately so re-runs don't hit the network again.
- Give the data-fetching step a hard cap — don't rabbit-hole on scraping for weeks, "good enough" beats "complete."
