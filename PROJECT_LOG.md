# Trail Search — Project Log

Running log of decisions and progress. Update this as you go. If starting a new chat, paste this whole file in first so Claude has context.

Repo: https://github.com/officiallymoaizattiq-bit/trail-search

---

## Status: Week 1 Task 1.3 COMPLETE — tokenizer built. Next: Task 1.4 (inverted index, THE HEART).

---

## Status: Week 1 Task 1.1 COMPLETE — 497 reports scraped & cached to data/reports.json. Next: Task 1.2 (Postgres) or 1.3 (tokenizer).

---

## Status: Week 1 Task 1.2 COMPLETE — 497 reports loaded into PostgreSQL. Next: Task 1.3 (tokenizer — first "by hand" piece).

---

## Status: Week 1 Task 1.3 COMPLETE — tokenizer built by hand. Next: Task 1.4 (inverted index — THE HEART).

---

## Progress: Task 1.3 — Tokenizer DONE (first by-hand engine piece)
`src/tokenizer.py` — turns raw text into clean comparable words. ~5 lines:
```python
import re
STOPWORDS = {"the", "a", "an", "and", "of", "to", "in", "on", "is", "it"}
def tokenize(text):
    text = text.lower()                              # 1. lowercase so Snow==snow
    words = re.findall(r"[a-z0-9]+", text)           # 2. split on non-letter/number (kills punctuation)
    return [w for w in words if w not in STOPWORDS]  # 3. drop junk stopwords
```
Tested: `"Snow on the PASS! Creek-crossing was DEEP, deep."` → `['snow','pass','creek','crossing','was','deep','deep']`. Correct — dupes preserved (counts matter for ranking).

**Concepts learned:**
- **Bug avoided:** never `.remove()` from a list while looping it — the list shifts and the loop skips elements. Use a list comprehension instead.
- **List comprehension** `[w for w in words if w not in STOPWORDS]` = build a fresh filtered list, no mutation. Common python pattern.
- Stopword list is intentionally tiny (10 words) for now — expand later IF junk clogs results. Learning *when* to expand (from bad results) beats copying a huge list upfront.
- `tokenizer.py` is a clean importable module — no test prints left in it.

---

## Progress: Task 1.2 — PostgreSQL DONE
- Installed `postgresql@16` via brew, started as a service (`brew services start postgresql@16`). `createdb`/`psql` already on PATH via `/opt/homebrew/bin`.
- Created database `trailsearch`.
- Created `documents` table:
  ```sql
  CREATE TABLE documents (
      id TEXT PRIMARY KEY,
      trail_name TEXT, date TEXT, region TEXT, author TEXT,
      body TEXT, url TEXT,
      conditions JSONB          -- dict stored as queryable json, not flat text
  );
  ```
- Installed driver: `pip install "psycopg[binary]"`.
- Wrote `scripts/load_db.py`: reads `data/reports.json`, inserts each report as a row. **497 rows loaded & committed, verified with `SELECT COUNT(*)`.**

