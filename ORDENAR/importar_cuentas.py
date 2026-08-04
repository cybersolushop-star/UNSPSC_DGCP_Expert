# importar_cuentas.py - Versión Corregida
import sqlite3
import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime

DB_PATH = Path("db/DGCP_UNSPSC.db")
EXCEL_PATH = Path("BASE_DATOS_CUENTAS_DGCP.xlsx")

def obtener_columnas_catalogo(conn):
    """Obtiene los nombres reales de las columnas del catálogo"""
    cursor = conn.execute("SELECT * FROM catalogo LIMIT 1")
    columnas = [description[0] for description in cursor.description]
    return columnas

def importar_cuentas():
    """Importa las cuentas verificadas desde el Excel"""
    
    print("="*70)
    print("  📥 IMPORTANDO CUENTAS DIGEPRES VERIFICADAS")
    print("="*70)
    
    # 1. Verificar que el Excel existe
    if not EXCEL_PATH.exists():
        print(f"❌ Archivo no encontrado: {EXCEL_PATH}")
        print("Asegúrate de tener el archivo en la carpeta del proyecto")
        return
    
    # 2. Hacer respaldo de la base de datos actual
    backup_path = DB_PATH.parent / f"DGCP_UNSPSC_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Respaldo creado: {backup_path}")
    
    # 3. Leer el Excel
    print(f"\n📂 Leyendo archivo: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH)
    
    print(f"📊 Registros encontrados: {len(df)}")
    print(f"📋 Columnas del Excel: {df.columns.tolist()}")
    
    # 4. Mostrar ejemplo de datos
    print("\n📋 Ejemplo de datos del Excel:")
    print(df.head(3))
    
    # 5. Conectar a la base de datos para ver las columnas
    conn = sqlite3.connect(DB_PATH)
    
    # Obtener columnas del catálogo
    columnas_catalogo = obtener_columnas_catalogo(conn)
    print(f"\n📋 Columnas del catálogo: {columnas_catalogo}")
    
    # Buscar la columna de código de familia en el catálogo
    columna_familia = None
    for col in columnas_catalogo:
        if 'familia' in col.lower() or 'Familia' in col:
            columna_familia = col
            break
    
    if columna_familia is None:
        print("❌ No se encontró la columna 'Familia' en el catálogo")
        print("Columnas disponibles:", columnas_catalogo)
        conn.close()
        return
    
    print(f"✅ Usando columna: '{columna_familia}' para el código de familia")
    
    # 6. Limpiar datos del Excel
    df_clean = pd.DataFrame()
    
    # Limpiar código UNSPSC (eliminar puntos, espacios, etc.)
    df_clean['codigo_original'] = df['Código UNSPSC'].astype(str).str.replace(r'[^0-9]', '', regex=True)
    
    # Extraer código de familia (primeros 8 dígitos)
    df_clean['codigo_familia'] = df_clean['codigo_original'].str[:8]
    
    # Cuenta DIGEPRES
    df_clean['cuenta_digepres'] = df['Cuenta Sugerida (DGCP)'].astype(str).str.strip()
    
    # Descripción de la cuenta
    df_clean['descripcion_digepres'] = df['Denominación Oficial de la Cuenta (DIGEPRES)'].astype(str).str.strip()
    
    # También guardar la descripción del ítem como referencia
    df_clean['descripcion_item'] = df['Descripción del Ítem'].astype(str).str.strip()
    
    # 7. Verificar códigos válidos (que tengan al menos 8 dígitos)
    df_clean['valido'] = df_clean['codigo_familia'].str.len() >= 8
    df_clean = df_clean[df_clean['valido']]
    
    print(f"\n📊 Registros con códigos válidos: {len(df_clean)}")
    
    # 8. Eliminar duplicados (mantener el primero)
    df_clean = df_clean.drop_duplicates(subset=['codigo_familia'], keep='first')
    
    print(f"📊 Registros únicos después de eliminar duplicados: {len(df_clean)}")
    
    # 9. Verificar qué códigos existen en el catálogo
    print("\n🔍 Verificando códigos en el catálogo...")
    
    # Obtener los códigos de familia del catálogo
    query = f"SELECT DISTINCT '{columna_familia}' FROM catalogo"
    df_catalogo = pd.read_sql(query, conn)
    
    # La columna puede tener nombre con tilde, usamos el índice 0
    col_familia_catalogo = df_catalogo.columns[0]
    print(f"✅ Columna de familia en catálogo: '{col_familia_catalogo}'")
    
    # Crear lista de códigos de familia existentes
    familias_existentes = set(df_catalogo[col_familia_catalogo].astype(str).str[:8])
    
    print(f"📊 Códigos de familia en el catálogo: {len(familias_existentes)}")
    
    # Filtrar solo los que existen en el catálogo
    df_clean['existe_en_catalogo'] = df_clean['codigo_familia'].isin(familias_existentes)
    df_validos = df_clean[df_clean['existe_en_catalogo']]
    
    print(f"✅ Códigos que existen en el catálogo: {len(df_validos)}")
    print(f"⚠️ Códigos que NO existen en el catálogo: {len(df_clean) - len(df_validos)}")
    
    if len(df_clean) - len(df_validos) > 0:
        print("\n⚠️ Algunos códigos no existen en el catálogo (ejemplos):")
        print(df_clean[~df_clean['existe_en_catalogo']][['codigo_familia', 'descripcion_item']].head(5))
        
        # Preguntar si quiere continuar
        continuar = input("\n¿Quieres continuar solo con los códigos que existen en el catálogo? (s/n): ")
        if continuar.lower() != 's':
            print("❌ Importación cancelada")
            conn.close()
            return
    
    # 10. Preparar datos finales para importar
    df_importar = df_validos[['codigo_familia', 'cuenta_digepres', 'descripcion_digepres']]
    
    # 11. Mostrar ejemplo de los datos a importar
    print("\n📋 Ejemplo de datos a importar:")
    print(df_importar.head(10))
    
    # 12. Confirmar
    confirmar = input("\n¿Deseas importar estos datos a la base de datos? (s/n): ")
    if confirmar.lower() != 's':
        print("❌ Importación cancelada")
        conn.close()
        return
    
    # 13. Importar a la base de datos
    print("\n🔄 Actualizando base de datos...")
    
    # Reemplazar la tabla equivalencias_digepres
    df_importar.to_sql("equivalencias_digepres", conn, if_exists="replace", index=False)
    
    # 14. Verificar la importación
    df_verificar = pd.read_sql("SELECT * FROM equivalencias_digepres LIMIT 5", conn)
    print("\n✅ Verificación de datos importados:")
    print(df_verificar)
    
    # 15. Estadísticas finales
    total = pd.read_sql("SELECT COUNT(*) FROM equivalencias_digepres", conn).iloc[0,0]
    print(f"\n📊 Total de registros en la tabla equivalencias_digepres: {total}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("✅ ¡Importación completada exitosamente!")
    print("="*70)

def verificar_importacion():
    """Verifica que los datos se hayan importado correctamente"""
    print("\n" + "="*70)
    print("  🔍 VERIFICANDO DATOS IMPORTADOS")
    print("="*70)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Verificar tabla
    df = pd.read_sql("SELECT * FROM equivalencias_digepres", conn)
    
    print(f"\n📊 Total de registros: {len(df)}")
    print(f"\n📋 Columnas: {df.columns.tolist()}")
    
    print("\n📋 Primeros 10 registros:")
    print(df.head(10))
    
    # Estadísticas
    print("\n📊 Estadísticas:")
    print(f"  - Códigos de familia únicos: {df['codigo_familia'].nunique()}")
    print(f"  - Cuentas únicas: {df['cuenta_digepres'].nunique()}")
    
    # Ver cuentas más comunes
    print("\n📋 Cuentas más frecuentes:")
    print(df['cuenta_digepres'].value_counts().head(10))
    
    # Verificar que no hay códigos vacíos
    vacios = df[df['codigo_familia'] == '']
    if len(vacios) > 0:
        print(f"\n⚠️ Registros con código vacío: {len(vacios)}")
    else:
        print("\n✅ No hay registros con código vacío")
    
    conn.close()

if __name__ == "__main__":
    importar_cuentas()
    verificar_importacion()