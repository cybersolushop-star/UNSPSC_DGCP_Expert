"""
Script para actualizar la base de datos con los sinónimos del archivo mapeo_completo.xlsx
"""

import sqlite3
import pandas as pd
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def actualizar_sinonimos_desde_excel():
    """Actualiza la tabla de sinónimos en la base de datos desde el Excel"""
    
    # Definir rutas
    base_dir = Path(".")
    ruta_excel = base_dir / "data" / "mapeo_completo.xlsx"
    ruta_db = base_dir / "db" / "DGCP_UNSPSC.db"
    
    print("\n" + "="*60)
    print("📊 ACTUALIZACIÓN DE SINÓNIMOS EN BASE DE DATOS")
    print("="*60)
    print(f"📁 Archivo Excel: {ruta_excel}")
    print(f"📁 Base de datos: {ruta_db}")
    print("="*60 + "\n")
    
    # Verificar que los archivos existen
    if not ruta_excel.exists():
        logger.error(f"❌ No se encontró el archivo: {ruta_excel}")
        return
    
    if not ruta_db.exists():
        logger.error(f"❌ No se encontró la base de datos: {ruta_db}")
        return
    
    # Leer Excel
    logger.info("📖 Leyendo archivo Excel...")
    df = pd.read_excel(ruta_excel)
    logger.info(f"✅ Excel cargado: {len(df)} filas")
    logger.info(f"📋 Columnas: {df.columns.tolist()}")
    
    # Verificar que tiene las columnas necesarias
    if 'Descripción' not in df.columns or 'Sinónimos' not in df.columns:
        logger.error("❌ El Excel no tiene las columnas 'Descripción' y 'Sinónimos'")
        return
    
    # Filtrar filas que tienen sinónimos
    df_sinonimos = df[df['Sinónimos'].notna() & (df['Sinónimos'].str.strip() != '')]
    logger.info(f"📊 Filas con sinónimos: {len(df_sinonimos)}")
    
    if len(df_sinonimos) == 0:
        logger.warning("⚠️ No se encontraron sinónimos en el Excel")
        return
    
    # Conectar a la base de datos
    conn = sqlite3.connect(ruta_db)
    cur = conn.cursor()
    
    # Crear tabla de sinónimos si no existe
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sinonimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            termino TEXT NOT NULL,
            sinonimo TEXT NOT NULL,
            capa INTEGER DEFAULT 1
        )
    """)
    
    # Eliminar sinónimos existentes (opcional: mantener los existentes)
    # Si quieres mantener los existentes, comenta esta línea
    logger.info("🧹 Eliminando sinónimos existentes...")
    cur.execute("DELETE FROM sinonimos")
    conn.commit()
    
    # Insertar nuevos sinónimos
    logger.info("📝 Insertando nuevos sinónimos...")
    total_insertados = 0
    total_errores = 0
    
    for idx, row in df_sinonimos.iterrows():
        termino = str(row['Descripción']).strip()
        sinonimos = str(row['Sinónimos']).strip()
        
        if not termino or not sinonimos:
            continue
        
        # Dividir los sinónimos (separados por coma)
        lista_sinonimos = [s.strip() for s in sinonimos.split(',') if s.strip()]
        
        for sinonimo in lista_sinonimos:
            if sinonimo.lower() == termino.lower():
                continue
            
            try:
                # Insertar relación bidireccional
                cur.execute(
                    "INSERT INTO sinonimos (termino, sinonimo, capa) VALUES (?, ?, 1)",
                    (termino, sinonimo)
                )
                cur.execute(
                    "INSERT INTO sinonimos (termino, sinonimo, capa) VALUES (?, ?, 1)",
                    (sinonimo, termino)
                )
                total_insertados += 2
            except Exception as e:
                total_errores += 1
                logger.debug(f"Error insertando {termino} ↔ {sinonimo}: {e}")
    
    conn.commit()
    conn.close()
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE ACTUALIZACIÓN")
    print("="*60)
    print(f"📊 Total de sinónimos insertados: {total_insertados}")
    print(f"❌ Errores: {total_errores}")
    print(f"📁 Base de datos actualizada: {ruta_db}")
    print("="*60)

if __name__ == "__main__":
    actualizar_sinonimos_desde_excel()