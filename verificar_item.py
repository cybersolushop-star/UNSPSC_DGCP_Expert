import sqlite3
conn = sqlite3.connect('db/DGCP_UNSPSC.db')
cur = conn.cursor()
cur.execute('SELECT "Código UNSPSC", "Descripción" FROM catalogo WHERE "Descripción" = "Servicios de cáterin"')
resultado = cur.fetchone()
if resultado:
    print(f'✅ Encontrado: {resultado[0]} - {resultado[1]}')
else:
    print('❌ No encontrado')
conn.close()