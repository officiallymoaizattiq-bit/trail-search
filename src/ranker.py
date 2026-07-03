import math
from src.tokenizer import tokenize

def idf(word, index, total_docs):
    n = len(index.get(word, {}))       # how many docs contain this word
    if n == 0:
        return 0
    return math.log(1 + (total_docs - n + 0.5) / (n + 0.5))

    #calculate the average document length
def avg_doc_len(doc_len):
    total_length = sum(doc_len.values())
    return total_length / len(doc_len) if doc_len else 0

def bm25_search(query, index, doc_len, avg_len, total_docs, k1=1.5, b=0.75):
    scores = {}
    for word in set(tokenize(query)):
        word_idf = idf(word, index, total_docs)
        for doc_id, tf in index.get(word, {}).items():
            norm = 1 - b + b * (doc_len[doc_id] / avg_len)
            score = word_idf * (tf * (k1 + 1)) / (tf + k1 * norm)
            scores[doc_id] = scores.get(doc_id, 0) + score
    return sorted(scores.items(), key=lambda x: -x[1])