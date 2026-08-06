"""
Aplicación principal UNSPSC DGCP Buscador - Emulación del estilo DGCP
"""

import sys
import os
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import sqlite3
import unicodedata
import re
import torch
from datetime import datetime
from io import BytesIO
import time

# Importar DatabaseManager desde database
from database import DatabaseManager

# Configuración de la página
st.set_page_config(
    page_title="UNSPSC DGCP BUSCADOR",
    page_icon="🔎",
    layout="wide"
)

# =====================================================
# ESTILOS CSS PERSONALIZADOS (EMULACIÓN DGCP)
# =====================================================

def inject_custom_css():
    """Inyecta CSS personalizado emulando el estilo de la DGCP"""
    st.markdown("""
    <style>
        /* =====================================================
           ESTILOS GENERALES (EMULACIÓN DGCP)
           ===================================================== */
        .main {
            background-color: #f8f9fa;
        }
        
        /* =====================================================
           HEADER
           ===================================================== */
        .dgcp-header {
            background-color: #fbfbfb;
            border-bottom: 1px solid #dbeafe;
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .dgcp-header .logo {
            height: 56px;
            width: auto;
            mix-blend-mode: multiply;
        }
        .dgcp-header h1 {
            font-size: 20px;
            font-weight: 600;
            color: #1a3a5c;
            text-align: center;
        }
        .dgcp-header p {
            font-size: 14px;
            color: #64748b;
            text-align: center;
            margin-top: 4px;
        }
        
        /* =====================================================
           BARRA DE BÚSQUEDA
           ===================================================== */
        .search-container {
            max-width: 896px;
            margin: 0 auto;
            padding: 32px 16px 8px 16px;
        }
        .search-wrapper {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .search-input-wrapper {
            position: relative;
            flex: 1;
        }
        .search-icon {
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            width: 20px;
            height: 20px;
            color: #6b7280;
            pointer-events: none;
        }
        .search-input {
            width: 100%;
            height: 56px;
            border-radius: 12px;
            border: 1px solid #d1d5db;
            background-color: white;
            padding-left: 48px;
            padding-right: 48px;
            font-size: 16px;
            color: #1a1a2e;
            outline: none;
            transition: all 0.2s ease;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .search-input::placeholder {
            color: #9ca3af;
        }
        .search-input:focus {
            border-color: #1a5276;
            box-shadow: 0 0 0 3px rgba(26, 82, 118, 0.2);
        }
        .search-clear-btn {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            border-radius: 9999px;
            padding: 4px;
            color: #6b7280;
            background: none;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .search-clear-btn:hover {
            background-color: #f3f4f6;
            color: #1a1a2e;
        }
        .search-btn {
            height: 56px;
            border-radius: 12px;
            background: linear-gradient(to right, #1a5276, #2e86c1);
            color: white;
            padding: 0 32px;
            font-size: 14px;
            font-weight: 500;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .search-btn:hover {
            box-shadow: 0 4px 12px rgba(26, 82, 118, 0.3);
            transform: translateY(-1px);
        }
        .search-btn:active {
            transform: translateY(0);
        }
        .search-btn svg {
            width: 20px;
            height: 20px;
        }
        .search-btn .btn-text {
            display: none;
        }
        @media (min-width: 640px) {
            .search-btn .btn-text {
                display: inline;
            }
        }
        
        /* =====================================================
           FILTRO
           ===================================================== */
        .filter-container {
            max-width: 896px;
            margin: 0 auto;
            padding: 8px 16px 16px 16px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }
        .filter-select {
            width: 220px;
            height: 36px;
            border-radius: 6px;
            border: 1px solid #d1d5db;
            background: white;
            padding: 0 12px;
            font-size: 14px;
            color: #1a1a2e;
            outline: none;
        }
        .filter-select:focus {
            border-color: #1a5276;
            box-shadow: 0 0 0 3px rgba(26, 82, 118, 0.1);
        }
        
        /* =====================================================
           RESULTADOS
           ===================================================== */
        .results-header {
            max-width: 1280px;
            margin: 0 auto;
            padding: 16px 16px 8px 16px;
        }
        .results-header h2 {
            font-size: 24px;
            font-weight: 700;
            color: #1a1a2e;
        }
        .results-header p {
            font-size: 14px;
            color: #6b7280;
            margin-top: 4px;
        }
        
        /* =====================================================
           TARJETA DE RESULTADO
           ===================================================== */
        .result-card {
            border-radius: 16px;
            border: 1px solid rgba(26, 82, 118, 0.2);
            background: white;
            padding: 28px;
            margin-bottom: 12px;
            transition: box-shadow 0.2s ease;
            max-width: 1280px;
            margin-left: auto;
            margin-right: auto;
        }
        .result-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .result-card .rank {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            border-radius: 9999px;
            background: #1a5276;
            color: white;
            font-weight: 600;
            font-size: 16px;
        }
        .result-card .code-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            border-radius: 9999px;
            background: #eff6ff;
            padding: 6px 16px;
            font-size: 14px;
            color: #1d4ed8;
        }
        .result-card .code-badge .code {
            font-family: monospace;
            font-weight: 600;
        }
        .result-card .title {
            font-size: 24px;
            font-weight: 700;
            color: #1a1a2e;
            margin: 16px 0;
        }
        .result-card .hierarchy-box {
            border-radius: 12px;
            border: 1px solid #dbeafe;
            background: rgba(219, 234, 254, 0.4);
            padding: 20px;
            margin-bottom: 16px;
        }
        .result-card .hierarchy-box .row {
            font-size: 16px;
            padding: 4px 0;
            color: #1a1a2e;
        }
        .result-card .hierarchy-box .row .label {
            font-weight: 600;
        }
        .result-card .hierarchy-box .row .value {
            color: #4b5563;
        }
        .result-card .hierarchy-box .budget {
            border-top: 1px solid #e5e7eb;
            padding-top: 12px;
            margin-top: 12px;
            font-size: 16px;
        }
        .result-card .hierarchy-box .budget .label {
            font-weight: 600;
        }
        .result-card .hierarchy-box .budget .value {
            color: #4b5563;
        }
        .result-card .definition {
            font-size: 16px;
            font-style: italic;
            color: #4b5563;
            margin-bottom: 16px;
            line-height: 1.6;
        }
        .result-card .synonyms-title {
            font-size: 16px;
            font-weight: 600;
            color: #1a1a2e;
            margin-bottom: 8px;
        }
        .result-card .synonym-badge {
            border-radius: 9999px;
            background: #ecfdf5;
            padding: 6px 16px;
            font-size: 14px;
            color: #065f46;
            display: inline-block;
            margin: 4px 4px 4px 0;
        }
        
        /* =====================================================
           PRODUCTOS RELACIONADOS
           ===================================================== */
        .related-section {
            max-width: 1280px;
            margin: 24px auto 0 auto;
            padding: 0 16px 48px 16px;
            border-top: 1px solid #e5e7eb;
            padding-top: 24px;
        }
        .related-section h3 {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 18px;
            font-weight: 600;
            color: #1a1a2e;
        }
        .related-section .subtitle {
            font-size: 14px;
            color: #6b7280;
            margin-top: 4px;
        }
        .related-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-top: 12px;
        }
        @media (min-width: 768px) {
            .related-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        @media (min-width: 1024px) {
            .related-grid {
                grid-template-columns: repeat(4, 1fr);
            }
        }
        .related-item {
            border: 1px solid rgba(26, 82, 118, 0.25);
            border-radius: 12px;
            background: white;
            padding: 16px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: left;
        }
        .related-item:hover {
            transform: translateY(-2px);
            border-color: #1a5276;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .related-item .rank {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 20px;
            height: 20px;
            border-radius: 9999px;
            background: #1a5276;
            color: white;
            font-size: 12px;
            font-weight: 600;
        }
        .related-item .title {
            font-size: 14px;
            font-weight: 600;
            color: #1a1a2e;
            margin: 8px 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .related-item .code {
            display: inline-block;
            border-radius: 9999px;
            background: #eff6ff;
            padding: 2px 10px;
            font-size: 12px;
            font-family: monospace;
            color: #1d4ed8;
        }
        .related-item .action {
            font-size: 12px;
            font-weight: 500;
            color: #1a5276;
            margin-top: 8px;
            display: block;
        }
        
        /* =====================================================
           PAGINACIÓN
           ===================================================== */
        .pagination-container {
            max-width: 1280px;
            margin: 0 auto;
            padding: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }
        .pagination-container .info {
            font-size: 14px;
            color: #6b7280;
        }
        
        /* =====================================================
           MÉTRICAS
           ===================================================== */
        .metrics-container {
            max-width: 1280px;
            margin: 0 auto;
            padding: 8px 16px;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }
        .metric-card {
            background: white;
            border-radius: 8px;
            padding: 12px 16px;
            border: 1px solid #e5e7eb;
            text-align: center;
        }
        .metric-card .value {
            font-size: 20px;
            font-weight: 700;
            color: #1a5276;
        }
        .metric-card .label {
            font-size: 12px;
            color: #6b7280;
            margin-top: 2px;
        }
        
        /* =====================================================
            OCULTAR ELEMENTOS DE STREAMLIT
            ===================================================== */
        .stTextInput > label {
            display: none !important;
        }
        .stTextInput > div {
            padding: 0 !important;
        }
        .stTextInput > div > div {
            display: none !important;
        }
        .stTextInput > div > div > input {
            display: none !important;
        }
        .st-emotion-cache-1y4p8pa {
            padding: 0 !important;
        }
        .stSelectbox > label {
            display: none !important;
        }
        
        /* =====================================================
            FOOTER
            ===================================================== */
        .dgcp-footer {
            text-align: center;
            padding: 24px 16px;
            border-top: 1px solid #dbeafe;
            background: white;
            margin-top: 24px;
        }
        .dgcp-footer .text {
            font-size: 14px;
            color: #6b7280;
        }
    </style>
    """, unsafe_allow_html=True)

