"""
Script optimizado para mapear sinónimos desde PDF a Excel
Versión con barra de progreso y procesamiento por lotes
"""

import pandas as pd
import pdfplumber
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

def extraer_datos_pdf_optimizado(ruta_pdf):
    """Extrae los datos del PDF optimizado con barra de progreso"""
    try:
        datos_pdf = []
        with pdfplumber.open(ruta_pdf) as pdf:
            total_paginas = len(pdf.pages)
            logger.info(f"📄 Procesando {total_paginas} páginas del PDF...")
            
            # Usar tqdm para barra de progreso
            for pagina in tqdm(pdf.pages, desc="Extrayendo PDF", unit="página"):
                tablas = pagina.extract_tables()
                for tabla in tablas:
                    if tabla:
                        for fila in tabla:
                            if fila and len(fila) >= 4:
                                # Buscar encabezados
                                if "Descripción Producto" in str(fila) and "Sinónimos" in str(fila):
                                    idx_desc = None
                                    idx_sin = None
                                    for i, col in enumerate(fila):
                                        if col and "Descripción Producto" in str(col):
                                            idx_desc = i
                                        if col and "Sinónimos" in str(col):
                                            idx_sin = i
                                    if idx_desc is not None and idx_sin is not None:
                                        # Extraer datos de las filas siguientes
                                        for fila_datos in tabla[tabla.index(fila)+1:]:
                                            if fila_datos and len(fila_datos) > max(idx_desc, idx_sin):
                                                desc = fila_datos[idx_desc] if idx_desc < len(fila_datos) else None
                                                sin = fila_datos[idx_sin] if idx_sin < len(fila_datos) else None
                                                if desc and str(desc).strip():
                                                    datos_pdf.append({
                                                        'descripcion': str(desc).strip(),
                                                        'sinonimos': str(sin).strip() if sin else ''
                                                    })
        logger.info(f"✅ PDF procesado: {len(datos_pdf)} registros encontrados")
        return datos_pdf
    except Exception as e:
        logger.error(f"❌ Error al leer PDF: {e}")
        return []

def normalizar_texto(texto):
    """Normaliza texto para comparación"""
    if not texto or pd.isna(texto):
        return ""
    texto = str(texto).lower().strip()
    import unicodedata
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def mapear_sinonimos_optimizado(df_excel, datos_pdf):
    """Mapea los sinónimos del PDF al Excel (optimizado)"""
    # Crear mapa de sinónimos
    mapa_sinonimos = {}
    for item in tqdm(datos_pdf, desc="Creando mapa de sinónimos", unit="registro"):
        desc_norm = normalizar_texto(item['descripcion'])
        if desc_norm:
            if desc_norm in mapa_sinonimos:
                if item['sinonimos'] and item['sinonimos'] not in mapa_sinonimos[desc_norm]:
                    mapa_sinonimos[desc_norm] += f", {item['sinonimos']}"
            else:
                mapa_sinonimos[desc_norm] = item['sinonimos']
    
    logger.info(f"📋 Mapa de sinónimos creado: {len(mapa_sinonimos)} entradas únicas")
    
    # Actualizar DataFrame
    columna_b = df_excel.columns[1]
    columna_d = df_excel.columns[3]
    
    coincidencias = 0
    no_coincidencias = 0
    
    # Usar tqdm para la barra de progreso
    for idx in tqdm(range(len(df_excel)), desc="Buscando coincidencias", unit="ítem"):
        row = df_excel.iloc[idx]
        item = row[columna_b]
        if pd.isna(item) or not str(item).strip():
            continue
        
        item_norm = normalizar_texto(item)
        
        # Buscar coincidencia exacta
        if item_norm in mapa_sinonimos:
            sin_val = mapa_sinonimos[item_norm]
            if sin_val and sin_val != 'nan':
                df_excel.at[idx, columna_d] = sin_val
                coincidencias += 1
        else:
            # Coincidencia parcial (limitada para rendimiento)
            for desc_norm, sin_val in list(mapa_sinonimos.items())[:50]:  # Limitar búsqueda
                if item_norm in desc_norm or desc_norm in item_norm:
                    if sin_val and sin_val != 'nan':
                        df_excel.at[idx, columna_d] = sin_val
                        coincidencias += 1
                        break
            else:
                no_coincidencias += 1
    
    logger.info(f"✅ Coincidencias: {coincidencias}, Sin coincidencias: {no_coincidencias}")
    return df_excel

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
    ruta_excel = base_dir / "mapeo_completo.xlsx"
    ruta_pdf = base_dir / "CATALOGO DIGEPRES SIN CUENTAS.pdf"
    ruta_salida = base_dir / "mapeo_completo_actualizado.xlsx"
    
    print("\n" + "="*60)
    print("📊 MAPEO DE SINÓNIMOS - VERSIÓN OPTIMIZADA")
    print("="*60)
    print(f"📁 Archivo Excel: {ruta_excel}")
    print(f"📁 Archivo PDF: {ruta_pdf}")
    print(f"📁 Archivo de salida: {ruta_salida}")
    print("="*60 + "\n")
    
    # Leer Excel
    df_excel = leer_excel(ruta_excel)
    if df_excel is None:
        return
    
    # Extraer datos del PDF
    datos_pdf = extraer_datos_pdf_optimizado(ruta_pdf)
    if not datos_pdf:
        logger.warning("⚠️ No se encontraron datos en el PDF")
        return
    
    # Mapear sinónimos
    df_actualizado = mapear_sinonimos_optimizado(df_excel, datos_pdf)
    
    # Guardar resultado
    guardar_excel(df_actualizado, ruta_salida)
    
    # Mostrar resumen
    elapsed_time = time.time() - start_time
    print("\n" + "="*60)
    print("📊 RESUMEN DE PROCESAMIENTO")
    print("="*60)
    print(f"📊 Total de ítems en Excel: {len(df_excel)}")
    print(f"📊 Total de registros en PDF: {len(datos_pdf)}")
    sin_actualizados = sum(1 for v in df_actualizado.iloc[:, 3] if pd.notna(v) and str(v).strip() and str(v).strip() != 'nan')
    print(f"📊 Coincidencias encontradas: {sin_actualizados}")
    print(f"⏱️ Tiempo total: {elapsed_time/60:.1f} minutos")
    print(f"📁 Archivo guardado en: {ruta_salida}")
    print("="*60)

if __name__ == "__main__":
    main()