"""
Script para buscar ítems en el catálogo
"""

import sqlite3

DB_FILE = "db/DGCP_UNSPSC.db"

def buscar_item(termino):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT "Código UNSPSC", "Descripción", "Familia" 
        FROM catalogo 
        WHERE "Descripción" LIKE ? OR "Descripción" LIKE ?
        LIMIT 10
    """, (f'%{termino}%', f'%{termino.capitalize()}%'))
    resultados = cur.fetchall()
    conn.close()
    return resultados

if __name__ == "__main__":
    termino = input("Ingresa el término a buscar: ").strip()
    if not termino:
        print("❌ Debes ingresar un término")
    else:
        resultados = buscar_item(termino)
        if resultados:
            print(f"\n📋 ítems encontrados para '{termino}':")
            for i, (codigo, desc, familia) in enumerate(resultados, 1):
                print(f"  {i}. {desc}")
                print(f"     Código: {codigo}")
                print(f"     Familia: {familia}")
        else:
            print(f"❌ No se encontraron ítems con '{termino}'")