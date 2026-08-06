"""
Script para agregar un sinónimo a un ítem específico
"""

import sqlite3
import sys

DB_FILE = "db/DGCP_UNSPSC.db"

def agregar_sinonimo():
    print("🔍 AGREGAR SINÓNIMO")
    print("=" * 40)
    
    # Buscar el ítem
    termino = input("Ingresa la descripción del ítem (ej: Dron): ").strip()
    sinonimo = input("Ingresa el sinónimo a agregar (ej: Drone): ").strip()
    
    if not termino or not sinonimo:
        print("❌ Debes ingresar ambos valores")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Verificar si el término existe
    cur.execute("SELECT COUNT(*) FROM sinonimos WHERE termino = ?", (termino,))
    existe = cur.fetchone()[0] > 0
    
    if not existe:
        print(f"⚠️ El término '{termino}' no existe en la tabla de sinónimos")
        print("   ¿Quieres agregarlo como término principal?")
        respuesta = input("   (s/n): ").strip().lower()
        if respuesta != 's':
            conn.close()
            return
    
    # Agregar sinónimo (bidireccional)
    cur.execute("INSERT OR IGNORE INTO sinonimos (termino, sinonimo) VALUES (?, ?)", (termino, sinonimo))
    cur.execute("INSERT OR IGNORE INTO sinonimos (termino, sinonimo) VALUES (?, ?)", (sinonimo, termino))
    conn.commit()
    conn.close()
    
    print(f"✅ Sinónimo agregado: {termino} ↔ {sinonimo}")

if __name__ == "__main__":
    agregar_sinonimo()