from collections import defaultdict, Counter
from src.tokenizer import tokenize


def build_index(documents):     # documents = list of dicts, each with id/title/body
    index = defaultdict(dict)   # word -> {doc_id: count}
    doc_len = {}                # doc_id -> total word count

    for doc in documents:
        words = tokenize(doc["trail_name"] + " " + doc["body"])
        doc_len[doc["id"]] = len(words)
        for word, count in Counter(words).items():
            index[word][doc["id"]] = count

    return index, doc_len