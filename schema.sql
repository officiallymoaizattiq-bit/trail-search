-- Trail Search schema — the single source of truth for the `documents` table.
-- Apply to a fresh database with:  psql "$DATABASE_URL" -f schema.sql
--
-- History note: the schema previously lived only in a live DB dashboard, which
-- is why a table hand-created on a new host silently diverged. Keep it here.

CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    trail_name  TEXT,
    date        TEXT,
    region      TEXT,
    author      TEXT,
    body        TEXT,
    url         TEXT,
    conditions  JSONB
);

-- Full-text search column used ONLY by benchmark.py (hand-built BM25 vs Postgres FTS).
-- The expression matches benchmark.py's to_tsquery('english', ...) config and the
-- original PROJECT_LOG definition EXACTLY: to_tsvector('english', trail_name || body).
-- (No space between trail_name and body — intentional, preserved for benchmark parity.)
-- GENERATED ALWAYS ... STORED keeps it in sync automatically on insert/update.
ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS search_vector tsvector
    GENERATED ALWAYS AS (to_tsvector('english', trail_name || body)) STORED;

CREATE INDEX IF NOT EXISTS documents_search_idx
    ON documents USING gin (search_vector);
