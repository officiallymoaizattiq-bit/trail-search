from src.db import connect
conn = connect()
cur = conn.cursor()
cur.execute("SELECT id, trail_name, region, url FROM documents WHERE body IS NULL OR body=''")
for row in cur.fetchall():
    print(row)
cur.close()
conn.close()