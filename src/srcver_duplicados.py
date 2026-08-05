import sqlite3

conn = sqlite3.connect(
    r"C:\UNSPSC_DGCP\db\DGCP_UNSPSC.db"
)

cursor = conn.cursor()

cursor.execute("""
SELECT
    termino,
    sinonimo,
    COUNT(*)
FROM sinonimos
GROUP BY
    termino,
    sinonimo
HAVING COUNT(*) > 1
""")

for fila in cursor.fetchall():

    print(fila)

conn.close()