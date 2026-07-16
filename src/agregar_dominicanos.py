import sqlite3

DB_FILE = r"C:\UNSPSC_DGCP\db\DGCP_UNSPSC.db"

datos = [

    ("automovil", "carro", 3),
    ("camioneta", "jeepeta", 3),
    ("motocicleta", "motor", 3),

    ("trapeador", "mapo", 3),

    ("jeringa", "jeringuilla", 3),

    ("bloque de concreto", "block", 3),

    ("computadora portatil", "laptop hp", 2),

    ("computadora portatil", "laptop dell", 2),

    ("impresora", "printer", 2)

]

conn = sqlite3.connect(DB_FILE)

cursor = conn.cursor()

cursor.executemany(
    """
    INSERT INTO sinonimos
    (termino,sinonimo,capa)
    VALUES (?,?,?)
    """,
    datos
)

conn.commit()

print(
    f"Insertados: {cursor.rowcount}"
)

conn.close()
