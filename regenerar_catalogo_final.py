"""
Script para regenerar catalogo_final.csv desde mapeo_completo.xlsx
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = BASE_DIR / "data" / "mapeo_completo.xlsx"
OUTPUT_FILE = BASE_DIR / "data" / "catalogo_final.csv"

def regenerar_catalogo():
    print("📂 Cargando archivo mapeo_completo.xlsx...")
    df = pd.read_excel(EXCEL_FILE)
    
    print(f"✅ Archivo cargado: {len(df)} ítems")
    
    # Verificar columnas necesarias
    columnas_requeridas = ['Código', 'Descripción', 'Definición', 'Auxiliar', 'Denominación']
    for col in columnas_requeridas:
        if col not in df.columns:
            print(f"⚠️ Columna '{col}' no encontrada. Verifica el archivo.")
            return
    
    # Crear nuevo DataFrame con la estructura de catalogo_final.csv
    df_nuevo = pd.DataFrame()
    
    # Mapear columnas
    df_nuevo['Código'] = df['Código'].astype(str).str.strip()
    df_nuevo['Descripción'] = df['Descripción'].astype(str).str.strip()
    df_nuevo['Definición'] = df['Definición'].astype(str).str.strip()
    df_nuevo['cuenta_digepres'] = df['Auxiliar'].astype(str).str.strip()
    df_nuevo['descripcion_digepres'] = df['Denominación'].astype(str).str.strip()
    
    # Limpiar filas sin cuenta DIGEPRES (opcional - las dejamos con NaN)
    # df_nuevo = df_nuevo[df_nuevo['cuenta_digepres'].notna()]
    
    # Eliminar duplicados por código (mantener el primero)
    df_nuevo = df_nuevo.drop_duplicates(subset=['Código'], keep='first')
    
    # Guardar archivo
    df_nuevo.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n✅ Archivo regenerado: {OUTPUT_FILE}")
    print(f"   Total de ítems: {len(df_nuevo)}")
    print(f"   Con cuenta DIGEPRES: {df_nuevo['cuenta_digepres'].notna().sum()}")
    print(f"   Sin cuenta DIGEPRES: {df_nuevo['cuenta_digepres'].isna().sum()}")
    
    # Mostrar cuentas únicas
    cuentas_unicas = df_nuevo['cuenta_digepres'].nunique()
    print(f"   Cuentas DIGEPRES únicas: {cuentas_unicas}")
    
    # Mostrar algunos ejemplos
    print("\n📋 Ejemplos de los primeros 5 ítems:")
    print(df_nuevo[['Código', 'Descripción', 'cuenta_digepres', 'descripcion_digepres']].head(5).to_string(index=False))

if __name__ == "__main__":
    regenerar_catalogo()