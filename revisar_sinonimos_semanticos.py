"""
Script para revisar sinónimos usando similitud semántica (embeddings)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
import torch

BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = BASE_DIR / "data" / "mapeo_completo.xlsx"
OUTPUT_FILE = BASE_DIR / "sinonimos_semanticos_revision.xlsx"

def revisar_sinonimos():
    print("🔍 REVISANDO SINÓNIMOS CON SIMILITUD SEMÁNTICA")
    print("=" * 70)
    
    # Cargar archivo
    print("📂 Cargando mapeo_completo.xlsx...")
    df = pd.read_excel(EXCEL_FILE)
    print(f"✅ Archivo cargado: {len(df)} ítems")
    
    # Cargar modelo
    print("🔄 Cargando modelo de embeddings...")
    modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    print("✅ Modelo cargado")
    
    resultados = []
    
    total = len(df)
    for idx, row in df.iterrows():
        desc = str(row['Descripción']).strip()
        sinonimos_str = str(row['Sinónimos']) if pd.notna(row['Sinónimos']) else ''
        
        if not sinonimos_str or not desc:
            continue
        
        sinonimos = [s.strip() for s in sinonimos_str.split(',') if s.strip()]
        
        if not sinonimos:
            continue
        
        # Embedding de la descripción
        emb_desc = modelo.encode(desc, convert_to_tensor=True, show_progress_bar=False)
        
        for sinonimo in sinonimos:
            if len(sinonimo) < 3:
                continue
            
            # Embedding del sinónimo
            emb_sin = modelo.encode(sinonimo, convert_to_tensor=True, show_progress_bar=False)
            
            # Calcular similitud coseno
            similitud = util.cos_sim(emb_desc, emb_sin).item()
            
            # Si la similitud es baja, marcar como sospechoso
            es_sospechoso = similitud < 0.5
            
            resultados.append({
                'Código': row['Código'],
                'Descripción': desc,
                'Sinónimo': sinonimo,
                'Similitud': round(similitud, 4),
                'Sospechoso': '⚠️ Sí' if es_sospechoso else '✅ No',
                'Acción sugerida': 'Revisar' if es_sospechoso else 'Mantener'
            })
        
        if (idx + 1) % 1000 == 0:
            print(f"   Procesados: {idx + 1}/{total}")
    
    # Crear DataFrame con resultados
    df_resultados = pd.DataFrame(resultados)
    
    # Guardar archivo
    df_resultados.to_excel(OUTPUT_FILE, index=False)
    print(f"\n✅ Resultados guardados en: {OUTPUT_FILE}")
    
    # Estadísticas
    total = len(df_resultados)
    sospechosos = len(df_resultados[df_resultados['Sospechoso'] == '⚠️ Sí'])
    
    print(f"\n📊 Resumen:")
    print(f"  Total de relaciones sinónimo-ítem evaluadas: {total}")
    print(f"  ⚠️ Sinónimos sospechosos (similitud < 0.5): {sospechosos} ({sospechosos/total*100:.1f}%)")
    print(f"  ✅ Sinónimos confiables: {total - sospechosos} ({(total-sospechosos)/total*100:.1f}%)")
    
    # Mostrar ejemplos de sospechosos
    if sospechosos > 0:
        print(f"\n📋 Ejemplos de sinónimos sospechosos (primeros 10):")
        ejemplos = df_resultados[df_resultados['Sospechoso'] == '⚠️ Sí'].head(10)
        for _, row in ejemplos.iterrows():
            print(f"  {row['Descripción'][:40]}... ↔ {row['Sinónimo']} (sim: {row['Similitud']})")

if __name__ == "__main__":
    revisar_sinonimos()