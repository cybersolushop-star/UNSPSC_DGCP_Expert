"""
Script para generar y agregar sinónimos a la base de datos usando diccionarios en línea
y enriquecimiento semántico.
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import time
from pathlib import Path
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
from rapidfuzz import fuzz

# =====================================================
# CONFIGURACIÓN
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "db" / "DGCP_UNSPSC.db"
MODELO = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Palabras comunes que se ignoran como sinónimos
STOPWORDS = {'de', 'la', 'el', 'los', 'las', 'un', 'una', 'unos', 'unas',
             'para', 'por', 'con', 'sin', 'sobre', 'entre', 'hasta', 'desde',
             'del', 'al', 'lo', 'le', 'les', 'se', 'me', 'te', 'nos', 'os',
             'y', 'o', 'u', 'ni', 'que', 'como', 'cuando', 'donde', 'cual'}

# =====================================================
# FUNCIONES PARA OBTENER SINÓNIMOS DE DICCIONARIOS
# =====================================================

def obtener_sinonimos_de_frase(frase):
    """Extrae palabras clave de una frase y busca sinónimos individuales"""
    palabras = [p for p in frase.lower().split() if p not in STOPWORDS and len(p) > 2]
    sinonimos = []
    
    for palabra in palabras[:3]:  # Limitar a 3 palabras clave
        sinonimos_palabra = obtener_sinonimos_wordreference(palabra)
        sinonimos.extend(sinonimos_palabra)
        time.sleep(0.5)  # Evitar bloqueos
    
    return list(set(sinonimos))[:20]

def obtener_sinonimos_wordreference(palabra):
    """Obtiene sinónimos de WordReference"""
    try:
        url = f"https://www.wordreference.com/sinonimos/{palabra}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        sinonimos = []
        # Buscar en diferentes selectores
        for li in soup.select('.sinonimos li, .related li, .list li, .sin li'):
            texto = li.get_text(strip=True)
            if texto and len(texto) > 2:
                texto = re.sub(r'^\d+\.\s*', '', texto)
                texto = re.sub(r'\([^)]*\)', '', texto)
                # Separar por comas si hay múltiples
                for parte in texto.split(','):
                    parte = parte.strip()
                    if len(parte) > 2 and parte not in sinonimos:
                        sinonimos.append(parte)
        
        return sinonimos[:15]
    except Exception as e:
        return []

def obtener_sinonimos_sinonimosonline(palabra):
    """Obtiene sinónimos de sinonimosonline.com"""
    try:
        url = f"https://www.sinonimosonline.com/sinonimo/{palabra}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        sinonimos = []
        for a in soup.select('.sinonimos a, .list a, .related a'):
            texto = a.get_text(strip=True)
            if texto and len(texto) > 2 and ',' not in texto:
                sinonimos.append(texto)
        
        return sinonimos[:15]
    except Exception as e:
        return []

def obtener_sinonimos_semanticos(frase, df_catalogo, top_n=10):
    """Encuentra sinónimos semánticos en el catálogo"""
    emb_frase = MODELO.encode(frase, convert_to_tensor=True, show_progress_bar=False)
    
    resultados = []
    for _, row in df_catalogo.iterrows():
        texto = f"{row['Descripción']} {row.get('Definición', '')}"
        emb_item = MODELO.encode(texto, convert_to_tensor=True, show_progress_bar=False)
        similitud = util.cos_sim(emb_frase, emb_item).item()
        if similitud > 0.4:
            resultados.append((similitud, row['Descripción'], row['Código UNSPSC']))
    
    resultados.sort(key=lambda x: x[0], reverse=True)
    return resultados[:top_n]

def obtener_sinonimos_combinados(frase, df_catalogo):
    """Combina todas las fuentes de sinónimos"""
    print(f"🔍 Buscando sinónimos para: '{frase}'")
    
    sinonimos = []
    
    # 1. Palabras clave de la frase
    palabras_clave = [p for p in frase.lower().split() if p not in STOPWORDS and len(p) > 2]
    print(f"   📝 Palabras clave: {', '.join(palabras_clave)}")
    
    # 2. Sinónimos de WordReference (por palabra clave)
    for palabra in palabras_clave[:3]:
        sinonimos_wr = obtener_sinonimos_wordreference(palabra)
        if sinonimos_wr:
            print(f"   📚 WordReference ({palabra}): {len(sinonimos_wr)} sinónimos")
            sinonimos.extend(sinonimos_wr)
        time.sleep(0.3)
    
    # 3. Sinónimos de sinonimosonline
    for palabra in palabras_clave[:2]:
        sinonimos_so = obtener_sinonimos_sinonimosonline(palabra)
        if sinonimos_so:
            print(f"   📚 SinonimosOnline ({palabra}): {len(sinonimos_so)} sinónimos")
            sinonimos.extend(sinonimos_so)
        time.sleep(0.3)
    
    # 4. Sinónimos semánticos del catálogo
    sinonimos_sem = obtener_sinonimos_semanticos(frase, df_catalogo, top_n=5)
    if sinonimos_sem:
        print(f"   🧠 Sinónimos semánticos: {len(sinonimos_sem)} ítems relacionados")
        for sim, desc, codigo in sinonimos_sem:
            sinonimos.append(desc)
            print(f"      - {desc} ({sim:.2f})")
    
    # Limpiar y normalizar
    sinonimos_limpios = []
    for s in sinonimos:
        s_clean = s.lower().strip()
        s_clean = re.sub(r'^\d+\.?\s*', '', s_clean)
        s_clean = re.sub(r'\([^)]*\)', '', s_clean)
        s_clean = s_clean.strip()
        if len(s_clean) > 2 and s_clean not in sinonimos_limpios and s_clean not in STOPWORDS:
            sinonimos_limpios.append(s_clean)
    
    return sinonimos_limpios[:20]

# =====================================================
# FUNCIONES AUXILIARES
# =====================================================

def cargar_catalogo():
    """Carga el catálogo desde la base de datos"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT \"Código UNSPSC\", \"Descripción\", \"Definición\", \"Segmento\", \"Familia\" FROM catalogo", conn)
    conn.close()
    return df

