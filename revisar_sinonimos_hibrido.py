"""
Script para revisar sinónimos usando enfoque híbrido (fuzzy + palabras clave + embeddings)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer, util

BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = BASE_DIR / "data" / "mapeo_completo.xlsx"
OUTPUT_FILE = BASE_DIR / "sinonimos_revision_hibrida.xlsx"

def normalizar(texto):
    import unicodedata
    import re
    texto = str(texto).lower().strip()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    texto = re.sub(r"\s+", " ", texto)
    return texto

def extraer_palabras_clave(texto):
    """Extrae palabras significativas de un texto"""
    stopwords = {'de', 'la', 'el', 'los', 'las', 'un', 'una', 'unos', 'unas',
                 'para', 'por', 'con', 'sin', 'sobre', 'entre', 'hasta', 'desde',
                 'del', 'al', 'lo', 'le', 'les', 'se', 'me', 'te', 'nos', 'os',
                 'y', 'o', 'u', 'ni', 'que', 'como', 'cuando', 'donde', 'cual',
                 'quien', 'cuyo', 'cuya', 'cuyos', 'cuyas', 'etc'}
    texto_norm = normalizar(texto)
    palabras = texto_norm.split()
    return [p for p in palabras if len(p) > 2 and p not in stopwords]

def revisar_sinonimos():
    print("🔍 REVISANDO SINÓNIMOS (ENFOQUE HÍBRIDO)")
    print("=" * 70)
    
    df = pd.read_excel(EXCEL_FILE)
    print(f"✅ Archivo cargado: {len(df)} ítems")
    
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
        
        palabras_clave_desc = extraer_palabras_clave(desc)
        
        for sinonimo in sinonimos:
            if len(sinonimo) < 3:
                continue
            
            sinonimo_norm = normalizar(sinonimo)
            
            # 1. Coincidencia de palabras clave
            palabras_clave_sin = extraer_palabras_clave(sinonimo)
            palabras_comunes = set(palabras_clave_desc) & set(palabras_clave_sin)
            score_palabras = len(palabras_comunes) / max(len(palabras_clave_sin), 1) if palabras_clave_sin else 0
            
            # 2. Fuzzy matching
            score_fuzzy = fuzz.token_sort_ratio(desc, sinonimo) / 100
            score_fuzzy_partial = fuzz.partial_ratio(desc, sinonimo) / 100
            score_fuzzy = max(score_fuzzy, score_fuzzy_partial)
            
            # 3. Score combinado (palabras clave + fuzzy)
            score_combinado = max(score_palabras * 0.6 + score_fuzzy * 0.4, score_fuzzy)
            
            # Si el sinónimo está contenido en la descripción, es válido
            if sinonimo_norm in normalizar(desc):
                score_combinado = 0.9
                es_sospechoso = False
            else:
                es_sospechoso = score_combinado < 0.4
            
            # Si el sinónimo es una palabra común (ej: "animales"), puede ser válido
            if len(sinonimo.split()) == 1 and score_palabras > 0:
                es_sospechoso = False
            
            resultados.append({
                'Código': row['Código'],
                'Descripción': desc[:60] + '...' if len(desc) > 60 else desc,
                'Sinónimo': sinonimo[:40] + '...' if len(sinonimo) > 40 else sinonimo,
                'Score Palabras': round(score_palabras, 3),
                'Score Fuzzy': round(score_fuzzy, 3),
                'Score Combinado': round(score_combinado, 3),
                'Palabras Comunes': ', '.join(list(palabras_comunes)[:5]),
                'Sospechoso': '⚠️ Sí' if es_sospechoso else '✅ No',
                'Acción sugerida': 'Revisar' if es_sospechoso else 'Mantener'
            })
        
        if (idx + 1) % 2000 == 0:
            print(f"   Procesados: {idx + 1}/{total}")
    
    df_resultados = pd.DataFrame(resultados)
    df_resultados.to_excel(OUTPUT_FILE, index=False)
    
    print(f"\n✅ Resultados guardados en: {OUTPUT_FILE}")
    
    total = len(df_resultados)
    sospechosos = len(df_resultados[df_resultados['Sospechoso'] == '⚠️ Sí'])
    
    print(f"\n📊 Resumen:")
    print(f"  Total de relaciones evaluadas: {total}")
    print(f"  ⚠️ Sinónimos sospechosos: {sospechosos} ({sospechosos/total*100:.1f}%)")
    print(f"  ✅ Sinónimos confiables: {total - sospechosos} ({(total-sospechosos)/total*100:.1f}%)")

if __name__ == "__main__":
    revisar_sinonimos()