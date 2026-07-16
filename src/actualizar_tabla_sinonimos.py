import sqlite3

DB_FILE = r"C:\UNSPSC_DGCP\db\DGCP_UNSPSC.db"

conn = sqlite3.connect(DB_FILE)

cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE sinonimos
        ADD COLUMN capa INTEGER DEFAULT 1
    """)

    print("Columna CAPA agregada.")

except Exception as e:

    print("La columna ya existe.")
    print(e)

conn.commit()
conn.close()