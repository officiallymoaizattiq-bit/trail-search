from src.tokenizer import tokenize
from src.index import build_index

# --- tokenizer tests ---
# hand-computed: lowercase, punctuation gone, "the"/"on"/"and" dropped as stopwords
assert tokenize("Snow on the PASS!") == ["snow", "pass"]
assert tokenize("creek-crossing, DEEP deep") == ["creek", "crossing", "deep", "deep"]
assert tokenize("the and of") == []          # all stopwords -> empty
print("tokenizer tests passed")

# --- index tests ---
# 3 tiny fake docs where we KNOW the right answer
docs = [
    {"id": "1", "trail_name": "snow", "body": "snow pass"},
    {"id": "2", "trail_name": "creek", "body": "creek crossing"},
    {"id": "3", "trail_name": "snow", "body": "snow creek"},
]
index, doc_len = build_index(docs)

# "snow" is in doc 1 (twice: name+body) and doc 3 (twice: name+body)
assert index["snow"] == {"1": 2, "3": 2}
# "creek" is in doc 2 (name+body = twice) and doc 3 (body once)
assert index["creek"] == {"2": 2, "3": 1}
# "pass" only in doc 1, once
assert index["pass"] == {"1": 1}
# a word nobody has -> not in index at all
assert "elephant" not in index

# doc lengths: doc1 = tokenize("snow snow pass") = 3 words
assert doc_len["1"] == 3
assert doc_len["2"] == 3    # "creek creek crossing"
assert doc_len["3"] == 3    # "snow snow creek"

print("index tests passed")
print("ALL SANITY CHECKS PASSED")