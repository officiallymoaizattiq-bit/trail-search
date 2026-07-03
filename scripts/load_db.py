import json
import os
import psycopg

# load the scraped reports back off disk
with open("data/reports.json") as f:
    reports = json.load(f)

print(f"loaded {len(reports)} reports from json")

# connect to the postgres database
conn = psycopg.connect(os.environ.get("DATABASE_URL", "dbname=trailsearch"))
cur = conn.cursor()

# insert every report as a row
for r in reports:
    cur.execute(
        """
        INSERT INTO documents (id, trail_name, date, region, author, body, url, conditions)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        (
            r["id"],
            r["trail_name"],
            r["date"],
            r["region"],
            r["author"],
            r["body"],
            r["url"],
            json.dumps(r["conditions"]),
        ),
    )

conn.commit()
print(f"inserted rows, committed to db")

cur.close()
conn.close()