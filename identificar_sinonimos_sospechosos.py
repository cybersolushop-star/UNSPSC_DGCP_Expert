"""
Script para identificar sinónimos sospechosos en mapeo_completo.xlsx
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = BASE_DIR / "data" / "mapeo_completo.xlsx"

def identificar_sospechosos():
    print("🔍 ANALIZANDO SINÓNIMOS SOSPECHOSOS")
    print("=" * 60)
    
    df = pd.read_excel(EXCEL_FILE)
    print(f"✅ Archivo cargado: {len(df)} ítems")
    
    # Lista de palabras que indican categorías muy diferentes
    palabras_sospechosas = [
        'zapatos', 'calzado', 'zapato', 'tenis', 'botas', 'sandalias',  # Calzado
        'vestido', 'camisa', 'pantalón', 'blusa', 'falda',  # Ropa
        'computadora', 'laptop', 'tablet', 'teléfono',  # Electrónica
        'cama', 'mesa', 'silla', 'sofá', 'armario',  # Muebles
    ]
    
    sospechosos = []
    
    for _, row in df.iterrows():
        desc = str(row['Descripción']).strip()
        sinonimos_str = str(row['Sinónimos']) if pd.notna(row['Sinónimos']) else ''
        
        if not sinonimos_str or not desc:
            continue
        
        sinonimos = [s.strip() for s in sinonimos_str.split(',') if s.strip()]
        
        for sinonimo in sinonimos:
            sinonimo_lower = sinonimo.lower()
            desc_lower = desc.lower()
            
            # Verificar si el sinónimo contiene palabras sospechosas
            for palabra in palabras_sospechosas:
                if palabra in sinonimo_lower and palabra not in desc_lower:
                    sospechosos.append({
                        'Código': row['Código'],
                        'Descripción': desc,
                        'Sinónimo sospechoso': sinonimo,
                        'Palabra clave': palabra
                    })
                    break
    
    if sospechosos:
        df_sospechosos = pd.DataFrame(sospechosos)
        print(f"\n⚠️ Se encontraron {len(df_sospechosos)} sinónimos sospechosos:")
        print(df_sospechosos.to_string(index=False))
        
        # Guardar en Excel
        output_file = BASE_DIR / "sinonimos_sospechosos.xlsx"
        df_sospechosos.to_excel(output_file, index=False)
        print(f"\n✅ Lista guardada en: {output_file}")
    else:
        print("\n✅ No se encontraron sinónimos sospechosos")

if __name__ == "__main__":
    identificar_sospechosos()