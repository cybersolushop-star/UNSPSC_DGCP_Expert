"""
Script para mapear sinónimos desde PDF a Excel
Compara la columna B del Excel con la columna "Descripción Producto" del PDF
y copia los sinónimos a la columna D del Excel
"""

import pandas as pd
import pdfplumber
import re
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def leer_excel(ruta_excel):
    """Lee el archivo Excel y devuelve un DataFrame"""
    try:
        df = pd.read_excel(ruta_excel)
        logger.info(f"✅ Excel cargado: {len(df)} filas")
        logger.info(f"📋 Columnas: {df.columns.tolist()}")
        return df
    except Exception as e:
        logger.error(f"❌ Error al leer Excel: {e}")
        return None

def extraer_datos_pdf(ruta_pdf):
    """Extrae los datos del PDF: Descripción Producto y Sinónimos"""
    try:
        datos_pdf = []
        with pdfplumber.open(ruta_pdf) as pdf:
            for pagina in pdf.pages:
                tablas = pagina.extract_tables()
                for tabla in tablas:
                    if tabla:
                        # Buscar encabezados
                        for fila in tabla:
                            if fila and len(fila) >= 2:
                                # Buscar si la fila tiene "Descripción Producto" y "Sinónimos"
                                if "Descripción Producto" in str(fila) and "Sinónimos" in str(fila):
                                    # Encontrar los índices de las columnas
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

def mapear_sinonimos(df_excel, datos_pdf):
    """Mapea los sinónimos del PDF al Excel"""
    # Crear un diccionario con las descripciones del PDF normalizadas
    mapa_sinonimos = {}
    for item in datos_pdf:
        desc_norm = normalizar_texto(item['descripcion'])
        if desc_norm:
            # Si ya existe, combinar sinónimos
            if desc_norm in mapa_sinonimos:
                if item['sinonimos'] and item['sinonimos'] not in mapa_sinonimos[desc_norm]:
                    mapa_sinonimos[desc_norm] += f", {item['sinonimos']}"
            else:
                mapa_sinonimos[desc_norm] = item['sinonimos']
    
    logger.info(f"📋 Mapa de sinónimos creado: {len(mapa_sinonimos)} entradas únicas")
    
    # Actualizar el DataFrame
    columna_b = df_excel.columns[1]  # Segunda columna (índice 1)
    columna_d = df_excel.columns[3]  # Cuarta columna (índice 3)
    
    logger.info(f"📌 Usando columna B: '{columna_b}'")
    logger.info(f"📌 Usando columna D: '{columna_d}'")
    
    # Buscar coincidencias
    coincidencias = 0
    for idx, row in df_excel.iterrows():
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
                logger.debug(f"✅ Coincidencia: '{item}' → '{sin_val[:50]}...'")
        else:
            # Buscar coincidencia parcial si no hay exacta
            for desc_norm, sin_val in mapa_sinonimos.items():
                if item_norm in desc_norm or desc_norm in item_norm:
                    if sin_val and sin_val != 'nan':
                        df_excel.at[idx, columna_d] = sin_val
                        coincidencias += 1
                        logger.debug(f"🔍 Coincidencia parcial: '{item}' → '{sin_val[:50]}...'")
                        break
    
    logger.info(f"✅ Coincidencias encontradas: {coincidencias} de {len(df_excel)} ítems")
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
    # Definir rutas - TODOS EN LA CARPETA DATA
    base_dir = Path("data")
    ruta_excel = base_dir / "mapeo_completo.xlsx"
    ruta_pdf = base_dir / "CATALOGO DIGEPRES SIN CUENTAS.pdf"
    ruta_salida = base_dir / "mapeo_completo_actualizado.xlsx"
    
    # Verificar que los archivos existen
    if not ruta_excel.exists():
        logger.error(f"❌ No se encontró el archivo: {ruta_excel}")
        logger.info(f"📁 Buscando en: {ruta_excel.absolute()}")
        return
    
    if not ruta_pdf.exists():
        logger.error(f"❌ No se encontró el archivo: {ruta_pdf}")
        logger.info(f"📁 Buscando en: {ruta_pdf.absolute()}")
        return
    
    print("\n" + "="*60)
    print("📊 MAPEO DE SINÓNIMOS")
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
    datos_pdf = extraer_datos_pdf(ruta_pdf)
    if not datos_pdf:
        logger.warning("⚠️ No se encontraron datos en el PDF")
        return
    
    # Mapear sinónimos
    df_actualizado = mapear_sinonimos(df_excel, datos_pdf)
    
    # Guardar resultado
    guardar_excel(df_actualizado, ruta_salida)
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE PROCESAMIENTO")
    print("="*60)
    print(f"📊 Total de ítems en Excel: {len(df_excel)}")
    print(f"📊 Total de registros en PDF: {len(datos_pdf)}")
    sin_actualizados = sum(1 for v in df_actualizado.iloc[:, 3] if pd.notna(v) and str(v).strip() and str(v).strip() != 'nan')
    print(f"📊 Coincidencias encontradas: {sin_actualizados}")
    print(f"📁 Archivo guardado en: {ruta_salida}")
    print("="*60)

if __name__ == "__main__":
    main()