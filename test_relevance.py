import psycopg
from src.tokenizer import tokenize
from src.index import build_index
from src.ranker import bm25_search, avg_doc_len

conn = psycopg.connect("dbname=trailsearch")
cur = conn.cursor()
cur.execute("SELECT id, trail_name, body FROM documents")
rows = cur.fetchall()
cur.close()
conn.close()

documents = [{"id": r[0], "trail_name": r[1], "body": r[2]} for r in rows]
names = {d["id"]: d["trail_name"] for d in documents}
index, doc_len = build_index(documents)
avg = avg_doc_len(doc_len)
total = len(documents)

# each query -> a substring we expect to see in a top-5 trail name
# (hand-verified as correct by eyeballing real results)
expectations = [
    ("snow on the pass", "Snowshoe"),
    ("river crossing dangerous high water", "Creek"),
    ("wildflowers in bloom", "Horse Lake"),
    ("bugs mosquitoes", "Lake"),
]

passed = 0
for query, expected_substr in expectations:
    top5 = bm25_search(query, index, doc_len, avg, total)[:5]
    top5_names = [names[doc_id] for doc_id, _ in top5]
    hit = any(expected_substr.lower() in n.lower() for n in top5_names)
    status = "PASS" if hit else "FAIL"
    if hit:
        passed += 1
    print(f"[{status}] '{query}' -> expected a result containing '{expected_substr}'")
    if not hit:
        print(f"        got: {top5_names}")

print(f"\n{passed}/{len(expectations)} relevance checks passed")
assert passed == len(expectations), "relevance regression detected"
print("ALL RELEVANCE CHECKS PASSED")