import sqlite3

conn = sqlite3.connect(
    r"C:\UNSPSC_DGCP\db\DGCP_UNSPSC.db"
)

cursor = conn.cursor()

cursor.execute("""
DELETE FROM sinonimos
WHERE id NOT IN (
    SELECT MIN(id)
    FROM sinonimos
    GROUP BY termino,sinonimo
)
""")

conn.commit()

print(
    f"Registros eliminados: {cursor.rowcount}"
)

conn.close()