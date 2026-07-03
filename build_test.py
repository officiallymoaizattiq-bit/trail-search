import psycopg
from src.tokenizer import tokenize
from src.index import build_index
from src.ranker import idf
from src.ranker import bm25_search, avg_doc_len

# pull all reports out of postgres
conn = psycopg.connect("dbname=trailsearch")
cur = conn.cursor()
cur.execute("SELECT id, trail_name, body FROM documents")
rows = cur.fetchall()
cur.close()
conn.close()

# turn each db row into a dict build_index expects
documents = []
for row in rows:
    documents.append({"id": row[0], "trail_name": row[1], "body": row[2]})

print(f"loaded {len(documents)} documents from db")

# build the index
index, doc_len = build_index(documents)

print(f"index has {len(index)} unique words")
print(f"reports containing 'snow': {len(index.get('snow', {}))}")
print(f"reports containing 'creek': {len(index.get('creek', {}))}")


import time

# --- the DUMB way: scan every document, no index ---
def slow_search(word, documents):
    results = []
    for doc in documents:
        words = tokenize(doc["trail_name"] + " " + doc["body"])
        if word in words:
            results.append(doc["id"])
    return results

# --- the FAST way: just look it up in the index ---
def fast_search(word, index):
    return list(index.get(word, {}).keys())

# --- race them ---
query = "snow"

start = time.time()
slow_results = slow_search(query, documents)
slow_time = time.time() - start

start = time.time()
fast_results = fast_search(query, index)
fast_time = time.time() - start

print(f"\nsearching for '{query}':")
print(f"  slow scan:  found {len(slow_results)} reports in {slow_time*1000:.2f} ms")
print(f"  index lookup: found {len(fast_results)} reports in {fast_time*1000:.2f} ms")
print(f"  index is {slow_time/fast_time:.0f}x faster")


total_docs = len(documents)
for word in ["snow", "wildflower", "postholing", "trail", "the"]:
    print(f"{word:12} idf={idf(word, index, total_docs):.3f}  (in {len(index.get(word, {}))} docs)")


avg_len = avg_doc_len(doc_len)
total_docs = len(documents)

# build a quick id -> trail_name lookup so results are readable
names = {d["id"]: d["trail_name"] for d in documents}

query = "river crossing high snow"
results = bm25_search(query, index, doc_len, avg_len, total_docs)

print(f"\ntop 10 for '{query}':")
for doc_id, score in results[:10]:
    print(f"  {score:.3f}  {names[doc_id]}")