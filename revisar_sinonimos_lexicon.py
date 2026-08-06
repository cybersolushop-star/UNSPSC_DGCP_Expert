"""
Script para revisar sinónimos usando un lexicon de sinónimos predefinidos
"""

import pandas as pd
from pathlib import Path
from rapidfuzz import fuzz
import re

BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = BASE_DIR / "data" / "mapeo_completo.xlsx"
OUTPUT_FILE = BASE_DIR / "sinonimos_revision_lexicon.xlsx"

# =====================================================
# LEXICON DE SINÓNIMOS CONFIABLES (COMPLETO)
# =====================================================

SINONIMOS_CONFIABLES = {
    # Animales
    'rata': ['roedor', 'ratón', 'ratones'],
    'perro': ['can', 'cachorro', 'canino'],
    'gato': ['felino', 'michino', 'minino'],
    'caballo': ['equino', 'corcel', 'rocín', 'yegua', 'potro'],
    'vaca': ['bovino', 'ternero', 'novillo'],
    'cerdo': ['porcino', 'chancho', 'cochino'],
    'oveja': ['ovino', 'borrego', 'carnero'],
    'pollo': ['ave', 'gallina', 'gallito'],
    'pez': ['pescado', 'peces'],
    'ratones': ['rata', 'ratón', 'roedor'],
    'perros': ['perro', 'can', 'cachorro'],
    'gatos': ['gato', 'felino', 'michino', 'minino'],
    
    # Vehículos
    'carro': ['automóvil', 'auto', 'vehículo', 'automovil'],
    'camión': ['camioneta', 'furgón', 'volqueta'],
    'camioneta': ['camión', 'pickup', 'furgoneta'],
    'moto': ['motocicleta', 'motor', 'ciclomotor'],
    'bicicleta': ['bici', 'ciclo', 'biciclo'],
    'automóvil': ['carro', 'auto', 'vehículo'],
    
    # Tecnología
    'computadora': ['ordenador', 'pc', 'laptop', 'portátil', 'notebook'],
    'teléfono': ['celular', 'móvil', 'smartphone', 'telefone'],
    'tablet': ['tableta', 'ipad', 'table'],
    
    # Herramientas
    'pinza': ['alicate', 'tenaza', 'pinzas', 'alicates'],
    'martillo': ['mazo', 'percusión'],
    'destornillador': ['atornillador', 'desarmador'],
    
    # Muebles
    'silla': ['asiento', 'butaca', 'sillón'],
    'mesa': ['tabla', 'escritorio', 'buró'],
    'cama': ['lecho', 'colchón', 'somier'],
    
    # Ropa
    'camisa': ['blusa', 'camiseta', 'playera'],
    'pantalón': ['pantalones', 'tejanos', 'vaqueros'],
    'zapato': ['calzado', 'zapatos', 'tenis'],
    'vestido': ['traje', 'falda', 'terno'],
    
    # Comida
    'pan': ['barra', 'hogaza', 'bollo'],
    'queso': ['cuajada', 'gouda', 'cheddar'],
    'leche': ['lácteo', 'descremada', 'entera'],
    
    # Materiales
    'madera': ['leña', 'tablón', 'tronco'],
    'metal': ['acero', 'hierro', 'aluminio'],
    'plástico': ['polímero', 'vinilo', 'pvc'],
    
    # Otros comunes
    'cuchillo': ['navaja', 'cuchilla', 'puñal'],
    'vaso': ['copa', 'jarra', 'taza'],
    'plato': ['bandeja', 'fuente', 'charola'],
    'libro': ['texto', 'manual', 'obra', 'publicación'],
    'juego': ['entretenimiento', 'pasatiempo', 'diversión'],
    'televisor': ['tv', 'tele', 'pantalla', 'monitor'],
    'radio': ['receptor', 'transistor', 'sintonizador'],
}

def normalizar(texto):
    import unicodedata
    import re
    texto = str(texto).lower().strip()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    texto = re.sub(r"\s+", " ", texto)
    return texto

