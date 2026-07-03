# Trail Search — Project Log

Running log of decisions and progress. Update this as you go. If starting a new chat, paste this whole file in first so Claude has context.

Repo: https://github.com/officiallymoaizattiq-bit/trail-search

---

## Status: WEEK 3 — nearly done. Full-stack search + index persistence + condition-search + Postgres benchmark all WORKING. Next: DEPLOY (last big piece).

> **Week 3 progress (tasks 3.1, 3.4, 3.5 all DONE):**
>
> **3.1 index persistence DONE.** `src/engine.py` now has `build_and_save_index()` (pickles `{documents, index, doc_len, avg_len}` to `data/index.pkl`) and `SearchEngine.__init__` loads the pickle if it exists, else builds fresh + saves. Separates INDEXING time (slow, offline, once) from QUERY time (fast, live, boot just loads a file). Measured: at 388 docs, pickle-load (0.114s) vs db-rebuild (0.108s) — basically identical. Honest finding: too small to show the benefit YET; the pattern pays off at scale (rebuild grows with corpus, load doesn't). **Interview answer: "separated indexing from query time, measured it, kept it because it's right for scale even though my corpus is too small to show it."** KNOWN DEBT: index is now STALE after data changes — must re-run `build_and_save_index()` or delete `data/index.pkl` + restart server. (Bit us immediately when adding conditions — had to rebuild pickle.)
>
> **3.4 condition search DONE (THE HIKING EDGE).** All 388 reports have 5 condition categories fully populated (Bugs, Road, Snow, Type of Hike, Trail Conditions) with rich human phrases ("Snow free", "Avalanche danger", "Trees down across trail", "Road impassable/closed"). Two edits: `load_documents` now SELECTs `conditions`; `build_index` folds condition values into the tokenized text (`cond_text = " ".join(str(v) for v in (doc.get("conditions") or {}).values())`). Now searching a CONDITION TAG works: "avalanche danger" → Mazama Ridge (10.38), Artist Point Snowshoe — reports where that's the tagged Snow condition, invisible before. Verified through the live website UI (avalanche danger / no bugs / road closed all return right trails). All tests still pass (sanity 4/4, relevance 4/4). This is what makes it more than "another search box." Skipped structured-filter checkboxes (part 2) as lowest-value — condition SEARCH already delivers the edge.
>
> **3.5 Postgres benchmark DONE (`benchmark.py`) — THE INTERVIEW MOVE.** Set up Postgres FTS on same table: `search_vector tsvector` column (`to_tsvector('english', trail_name || body)`), GIN index, `ts_rank`. Ran 4 queries head-to-head. **Findings (the interview script):**
>   1. **Speed: MY engine WON at this scale.** "snow on the pass": mine 0.21ms vs Postgres 7.54ms (35x). Because my index is in RAM (pickle) vs Postgres hitting GIN on disk + query parsing. Nuanced truth: at 10M docs Postgres wins (doesn't load all to RAM); at 388 in-memory beats it. Defensible, scale-aware answer.
>   2. **THE money shot — recall on "avalanche danger": mine 5 results, Postgres only 2.** Postgres only indexed trail_name+body; I folded in condition tags. I beat the industry-standard tool on recall because I understood the domain and indexed the structured condition data it can't see.
>   3. **Ranking differs, explainable:** BM25 (mine) weights rare terms + penalizes long docs; Postgres `ts_rank` mostly counts frequency, no real IDF/length-norm. Different top results, and I can say why.
>   4. **Postgres has a dedup quirk** (returned "Melakwa Lake" twice); mine doesn't.
>
> **NEXT — DEPLOY (last big Week 3 piece):** get it live on a real URL (Fly.io / Railway per plan). Note for deploy: `main.py` builds `SearchEngine()` on boot which needs either the pickle present OR Postgres reachable to build fresh. `data/` is gitignored so the pickle won't be in the repo — deploy must either build the pickle on the box or ship it separately. Also tighten CORS `allow_origins` from `["*"]` to the real frontend domain in prod.



> **Week 3 progress — the website is LIVE (locally):**
> - **Refactor DONE.** Pulled search logic out of `build_test.py` into `src/engine.py` — a `SearchEngine` class that loads docs from Postgres, builds the index ONCE in `__init__`, exposes `search(query, limit)` returning clean dicts (trail_name, region, url, score). This is the importable module the web server needed.
> - **Backend DONE — `main.py` (FastAPI).** `engine = SearchEngine()` at module level (builds index once on boot, reused per request). `GET /search?q=...` endpoint. Two things baked in: CORS middleware (so React on :5173 can call API on :8000), and `Query(..., min_length=1, max_length=200)` which fixes the devil's-advocate DoS/empty-query risk at the door (verified: empty query returns 422). Run with `python -m uvicorn main:app --reload` (must use `python -m` or it grabs system pyenv python, not venv → psycopg ModuleNotFoundError).
> - **Frontend DONE — `frontend/` (React + Vite).** `frontend/src/App.jsx` = search box + button, fetches `/search`, renders results as clickable cards linking to real WTA reports. `npm run dev` serves on :5173. Uses `encodeURIComponent` on the query.
> - **VERIFIED end-to-end:** typed "snow on the pass" in browser → ranked cards (Enchantments, Skyline Lake Snowshoe, Melakwa Lake...) each linking to the actual report. Full stack: React → HTTP → FastAPI → hand-built tokenizer/stemmer/index/BM25 → Postgres → rendered.
>
> **To run the whole thing (2 terminals):** (1) backend: `python -m uvicorn main:app --reload`; (2) frontend: `cd frontend && npm run dev`, open localhost:5173.
> **gitignore updated:** added `node_modules/`, `frontend/node_modules/`, `frontend/dist/`.
> **Debugging note:** pasting code into chat mangles indentation/eats chars (broke App.jsx twice — empty line where `<a` should be). Terminal Claude CLI can read actual bytes off disk — use it for file-level debugging instead of screenshot paste-telephone.



> **Devil's-advocate review (end of Week 2) — bugs found & fixed:**
> - **BUG: `k1` left at 5** from the tuning experiment (never reset). Fixed → `k1=1.5`. Search was running with repetition maxed out.
> - **BUG: query terms not deduped.** `bm25_search` looped `tokenize(query)`, so "snow snow" double-scored "snow" (verified: 1.224 → 2.449). Fixed: `for word in set(tokenize(query))`. A query term's weight shouldn't depend on how many times the USER typed it. Re-verified: both score 1.224 now.
> - **DATA: 3 empty-body reports deleted.** Were genuine photo-only WTA posts (metadata + condition tags filled, zero body text). Deleted via `DELETE FROM documents WHERE body IS NULL OR body=''`. Corpus now **388 clean text-bearing reports**. NOTE: `data/reports.json` still has all 391 — DB and JSON slightly out of sync; re-running load_db would re-add them. Week-3 polish: strip empties in load_db too.
>
> **Confirmed KNOWN DEBT (defensible, not fixing now):**
> - Stemmer false-split: "pass"→"pas" but "passed"→"pass" — same concept, different roots, don't merge. Plan says don't chase stemmer perfection. Now nameable as a known failure mode.
> - **Conditions field is FULLY POPULATED in DB but INVISIBLE to search.** `build_index` only tokenizes `trail_name + body`, ignores `conditions`. This is true for ALL reports, not just the deleted 3. Folding condition tags into searchable text = literally Week 3 task 3.4 (the "hiking edge"). The data is already sitting there ready.
> - `build_test.py` still holds the only working "load DB → build index → search" path. Week 3 needs it as a real `src/` function.
> - **No relevance measurement** — can't yet answer "how good are your results?" Closing this next (small query→expected-results harness).
>
> **Relevance measurement DONE (`test_relevance.py`).** Closed the "how good are results?" gap. Ran 5 varied queries (`relevance_explore.py`), eyeballed results — all genuinely good (snow query → Snowshoe trails, water query → Creek/River trails, wildflower query → eastern-WA shrub-steppe spots, bug query → lake basins). Locked 4 as a regression test: each query asserts a hand-verified sensible result lands in top-5 (loose substring match, survives minor ranking shifts, catches real breakage). **4/4 passing.** Interview answer for "how do you know it's good" is now "measured, not vibed."
>
> **Engine now guarded by 3 test files:** `test_sanity.py` (tokenizer/index math), `test_devil.py` (bug regressions), `test_relevance.py` (result quality). Run all three after any Week 3 change.



> **Task 2.4 stemming DONE.** Added `stem(word)` to `src/tokenizer.py` — rough suffix stripper (chops -ing/-ed/-es/-s, guard: only if ≥3 chars remain). Wired into `tokenize` via `[stem(w) for w in words if w not in STOPWORDS]`, so it runs on BOTH indexing and querying automatically (that's what makes matching work — "hiking" in a report and "hike" in a query both reduce to same root). Verified: `stem("hiking")==stem("hikes")==stem("hiked")`.
> - **Measured impact:** index 6204 → 5269 unique words (~935 variants collapsed). "wildflower" went from 4 docs (idf 4.467) to 21 docs (idf 2.903) — "wildflower"+"wildflowers" merged, 17 previously-invisible reports now match. Search relevance held (Entiat River / High Divide still top for "river crossing high snow"). This is the recall win, concretely.
> - **Rough by design** (per build plan — don't chase linguistic perfection): does dumb things sometimes ("business"→"busine"), doesn't matter. "pass"→"pas" etc. Fine.
> - **Sanity tests updated** to stemmed expectations + a new stemming-specific test block. All pass.
> - **WEEK 2 SHIPPABLE MET:** type a real query → genuinely good reports ranked best-first, hand-built BM25 + stemming.



> **Week 2 progress (BM25 ranking, `src/ranker.py`):**
> - **2.1 IDF DONE.** `idf(word, index, total_docs)` — `math.log(1 + (total_docs - n + 0.5)/(n + 0.5))`, n = docs containing word. Verified on real data: trail=0.211 (in 317 docs, common→low), snow=1.332 (103 docs), wildflower=4.467 (4 docs, rare→high). Rare words score way higher. (Seasonal corpus fix paid off — wildflower only has a meaningful IDF because we scraped summer.)
> - **helper: `avg_doc_len(doc_len)`** — mean of doc_len.values(), guards empty. Needed for the length penalty.
> - **2.2 BM25 scorer DONE.** `bm25_search(query, index, doc_len, avg_len, total_docs, k1=1.5, b=0.75)`. Tokenizes query, loops ONLY docs containing each word (via inverted index), scores `word_idf * (tf*(k1+1)) / (tf + k1*norm)` where `norm = 1 - b + b*(doc_len/avg_len)`, sums per-word scores per doc, returns sorted best-first. Tested on "river crossing high snow" → top results are genuinely river/snow/high-elevation trails (High Divide, Entiat River, Middle Fork Snoqualmie). Scores descend cleanly, sane range. Matching became real ranking.
> - **2.3 knob tuning DONE (watched them move).** `b` (length penalty): b=0 → long verbose docs dominate (scores spread 5.4–8.1), b=1 → short focused docs win (compressed 5.1–6.1), b=0.75 = balance. `k1` (mention saturation): k1=0.5 → repetition barely matters (scores squished 4.6–5.5), k1=5 → repetition dominates, spammy docs climb (Entiat River → 8.3). k1=1.5 = diminishing returns middle. **Both reset to defaults (k1=1.5, b=0.75) after testing.** Can now defend "why 0.75/1.5" from having SEEN it, not from a paper.
> - **NOTE:** BM25 testing code is bolted onto the bottom of `build_test.py` (imports idf, avg_doc_len, bm25_search). Fine for now; will move to a real search function for Week 3's FastAPI.



> Pre-Week-2 fixes applied (addressing the senior review in CONTEXT_HANDOFF.md section 10):
> - **Corpus skew FIXED.** Re-scraped ~391 reports across 4 seasonal date windows (winter/spring/summer/fall) using WTA's `tripdate_min`/`tripdate_max` URL filters (format `YYYY-MM-DD` on the `@@search_tripreport_listing` endpoint). Verified diversity: `snowshoe` in 20 reports, `wildflower` in 21 — winter AND summer vocab both present, so IDF will now reflect real rarity, not seasonal coincidence. (NOTE: deep pagination `b_start` offsets DON'T work — WTA clamps them back to recent; date filters are the real diversity lever.)
> - **id parsing FIXED.** `report_id = re.search(r"(\d+)$", url).group(1)` — handles both dot-format (new) and dash-format (old) URLs; also robust to dots earlier in the URL. Old `url.split(".")[-1]` was fragile.
> - **Sanity tests ADDED.** `test_sanity.py` (project root) — asserts tokenizer + build_index produce hand-computed answers over 3 toy docs. Run `python test_sanity.py` before/after Week 2 changes. This is the safety net for BM25 math (wrong-but-plausible scores).
> - **Known debt (deferred, fine):** a few reports have a date field that's just `,` (different h1 layout, next_sibling grabbed wrong node). Harmless until Week 3 date filtering. Don't fix now.



---

## Status: Week 1 Task 1.1 COMPLETE — 497 reports scraped & cached to data/reports.json. Next: Task 1.2 (Postgres) or 1.3 (tokenizer).

---

## Status: Week 1 Task 1.2 COMPLETE — 497 reports loaded into PostgreSQL. Next: Task 1.3 (tokenizer — first "by hand" piece).

---

## Status: Week 1 Task 1.3 COMPLETE — tokenizer built by hand. Next: Task 1.4 (inverted index — THE HEART).

---

## Status: WEEK 1 COMPLETE ✓ (all 5 tasks). Engine does instant word-matching over 497 real reports. Next: WEEK 2 — BM25 ranking (the meat).

---

## Progress: Task 1.4 — Inverted Index DONE (THE HEART)
`src/index.py` — `build_index(documents)` returns `(index, doc_len)`:
```python
from collections import defaultdict, Counter
from src.tokenizer import tokenize   # note: src. prefix needed when run from project root

def build_index(documents):
    index = defaultdict(dict)   # word -> {doc_id: count}
    doc_len = {}                # doc_id -> total word count (for week-2 ranking)
    for doc in documents:
        words = tokenize(doc["trail_name"] + " " + doc["body"])
        doc_len[doc["id"]] = len(words)
        for word, count in Counter(words).items():
            index[word][doc["id"]] = count
    return index, doc_len
```
- **Inverted = word→documents** (normal is doc→words). Flip it once, ahead of time, so search is a lookup not a scan.
- `Counter(words)` counts word frequencies in one step. `defaultdict(dict)` auto-creates empty dict for new words (no KeyError).
- Built over real data: **7,125 unique words**, snow in 125 reports, creek in 118. Retrieved instantly via `index.get('snow')`.

## Progress: Task 1.5 — Proved it works DONE (the payoff)
Built `build_test.py` (project root) that: pulls all rows from postgres, reshapes to dicts, builds index, then RACES slow-scan vs index-lookup.
- **Result: index is 12,265x faster** (11.70ms scan vs ~0.00ms lookup), both find the same 125 reports.
- **The core lesson (unfakeable):** scan is LINEAR (2x data = 2x time → unusable at 30k). Index lookup is CONSTANT time (dict lookup doesn't care about total size). This is why every search engine pre-builds an index.

## Note on imports
`build_test.py` at project root imports `from src.tokenizer import tokenize` and `from src.index import build_index`. Because of this, `src/index.py` uses `from src.tokenizer import tokenize` (with `src.` prefix). Run everything from the project root dir.

**WEEK 1 SHIPPABLE MET:** type a word → instantly get every matching report out of 497 real ones, via hand-built index. No ranking yet (that's week 2). ✓

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