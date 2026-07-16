from src.db import connect
from src.tokenizer import tokenize
from src.index import build_index
from src.ranker import bm25_search, avg_doc_len

conn = connect()
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

queries = [
    "snow on the pass",
    "river crossing dangerous high water",
    "wildflowers in bloom",
    "muddy trail blowdowns",
    "bugs mosquitoes",
]

for q in queries:
    print(f"\n=== '{q}' ===")
    for doc_id, score in bm25_search(q, index, doc_len, avg, total)[:5]:
        print(f"  {score:.2f}  {names[doc_id]}")