def extraer_palabra_base(texto):
    """Extrae la palabra base de una descripción (elimina plurales y variaciones)"""
    texto_norm = normalizar(texto)
    palabras = texto_norm.split()
    if not palabras:
        return texto_norm
    return palabras[0]

def revisar_con_lexicon():
    print("🔍 REVISANDO SINÓNIMOS CON LEXICON (COMPLETO)")
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
        
        desc_base = extraer_palabra_base(desc)
        
        for sinonimo in sinonimos:
            if len(sinonimo) < 3:
                continue
            
            sinonimo_norm = normalizar(sinonimo)
            sinonimo_base = extraer_palabra_base(sinonimo)
            
            # Verificar en lexicon
            es_confiable_lexicon = False
            for key, valores in SINONIMOS_CONFIABLES.items():
                if desc_base in [key] + valores or key in desc_base:
                    if sinonimo_base in valores or sinonimo_base == key:
                        es_confiable_lexicon = True
                        break
                if sinonimo_base == key and desc_base in valores:
                    es_confiable_lexicon = True
                    break
            
            # Fuzzy
            score_fuzzy = fuzz.token_sort_ratio(desc, sinonimo) / 100
            score_fuzzy_partial = fuzz.partial_ratio(desc, sinonimo) / 100
            score_fuzzy = max(score_fuzzy, score_fuzzy_partial)
            
            # Decisión final
            if es_confiable_lexicon:
                score_final = 0.9
                es_sospechoso = False
                metodo = "✅ Lexicon"
            elif sinonimo_norm in normalizar(desc):
                score_final = 0.9
                es_sospechoso = False
                metodo = "✅ Contenido"
            elif score_fuzzy > 0.6:
                score_final = score_fuzzy
                es_sospechoso = False
                metodo = "✅ Fuzzy"
            else:
                score_final = score_fuzzy
                es_sospechoso = True
                metodo = "⚠️ Sospechoso"
            
            resultados.append({
                'Código': row['Código'],
                'Descripción': desc[:50] + '...' if len(desc) > 50 else desc,
                'Descripción Base': desc_base,
                'Sinónimo': sinonimo[:30] + '...' if len(sinonimo) > 30 else sinonimo,
                'Sinónimo Base': sinonimo_base,
                'Score': round(score_final, 3),
                'Método': metodo,
                'Sospechoso': '⚠️ Sí' if es_sospechoso else '✅ No',
                'Acción': 'Revisar' if es_sospechoso else 'Mantener'
            })
        
        if (idx + 1) % 2000 == 0:
            print(f"   Procesados: {idx + 1}/{total}")
    
    df_resultados = pd.DataFrame(resultados)
    df_resultados.to_excel(OUTPUT_FILE, index=False)
    
    print(f"\n✅ Resultados guardados en: {OUTPUT_FILE}")
    
    total = len(df_resultados)
    sospechosos = len(df_resultados[df_resultados['Sospechoso'] == '⚠️ Sí'])
    lexicon = len(df_resultados[df_resultados['Método'] == '✅ Lexicon'])
    
    print(f"\n📊 Resumen:")
    print(f"  Total de relaciones evaluadas: {total}")
    print(f"  ✅ Reconocidas por lexicon: {lexicon} ({lexicon/total*100:.1f}%)")
    print(f"  ⚠️ Sinónimos sospechosos: {sospechosos} ({sospechosos/total*100:.1f}%)")
    print(f"  ✅ Sinónimos confiables: {total - sospechosos} ({(total-sospechosos)/total*100:.1f}%)")
    
    print(f"\n📋 Ejemplos de sinónimos reconocidos por lexicon:")
    ejemplos_lexicon = df_resultados[df_resultados['Método'] == '✅ Lexicon'].head(20)
    for _, row in ejemplos_lexicon.iterrows():
        print(f"  {row['Descripción'][:30]}... ↔ {row['Sinónimo']} (Score: {row['Score']})")

if __name__ == "__main__":
    revisar_con_lexicon()