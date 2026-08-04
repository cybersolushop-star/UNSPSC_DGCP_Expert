"""
Script para integrar el archivo mapeo_completo.xlsx a la base de datos
Incluye: equivalencias por ítem y sinónimos
"""

import sqlite3
import pandas as pd
import re
import unicodedata
from pathlib import Path
from datetime import datetime

# =====================================================
# CONFIGURACIÓN
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "db" / "DGCP_UNSPSC.db"
ARCHIVO_MADRE = BASE_DIR / "data" / "mapeo_completo.xlsx"

# =====================================================
# FUNCIONES AUXILIARES
# =====================================================

def normalizar(texto):
    """Normaliza texto: minúsculas, sin tildes, sin espacios extra"""
    if pd.isna(texto):
        return ""
    texto = str(texto).lower().strip()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    texto = re.sub(r"\s+", " ", texto)
    return texto

def limpiar_sinonimos(sinonimos_str):
    """Convierte una cadena de sinónimos separados por comas en una lista"""
    if pd.isna(sinonimos_str) or not sinonimos_str:
        return []
    
    # Separar por comas o punto y coma
    sinonimos = re.split(r'[,;]\s*', str(sinonimos_str))
    # Limpiar y normalizar
    sinonimos_limpios = []
    for s in sinonimos:
        s = s.strip()
        if s and len(s) > 1:
            sinonimos_limpios.append(normalizar(s))
    
    # Eliminar duplicados
    return list(set(sinonimos_limpios))

# =====================================================
# FUNCIONES PRINCIPALES
# =====================================================

def cargar_archivo():
    """Carga el archivo mapeo_completo.xlsx"""
    if not ARCHIVO_MADRE.exists():
        print(f"❌ ERROR: No se encontró el archivo en: {ARCHIVO_MADRE}")
        return None
    
    print(f"📂 Cargando archivo: {ARCHIVO_MADRE.name}")
    df = pd.read_excel(ARCHIVO_MADRE, dtype={'Código': str, 'Auxiliar': str})
    print(f"   ✅ Archivo cargado: {len(df)} ítems")
    
    print(f"\n📋 Columnas disponibles:")
    for col in df.columns:
        print(f"   - {col}")
    
    return df

def verificar_columnas(df):
    """Verifica que las columnas necesarias existan"""
    columnas_requeridas = ['Código', 'Auxiliar', 'Sinónimos']
    faltantes = [col for col in columnas_requeridas if col not in df.columns]
    
    if faltantes:
        print(f"❌ Columnas faltantes: {faltantes}")
        print("   Asegúrate de que el archivo tenga las columnas: Código, Auxiliar, Sinónimos")
        return False
    
    # Verificar columna Sinónimos (puede estar vacía)
    if 'Sinónimos' not in df.columns:
        print("⚠️ No se encontró la columna 'Sinónimos'. Se creará vacía.")
        df['Sinónimos'] = ""
    
    return True

def actualizar_equivalencias_item(df, conn):
    """Actualiza la tabla equivalencias_por_item"""
    cur = conn.cursor()
    
    # Crear tabla si no existe
    cur.execute("""
        CREATE TABLE IF NOT EXISTS equivalencias_por_item (
            codigo_unspsc TEXT PRIMARY KEY,
            cuenta_digepres TEXT NOT NULL,
            descripcion_digepres TEXT NOT NULL,
            descripcion_item TEXT,
            definicion_item TEXT,
            fecha_actualizacion TEXT
        )
    """)
    conn.commit()
    
    actualizados = 0
    insertados = 0
    errores = 0
    
    print("\n🔄 Actualizando equivalencias por ítem...")
    
    for _, row in df.iterrows():
        codigo = str(row['Código']).strip()
        cuenta = str(row['Auxiliar']).strip() if pd.notna(row['Auxiliar']) else ""
        
        if not cuenta or len(cuenta) < 5:
            continue
        
        descripcion_cuenta = str(row['Denominación']).strip() if 'Denominación' in row and pd.notna(row['Denominación']) else ""
        descripcion_item = str(row['Descripción']).strip() if 'Descripción' in row and pd.notna(row['Descripción']) else ""
        definicion_item = str(row['Definición']).strip() if 'Definición' in row and pd.notna(row['Definición']) else ""
        
        try:
            cur.execute("SELECT COUNT(*) FROM equivalencias_por_item WHERE codigo_unspsc = ?", (codigo,))
            existe = cur.fetchone()[0] > 0
            
            if existe:
                cur.execute("""
                    UPDATE equivalencias_por_item 
                    SET cuenta_digepres = ?, 
                        descripcion_digepres = ?,
                        descripcion_item = ?,
                        definicion_item = ?,
                        fecha_actualizacion = ?
                    WHERE codigo_unspsc = ?
                """, (cuenta, descripcion_cuenta, descripcion_item, definicion_item, 
                      datetime.now().isoformat(), codigo))
                actualizados += 1
            else:
                cur.execute("""
                    INSERT INTO equivalencias_por_item 
                    (codigo_unspsc, cuenta_digepres, descripcion_digepres, descripcion_item, definicion_item, fecha_actualizacion)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (codigo, cuenta, descripcion_cuenta, descripcion_item, definicion_item, 
                      datetime.now().isoformat()))
                insertados += 1
                
        except Exception as e:
            print(f"⚠️ Error con código {codigo}: {e}")
            errores += 1
    
    conn.commit()
    print(f"   ✅ Actualizados: {actualizados}, Insertados: {insertados}, Errores: {errores}")
    return actualizados, insertados, errores

def actualizar_sinonimos(df, conn):
    """Actualiza la tabla sinonimos con los sinónimos del archivo"""
    cur = conn.cursor()
    
    # Crear tabla si no existe
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sinonimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            termino TEXT NOT NULL,
            sinonimo TEXT NOT NULL,
            capa INTEGER DEFAULT 1,
            codigo_unspsc TEXT,
            fecha_actualizacion TEXT
        )
    """)
    
    # Crear índice para búsqueda rápida
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sinonimos_termino ON sinonimos(termino)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sinonimos_sinonimo ON sinonimos(sinonimo)")
    conn.commit()
    
    # Limpiar sinónimos existentes
    cur.execute("DELETE FROM sinonimos")
    conn.commit()
    
    sinonimnos_insertados = 0
    
    print("\n🔄 Procesando sinónimos...")
    
    for _, row in df.iterrows():
        codigo = str(row['Código']).strip()
        sinonimos_str = row.get('Sinónimos', '')
        
        if pd.isna(sinonimos_str) or not sinonimos_str:
            continue
        
        # Obtener el término principal (descripción normalizada)
        termino_principal = normalizar(row['Descripción']) if 'Descripción' in row and pd.notna(row['Descripción']) else ""
        if not termino_principal:
            continue
        
        # Limpiar sinónimos
        sinonimos_lista = limpiar_sinonimos(sinonimos_str)
        
        # Insertar sinónimos
        for sinonimo in sinonimos_lista:
            if sinonimo and sinonimo != termino_principal:
                try:
                    cur.execute("""
                        INSERT INTO sinonimos (termino, sinonimo, capa, codigo_unspsc, fecha_actualizacion)
                        VALUES (?, ?, ?, ?, ?)
                    """, (termino_principal, sinonimo, 1, codigo, datetime.now().isoformat()))
                    sinonimnos_insertados += 1
                    
                    # También agregar la relación inversa
                    cur.execute("""
                        INSERT INTO sinonimos (termino, sinonimo, capa, codigo_unspsc, fecha_actualizacion)
                        VALUES (?, ?, ?, ?, ?)
                    """, (sinonimo, termino_principal, 1, codigo, datetime.now().isoformat()))
                    sinonimnos_insertados += 1
                    
                except Exception as e:
                    print(f"⚠️ Error insertando sinónimo '{sinonimo}': {e}")
    
    conn.commit()
    print(f"   ✅ Sinónimos insertados: {sinonimnos_insertados}")
    return sinonimnos_insertados

