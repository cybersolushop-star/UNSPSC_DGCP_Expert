import pandas as pd
import sqlite3
from pathlib import Path

CSV_FILE = r"C:\UNSPSC_DGCP\data\CATALOGO_DGCP.csv"
DB_FILE = r"C:\UNSPSC_DGCP\db\DGCP_UNSPSC.db"

print("Leyendo catálogo...")

# Intentar varias codificaciones
for encoding in ["utf-8", "latin1", "cp1252"]:
    try:
        df = pd.read_csv(
            CSV_FILE,
            sep=None,
            engine="python",
            encoding=encoding
        )
        print(f"Catálogo leído usando {encoding}")
        break
    except Exception:
        continue

# Limpiar nombres de columnas
df.columns = [c.strip() for c in df.columns]

# Eliminar filas vacías
df = df.dropna(subset=["Código UNSPSC", "Descripción"])

# Convertir códigos a texto
df["Código UNSPSC"] = df["Código UNSPSC"].astype(str)

# Crear carpeta db si no existe
Path(r"C:\UNSPSC_DGCP\db").mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_FILE)

# Guardar catálogo
df.to_sql(
    "catalogo",
    conn,
    if_exists="replace",
    index=False
)

cursor = conn.cursor()

# Índices para acelerar búsquedas
cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_codigo
ON catalogo ("Código UNSPSC")
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_descripcion
ON catalogo ("Descripción")
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_segmento
ON catalogo ("Segmento")
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_familia
ON catalogo ("Familia")
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_clase
ON catalogo ("Clase")
""")

# Historial de consultas
cursor.execute("""
CREATE TABLE IF NOT EXISTS historial_busquedas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    consulta TEXT
)
""")

conn.commit()
conn.close()

print("====================================")
print("BASE DE DATOS CREADA CORRECTAMENTE")
print("Archivo:", DB_FILE)
print("Registros:", len(df))
print("====================================")