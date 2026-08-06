"""
Script para revisar casos específicos del archivo sinonimos_revision_hibrida.xlsx
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "sinonimos_revision_hibrida.xlsx"

def revisar_casos():
    print("🔍 REVISANDO CASOS ESPECÍFICOS")
    print("=" * 70)
    
    df = pd.read_excel(INPUT_FILE)
    
    # 1. Casos donde el sinónimo es una palabra muy común y válida
    sinonimos_validos = ['can', 'gato', 'felino', 'bayo', 'perro', 'caballo', 'animal', 'animales']
    
    print("\n📋 CASOS QUE SON SINÓNIMOS VÁLIDOS (falsos positivos):")
    for sinonimo in sinonimos_validos:
        casos = df[df['Sinónimo'].str.contains(sinonimo, case=False, na=False)]
        if not casos.empty:
            print(f"\n  '{sinonimo}': {len(casos)} casos")
            for _, row in casos.head(3).iterrows():
                print(f"    {row['Descripción'][:40]}... ↔ {row['Sinónimo']} (Score: {row['Score Combinado']})")
    
    # 2. Casos donde el sinónimo está contenido en la descripción
    print("\n\n📋 CASOS DONDE EL SINÓNIMO ESTÁ CONTENIDO EN LA DESCRIPCIÓN:")
    casos_contenidos = df[df.apply(lambda r: r['Sinónimo'].lower() in r['Descripción'].lower() if pd.notna(r['Sinónimo']) else False, axis=1)]
    print(f"  Total: {len(casos_contenidos)} casos")
    if not casos_contenidos.empty:
        for _, row in casos_contenidos.head(10).iterrows():
            print(f"    {row['Descripción'][:40]}... ↔ {row['Sinónimo']}")
    
    # 3. Casos con score muy bajo (los más sospechosos)
    print("\n\n📋 CASOS CON SCORE MUY BAJO (< 0.2):")
    casos_muy_bajos = df[df['Score Combinado'] < 0.2]
    print(f"  Total: {len(casos_muy_bajos)} casos")
    if not casos_muy_bajos.empty:
        for _, row in casos_muy_bajos.head(10).iterrows():
            print(f"    {row['Descripción'][:40]}... ↔ {row['Sinónimo']} (Score: {row['Score Combinado']})")

if __name__ == "__main__":
    revisar_casos()