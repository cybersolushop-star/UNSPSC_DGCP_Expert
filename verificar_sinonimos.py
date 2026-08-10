"""
Script para verificar sinónimos de un término
"""

import sqlite3
import sys
from pathlib import Path

DB_FILE = "db/DGCP_UNSPSC.db"

def verificar_sinonimos(termino):
    """Verifica los sinónimos de un término"""
    
    # Verificar que la base de datos existe
    if not Path(DB_FILE).exists():
        print(f"❌ Base de datos no encontrada: {DB_FILE}")
        print(f"📁 Directorio actual: {Path.cwd()}")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Buscar sinónimos donde el término es el principal
    cur.execute("""
        SELECT sinonimo FROM sinonimos 
        WHERE termino = ?
        ORDER BY sinonimo
    """, (termino,))
    
    sinonimos = cur.fetchall()
    
    # Buscar si el término es sinónimo de otro
    cur.execute("""
        SELECT termino FROM sinonimos 
        WHERE sinonimo = ?
        ORDER BY termino
    """, (termino,))
    
    es_sinonimo_de = cur.fetchall()
    
    # Contar total de relaciones
    cur.execute("""
        SELECT COUNT(*) FROM sinonimos 
        WHERE termino = ? OR sinonimo = ?
    """, (termino, termino))
    
    total_relaciones = cur.fetchone()[0]
    
    conn.close()
    
    print("=" * 60)
    print(f"🔍 VERIFICANDO: '{termino}'")
    print("=" * 60)
    
    if sinonimos:
        print(f"\n✅ '{termino}' tiene {len(sinonimos)} sinónimos:")
        for i, s in enumerate(sinonimos, 1):
            print(f"  {i}. {s[0]}")
    else:
        print(f"\n❌ '{termino}' NO tiene sinónimos registrados como término principal")
    
    if es_sinonimo_de:
        print(f"\n📌 '{termino}' es sinónimo de:")
        for i, s in enumerate(es_sinonimo_de, 1):
            print(f"  {i}. {s[0]}")
    
    print(f"\n📊 Total de relaciones encontradas: {total_relaciones}")
    print("=" * 60)

def ver_todos_los_terminos():
    """Muestra todos los términos que tienen sinónimos"""
    if not Path(DB_FILE).exists():
        print(f"❌ Base de datos no encontrada: {DB_FILE}")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT termino, COUNT(*) as cantidad 
        FROM sinonimos 
        GROUP BY termino 
        ORDER BY termino
    """)
    
    resultados = cur.fetchall()
    conn.close()
    
    if resultados:
        print("📋 TODOS LOS TÉRMINOS CON SINÓNIMOS:")
        print("=" * 50)
        total = 0
        for termino, cantidad in resultados:
            print(f"  • {termino}: {cantidad} sinónimos")
            total += cantidad
        print("=" * 50)
        print(f"📊 Total: {len(resultados)} términos, {total} relaciones")
    else:
        print("❌ No hay sinónimos en la base de datos")

def ver_tabla_completa():
    """Muestra todos los registros de la tabla sinonimos"""
    if not Path(DB_FILE).exists():
        print(f"❌ Base de datos no encontrada: {DB_FILE}")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("SELECT termino, sinonimo FROM sinonimos ORDER BY termino")
    resultados = cur.fetchall()
    conn.close()
    
    if resultados:
        print("📋 TABLA COMPLETA DE SINÓNIMOS:")
        print("=" * 60)
        termino_actual = None
        for termino, sinonimo in resultados:
            if termino != termino_actual:
                if termino_actual is not None:
                    print()
                print(f"📌 {termino}:")
                termino_actual = termino
            print(f"  - {sinonimo}")
        print("=" * 60)
        print(f"📊 Total de relaciones: {len(resultados)}")
    else:
        print("❌ La tabla de sinónimos está vacía")

if __name__ == "__main__":
    print("\n🔍 VERIFICADOR DE SINÓNIMOS")
    print("=" * 60)
    print("1. Verificar un término específico")
    print("2. Ver todos los términos con sinónimos")
    print("3. Ver toda la tabla de sinónimos")
    print("4. Verificar 'Estanterías para almacenaje'")
    print("=" * 60)
    
    opcion = input("\nSelecciona una opción (1-4): ").strip()
    
    if opcion == "1":
        termino = input("📝 Ingresa el término: ").strip()
        if termino:
            verificar_sinonimos(termino)
        else:
            print("❌ Debes ingresar un término")
    elif opcion == "2":
        ver_todos_los_terminos()
    elif opcion == "3":
        ver_tabla_completa()
    elif opcion == "4":
        verificar_sinonimos("Estanterías para almacenaje")
    else:
        print("❌ Opción no válida")