# =====================================================
# FUNCIONES DE NORMALIZACIÓN
# =====================================================

def normalizar(texto):
    texto = str(texto).lower().strip()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    texto = re.sub(r"\s+", " ", texto)
    return texto

# =====================================================
# BÚSQUEDA POR CÓDIGO
# =====================================================

def buscar_por_codigo(df, consulta):
    """
    Busca ítems por código UNSPSC.
    Soporta búsqueda exacta y parcial.
    """
    consulta_limpia = re.sub(r"\s+", "", consulta).strip()
    
    # Intentar coincidencia exacta
    resultado_exacto = df[df["Código UNSPSC"].astype(str) == consulta_limpia]
    if not resultado_exacto.empty:
        return resultado_exacto
    
    # Intentar coincidencia parcial (códigos que comiencen con el número)
    resultado_parcial = df[df["Código UNSPSC"].astype(str).str.startswith(consulta_limpia)]
    if not resultado_parcial.empty:
        return resultado_parcial
    
    # Intentar coincidencia que contenga el número en cualquier parte
    resultado_contiene = df[df["Código UNSPSC"].astype(str).str.contains(consulta_limpia, na=False)]
    if not resultado_contiene.empty:
        return resultado_contiene
    
    return pd.DataFrame()

def es_busqueda_por_codigo(consulta):
    """
    Detecta si la consulta parece ser un código UNSPSC.
    """
    consulta_limpia = re.sub(r"\s+", "", consulta).strip()
    
    if re.match(r"^\d{8,}$", consulta_limpia):
        return True
    if re.match(r"^[\d\-]+$", consulta_limpia):
        return True
    
    return False

