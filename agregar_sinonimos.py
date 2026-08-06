"""
Script para AGREGAR sinónimos desde mapeo_completo.xlsx sin eliminar los existentes
"""

import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "db" / "DGCP_UNSPSC.db"
EXCEL_FILE = BASE_DIR / "data" / "mapeo_completo.xlsx"

def agregar_sinonimos():
    print("📂 Cargando archivo mapeo_completo.xlsx...")
    df = pd.read_excel(EXCEL_FILE)
    print(f"✅ Archivo cargado: {len(df)} ítems")
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Verificar cuántos sinónimos existen actualmente
    cur.execute("SELECT COUNT(*) FROM sinonimos")
    total_existentes = cur.fetchone()[0]
    print(f"📊 Sinónimos existentes en la base de datos: {total_existentes}")
    
    insertados = 0
    duplicados = 0
    
    for _, row in df.iterrows():
        desc = str(row['Descripción']).strip()
        sinonimos_str = str(row['Sinónimos']) if pd.notna(row['Sinónimos']) else ''
        
        if not sinonimos_str or not desc:
            continue
        
        sinonimos_lista = [s.strip() for s in sinonimos_str.split(',') if s.strip()]
        
        for sinonimo in sinonimos_lista:
            if len(sinonimo) > 1 and sinonimo != desc:
                # Verificar si ya existe la relación (desc → sinonimo)
                cur.execute("""
                    SELECT COUNT(*) FROM sinonimos 
                    WHERE termino = ? AND sinonimo = ?
                """, (desc, sinonimo))
                
                if cur.fetchone()[0] == 0:
                    # Insertar dirección directa (desc → sinonimo)
                    cur.execute("""
                        INSERT INTO sinonimos (termino, sinonimo, capa)
                        VALUES (?, ?, 1)
                    """, (desc, sinonimo))
                    insertados += 1
                    
                    # Insertar dirección inversa (sinonimo → desc)
                    cur.execute("""
                        INSERT OR IGNORE INTO sinonimos (termino, sinonimo, capa)
                        VALUES (?, ?, 1)
                    """, (sinonimo, desc))
                    insertados += 1
                else:
                    duplicados += 1
        
        if insertados % 1000 == 0 and insertados > 0:
            print(f"   Procesados: {insertados} sinónimos insertados...")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Sinónimos insertados: {insertados}")
    print(f"🔄 Sinónimos duplicados (omitidos): {duplicados}")
    print(f"📊 Total de sinónimos en la base de datos: {total_existentes + insertados}")

if __name__ == "__main__":
    agregar_sinonimos()