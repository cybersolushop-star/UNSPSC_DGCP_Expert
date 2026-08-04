import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "db" / "DGCP_UNSPSC.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Eliminar tabla antigua
cur.execute("DROP TABLE IF EXISTS sinonimos")
print("🗑️ Tabla 'sinonimos' eliminada")

# Crear tabla con la estructura correcta
cur.execute("""
    CREATE TABLE sinonimos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        termino TEXT NOT NULL,
        sinonimo TEXT NOT NULL,
        capa INTEGER DEFAULT 1,
        codigo_unspsc TEXT,
        fecha_actualizacion TEXT
    )
""")
print("✅ Tabla 'sinonimos' creada con la estructura correcta")

# Crear índices
cur.execute("CREATE INDEX idx_sinonimos_termino ON sinonimos(termino)")
cur.execute("CREATE INDEX idx_sinonimos_sinonimo ON sinonimos(sinonimo)")
print("✅ Índices creados")

conn.commit()
conn.close()
print("🎯 ¡Listo! Ahora puedes ejecutar el script de integración nuevamente.")