**SQL/db concepts learned (interview-worthy):**
- `%s` placeholders + separate values tuple → prevents SQL injection. NEVER f-string values into SQL.
- `ON CONFLICT (id) DO NOTHING` → idempotent inserts, script is safe to re-run (won't duplicate on the primary key).
- `conn.commit()` is required — postgres doesn't persist inserts until committed.
- `json.dumps(conditions)` to store the dict into the JSONB column.
- psql: backslash commands (`\dt` list tables, `\q` quit); SQL statements end with `;`.

**Handy verify commands:** `psql trailsearch` then `SELECT COUNT(*) FROM documents;` / `SELECT id, trail_name, region FROM documents LIMIT 10;`

---

## Progress: fetch_reports.py — FULLY WORKING (all 4 pieces done)
Full pipeline runs end to end: collect URLs → parse each report → cache to JSON.
- **Result: 497/503 reports saved** to `data/reports.json` (~99% success).
- Structure = 3 stages (separation of concerns, interview-worthy): `get_report_urls()` crawls listing pages, `parse_report()` extracts 8 fields, main block loops + caches.

**The 6 skips (real-world data lessons, NOT bugs to fix — "good enough beats complete"):**
- `'NoneType' object has no attribute 'get_text'` — report missing an expected field (no author / different h1). `.find()` returned None, `.get_text()` on None crashes. Caught by try/except.
- `Invalid URL ... No scheme supplied` (x2) — some listing links are RELATIVE (`trip_report-...` with no domain). Filter caught them but requests can't fetch without `https://`. Could fix later by prepending domain if missing.
- Also saw a couple `http://` (not https) and older 2020/2025 reports mixed into the 2026 feed — normal feed messiness.
- **Design lesson proven:** the try/except around `parse_report` is what let 1 bad page not kill the whole 8-min run. This is the robustness pattern.

**Full working file is committed. To re-scrape or scale up:** change `range(0, 500, 50)` — bigger 2nd number = more reports. Week 4 scaling will crank this to 10k+.

---

## Progress: fetch_reports.py — piece 1 & 2 done
- **Piece 1 (get past bot block): DONE.** `requests.get` with browser User-Agent header returns 200. Plain requests would 403.
- **Piece 2 (parse one report): DONE.** All 8 fields extract clean from a single report page.

**The 8 fields + how they're pulled:**
- `report_id` → `url.split(".")[-1]` (the number at end of URL, e.g. `210341804556`) — no scraping needed
- `author` → `soup.find("span", itemprop="author").find("span", class_="wta-icon-headline__text").get_text().strip()`
- trail name → `h1.find("a").get_text()` where `h1 = soup.find("h1", class_="documentFirstHeading")`
- hike page URL (bonus) → the `<a href>` inside that h1
- date → `h1.find("a").next_sibling.strip()` (still has leading `— `, clean later)
- region → `soup.find(id="hike-region").get_text().strip()`
- body → `soup.find(id="tripreport-body-text").get_text().strip()`
- conditions dict → loop `div.trip-condition` inside `#trip-conditions`, `{h4_text: span_text}`

**Known quirks (not bugs, handle later):**
- `\xa0` (non-breaking space) appears in some condition values — tokenizer will strip it, ignore for now.
- date string still has leading `— ` — strip when parsing to real date via `datetime.strptime`.
- **RISK:** not every report may have a `#trip-conditions` block (older/lazy reports). When scaling in piece 4, wrap conditions parsing in an `if block:` check or the loop crashes on `None`.
- **LESSON (bit us 3x):** unsaved file in VS Code = running OLD code. The dot on the tab means unsaved. Cmd+S before every run.

## Next step (pick up here)
Piece 3: collect MANY report URLs. Go to WTA trip-reports listing page, find (1) the href pattern for each report link in the list, (2) how pagination works (URL change on next page). Then loop to gather hundreds/thousands of URLs.

Then piece 4: tie it together — loop URLs, parse each (piece 2 logic), `time.sleep(1)` between, cache to `data/reports.json`.

---

## WTA scraping notes (confirmed by inspecting a live trip report)

Example report URL pattern:
`https://www.wta.org/go-hiking/trip-reports/trip_report-2026-06-30.210341804556`

**IMPORTANT — WTA has bot detection.** A plain `requests.get(url)` gets blocked (403). Must send a browser-like User-Agent header, e.g.:
```python
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
requests.get(url, headers=headers)
```

**Confirmed selectors (per report page):**
- **Title / trail name** — `h1.documentFirstHeading` contains an `<a>` (trail name, e.g. "Goat Mountain") AND trailing loose text with the date. Parse separately:
  - trail name → `h1.find("a").get_text()`
  - hike page URL (bonus) → the `<a href>` inside the h1
  - date → the text node after the `<a>` (e.g. `" — Wednesday, Jul. 1, 2026"`), strip the `" — "` prefix. Raw string for now; parse to real date later with `datetime.strptime`.
- **Region / area** — `id="hike-region"` (city + mountain range area)
- **Related hike** — `class="related-hike-links"` (may be redundant with the h1 `<a>` — check)
- **Report body** — `id="tripreport-body-text"` (the main text you actually index)
- **Structured conditions block (the WTA gold for week-3 condition tagging):**
  - Container: `div#trip-conditions` (also has class `alpha`), inside `div.trip-report-features`
  - Each condition: `div.trip-condition` containing:
    - `<h4>` = category label ("Trail Conditions", "Road", "Bugs", "Snow", "Type of Hike"...). The `::after` is CSS decoration, ignore it.
    - `<span>` = the value ("Road suitable for all vehicles", "No bugs", "Intermittent snow – not hard to cross"...)
  - Parse into a dict: `{h4_text: span_text}`. Handle empty/collapsed h4 gracefully.
  - This gives BOTH structured condition tags AND freeform body — stronger than the plan assumes, most scrapers only get freeform.

**Politeness:** respect `wta.org/robots.txt`, add `time.sleep(1)` between requests, cache to disk immediately so re-runs don't re-hit the network.

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