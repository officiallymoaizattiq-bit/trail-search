from src.db import connect
conn = connect()
cur = conn.cursor()
cur.execute("DELETE FROM documents WHERE body IS NULL OR body=''")
print(f"deleted {cur.rowcount} empty-body reports")
conn.commit()
cur.close()
conn.close()