def es_busqueda_por_cuenta(consulta):
    """
    Detecta si la consulta parece ser una cuenta DIGEPRES.
    Formato: X.X.X.X.XX (ej: 2.3.9.4.01)
    """
    consulta_limpia = consulta.strip()
    return bool(re.match(r'^\d+\.\d+\.\d+\.\d+\.\d+$', consulta_limpia))

# =====================================================
# CARGAR DATOS
# =====================================================

@st.cache_data
def cargar_catalogo():
    conn = sqlite3.connect("db/DGCP_UNSPSC.db")
    df = pd.read_sql("SELECT * FROM catalogo", conn)
    conn.close()
    return df

@st.cache_data
def cargar_catalogo_con_digepres():
    """Carga el catálogo con DIGEPRES desde catalogo_final.csv"""
    try:
        csv_path = Path("data/catalogo_final.csv")
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df['Código'] = df['Código'].astype(str).str.strip()
            df['cuenta_digepres'] = df['cuenta_digepres'].astype(str).str.strip()
            return df
        else:
            st.warning("No se encontró el archivo catalogo_final.csv")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error cargando catalogo_final.csv: {e}")
        return pd.DataFrame()

@st.cache_data
def cargar_embeddings():
    """Carga embeddings desde archivo .pt"""
    data = torch.load("db/embeddings.pt", map_location="cpu")
    
    if isinstance(data, dict):
        if 'embeddings' in data:
            return data['embeddings']
        else:
            for key, value in data.items():
                if isinstance(value, torch.Tensor):
                    return value
    
    if isinstance(data, torch.Tensor):
        return data
    
    raise ValueError(f"Formato de embeddings no soportado: {type(data)}")

@st.cache_resource
def cargar_modelo():
    """Carga el modelo de embeddings (cacheado en memoria para no recargar cada vez)"""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

@st.cache_data
def cargar_sinonimos():
    try:
        conn = sqlite3.connect("db/DGCP_UNSPSC.db")
        df = pd.read_sql("SELECT termino, sinonimo FROM sinonimos", conn)
        conn.close()
        dic = {}
        for _, row in df.iterrows():
            t = normalizar(row["termino"])
            s = normalizar(row["sinonimo"])
            if t not in dic:
                dic[t] = []
            if s not in dic[t]:
                dic[t].append(s)
        return dic
    except:
        return {}

# =====================================================
# FUNCIÓN DE CONFIANZA (como en la DGCP)
# =====================================================

def calcular_confianza(score):
    """
    Calcula el nivel de confianza basado en el score.
    HIGH: > 0.70, MEDIUM: 0.40-0.70, LOW: < 0.40
    """
    if score >= 0.70:
        return "HIGH"
    elif score >= 0.40:
        return "MEDIUM"
    else:
        return "LOW"

