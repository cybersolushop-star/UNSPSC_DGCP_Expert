"""
Script para mapear sinónimos desde Excel a Excel
Compara la columna B del archivo mapeo_completo.xlsx con la columna "Descripción" de catalogo_digepres_limpio.xlsx
y copia los sinónimos a la columna D del archivo mapeo_completo.xlsx
"""

import pandas as pd
import re
from pathlib import Path
import logging
import time
from tqdm import tqdm

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def leer_excel(ruta_excel):
    """Lee el archivo Excel y devuelve un DataFrame"""
    try:
        df = pd.read_excel(ruta_excel)
        logger.info(f"✅ Excel cargado: {len(df)} filas")
        return df
    except Exception as e:
        logger.error(f"❌ Error al leer Excel: {e}")
        return None

def normalizar_texto(texto):
    """Normaliza texto para comparación (sin acentos, mayúsculas, espacios)"""
    if not texto or pd.isna(texto):
        return ""
    texto = str(texto).lower().strip()
    # Eliminar acentos
    import unicodedata
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    # Eliminar caracteres especiales y espacios extra
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def mapear_sinonimos(df_mapeo, df_catalogo):
    """
    Mapea los sinónimos del catálogo al archivo de mapeo
    """
    # Crear un diccionario con las descripciones del catálogo normalizadas
    logger.info("📋 Creando mapa de sinónimos desde el catálogo...")
    mapa_sinonimos = {}
    
    for idx, row in tqdm(df_catalogo.iterrows(), total=len(df_catalogo), desc="Procesando catálogo", unit="registro"):
        desc = row['Descripción']
        sinonimos = row['Sinónimos']
        
        if pd.notna(desc) and str(desc).strip():
            desc_norm = normalizar_texto(desc)
            if desc_norm:
                if desc_norm in mapa_sinonimos:
                    # Si ya existe, combinar sinónimos
                    if pd.notna(sinonimos) and str(sinonimos).strip():
                        if str(sinonimos).strip() not in mapa_sinonimos[desc_norm]:
                            mapa_sinonimos[desc_norm] += f", {sinonimos}"
                else:
                    mapa_sinonimos[desc_norm] = str(sinonimos).strip() if pd.notna(sinonimos) else ''
    
    logger.info(f"📋 Mapa de sinónimos creado: {len(mapa_sinonimos)} entradas únicas")
    
    # Mostrar algunos ejemplos para verificar
    if len(mapa_sinonimos) > 0:
        ejemplos = list(mapa_sinonimos.items())[:5]
        logger.info("📋 Ejemplos de sinónimos cargados:")
        for desc, sin in ejemplos:
            sin_short = sin[:50] + "..." if len(sin) > 50 else sin
            logger.info(f"  • {desc} → {sin_short}")
    
    # Actualizar el archivo de mapeo
    columna_b = df_mapeo.columns[1]  # Segunda columna (Descripción)
    columna_d = df_mapeo.columns[3]  # Cuarta columna (Sinónimos)
    
    logger.info(f"📌 Usando columna B: '{columna_b}'")
    logger.info(f"📌 Usando columna D: '{columna_d}'")
    
    coincidencias_exactas = 0
    coincidencias_parciales = 0
    no_coincidencias = 0
    
    # Buscar coincidencias
    for idx in tqdm(range(len(df_mapeo)), desc="Buscando coincidencias", unit="ítem"):
        row = df_mapeo.iloc[idx]
        item = row[columna_b]
        
        if pd.isna(item) or not str(item).strip():
            continue
        
        item_norm = normalizar_texto(item)
        
        # Buscar coincidencia exacta
        if item_norm in mapa_sinonimos:
            sin_val = mapa_sinonimos[item_norm]
            if sin_val and sin_val != 'nan':
                df_mapeo.at[idx, columna_d] = sin_val
                coincidencias_exactas += 1
        else:
            # Buscar coincidencia parcial (si el item está contenido en la descripción)
            encontrado = False
            for desc_norm, sin_val in mapa_sinonimos.items():
                if item_norm and desc_norm and (item_norm in desc_norm or desc_norm in item_norm):
                    if sin_val and sin_val != 'nan':
                        df_mapeo.at[idx, columna_d] = sin_val
                        coincidencias_parciales += 1
                        encontrado = True
                        break
            if not encontrado:
                no_coincidencias += 1
    
    logger.info(f"✅ Coincidencias exactas: {coincidencias_exactas}")
    logger.info(f"🔍 Coincidencias parciales: {coincidencias_parciales}")
    logger.info(f"❌ Sin coincidencias: {no_coincidencias}")
    
    return df_mapeo

def guardar_excel(df, ruta_salida):
    """Guarda el DataFrame en un archivo Excel"""
    try:
        df.to_excel(ruta_salida, index=False)
        logger.info(f"✅ Excel guardado en: {ruta_salida}")
        return True
    except Exception as e:
        logger.error(f"❌ Error al guardar Excel: {e}")
        return False

def main():
    start_time = time.time()
    
    # Definir rutas
    base_dir = Path("data")
    ruta_mapeo = base_dir / "mapeo_completo.xlsx"
    ruta_catalogo = base_dir / "catalogo_digepres_limpio.xlsx"
    ruta_salida = base_dir / "mapeo_completo_actualizado.xlsx"
    
    print("\n" + "="*60)
    print("📊 MAPEO DE SINÓNIMOS DESDE EXCEL")
    print("="*60)
    print(f"📁 Archivo de mapeo: {ruta_mapeo}")
    print(f"📁 Archivo de catálogo: {ruta_catalogo}")
    print(f"📁 Archivo de salida: {ruta_salida}")
    print("="*60 + "\n")
    
    # Verificar que los archivos existen
    if not ruta_mapeo.exists():
        logger.error(f"❌ No se encontró el archivo: {ruta_mapeo}")
        return
    
    if not ruta_catalogo.exists():
        logger.error(f"❌ No se encontró el archivo: {ruta_catalogo}")
        return
    
    # Leer archivos
    df_mapeo = leer_excel(ruta_mapeo)
    if df_mapeo is None:
        return
    
    df_catalogo = leer_excel(ruta_catalogo)
    if df_catalogo is None:
        return
    
    logger.info(f"📊 Mapeo: {len(df_mapeo)} filas")
    logger.info(f"📊 Catálogo: {len(df_catalogo)} filas")
    
    # Mapear sinónimos
    df_actualizado = mapear_sinonimos(df_mapeo, df_catalogo)
    
    # Guardar resultado
    guardar_excel(df_actualizado, ruta_salida)
    
    # Mostrar resumen
    elapsed_time = time.time() - start_time
    print("\n" + "="*60)
    print("📊 RESUMEN DE PROCESAMIENTO")
    print("="*60)
    print(f"📊 Total de ítems en mapeo: {len(df_mapeo)}")
    print(f"📊 Total de registros en catálogo: {len(df_catalogo)}")
    
    sin_actualizados = sum(1 for v in df_actualizado.iloc[:, 3] if pd.notna(v) and str(v).strip() and str(v).strip() != 'nan')
    print(f"📊 Columnas con sinónimos actualizados: {sin_actualizados}")
    print(f"⏱️ Tiempo total: {elapsed_time/60:.1f} minutos")
    print(f"📁 Archivo guardado en: {ruta_salida}")
    print("="*60)

if __name__ == "__main__":
    main()