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

## 9. Exactly where to pick up: WEEK 2 — BM25 RANKING ("the meat")

Right now search returns matches in no particular order. Week 2 makes the BEST match rank first, using **BM25** — the same ranking math real search engines use. It's three common-sense ideas turned into arithmetic:
1. **More mentions = higher score** — but with diminishing returns (10 mentions isn't 10× better than 1). Tuning knob `k1` (~1.5).
2. **Rare words count more** — matching "postholing" means more than matching "trail". This is **IDF** (inverse document frequency).
3. **Short focused docs beat long ramblers** — a tight snow report beats a 5,000-word essay that says "snow" once. Tuning knob `b` (~0.75), using `docLen / avgLen`.

Formula per query word (summed over all query words):
```
score(word, doc) = IDF(word) * ( tf * (k1 + 1) ) / ( tf + k1 * (1 - b + b * docLen/avgLen) )
```
where `tf` = how many times the word appears in that doc (already stored in the index from Week 1).

**Week 2 tasks:** (2.1) compute IDF per word, (2.2) write the full BM25 scorer in `src/ranker.py`, (2.3) tune `b` and `k1` and watch results move, (2.4) add simple stemming (so "hiking"/"hiked"/"hikes" match "hike").

We already have what BM25 needs: the index stores per-word counts (`tf`) and `doc_len` stores document lengths. Average length = mean of `doc_len` values.

**What to deliberately NOT build:** embeddings / vector search / any AI model (nukes the "by hand" pitch), user accounts, a perfect stemmer, crawler frameworks / microservices. One Python codebase, one database.