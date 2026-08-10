"""
Script para convertir CATALOGO DIGEPRES SIN CUENTAS.pdf a Excel
Extrae todas las tablas del PDF y las convierte en un archivo Excel limpio
"""

import pdfplumber
import pandas as pd
from pathlib import Path
import logging
import re
from tqdm import tqdm

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extraer_tablas_pdf_a_dataframe(ruta_pdf):
    """
    Extrae todas las tablas del PDF y las convierte en un DataFrame unificado
    """
    try:
        todas_las_filas = []
        encabezados = None
        
        with pdfplumber.open(ruta_pdf) as pdf:
            total_paginas = len(pdf.pages)
            logger.info(f"📄 Procesando {total_paginas} páginas del PDF...")
            
            for i, pagina in enumerate(tqdm(pdf.pages, desc="Extrayendo PDF", unit="página")):
                tablas = pagina.extract_tables()
                
                for tabla in tablas:
                    if not tabla:
                        continue
                    
                    # Buscar encabezados en la tabla
                    for fila in tabla:
                        if fila and len(fila) >= 4:
                            # Verificar si es fila de encabezados
                            fila_str = [str(cell).lower() if cell else '' for cell in fila]
                            if any('código' in cell or 'producto' in cell for cell in fila_str[:3]):
                                if any('descripción' in cell for cell in fila_str) or any('descripcion' in cell for cell in fila_str):
                                    encabezados = fila
                                    logger.info(f"📌 Encabezados encontrados en página {i+1}: {encabezados}")
                                    break
                    
                    # Si no hay encabezados, usar los que ya tenemos
                    if encabezados is None:
                        encabezados = ['Código', 'Descripción', 'Definición', 'Sinónimos', 'Clase', 'Familia', 'Segmento']
                    
                    # Extraer datos
                    for fila in tabla:
                        if fila and len(fila) >= 4:
                            # Verificar que sea una fila de datos válida
                            primer_valor = str(fila[0]).strip() if fila[0] else ''
                            if primer_valor and primer_valor != 'Código' and primer_valor != 'Código\nProducto':
                                # Verificar que sea un código numérico (8 dígitos) o similar
                                if re.match(r'^\d{8}$', primer_valor) or re.match(r'^\d{6,8}$', primer_valor):
                                    # Asegurar que la fila tenga suficientes columnas
                                    while len(fila) < 7:
                                        fila.append('')
                                    
                                    todas_las_filas.append({
                                        'Código': str(fila[0]).strip() if fila[0] else '',
                                        'Descripción': str(fila[1]).strip() if fila[1] else '',
                                        'Definición': str(fila[2]).strip() if fila[2] else '',
                                        'Sinónimos': str(fila[3]).strip() if fila[3] else '',
                                        'Clase': str(fila[4]).strip() if len(fila) > 4 and fila[4] else '',
                                        'Familia': str(fila[5]).strip() if len(fila) > 5 and fila[5] else '',
                                        'Segmento': str(fila[6]).strip() if len(fila) > 6 and fila[6] else ''
                                    })
        
        logger.info(f"✅ Total de registros extraídos: {len(todas_las_filas)}")
        return pd.DataFrame(todas_las_filas)
    
    except Exception as e:
        logger.error(f"❌ Error al procesar PDF: {e}")
        return pd.DataFrame()

def limpiar_dataframe(df):
    """
    Limpia el DataFrame eliminando filas vacías, duplicados y normalizando datos
    """
    logger.info("🧹 Limpiando datos...")
    
    # Eliminar filas vacías
    df = df.dropna(subset=['Código', 'Descripción'], how='all')
    df = df[df['Código'].str.strip() != '']
    df = df[df['Descripción'].str.strip() != '']
    
    # Eliminar duplicados basados en Código
    df = df.drop_duplicates(subset=['Código'], keep='first')
    
    # Eliminar filas que contienen encabezados en los datos
    df = df[~df['Código'].str.contains('Código', case=False, na=False)]
    df = df[~df['Descripción'].str.contains('Descripción', case=False, na=False)]
    
    # Limpiar espacios en blanco
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip()
    
    # Normalizar sinónimos (eliminar saltos de línea, espacios extra)
    df['Sinónimos'] = df['Sinónimos'].str.replace('\n', ',', regex=False)
    df['Sinónimos'] = df['Sinónimos'].str.replace(r'\s+', ' ', regex=True)
    df['Sinónimos'] = df['Sinónimos'].str.strip()
    
    logger.info(f"✅ Datos limpios: {len(df)} registros")
    return df

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
    # Definir rutas
    base_dir = Path("data")
    ruta_pdf = base_dir / "CATALOGO DIGEPRES SIN CUENTAS.pdf"
    ruta_excel_temp = base_dir / "catalogo_digepres_temp.xlsx"
    ruta_excel_limpio = base_dir / "catalogo_digepres_limpio.xlsx"
    
    print("\n" + "="*60)
    print("📊 CONVERSIÓN PDF A EXCEL")
    print("="*60)
    print(f"📁 Archivo PDF: {ruta_pdf}")
    print(f"📁 Archivo Excel temporal: {ruta_excel_temp}")
    print(f"📁 Archivo Excel limpio: {ruta_excel_limpio}")
    print("="*60 + "\n")
    
    # Verificar que el PDF existe
    if not ruta_pdf.exists():
        logger.error(f"❌ No se encontró el archivo: {ruta_pdf}")
        return
    
    # Extraer datos del PDF
    df = extraer_tablas_pdf_a_dataframe(ruta_pdf)
    
    if df.empty:
        logger.error("❌ No se extrajeron datos del PDF")
        return
    
    # Guardar versión sin limpiar
    guardar_excel(df, ruta_excel_temp)
    logger.info(f"📊 Versión sin limpiar: {len(df)} registros")
    
    # Limpiar datos
    df_limpio = limpiar_dataframe(df)
    
    # Guardar versión limpia
    guardar_excel(df_limpio, ruta_excel_limpio)
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE CONVERSIÓN")
    print("="*60)
    print(f"📊 Registros extraídos (sin limpiar): {len(df)}")
    print(f"📊 Registros después de limpieza: {len(df_limpio)}")
    print(f"📁 Archivos generados:")
    print(f"  • {ruta_excel_temp}")
    print(f"  • {ruta_excel_limpio}")
    print("="*60)
    
    # Mostrar primeros registros para verificar
    print("\n📋 Primeros 5 registros del archivo limpio:")
    print(df_limpio[['Código', 'Descripción', 'Sinónimos']].head())

if __name__ == "__main__":
    main()