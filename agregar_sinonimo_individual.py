"""
Script para agregar uno o múltiples sinónimos a un ítem específico
"""

import sqlite3

DB_FILE = "db/DGCP_UNSPSC.db"

def agregar_sinonimos():
    print("🔍 AGREGAR SINÓNIMOS")
    print("=" * 50)
    
    # Paso 1: Ingresar el término principal
    termino = input("📝 Ingresa el término principal (ej: Ollas para uso doméstico): ").strip()
    if not termino:
        print("❌ Debes ingresar un término")
        return
    
    # Paso 2: Ingresar los sinónimos (separados por comas)
    sinonimos_input = input("📝 Ingresa los sinónimos (separados por coma): ").strip()
    if not sinonimos_input:
        print("❌ Debes ingresar al menos un sinónimo")
        return
    
    # Limpiar y dividir sinónimos
    sinonimos = [s.strip() for s in sinonimos_input.split(',') if s.strip()]
    
    if not sinonimos:
        print("❌ No se ingresaron sinónimos válidos")
        return
    
    # Mostrar resumen
    print(f"\n📋 Término: {termino}")
    print(f"📋 Sinónimos a agregar ({len(sinonimos)}):")
    for s in sinonimos:
        print(f"  - {s}")
    
    confirmar = input("\n¿Agregar estos sinónimos? (s/n): ").strip().lower()
    if confirmar != 's':
        print("❌ Operación cancelada")
        return
    
    # Conectar a la base de datos
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    agregados = 0
    duplicados = 0
    errores = 0
    
    for sinonimo in sinonimos:
        if sinonimo.lower() == termino.lower():
            print(f"  ⚠️ '{sinonimo}' es igual al término, omitido")
            errores += 1
            continue
        
        # Verificar si la relación ya existe
        cur.execute("""
            SELECT COUNT(*) FROM sinonimos 
            WHERE termino = ? AND sinonimo = ?
        """, (termino, sinonimo))
        
        if cur.fetchone()[0] > 0:
            print(f"  ⚠️ La relación '{termino} ↔ {sinonimo}' ya existe")
            duplicados += 1
            continue
        
        # Agregar sinónimo (bidireccional)
        cur.execute("INSERT INTO sinonimos (termino, sinonimo, capa) VALUES (?, ?, 1)", (termino, sinonimo))
        cur.execute("INSERT INTO sinonimos (termino, sinonimo, capa) VALUES (?, ?, 1)", (sinonimo, termino))
        conn.commit()
        
        print(f"  ✅ {termino} ↔ {sinonimo}")
        agregados += 1
    
    conn.close()
    
    print(f"\n📊 Resumen:")
    print(f"  ✅ Sinónimos agregados: {agregados}")
    print(f"  ⚠️ Duplicados omitidos: {duplicados}")
    print(f"  ❌ Errores: {errores}")

if __name__ == "__main__":
    agregar_sinonimos()