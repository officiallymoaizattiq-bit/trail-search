# Trail Search Engine — Complete Context & Handoff

> **Purpose of this file:** a total brain-dump of the project so that Claude (in a new chat) or any human can pick up with FULL understanding of what's built, why every decision was made, and exactly where to continue. If starting a new chat, paste this whole file first.

---

## 1. What this project is

A **search engine for hiking trip reports, built from scratch** — no search libraries. It's a one-month flagship portfolio project for **Moaiz Attiq** (early CS student). The whole point: build the *hard parts by hand* (the text tokenizer, the inverted index, the BM25 ranking) so it can't be faked and can be defended in interviews for years.

- **The one rule:** the "search brain" (index, ranking, word handling) is hand-written. The moment a search library does the searching for you, the project is dead. Everything ELSE (web server, database, frontend) uses normal standard tools.
- **Data:** thousands of real hiking trip reports.
- **Stack:** Python · PostgreSQL · FastAPI · React.
- **Timeline:** 4 weeks. Week 1 = data + index. Week 2 = BM25 ranking. Week 3 = website + hiking-condition tagging. Week 4 = scale + deploy + real users.
- **Repo:** https://github.com/officiallymoaizattiq-bit/trail-search
- **Editor:** VS Code. **Machine:** macOS (Apple Silicon), Homebrew.

---

## 2. Current status

**WEEK 1 IS COMPLETE (all 5 tasks).** The engine can take a word and instantly return every one of 497 real trip reports that contains it, via a hand-built inverted index. No ranking yet — that's Week 2.

Next up: **Week 2 — BM25 ranking** ("the meat"). Turns unordered matches into best-first results.

---

## 3. The single most important decision: data source changed from the plan

**The original build plan said to use the Reddit API. That path is DEAD.**

- As of **November 2025**, Reddit closed self-serve OAuth app creation ("Responsible Builder Policy"). The create-app form at reddit.com/prefs/apps now silently fails — you check the recaptcha, hit "create app," and it just resets with no error. It no longer issues credentials to individuals; it submits an approval request that can take weeks or never resolve.
- **We switched to scraping public trip-report websites instead.** No API keys, no OAuth, no approval queue.
- **Primary source chosen: WTA (Washington Trails Association)** — ~280,000 public trip reports, no login to read, and — crucially — every report is *purpose-built to describe trail conditions*. That's a perfect fit for the Week 3 "hiking edge" feature (condition tagging). Reddit would've been noisier (gear talk, photos, beginner questions); WTA is pre-filtered to exactly the condition-focused text we want.
- Planned additional sources for later (for writing-style diversity, which stress-tests ranking): **Oregon Hikers forum**, **SummitPost**. Explicitly **NOT AllTrails** — hostile anti-scraping ToS and data-ownership terms.
- **Verdict:** this is arguably a *stronger* version of the original plan, not a compromise.

---

## 4. Environment setup (all done)

- **Python 3.13** (venv was built off the system python3, not the Homebrew 3.12 — this is fine, 3.13 is newer and works).
- **venv:** `.venv/` in project root. Activate every session with `source .venv/bin/activate`. When active the prompt shows `(.venv)`.
- **Git:** configured (`user.name` = officiallymoaizattiq-bit, `user.email` = officiallymoaizattiq@gmail.com), pushing to GitHub over HTTPS.
- **PostgreSQL 16:** installed via `brew install postgresql@16`, running as a background service (`brew services start postgresql@16`). Commands (`psql`, `createdb`) are on PATH via `/opt/homebrew/bin`.
- **Installed Python packages:** `requests`, `beautifulsoup4`, `psycopg[binary]` (all frozen into `requirements.txt` via `pip freeze`).

---

## 5. Project structure

```
trail-search/
├── .venv/                  # virtual environment (gitignored)
├── data/                   # gitignored — too big for the repo
│   └── reports.json        # 497 scraped reports, cached (compact single-line JSON)
├── scripts/
│   ├── fetch_reports.py    # THE SCRAPER — crawls WTA, parses reports, caches to JSON
│   └── load_db.py          # reads reports.json, inserts each into Postgres
├── src/
│   ├── __init__.py
│   ├── tokenizer.py        # BY HAND: text -> clean list of words
│   ├── index.py            # BY HAND: builds the inverted index (the heart)
│   ├── ranker.py           # empty — Week 2 (BM25)
│   └── search.py           # empty — Week 2/3 (ties query -> ranked results)
├── build_test.py           # project root — builds index over the DB & proves it's fast
├── requirements.txt
├── README.md
├── PROJECT_LOG.md          # running progress log
└── .gitignore              # ignores .venv/, __pycache__/, data/, *.pkl, .env, .DS_Store
```

