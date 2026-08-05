import sqlite3

DB_FILE = r"C:\UNSPSC_DGCP\db\DGCP_UNSPSC.db"

conn = sqlite3.connect(DB_FILE)

cursor = conn.cursor()

cursor.execute("""
UPDATE sinonimos
SET capa = 1
WHERE capa IS NULL
""")

conn.commit()

print(
    f"Registros actualizados: {cursor.rowcount}"
)

conn.close()