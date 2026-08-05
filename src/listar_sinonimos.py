import sqlite3

DB_FILE = r"C:\UNSPSC_DGCP\db\DGCP_UNSPSC.db"

conn = sqlite3.connect(DB_FILE)

cursor = conn.cursor()

cursor.execute("""
SELECT termino,
       sinonimo,
       capa
FROM sinonimos
ORDER BY termino
""")

for fila in cursor.fetchall():

    print(fila)

conn.close()