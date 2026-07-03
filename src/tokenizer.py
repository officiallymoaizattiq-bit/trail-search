import re

STOPWORDS = {"the", "a", "an", "and", "of", "to", "in", "on", "is", "it"}

def stem(word):
    for suffix in ["ing", "ed", "es", "s"]:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word

def tokenize(text):
    text = text.lower()                          # 1. lowercase
    words = re.findall(r"[a-z0-9]+", text)       # 2. split on non-letters/numbers
    return [stem(w) for w in words if w not in STOPWORDS]   # 3. drop stopwords
