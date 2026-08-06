"""
Script para verificar sinónimos de un término
"""

import sqlite3
import sys

DB_FILE = "db/DGCP_UNSPSC.db"

def verificar_sinonimos(termino):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT termino, sinonimo FROM sinonimos 
        WHERE termino = ? OR sinonimo = ?
    """, (termino, termino))
    
    resultados = cur.fetchall()
    conn.close()
    
    if resultados:
        print(f"📋 Sinónimos relacionados con '{termino}':")
        for t, s in resultados:
            print(f"   {t} ↔ {s}")
    else:
        print(f"❌ No se encontraron sinónimos para '{termino}'")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        verificar_sinonimos(sys.argv[1])
    else:
        termino = input("Ingresa el término a verificar: ").strip()
        if termino:
            verificar_sinonimos(termino)