---

## 6. What each file does & every field/selector

### The 8 fields scraped per report
| field | meaning | how it's extracted |
|---|---|---|
| `id` | unique report id | `url.split(".")[-1]` — the number at the end of the URL |
| `url` | the report's page URL | we already have it (the URL we requested) |
| `trail_name` | the hike name | `<a>` text inside `h1.documentFirstHeading` |
| `date` | date hiked | text node after the `<a>` in the h1 (still has leading `— `; clean later) |
| `region` | area/region | `id="hike-region"` |
| `author` | who posted | `span[itemprop="author"] > span.wta-icon-headline__text` |
| `body` | the report text (what we index) | `id="tripreport-body-text"` |
| `conditions` | structured trail-condition tags | see below |

### The conditions block (the Week-3 gold)
WTA hand-labels trail conditions in a structured block — most scrapers only get freeform text; we get BOTH.
- Container: `div#trip-conditions`
- Each condition: `div.trip-condition` containing an `<h4>` (category label like "Snow", "Bugs", "Road", "Trail Conditions", "Type of Hike") and a `<span>` (the value).
- Parsed into a dict: `{h4_text: span_text}`, e.g. `{"Snow": "Intermittent snow – not hard to cross", "Bugs": "No bugs"}`.

### WTA scraping gotchas (learned the hard way)
- **WTA has bot detection.** A plain `requests.get(url)` returns 403. **Must** send a browser-like `User-Agent` header. (This is why our fetch has `headers = {"User-Agent": "Mozilla/5.0 ..."}`.)
- **Listing pages paginate by offset:** URL is `https://www.wta.org/@@search_tripreport_listing?b_size=50&b_start:int=N` where N = 0, 50, 100, ... (50 reports per page). Full feed is ~5,638 pages / ~281,877 reports.
- **Each report is linked twice** on a listing page (title + thumbnail), so we dedupe with a `set()`.
- **Report links live in** `h3.listitem-title > a` — but we grab them more robustly by taking every `<a>` whose href contains `trip_report-` (survives markup changes).
- Some links are relative (no domain) or `http://` — a few of these cause skips; that's fine.