def mostrar_resumen(df, equiv_actualizados, equiv_insertados, equiv_errores, sinonimos_insertados):
    """Muestra un resumen de la operación"""
    print("\n" + "=" * 60)
    print("📊 REPORTE DE INTEGRACIÓN")
    print("=" * 60)
    print(f"   📁 Archivo procesado: {ARCHIVO_MADRE.name}")
    print(f"   📋 Total de ítems: {len(df)}")
    print(f"   📋 Ítems con cuenta DIGEPRES: {df['Auxiliar'].notna().sum()}")
    print(f"   📋 Ítems con sinónimos: {df['Sinónimos'].notna().sum()}")
    print("-" * 60)
    print(f"   ✅ Equivalencias actualizadas: {equiv_actualizados}")
    print(f"   🆕 Equivalencias insertadas: {equiv_insertados}")
    print(f"   ❌ Errores en equivalencias: {equiv_errores}")
    print(f"   🔗 Sinónimos insertados: {sinonimos_insertados}")
    print("=" * 60)
    
    # Mostrar ejemplo de sinónimos
    if sinonimos_insertados > 0:
        print("\n📋 Ejemplos de sinónimos procesados:")
        for _, row in df.head(5).iterrows():
            if pd.notna(row.get('Sinónimos', '')):
                codigo = str(row['Código']).strip()
                desc = str(row['Descripción'])[:40] if 'Descripción' in row else ""
                sinonimos = str(row['Sinónimos'])[:60]
                print(f"   - {codigo}: {desc}... → {sinonimos}...")

def main():
    print("🔍 INICIANDO INTEGRACIÓN DE MAPEO COMPLETO")
    print("=" * 60)
    
    # 1. Cargar archivo
    df = cargar_archivo()
    if df is None:
        return
    
    # 2. Verificar columnas
    if not verificar_columnas(df):
        return
    
    # 3. Mostrar vista previa
    print(f"\n📋 Vista previa (primeros 3 ítems):")
    columnas_mostrar = ['Código', 'Descripción', 'Auxiliar', 'Denominación', 'Sinónimos']
    columnas_existentes = [c for c in columnas_mostrar if c in df.columns]
    print(df[columnas_existentes].head(3).to_string())
    
    # 4. Confirmar
    print(f"\n⚠️ Se procesarán {len(df)} ítems en la base de datos.")
    confirm = input("¿Deseas continuar? (s/n): ")
    if confirm.lower() != 's':
        print("❌ Operación cancelada.")
        return
    
    # 5. Conectar a la base de datos
    print("\n🔌 Conectando a la base de datos...")
    conn = sqlite3.connect(DB_FILE)
    
    try:
        # 6. Actualizar equivalencias por ítem
        equiv_actualizados, equiv_insertados, equiv_errores = actualizar_equivalencias_item(df, conn)
        
        # 7. Actualizar sinónimos
        sinonimos_insertados = actualizar_sinonimos(df, conn)
        
        # 8. Mostrar resumen
        mostrar_resumen(df, equiv_actualizados, equiv_insertados, equiv_errores, sinonimos_insertados)
        
    except Exception as e:
        print(f"❌ Error durante la integración: {e}")
        conn.rollback()
    
    finally:
        conn.close()
    
    print("\n🎯 ¡Integración completada!")

if __name__ == "__main__":
    main()