import sys
from pathlib import Path
import sqlite3
import pandas as pd

# 1. Definir las rutas absolutas basadas en la estructura de tu proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

DB_FILE = Path(r"C:\UNSPSC_DGCP\db\DGCP_UNSPSC.db")
ARCHIVO_EXCEL = BASE_DIR / "data" / "sinonimos.xlsx"

# 2. Validar si el archivo de Excel existe en la ruta indicada
if not ARCHIVO_EXCEL.exists():
    print(f"❌ ERROR: No se encontró el archivo Excel en: {ARCHIVO_EXCEL}")
    sys.exit(1)

print(f"📖 Leyendo catálogo desde: {ARCHIVO_EXCEL}")
try:
    # Leer el archivo Excel
    df_plano = pd.read_excel(ARCHIVO_EXCEL)
except Exception as e:
    print(f"❌ ERROR al leer el archivo Excel: {e}")
    sys.exit(1)

# Nos aseguramos de seleccionar estrictamente las tres columnas en el orden correcto
try:
    df_plano = df_plano[['TERMINO', 'SINONIMO', 'CAPA']]
except KeyError:
    print("❌ ERROR: El archivo Excel debe tener las columnas 'TERMINO', 'SINONIMO' y 'CAPA' en la primera fila.")
    sys.exit(1)

# Limpiar espacios en blanco innecesarios en los textos
df_plano['TERMINO'] = df_plano['TERMINO'].astype(str).str.strip()
df_plano['SINONIMO'] = df_plano['SINONIMO'].astype(str).str.strip()
# Aseguramos que CAPA se mantenga como número entero
df_plano['CAPA'] = pd.to_numeric(df_plano['CAPA'], errors='coerce').fillna(3).astype(int)

# Convertir el DataFrame (de 3 columnas) en una lista de tuplas para executemany
datos_excel = list(df_plano.itertuples(index=False, name=None))

print(f"🔌 Conectando a la base de datos SQLite en: {DB_FILE}")
# Nos aseguramos de crear la carpeta de la base de datos si no existiera
DB_FILE.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(str(DB_FILE))
cursor = conn.cursor()

# 3. Reconstruir la tabla incluyendo el campo capa
cursor.execute("DROP TABLE IF EXISTS sinonimos;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sinonimos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    termino TEXT,
    sinonimo TEXT,
    capa INTEGER
)
""")

print(f"📥 Insertando {len(datos_excel)} registros con sus capas en la tabla...")
# 4. Inserción masiva de 3 campos
cursor.executemany(
    """
    INSERT INTO sinonimos
    (termino, sinonimo, capa)
    VALUES (?, ?, ?)
    """,
    datos_excel
)

conn.commit()
conn.close()

print("\n🚀 ¡Tabla de sinónimos (con columna CAPA) actualizada con éxito!")
