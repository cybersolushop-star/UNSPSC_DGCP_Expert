import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "db" / "DGCP_UNSPSC.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Verificar si la columna existe
cur.execute("PRAGMA table_info(sinonimos)")
columnas = [col[1] for col in cur.fetchall()]
print(f"📋 Columnas actuales: {columnas}")

if 'codigo_unspsc' not in columnas:
    print("➕ Agregando columna 'codigo_unspsc'...")
    cur.execute("ALTER TABLE sinonimos ADD COLUMN codigo_unspsc TEXT")
    conn.commit()
    print("✅ Columna agregada")
else:
    print("✅ La columna 'codigo_unspsc' ya existe")

conn.close()