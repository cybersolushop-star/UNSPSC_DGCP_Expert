import sqlite3
import pandas as pd

DB_FILE = r"C:\UNSPSC_DGCP\db\DGCP_UNSPSC.db"

EXCEL_FILE = r"C:\UNSPSC_DGCP\data\sinonimos.xlsx"

# Leer Excel
df = pd.read_excel(
    EXCEL_FILE,
    engine="openpyxl"
)

# ===== PRUEBA =====
print(df.head())
print(f"Filas encontradas: {len(df)}")
# ==================

# Conexión SQLite
conn = sqlite3.connect(DB_FILE)

cursor = conn.cursor()

# Insertar registros
for _, fila in df.iterrows():

    cursor.execute(
        """
        INSERT INTO sinonimos
        (termino,sinonimo,capa)
        VALUES (?,?,?)
        """,
        (
            str(fila["TERMINO"]).strip(),
            str(fila["SINONIMO"]).strip(),
            int(fila["CAPA"])
        )
    )

conn.commit()

print(
    f"Insertados {len(df)} registros."
)

conn.close()