# =====================================================
# BUSCADOR HÍBRIDO OPTIMIZADO
# =====================================================

def buscar_hibrido(df, embeddings, consulta, sinonimos):
    from rapidfuzz import fuzz
    from sentence_transformers import util
    import torch
    
    modelo = cargar_modelo()
    
    consulta_norm = normalizar(consulta)
    
    # Extraer palabras clave (sin stopwords)
    stopwords = {'de', 'la', 'el', 'los', 'las', 'un', 'una', 'unos', 'unas',
                 'para', 'por', 'con', 'sin', 'sobre', 'entre', 'hasta', 'desde',
                 'del', 'al', 'lo', 'le', 'les', 'se', 'me', 'te', 'nos', 'os',
                 'y', 'o', 'u', 'ni', 'que', 'como', 'cuando', 'donde', 'cual'}
    
    palabras_clave = [p for p in consulta_norm.split() if len(p) > 2 and p not in stopwords]
    
    terminos = [consulta_norm] + sinonimos + palabras_clave
    
    emb_consulta = modelo.encode(consulta_norm, convert_to_tensor=True, show_progress_bar=False)
    
    if not isinstance(embeddings, torch.Tensor):
        embeddings = torch.tensor(embeddings)
    
    similitudes = util.cos_sim(emb_consulta, embeddings)[0]
    
    top_k = min(500, len(similitudes))
    top_scores, top_indices = torch.topk(similitudes, top_k)
    
    top_indices_list = top_indices.cpu().numpy().tolist()
    top_scores_list = top_scores.cpu().numpy().tolist()
    
    resultados = []
    
    for idx, sem_score in zip(top_indices_list, top_scores_list):
        fila = df.iloc[idx]
        desc = normalizar(fila["Descripción"])
        definicion = normalizar(fila.get("Definición", ""))
        contexto = normalizar(f"{fila['Segmento']} {fila['Familia']} {fila['Clase']}")
        
        fuzzy_desc = 0
        fuzzy_def = 0
        fuzzy_ctx = 0
        
        for t in terminos:
            fs_desc = fuzz.token_sort_ratio(t, desc)
            fs_desc_partial = fuzz.partial_ratio(t, desc)
            fs_desc = max(fs_desc, fs_desc_partial)
            fs_def = fuzz.token_sort_ratio(t, definicion) if definicion else 0
            fs_ctx = fuzz.token_sort_ratio(t, contexto)
            
            if fs_desc > fuzzy_desc:
                fuzzy_desc = fs_desc
            if fs_def > fuzzy_def:
                fuzzy_def = fs_def
            if fs_ctx > fuzzy_ctx:
                fuzzy_ctx = fs_ctx
        
        fuzzy = (fuzzy_desc * 0.6) + (fuzzy_def * 0.2) + (fuzzy_ctx * 0.2)
        
        # Coincidencia de palabras clave
        palabras_en_desc = sum(1 for p in palabras_clave if p in desc)
        palabras_en_def = sum(1 for p in palabras_clave if p in definicion)
        
        if palabras_clave:
            porcentaje_palabras = (palabras_en_desc + palabras_en_def * 0.5) / len(palabras_clave)
        else:
            porcentaje_palabras = 0
        
        bono_palabras_clave = min(porcentaje_palabras * 30, 30)
        
        semantico = float(sem_score) * 100
        
        if porcentaje_palabras > 0.3:
            score = (semantico * 0.1) + (fuzzy * 0.9) + bono_palabras_clave
        else:
            score = (semantico * 0.2) + (fuzzy * 0.8) + bono_palabras_clave
        
        exacto = False
        if palabras_clave and all(p in desc for p in palabras_clave):
            exacto = True
        if fuzzy_desc >= 90:
            exacto = True
        if consulta_norm in desc:
            exacto = True
            score = max(score, 85)
        
        if palabras_clave and palabras_en_desc == 0 and palabras_en_def == 0:
            score = score * 0.3
        
        if score >= 40 or exacto:
            resultados.append((score, exacto, fila))
    
    resultados.sort(key=lambda x: (-x[1], -x[0]))
    return resultados[:200]

# =====================================================
# MOSTRAR RESULTADO (ESTILO DGCP)
# =====================================================

