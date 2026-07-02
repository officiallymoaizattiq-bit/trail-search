import re

STOPWORDS = {"the", "a", "an", "and", "of", "to", "in", "on", "is", "it"}


def tokenize(text):
    text = text.lower()                          # 1. lowercase
    words = re.findall(r"[a-z0-9]+", text)       # 2. split on non-letters/numbers
    return [w for w in words if w not in STOPWORDS]   # 3. drop stopwords
