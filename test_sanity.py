from src.tokenizer import tokenize, stem
from src.index import build_index

# --- tokenizer tests (now with stemming) ---
assert tokenize("Snow on the PASS!") == ["snow", "pas"]           # pass -> pas
assert tokenize("creek-crossing, DEEP deep") == ["creek", "cross", "deep", "deep"]  # crossing -> cross
assert tokenize("the and of") == []                               # all stopwords
print("tokenizer tests passed")

# --- stemming tests: the whole point is these collapse together ---
assert stem("hiking") == stem("hikes") == stem("hiked")           # all -> same root
assert stem("snow") == "snow"                                     # short/no suffix untouched
assert stem("crossing") == "cross"
print("stemming tests passed")

# --- index tests ---
docs = [
    {"id": "1", "trail_name": "snow", "body": "snow pass"},
    {"id": "2", "trail_name": "creek", "body": "creek crossing"},
    {"id": "3", "trail_name": "snow", "body": "snow creek"},
]
index, doc_len = build_index(docs)

# "snow" doesn't stem, still in doc 1 (x2) and doc 3 (x2)
assert index["snow"] == {"1": 2, "3": 2}
# "creek" doesn't stem, doc 2 (x2) and doc 3 (x1)
assert index["creek"] == {"2": 2, "3": 1}
# "pass" -> "pas", only doc 1
assert index["pas"] == {"1": 1}
# "crossing" -> "cross", only doc 2
assert index["cross"] == {"2": 1}
# doc lengths unchanged (stemming doesn't change word COUNT)
assert doc_len["1"] == 3
assert doc_len["2"] == 3
assert doc_len["3"] == 3
print("index tests passed")
print("ALL SANITY CHECKS PASSED")