### scripts/fetch_reports.py — the scraper (3 stages = separation of concerns)
1. `get_report_urls(b_start)` — fetches one listing page, returns all `trip_report-` URLs on it (deduped via set).
2. `parse_report(url)` — fetches one report page, extracts all 8 fields, returns a dict. Has an `if block:` guard so reports with no conditions block don't crash.
3. Main block — loops `b_start` 0→450 (10 pages), dedupes, then loops every URL calling `parse_report` wrapped in `try/except` (one bad page can't kill the whole run), `time.sleep(1)` between requests (politeness / avoid ban), and `json.dump`s everything to `data/reports.json`.
- **Result: 497/503 reports saved (~99%).** The 6 skips were real-world messiness (missing fields → None, relative URLs) — caught by try/except. "Good enough beats complete."

### scripts/load_db.py — JSON → Postgres
- `json.load`s reports.json, connects with `psycopg.connect("dbname=trailsearch")`, loops and `INSERT`s each row, `conn.commit()`.
- Uses `%s` placeholders + a values tuple (**prevents SQL injection** — never f-string values into SQL).
- `ON CONFLICT (id) DO NOTHING` makes it **idempotent** (safe to re-run, won't duplicate on the primary key).
- `conditions` dict is stored via `json.dumps(...)` into a `JSONB` column (keeps it queryable, not flat text).
- **Result: 497 rows loaded & committed.**

### The `documents` table (Postgres, db name `trailsearch`)
```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    trail_name TEXT, date TEXT, region TEXT, author TEXT,
    body TEXT, url TEXT,
    conditions JSONB
);
```

### src/tokenizer.py — BY HAND (first engine piece)
```python
import re
STOPWORDS = {"the", "a", "an", "and", "of", "to", "in", "on", "is", "it"}
def tokenize(text):
    text = text.lower()                              # 1. lowercase (Snow == snow)
    words = re.findall(r"[a-z0-9]+", text)           # 2. split on non-letter/number (drops punctuation)
    return [w for w in words if w not in STOPWORDS]  # 3. drop junk stopwords
```
- Stopword list is deliberately tiny (10 words). Expand later only if junk clogs results.
- **Lesson:** never `.remove()` from a list you're looping — it shifts and skips. Use a list comprehension.

### src/index.py — BY HAND (THE HEART: the inverted index)
```python
from collections import defaultdict, Counter
from src.tokenizer import tokenize        # src. prefix needed (run from project root)

def build_index(documents):
    index = defaultdict(dict)   # word -> {doc_id: count}
    doc_len = {}                # doc_id -> total word count (for Week-2 ranking)
    for doc in documents:
        words = tokenize(doc["trail_name"] + " " + doc["body"])
        doc_len[doc["id"]] = len(words)
        for word, count in Counter(words).items():
            index[word][doc["id"]] = count
    return index, doc_len
```
- **Inverted** = word→documents (normal is doc→words). Build once ahead of time, so search is a *lookup* not a *scan*.
- `Counter(words)` counts word frequencies in one step; `defaultdict(dict)` auto-creates an empty dict for each new word (no KeyError).
- Built over real data: **7,125 unique words**; "snow" in 125 reports, "creek" in 118.

### build_test.py — proves the index (Task 1.5)
- Pulls all rows from Postgres, reshapes to dicts, builds the index, then RACES a dumb full-scan vs an index lookup for the word "snow".
- **Result: index is 12,265× faster** (11.70 ms scan vs ~0.00 ms lookup), both find the same 125 reports.
- **The core lesson:** the scan is LINEAR (2× data = 2× time → unusable at 30k). The index lookup is ~CONSTANT time (dict lookup doesn't care about total size). This is why every search engine pre-builds an index.

---

## 7. Recurring lessons / gotchas (so we don't repeat mistakes)

- **Unsaved file = running OLD code.** VS Code shows a dot on the tab when unsaved. This bit us ~4 times (a script would run with no output, or throw a NameError for something already "fixed"). Always Cmd+S before running.
- **Pasting code into chat mangles indentation.** Python cares about indentation. Fix: paste inside triple-backtick code blocks, OR just paste the terminal error (which is plain text and survives). Screenshots also preserve indentation.
- **`python scripts/x.py`**, not `scripts/x.py` — must prefix with `python` or zsh gives "permission denied".
- **psql commands use a BACKSLASH:** `\dt` (list tables), `\q` (quit). Not `/`.
- **Imports:** `build_test.py` runs from project root and imports `from src.tokenizer ...` / `from src.index ...`, so `index.py` also uses the `src.` prefix. Keep running from the project root.

---

## 8. Git history (the story so far)
Clean, honest commit history documenting the build week by week:
1. initial project skeleton
2. add project log
3. add requests + beautifulsoup deps
4. week1: single report extraction works, all 8 fields
5. week1: full scraper working, 497 reports cached
6. week1: task 1.2 - load reports into postgres
7. week1: task 1.3 tokenizer
8. week1 complete: tokenizer + inverted index, 12000x faster than scan

---

## 9. Where to pick up: WEEK 2 — BM25 RANKING (IN PROGRESS, next = stemming)

BM25 is three common-sense ideas as arithmetic: (1) more mentions = higher, diminishing returns, knob `k1`~1.5; (2) rare words count more = IDF; (3) short focused docs beat long ramblers, knob `b`~0.75 via docLen/avgLen.

Per-word score, summed over query words:
```
score(word, doc) = IDF(word) * ( tf * (k1 + 1) ) / ( tf + k1 * (1 - b + b * docLen/avgLen) )
```

**DONE so far (all in `src/ranker.py`, tested via `build_test.py`):**
- **2.1 IDF** — `idf(word, index, total_docs)` = `math.log(1 + (total_docs - n + 0.5)/(n + 0.5))`. Verified: trail 0.211 (common), snow 1.332, wildflower 4.467 (rare). Works.
- **helper `avg_doc_len(doc_len)`** — mean of doc_len.values(), empty-guarded.
- **2.2 BM25 scorer** — `bm25_search(query, index, doc_len, avg_len, total_docs, k1=1.5, b=0.75)`. Loops only docs containing each query word (inverted index), sums per-word scores, returns sorted best-first. Real query "river crossing high snow" returns genuinely relevant trails. Working.
- **2.3 tuning** — watched `b` (0→long docs win, 1→short docs win) and `k1` (low→repetition ignored, high→repetition dominates) move the rankings. Reset to defaults k1=1.5, b=0.75.

**NEXT — 2.4 stemming:** make "hiking"/"hiked"/"hikes" all match "hike". Write a rough suffix stripper by hand (chop -ing/-ed/-s), apply it inside `tokenize` so both indexing and querying stem consistently. Don't chase linguistic perfection — rough and useful. This is the last Week 2 task before the Week 2 shippable (good ranked results on a real query).

**What to deliberately NOT build:** embeddings/vector search/AI models (nukes the by-hand pitch), user accounts, a perfect stemmer, crawler frameworks/microservices.

**Reminder for after Week 2:** the BM25 test code is currently bolted onto `build_test.py`. Week 3's FastAPI server needs the "load from DB + build index + search" path as a real function in `src/` — refactor at the Week 2→3 boundary (see section 10).

---

## 10. Senior engineering review (end of Week 1) — read before Week 2

A critical review of the Week 1 foundation. These are risks/tech-debt items, ordered by impact. The first two should be addressed BEFORE Week 2; the rest are notes-to-self to handle when the relevant week forces them.

### DO BEFORE WEEK 2

**[HIGH] Corpus is temporally skewed — all ~497 reports are from one ~10-day window (late June 2026).**
The scrape used `range(0, 500, 50)` = the 500 NEWEST reports, so nearly every URL is `trip_report-2026-06-2X`. They all describe the same season (snowmelt: high creeks, lingering snow, early bugs). This poisons BM25: IDF measures term *rarity*, but "snow in 125/497" here reflects seasonal coincidence, not meaningful rarity. Tuning `k1`/`b` against this corpus tunes against an unrepresentative distribution; it'll silently mislead in Week 2 and break when Week 4 scales to multi-season data.
- **Fix (cheap, ~20 min):** change the scrape to sample ACROSS the feed instead of just the newest. e.g. loop `b_start` over spread-out offsets like 0, 500, 2000, 5000, 20000, 50000 (feed is ~5,600 pages / ~281k reports). Gets seasonal + geographic spread for free. Re-run scrape, re-run load_db (ON CONFLICT makes it safe).

**[HIGH] No tests — verification is "run it and eyeball the terminal."**
Fine for scraping; dangerous for Week 2, which is MATH (idf, BM25 scorer). Math bugs are silent and plausible-looking (wrong denominator, off-by-one count) — you can't catch them by eye.
- **Fix (~30 min, do it at the START of Week 2):** 3–4 `assert` statements over a toy 3-document index where you hand-computed the right answer. No framework needed. Turns "my ranking is wrong and I'm confused" into "my test caught it in the toy case."

### HANDLE WHEN THE RELEVANT WEEK FORCES IT

**[MED] `build_test.py` is load-bearing throwaway code.** It holds the only working "DB → build index → search" path, but it's named "test" and lives in project root. Week 3's FastAPI server needs exactly this logic on boot. Refactor the "load docs from DB + build index" part into a real function in `src/` (e.g. `src/search.py` or a `src/loader.py`) before/when starting Week 3, so the server imports it instead of duplicating it.

**[MED] `id` extraction is fragile for old-format URLs.** `report_id = url.split(".")[-1]` assumes the modern `trip_report-2026-06-30.210341804556` (dot) format. OLD reports use a DASH format (`trip_report-2020-08-01-6654865899`) — seen in the scrape, currently skipped as bad URLs. When the corpus is widened (see HIGH item above), more old-format URLs will appear; `.split(".")[-1]` returns the wrong/possibly-non-unique id → silent PRIMARY KEY collisions / mystery ON CONFLICT skips. Handle both formats (regex the trailing id, or detect dash vs dot) when broadening the scrape.

### EXPLICITLY FINE TO DEFER (do NOT gold-plate these now)
- **Raw date string with leading `— `:** defer until Week 3 date filtering actually needs it. Parsing now = speculative work.
- **`\xa0` non-breaking spaces in body/conditions text:** the tokenizer's `[a-z0-9]+` regex already discards them at index time. Leave it.
- **10-word stopword list:** expand only when you SEE junk words topping rankings in Week 2. Data-driven > speculative.
- **Only 497 reports (the count):** fine for building/testing. It's the *distribution* (HIGH item) that matters, not the number. Do NOT scrape 10k yet — plan correctly saves scale for Week 4.

### Review verdict
Architecture is sound (clean scrape → cache → load → index separation; safe SQL; idempotent inserts; try/except robustness). The foundation is good. The one thing that genuinely threatens Week 2's correctness is the **corpus skew** — fix that and add a few asserts, and Week 2 stands on solid ground.