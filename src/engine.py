import psycopg
from src.index import build_index
from src.ranker import bm25_search, avg_doc_len


def load_documents():
    conn = psycopg.connect("dbname=trailsearch")
    cur = conn.cursor()
    cur.execute("SELECT id, trail_name, body, region, url FROM documents")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "trail_name": r[1], "body": r[2], "region": r[3], "url": r[4]}
        for r in rows
    ]


class SearchEngine:
    def __init__(self):
        self.documents = load_documents()
        self.docs_by_id = {d["id"]: d for d in self.documents}
        self.index, self.doc_len = build_index(self.documents)
        self.avg_len = avg_doc_len(self.doc_len)
        self.total_docs = len(self.documents)

    def search(self, query, limit=10):
        ranked = bm25_search(
            query, self.index, self.doc_len, self.avg_len, self.total_docs
        )
        results = []
        for doc_id, score in ranked[:limit]:
            doc = self.docs_by_id[doc_id]
            results.append({
                "id": doc["id"],
                "trail_name": doc["trail_name"],
                "region": doc["region"],
                "url": doc["url"],
                "score": round(score, 3),
            })
        return results