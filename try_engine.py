from src.engine import SearchEngine

eng = SearchEngine()
print(f"loaded {eng.total_docs} docs")
for r in eng.search("snow on the pass", limit=5):
    print(f"  {r['score']}  {r['trail_name']} ({r['region']})")