def mostrar_resultado(score, fila, rank, tipo_busqueda="texto"):
    db = DatabaseManager()
    cuenta, descripcion, fuente, confianza = db.obtener_digepres(
        fila["Código Familia"],
        descripcion_item=fila["Descripción"]
    )
    
    score_normalizado = score / 100
    nivel_confianza = calcular_confianza(score_normalizado)
    
    if nivel_confianza == "HIGH":
        confianza_emoji = "🟢"
        confianza_texto = "Alta"
    elif nivel_confianza == "MEDIUM":
        confianza_emoji = "🟡"
        confianza_texto = "Media"
    else:
        confianza_emoji = "🔴"
        confianza_texto = "Baja"
    
    # Extraer código de segmento, familia y clase de los nombres
    segmento = fila['Segmento']
    familia = fila['Familia']
    clase = fila['Clase']
    
    # Extraer códigos numéricos de los textos (si están disponibles)
    codigo_completo = str(fila['Código UNSPSC'])
    codigo_familia = codigo_completo[:4] if len(codigo_completo) >= 4 else ""
    codigo_clase = codigo_completo[:6] if len(codigo_completo) >= 6 else ""
    
    # Construir HTML del resultado
    html = f"""
    <div class="result-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
            <span class="code-badge">
                Código Subclase: <span class="code">{codigo_completo}</span>
                <button type="button" style="cursor:pointer;opacity:0.5;background:none;border:none;" onclick="navigator.clipboard.writeText('{codigo_completo}')">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                </button>
            </span>
            <span class="rank">{rank}</span>
        </div>
        <h3 class="title">{fila['Descripción']}</h3>
        <div class="hierarchy-box">
            <div class="row"><span class="label">Segmento:</span> <span class="value">{segmento}</span></div>
            <div class="row"><span class="label">Familia:</span> <span class="value">{familia}</span></div>
            <div class="row"><span class="label">Clase:</span> <span class="value">{clase}</span></div>
            <div class="budget">
                <span class="label">Cuenta Presupuestaria:</span>
                <span class="value">{cuenta if cuenta else 'No asignada'} {f' - {descripcion}' if cuenta and descripcion else ''}</span>
            </div>
        </div>
        <p class="definition">{fila.get('Definición', 'No hay definición disponible')[:300]}{'...' if len(str(fila.get('Definición', ''))) > 300 else ''}</p>
        <div>
            <p class="synonyms-title">Sinónimos:</p>
            <div>
    """
    
    # Agregar sinónimos desde la base de datos
    try:
        conn = sqlite3.connect("db/DGCP_UNSPSC.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT sinonimo 
            FROM sinonimos 
            WHERE termino = ? AND sinonimo != ?
            LIMIT 10
        """, (fila["Descripción"], fila["Descripción"]))
        sinonimos_list = cur.fetchall()
        conn.close()
        if sinonimos_list:
            for s in sinonimos_list:
                html += f'<span class="synonym-badge">{s[0]}</span>'
        else:
            html += '<span class="synonym-badge" style="background:#f3f4f6;color:#6b7280;">No hay sinónimos registrados</span>'
    except:
        html += '<span class="synonym-badge" style="background:#f3f4f6;color:#6b7280;">No hay sinónimos registrados</span>'
    
    html += """
            </div>
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

# =====================================================
# PRODUCTOS RELACIONADOS (ESTILO DGCP)
# =====================================================

def mostrar_productos_relacionados(df, codigo_actual, fila_actual):
    """Muestra productos relacionados en el estilo de la DGCP"""
    try:
        # Intentar obtener la familia del ítem actual
        familia_actual = fila_actual.get('Familia', '')
        if not familia_actual:
            return
        
        # Buscar productos de la misma familia
        relacionados = df[df['Familia'] == familia_actual].head(8)
        
        if len(relacionados) < 2:
            return
        
        st.markdown("""
        <div class="related-section">
            <h3>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a5276" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z"/>
                    <path d="M12 22V12"/>
                    <polyline points="3.29 7 12 12 20.71 7"/>
                    <path d="m7.5 4.27 9 5.15"/>
                </svg>
                Productos Relacionados
            </h3>
            <p class="subtitle">Frecuentemente comprados con <span style="font-weight:600;color:#1a1a2e;">{}</span></p>
            <div class="related-grid">
        """.format(fila_actual.get('Descripción', '')[:40]), unsafe_allow_html=True)
        
        rank = 1
        for _, row in relacionados.iterrows():
            if row['Código UNSPSC'] == codigo_actual:
                continue
            if rank > 8:
                break
            
            desc = str(row.get('Descripción', ''))[:50]
            codigo = str(row.get('Código UNSPSC', ''))
            
            st.markdown(f"""
            <div class="related-item" onclick="window.location.href='?q={codigo}'">
                <span class="rank">{rank}</span>
                <p class="title">{desc}</p>
                <span class="code">{codigo}</span>
                <span class="action">Buscar producto →</span>
            </div>
            """, unsafe_allow_html=True)
            rank += 1
        
        st.markdown("</div></div>", unsafe_allow_html=True)
        
    except Exception as e:
        pass

# =====================================================
# INTERFAZ PRINCIPAL
# =====================================================

# Inicializar estado
if "consulta" not in st.session_state:
    st.session_state.consulta = ""
if "resultados" not in st.session_state:
    st.session_state.resultados = []
if "sinonimos" not in st.session_state:
    st.session_state.sinonimos = []
if "df_filtrado" not in st.session_state:
    st.session_state.df_filtrado = pd.DataFrame()
if "tipo_busqueda" not in st.session_state:
    st.session_state.tipo_busqueda = "texto"
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = 1
if "ultima_busqueda" not in st.session_state:
    st.session_state.ultima_busqueda = ""
if "search_time_ms" not in st.session_state:
    st.session_state.search_time_ms = 0

# Inyectar CSS
inject_custom_css()

# =====================================================
# HEADER (EMULACIÓN DGCP)
# =====================================================

st.markdown("""
<div class="dgcp-header">
    <div style="display:flex;align-items:center;gap:16px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 100 100" style="mix-blend-mode:multiply;">
            <circle cx="50" cy="50" r="48" fill="#1a5276"/>
            <path d="M50 20 L30 40 L35 45 L50 30 L65 45 L70 40 L50 20Z" fill="white"/>
            <path d="M50 80 L30 60 L35 55 L50 70 L65 55 L70 60 L50 80Z" fill="white"/>
            <rect x="25" y="40" width="50" height="20" rx="4" fill="white"/>
            <circle cx="50" cy="50" r="8" fill="#1a5276"/>
            <circle cx="50" cy="50" r="4" fill="#e8b931"/>
        </svg>
        <div>
            <h1>Sistema de Búsqueda de Catálogo UNSPSC</h1>
            <p>18,000+ Productos y Servicios</p>
        </div>
    </div>
    <div>
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Escudo_de_la_Rep%C3%BAblica_Dominicana.svg/1200px-Escudo_de_la_Rep%C3%BAblica_Dominicana.svg.png" style="height:56px;width:auto;mix-blend-mode:multiply;" alt="Escudo RD">
    </div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR - FILTROS
# =====================================================

with st.sidebar:
    st.header("📂 Filtros")
    
    try:
        df_catalogo = cargar_catalogo()
        
        if df_catalogo is not None and not df_catalogo.empty:
            segmentos = sorted(df_catalogo["Segmento"].dropna().unique())
            segmento = st.selectbox("Segmento", ["Todos"] + list(segmentos))
            
            if segmento != "Todos":
                df_filtrado = df_catalogo[df_catalogo["Segmento"] == segmento]
            else:
                df_filtrado = df_catalogo
            
            familias = sorted(df_filtrado["Familia"].dropna().unique())
            familia = st.selectbox("Familia", ["Todas"] + list(familias))
            
            if familia != "Todas":
                df_filtrado = df_filtrado[df_filtrado["Familia"] == familia]
            
            clases = sorted(df_filtrado["Clase"].dropna().unique())
            clase = st.selectbox("Clase", ["Todas"] + list(clases))
            
            if clase != "Todas":
                df_filtrado = df_filtrado[df_filtrado["Clase"] == clase]
            
            st.caption(f"📊 {len(df_filtrado)} ítems disponibles")
            st.session_state.df_filtrado = df_filtrado
        else:
            st.warning("No se pudo cargar el catálogo")
            st.session_state.df_filtrado = pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error cargando filtros: {e}")
        st.session_state.df_filtrado = pd.DataFrame()
    
    st.divider()
    if st.button("🧹 Limpiar Búsqueda", use_container_width=True):
        st.session_state.consulta = ""
        st.session_state.resultados = []
        st.session_state.sinonimos = []
        st.session_state.tipo_busqueda = "texto"
        st.session_state.pagina_actual = 1
        st.session_state.ultima_busqueda = ""
        st.rerun()
    
    st.divider()
    st.caption("🔎 UNSPSC DGCP Expert v2.0")

# =====================================================
# BARRA DE BÚSQUEDA (ESTILO DGCP)
# =====================================================

st.markdown("""
<div class="search-container">
    <div class="search-wrapper">
        <div class="search-input-wrapper">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.3-4.3"></path>
            </svg>
            <input id="search_input" class="search-input" type="text" placeholder="Buscar productos por nombre, código o descripción..." maxlength="500" value="">
            <button class="search-clear-btn" id="search_clear" type="button" style="display: none;" onclick="document.getElementById('search_input').value=''; document.getElementById('search_input').dispatchEvent(new Event('input', {bubbles: true}));">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 6 6 18"></path>
                    <path d="m6 6 12 12"></path>
                </svg>
            </button>
        </div>
        <button class="search-btn" id="search_button">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.3-4.3"></path>
            </svg>
            <span class="btn-text">Buscar</span>
        </button>
    </div>
</div>
""", unsafe_allow_html=True)

# Script para manejar el input y el botón
st.markdown("""
<script>
    const input = document.getElementById('search_input');
    const clearBtn = document.getElementById('search_clear');
    const searchBtn = document.getElementById('search_button');
    
    // Cargar valor desde session_state si existe
    const savedValue = window.location.search ? new URLSearchParams(window.location.search).get('q') : '';
    if (savedValue) {
        input.value = savedValue;
        clearBtn.style.display = 'block';
    }
    
    input.addEventListener('input', function() {
        if (this.value.length > 0) {
            clearBtn.style.display = 'block';
        } else {
            clearBtn.style.display = 'none';
        }
    });
    
    searchBtn.addEventListener('click', function() {
        const event = new Event('input', {bubbles: true});
        input.dispatchEvent(event);
        // También actualizar el input oculto de Streamlit
        const streamlitInput = document.querySelector('input[data-testid="stTextInput"]');
        if (streamlitInput) {
            streamlitInput.value = input.value;
            streamlitInput.dispatchEvent(new Event('input', {bubbles: true}));
        }
    });
    
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            searchBtn.click();
        }
    });
