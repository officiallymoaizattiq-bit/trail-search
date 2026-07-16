# test_devil.py — run from project root
from src.tokenizer import tokenize, stem
from src.index import build_index
from src.ranker import bm25_search, avg_doc_len, idf
from src.db import connect

print("=" * 55)
print("BUG 2: does repeating a query word inflate its score?")
print("=" * 55)
docs = [
    {"id": "1", "trail_name": "snow", "body": "snow snow snow"},
    {"id": "2", "trail_name": "creek", "body": "creek water"},
]
index, doc_len = build_index(docs)
avg = avg_doc_len(doc_len)
single = dict(bm25_search("snow", index, doc_len, avg, 2))
double = dict(bm25_search("snow snow", index, doc_len, avg, 2))
print(f"  query 'snow':      doc1 score = {single.get('1', 0):.3f}")
print(f"  query 'snow snow': doc1 score = {double.get('1', 0):.3f}")
if abs(double.get("1", 0) - single.get("1", 0)) > 0.001:
    print("  -> CONFIRMED BUG: repeating a word changed the score. query terms not deduped.")
else:
    print("  -> ok, no inflation")

print()
print("=" * 55)
print("STEMMER: collision + false-merge spot check")
print("=" * 55)
# words that SHOULD merge
should_merge = [("hiking", "hiked", "hikes"), ("camping", "camps"), ("crossing", "crossed")]
for group in should_merge:
    roots = [stem(w) for w in group]
    ok = len(set(roots)) == 1
    print(f"  {group} -> {roots}  {'OK merged' if ok else 'DID NOT merge'}")
# words that should NOT merge but might (false collisions)
should_not = [("snow", "snows"), ("bear", "bears"), ("pass", "passed")]
for a, b in should_not:
    print(f"  {a}->{stem(a)}  {b}->{stem(b)}  {'(merged)' if stem(a)==stem(b) else '(separate)'}")

print()
print("=" * 55)
print("DATA INTEGRITY: db check")
print("=" * 55)
conn = connect()
cur = conn.cursor()
cur.execute("SELECT COUNT(*), COUNT(DISTINCT id) FROM documents")
total, distinct = cur.fetchone()
print(f"  rows: {total}   distinct ids: {distinct}   {'OK' if total==distinct else 'ID COLLISION'}")
cur.execute("SELECT COUNT(*) FROM documents WHERE body IS NULL OR body=''")
print(f"  empty bodies: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM documents WHERE trail_name IS NULL OR trail_name=''")
print(f"  empty trail_names: {cur.fetchone()[0]}")
cur.execute("SELECT body, COUNT(*) c FROM documents GROUP BY body HAVING COUNT(*)>1 ORDER BY c DESC LIMIT 3")
dups = cur.fetchall()
print(f"  duplicate-body groups: {len(dups)}")
for body, c in dups:
    print(f"    {c}x: {(body or '')[:50]}")
cur.close()
conn.close()