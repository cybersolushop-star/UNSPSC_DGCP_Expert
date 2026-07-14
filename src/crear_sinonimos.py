import sqlite3

DB_FILE = r"C:\UNSPSC_DGCP\db\DGCP_UNSPSC.db"

conn = sqlite3.connect(DB_FILE)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sinonimos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    termino TEXT,
    sinonimo TEXT
)
""")

datos = [

    ("rack", "anaquel"),
    ("rack", "estante"),
    ("rack", "estanteria"),

    ("anaquel", "rack"),
    ("anaquel", "estante"),

    ("abanico", "ventilador"),

    ("laptop", "computadora portatil"),
    ("notebook", "computadora portatil"),

    ("impresora", "printer"),

    ("aire acondicionado", "acondicionador de aire")
]

cursor.executemany(
    """
    INSERT INTO sinonimos
    (termino,sinonimo)
    VALUES (?,?)
    """,
    datos
)

conn.commit()
conn.close()

print("Tabla de sinónimos creada.")