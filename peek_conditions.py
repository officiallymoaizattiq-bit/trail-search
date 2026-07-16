import json
from collections import Counter

from src.db import connect

conn = connect()
cur = conn.cursor()
cur.execute("SELECT conditions FROM documents")
rows = cur.fetchall()
cur.close()
conn.close()

# conditions is stored as JSONB, comes back as a dict already
keys = Counter()
sample_values = {}
for (cond,) in rows:
    if not cond:
        continue
    for k, v in cond.items():
        keys[k] += 1
        sample_values.setdefault(k, set()).add(v)

print("=== condition categories (how many reports have each) ===")
for k, count in keys.most_common():
    print(f"  {k}: {count} reports")

print("\n=== sample values per category ===")
for k, vals in sample_values.items():
    print(f"\n{k}:")
    for v in list(vals)[:6]:
        print(f"    - {v}")