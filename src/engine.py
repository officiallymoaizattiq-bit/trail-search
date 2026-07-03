import os
import pickle

import psycopg
from src.index import build_index
from src.ranker import bm25_search, avg_doc_len

INDEX_PATH = "data/index.pkl"


def load_documents():
    conn = psycopg.connect("dbname=trailsearch")
    cur = conn.cursor()
    cur.execute("SELECT id, trail_name, body, region, url, conditions FROM documents")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "trail_name": r[1], "body": r[2], "region": r[3], "url": r[4], "conditions": r[5]}
        for r in rows
    ]


def build_and_save_index():
    documents = load_documents()
    index, doc_len = build_index(documents)
    avg_len = avg_doc_len(doc_len)
    data = {
        "documents": documents,
        "index": index,
        "doc_len": doc_len,
        "avg_len": avg_len,
    }
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump(data, f)
    print(f"indexed {len(documents)} docs -> {INDEX_PATH}")
    return data


class SearchEngine:
    def __init__(self):
        if os.path.exists(INDEX_PATH):
            with open(INDEX_PATH, "rb") as f:
                data = pickle.load(f)
        else:
            data = build_and_save_index()
        self.documents = data["documents"]
        self.docs_by_id = {d["id"]: d for d in self.documents}
        self.index = data["index"]
        self.doc_len = data["doc_len"]
        self.avg_len = data["avg_len"]
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
