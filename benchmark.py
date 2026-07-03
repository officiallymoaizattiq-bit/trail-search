import time
import psycopg
from src.engine import SearchEngine

# --- your engine ---
print("building your engine...")
mine = SearchEngine()

# --- postgres connection for its full-text search ---
conn = psycopg.connect("dbname=trailsearch")

def postgres_search(query, limit=5):
    # turn "snow on the pass" into "snow & on & the & pass" for to_tsquery
    terms = " & ".join(query.split())
    cur = conn.cursor()
    cur.execute(
        """
        SELECT trail_name, ts_rank(search_vector, to_tsquery('english', %s)) AS rank
        FROM documents
        WHERE search_vector @@ to_tsquery('english', %s)
        ORDER BY rank DESC
        LIMIT %s
        """,
        (terms, terms, limit),
    )
    rows = cur.fetchall()
    cur.close()
    return rows

queries = [
    "snow on the pass",
    "avalanche danger",
    "no bugs",
    "wildflowers bloom",
]

for q in queries:
    print("\n" + "=" * 60)
    print(f"QUERY: '{q}'")
    print("=" * 60)

    # time your engine
    t = time.time()
    my_results = mine.search(q, limit=5)
    my_time = (time.time() - t) * 1000

    # time postgres
    t = time.time()
    try:
        pg_results = postgres_search(q, limit=5)
    except Exception as e:
        pg_results = []
        print(f"  (postgres error: {e})")
    pg_time = (time.time() - t) * 1000

    print(f"\n  YOUR ENGINE ({my_time:.2f}ms):")
    for r in my_results:
        print(f"    {r['score']:.2f}  {r['trail_name']}")

    print(f"\n  POSTGRES FTS ({pg_time:.2f}ms):")
    for name, rank in pg_results:
        print(f"    {rank:.4f}  {name}")

conn.close()