</script>
""", unsafe_allow_html=True)

# Input oculto para Streamlit
consulta = st.text_input(
    "Buscar productos por nombre, código o descripción...",
    value=st.session_state.consulta,
    placeholder="Buscar productos por nombre, código o descripción...",
    key="input_busqueda",
    label_visibility="collapsed"
)

# =====================================================
# FILTRO DE NIVEL (ESTILO DGCP)
# =====================================================

st.markdown('<div class="filter-container">', unsafe_allow_html=True)
filtro_nivel = st.selectbox(
    "Seleccione nivel de filtro",
    ["Todos", "Segmento", "Familia", "Clase", "Subclase"],
    key="filtro_nivel",
    label_visibility="collapsed"
)
st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# EJECUTAR BÚSQUEDA
# =====================================================

if consulta and consulta != st.session_state.ultima_busqueda:
    st.session_state.ultima_busqueda = consulta
    st.session_state.consulta = consulta
    st.session_state.pagina_actual = 1
    
    search_start = time.time()
    
    with st.spinner("🔍 Buscando..."):
        try:
            df = st.session_state.df_filtrado
            if df.empty:
                df = cargar_catalogo()
            
            if df is not None and not df.empty:
                if es_busqueda_por_cuenta(consulta):
                    df_digepres = cargar_catalogo_con_digepres()
                    if not df_digepres.empty:
                        df_cuenta = df_digepres[df_digepres['cuenta_digepres'].astype(str).str.strip() == consulta.strip()]
                        if not df_cuenta.empty:
                            resultados = []
                            for _, fila in df_cuenta.iterrows():
                                codigo = fila['Código']
                                fila_catalogo = df[df["Código UNSPSC"].astype(str).str.strip() == str(codigo).strip()]
                                if not fila_catalogo.empty:
                                    resultados.append((100.0, True, fila_catalogo.iloc[0]))
                                else:
                                    resultados.append((100.0, True, fila))
                            st.session_state.resultados = resultados
                            st.session_state.sinonimos = []
                            st.session_state.tipo_busqueda = "cuenta"
                        else:
                            st.session_state.resultados = []
                            st.session_state.sinonimos = []
                            st.session_state.tipo_busqueda = "cuenta"
                    else:
                        st.session_state.resultados = []
                        st.session_state.sinonimos = []
                        st.session_state.tipo_busqueda = "cuenta"
                elif es_busqueda_por_codigo(consulta):
                    resultados_codigo = buscar_por_codigo(df, consulta)
                    if not resultados_codigo.empty:
                        resultados = []
                        for _, fila in resultados_codigo.iterrows():
                            resultados.append((100.0, True, fila))
                        st.session_state.resultados = resultados
                        st.session_state.sinonimos = []
                        st.session_state.tipo_busqueda = "código"
                    else:
                        st.session_state.resultados = []
                        st.session_state.sinonimos = []
                        st.session_state.tipo_busqueda = "código"
                else:
                    embeddings = cargar_embeddings()
                    sinonimos_dict = cargar_sinonimos()
                    sinonimos = sinonimos_dict.get(normalizar(consulta), [])
                    resultados = buscar_hibrido(df, embeddings, consulta, sinonimos)
                    st.session_state.resultados = resultados
                    st.session_state.sinonimos = sinonimos
                    st.session_state.tipo_busqueda = "texto"
            else:
                st.warning("No hay datos para buscar")
                
        except Exception as e:
            st.error(f"❌ Error en la búsqueda: {e}")
            import traceback
            with st.expander("🔍 Ver detalles del error"):
                st.code(traceback.format_exc())
    
    st.session_state.search_time_ms = (time.time() - search_start) * 1000

elif not consulta:
    st.session_state.resultados = []
    st.session_state.sinonimos = []

# =====================================================
# MOSTRAR RESULTADOS (ESTILO DGCP)
# =====================================================

resultados = st.session_state.resultados
sinonimos = st.session_state.sinonimos
tipo_busqueda = st.session_state.get("tipo_busqueda", "texto")
search_time_ms = st.session_state.get("search_time_ms", 0)

if resultados:
    # =====================================================
    # MÉTRICAS
    # =====================================================
    st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{len(resultados)}</div>
            <div class="label">Resultados</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">Híbrido</div>
            <div class="label">Método</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{len(sinonimos)}</div>
            <div class="label">Sinónimos</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{search_time_ms:.0f} ms</div>
            <div class="label">Tiempo</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # =====================================================
    # EXPORTAR A EXCEL
    # =====================================================
    if st.button("📥 Exportar a Excel", use_container_width=False):
        export_data = []
        for score, exacto, fila in resultados:
            export_data.append({
                "Tipo": "Exacta" if exacto else "Relacionada",
                "Score": round(score, 2),
                "Código UNSPSC": fila["Código UNSPSC"],
                "Descripción": fila["Descripción"],
                "Segmento": fila["Segmento"],
                "Familia": fila["Familia"],
                "Clase": fila["Clase"]
            })
        df_export = pd.DataFrame(export_data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=False)
        st.download_button(
            "📥 Descargar Excel",
            output.getvalue(),
            file_name=f"resultados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # =====================================================
    # HEADER DE RESULTADOS
    # =====================================================
    st.markdown(f"""
    <div class="results-header">
        <h2>Resultados de Búsqueda</h2>
        <p>{len(resultados)} resultados encontrados para ‘{consulta}’</p>
    </div>
    """, unsafe_allow_html=True)
    
    # =====================================================
    # PAGINACIÓN
    # =====================================================
    items_por_pagina = 8
    total_items = len(resultados)
    total_paginas = (total_items + items_por_pagina - 1) // items_por_pagina
    
    if st.session_state.pagina_actual < 1:
        st.session_state.pagina_actual = 1
    if st.session_state.pagina_actual > total_paginas and total_paginas > 0:
        st.session_state.pagina_actual = total_paginas
    
    inicio = (st.session_state.pagina_actual - 1) * items_por_pagina
    fin = min(inicio + items_por_pagina, total_items)
    resultados_pagina = resultados[inicio:fin]
    
    # Controles de paginación (arriba)
    if total_paginas > 1:
        col_prev, col_info, col_next = st.columns([1, 3, 1])
        with col_prev:
            if st.button("◀ Anterior", use_container_width=True, key="prev_top"):
                if st.session_state.pagina_actual > 1:
                    st.session_state.pagina_actual -= 1
        with col_info:
            st.markdown(f"<div style='text-align:center;font-size:14px;color:#6b7280;'>Página {st.session_state.pagina_actual} de {total_paginas} (mostrando {len(resultados_pagina)} de {total_items} ítems)</div>", unsafe_allow_html=True)
        with col_next:
            if st.button("Siguiente ▶", use_container_width=True, key="next_top"):
                if st.session_state.pagina_actual < total_paginas:
                    st.session_state.pagina_actual += 1
    
    # Mostrar resultados
    rank = inicio + 1
    exactos = [r for r in resultados_pagina if r[1]]
    relacionados = [r for r in resultados_pagina if not r[1]]
    
    # Guardar el primer resultado para productos relacionados
    primer_resultado = resultados[0] if resultados else None
    
    for score, exacto, fila in resultados_pagina:
        mostrar_resultado(score, fila, rank, tipo_busqueda)
        rank += 1
    
    # Mostrar productos relacionados (solo si hay al menos un resultado)
    if primer_resultado:
        mostrar_productos_relacionados(df, primer_resultado[2]['Código UNSPSC'], primer_resultado[2])
    
    # Controles de paginación (abajo)
    if total_paginas > 1:
        st.divider()
        col_prev, col_info, col_next = st.columns([1, 3, 1])
        with col_prev:
            if st.button("◀ Anterior", use_container_width=True, key="prev_bottom"):
                if st.session_state.pagina_actual > 1:
                    st.session_state.pagina_actual -= 1
        with col_info:
            st.markdown(f"<div style='text-align:center;font-size:14px;color:#6b7280;'>Página {st.session_state.pagina_actual} de {total_paginas}</div>", unsafe_allow_html=True)
        with col_next:
            if st.button("Siguiente ▶", use_container_width=True, key="next_bottom"):
                if st.session_state.pagina_actual < total_paginas:
                    st.session_state.pagina_actual += 1

elif consulta:
    st.info("ℹ️ No se encontraron resultados para esta búsqueda.")
    st.caption("Sugerencias: prueba con sinónimos o términos más generales.")

# =====================================================
# FOOTER
# =====================================================

st.markdown("""
<div class="dgcp-footer">
    <p class="text">© 2026, todos los derechos reservados. | BUSCADOR UNSPSC DGCP</p>
</div>
""", unsafe_allow_html=True)