def agregar_sinonimos_a_bd(termino_principal, sinonimos):
    """Agrega sinónimos a la base de datos"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    agregados = 0
    duplicados = 0
    for sinonimo in sinonimos:
        if sinonimo.lower() == termino_principal.lower():
            continue
        
        cur.execute("SELECT COUNT(*) FROM sinonimos WHERE termino = ? AND sinonimo = ?", (termino_principal, sinonimo))
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO sinonimos (termino, sinonimo, capa) VALUES (?, ?, 1)", (termino_principal, sinonimo))
            cur.execute("INSERT INTO sinonimos (termino, sinonimo, capa) VALUES (?, ?, 1)", (sinonimo, termino_principal))
            agregados += 1
            print(f"   ✅ {termino_principal} ↔ {sinonimo}")
        else:
            duplicados += 1
    
    conn.commit()
    conn.close()
    print(f"\n✅ Sinónimos agregados: {agregados}")
    if duplicados > 0:
        print(f"⏩ Duplicados omitidos: {duplicados}")

def buscar_items_por_frase(frase, df_catalogo):
    """Busca ítems en el catálogo que coincidan con la frase"""
    resultados = []
    for _, row in df_catalogo.iterrows():
        desc = row['Descripción'].lower()
        # Buscar coincidencia de palabras clave
        palabras = [p for p in frase.lower().split() if p not in STOPWORDS and len(p) > 2]
        coincidencias = sum(1 for p in palabras if p in desc)
        if coincidencias > 0:
            resultados.append((coincidencias, row['Descripción'], row['Código UNSPSC']))
    
    resultados.sort(key=lambda x: x[0], reverse=True)
    return resultados[:5]

# =====================================================
# FUNCIÓN PRINCIPAL
# =====================================================

def generar_y_agregar_sinonimos(palabra_clave):
    """Función principal: busca sinónimos y los agrega a la base de datos"""
    print("=" * 60)
    print(f"🔄 Generando sinónimos para: '{palabra_clave}'")
    print("=" * 60)
    
    df_catalogo = cargar_catalogo()
    
    # 1. Buscar ítems existentes que coincidan
    items_coincidentes = buscar_items_por_frase(palabra_clave, df_catalogo)
    if items_coincidentes:
        print("\n📋 Ítems existentes que coinciden con la búsqueda:")
        for i, (coinc, desc, codigo) in enumerate(items_coincidentes, 1):
            print(f"   {i}. {desc} ({codigo}) - {coinc} coincidencias")
    else:
        print("\n⚠️ No se encontraron ítems que coincidan exactamente con la búsqueda")
    
    # 2. Buscar sinónimos
    sinonimos = obtener_sinonimos_combinados(palabra_clave, df_catalogo)
    
    if not sinonimos:
        print("❌ No se encontraron sinónimos")
        return
    
    print(f"\n📋 Sinónimos encontrados ({len(sinonimos)}):")
    for s in sinonimos[:10]:
        print(f"   - {s}")
    if len(sinonimos) > 10:
        print(f"   ... y {len(sinonimos) - 10} más")
    
    # 3. Seleccionar el ítem destino
    print("\n📋 ¿A qué ítem quieres asociar estos sinónimos?")
    
    if items_coincidentes:
        print("   Opciones:")
        for i, (coinc, desc, codigo) in enumerate(items_coincidentes, 1):
            print(f"   {i}. {desc} ({codigo})")
        print("   s. Buscar otro ítem")
        print("   c. Cancelar")
        
        opcion = input("\nSelecciona una opción: ").strip()
        
        if opcion.lower() == 'c':
            print("❌ Operación cancelada")
            return
        elif opcion.lower() == 's':
            termino_principal = input("Ingresa la descripción exacta del ítem: ").strip()
            if not termino_principal:
                print("❌ No se ingresó ningún ítem")
                return
        else:
            try:
                idx = int(opcion) - 1
                termino_principal = items_coincidentes[idx][1]
            except:
                print("❌ Opción inválida")
                return
    else:
        termino_principal = input("Ingresa la descripción exacta del ítem: ").strip()
        if not termino_principal:
            print("❌ No se ingresó ningún ítem")
            return
    
    # 4. Confirmar y agregar
    print(f"\n📋 Se agregarán {len(sinonimos)} sinónimos a '{termino_principal}'")
    confirmar = input("¿Confirmar? (s/n): ").strip().lower()
    
    if confirmar == 's':
        agregar_sinonimos_a_bd(termino_principal, sinonimos)
    else:
        print("❌ Operación cancelada")

# =====================================================
# MAIN
# =====================================================

def main():
    print("🔍 GENERADOR DE SINÓNIMOS")
    print("=" * 60)
    print("Este script busca sinónimos en diccionarios en línea y los asocia a ítems del catálogo.")
    print("Requiere conexión a internet.")
    print("-" * 60)
    
    while True:
        palabra = input("\n📝 Ingresa una palabra o frase (o 'salir' para terminar): ").strip()
        if palabra.lower() == 'salir':
            break
        if not palabra:
            continue
        generar_y_agregar_sinonimos(palabra)

if __name__ == "__main__":
    main()