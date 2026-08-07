"""
Aplicación principal UNSPSC DGCP Buscador - Versión Optimizada
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
import base64

# Importar DatabaseManager desde database
from database import DatabaseManager

# =====================================================
# FUNCIÓN PARA OBTENER LOGO COMO BASE64
# =====================================================

def obtener_logo_base64():
    """Lee el logo.png y lo convierte a Base64 en tiempo real"""
    try:
        # Buscar el logo en múltiples rutas posibles
        rutas_posibles = [
            Path("data/logo.png"),
            Path("./data/logo.png"),
            Path(os.path.join(os.path.dirname(__file__), "data", "logo.png")),
            Path(os.path.join(os.getcwd(), "data", "logo.png")),
        ]
        
        for ruta in rutas_posibles:
            if ruta.exists():
                with open(ruta, "rb") as f:
                    logo_bytes = f.read()
                    logo_base64 = base64.b64encode(logo_bytes).decode()
                    return f"data:image/png;base64,{logo_base64}"
        
        return None
    except Exception as e:
        print(f"Error cargando logo: {e}")
        return None

# =====================================================
# ESTILOS CSS
# =====================================================

def inject_custom_css():
    """Inyecta CSS personalizado"""
    st.markdown("""
    <style>
        /* Reducir espacio superior de la página */
        .main > div {
            padding-top: 0 !important;
        }
        .block-container {
            padding-top: 0.5rem !important;
        }
        
        .stTextInput > label {
            display: none !important;
        }
        .stTextInput > div {
            padding: 0 !important;
        }
        .stTextInput > div > div > input {
            border-radius: 12px !important;
            border: 1px solid #d1d5db !important;
            padding: 14px 16px !important;
            font-size: 16px !important;
            color: #1a1a2e !important;
            background-color: white !important;
            outline: none !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
            width: 100% !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #1a5276 !important;
            box-shadow: 0 0 0 3px rgba(26, 82, 118, 0.2) !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: #9ca3af !important;
        }
        
        /* Selectores en sidebar */
        .stSelectbox > div > div {
            background-color: #1e293b !important;
            border-color: #334155 !important;
            color: #f1f5f9 !important;
            border-radius: 8px !important;
        }
        .stSelectbox > div > div > div {
            color: #f1f5f9 !important;
        }
        .stSelectbox > div > div:hover {
            border-color: #3b82f6 !important;
        }
        .stSelectbox label {
            color: #94a3b8 !important;
        }
        
        .main-header {
            text-align: center;
            padding: 8px 0 4px 0;
        }
        .main-header h1 {
            color: #1a5276;
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
        }
        .main-header h1 a {
            color: #1a5276;
            text-decoration: none;
        }
        .main-header h1 a:hover {
            color: #154360;
            text-decoration: underline;
        }
        .main-header p {
            color: #5d6d7e;
            font-size: 1.1rem;
            margin: 2px 0 0 0;
        }
        .main-header .credits {
            color: #5d6d7e;
            font-size: 0.9rem;
            font-style: italic;
            margin: 2px 0 0 0;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
        }
        [data-testid="stSidebar"] .stSelectbox label {
            color: #94a3b8 !important;
        }
        [data-testid="stSidebar"] .stSelectbox > div > div {
            background-color: #1e293b !important;
            border-color: #334155 !important;
            color: #f1f5f9 !important;
        }
        [data-testid="stSidebar"] .stSelectbox > div > div > div {
            color: #f1f5f9 !important;
        }
        [data-testid="stSidebar"] .stSelectbox > div > div:hover {
            border-color: #3b82f6 !important;
        }
        [data-testid="stSidebar"] .stCaption {
            color: #94a3b8 !important;
        }
        [data-testid="stSidebar"] .stMarkdown {
            color: #f1f5f9 !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            background-color: #1a5276 !important;
            color: white !important;
            border: none !important;
        }
        
        /* Logo en sidebar */
        .sidebar-logo-container {
            text-align: center;
            padding: 5px 0 5px 0;
            border-bottom: 2px solid #334155;
            margin-bottom: 10px;
        }
        .sidebar-logo-wrapper {
            background: white;
            border-radius: 12px;
            padding: 6px;
            margin: 0 auto;
            max-width: 130px;
            box-shadow: 0 3px 5px rgba(0,0,0,0.25);
        }
        .sidebar-logo-wrapper img {
            display: block;
            width: 100%;
            height: auto;
            border-radius: 6px;
        }
        .sidebar-logo-title {
            font-size: 0.75rem;
            color: #94a3b8;
            margin-top: 4px;
        }
        
        .result-card {
            border-radius: 12px;
            border: 1px solid #e8e8e8;
            background: white;
            padding: 20px;
            margin-bottom: 12px;
            transition: box-shadow 0.2s ease;
        }
        .result-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .result-card .title {
            font-size: 20px;
            font-weight: 700;
            color: #1a5276;
            margin: 8px 0;
        }
        .result-card .hierarchy {
            font-size: 14px;
            color: #4a4a4a;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            margin: 8px 0;
        }
        .result-card .hierarchy .label {
            font-weight: 600;
        }
        .result-card .digepres {
            background: #e8f4f8;
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            border-left: 4px solid #1a5276;
        }
        .result-card .digepres .label {
            font-weight: 600;
        }
        
        .footer {
            text-align: center;
            padding: 20px 16px;
            border-top: 1px solid #e8e8e8;
            margin-top: 24px;
            color: #6b7280;
            font-size: 14px;
        }
        .stExpander {
            border: 1px solid #e8e8e8 !important;
            border-radius: 12px !important;
            margin-bottom: 12px !important;
        }
        .stExpander > div:first-child {
            border-radius: 12px !important;
        }
        
        .results-header-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            max-width: 1280px;
            margin: 12px auto 8px auto;
            padding: 0 16px;
        }
        .results-header-container h2 {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1a5276;
            margin: 0;
        }
        .results-header-container .export-btn {
            margin-left: auto;
        }
        
        .stSidebar .stMarkdown h1, 
        .stSidebar .stMarkdown h2, 
        .stSidebar .stMarkdown h3 {
            margin-top: 0 !important;
            margin-bottom: 6px !important;
        }
        .stSidebar .stSelectbox {
            margin-top: 0 !important;
            margin-bottom: 6px !important;
        }
        .stSidebar hr {
            margin-top: 6px !important;
            margin-bottom: 6px !important;
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
    consulta_limpia = re.sub(r"\s+", "", consulta).strip()
    
    resultado_exacto = df[df["Código UNSPSC"].astype(str) == consulta_limpia]
    if not resultado_exacto.empty:
        return resultado_exacto
    
    resultado_parcial = df[df["Código UNSPSC"].astype(str).str.startswith(consulta_limpia)]
    if not resultado_parcial.empty:
        return resultado_parcial
    
    resultado_contiene = df[df["Código UNSPSC"].astype(str).str.contains(consulta_limpia, na=False)]
    if not resultado_contiene.empty:
        return resultado_contiene
    
    return pd.DataFrame()

def es_busqueda_por_codigo(consulta):
    consulta_limpia = re.sub(r"\s+", "", consulta).strip()
    if re.match(r"^\d{8,}$", consulta_limpia):
        return True
    if re.match(r"^[\d\-]+$", consulta_limpia):
        return True
    return False

def es_busqueda_por_cuenta(consulta):
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
    try:
        csv_path = Path("data/catalogo_final.csv")
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df['Código'] = df['Código'].astype(str).str.strip()
            df['cuenta_digepres'] = df['cuenta_digepres'].astype(str).str.strip()
            return df
        else:
            return pd.DataFrame()
    except:
            return pd.DataFrame()

@st.cache_data
def cargar_embeddings():
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
# BUSCADOR HÍBRIDO
# =====================================================

def buscar_hibrido(df, embeddings, consulta, sinonimos):
    from rapidfuzz import fuzz
    from sentence_transformers import util
    import torch
    
    modelo = cargar_modelo()
    
    consulta_norm = normalizar(consulta)
    
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
# MOSTRAR RESULTADO (CON ST.EXPANDER)
# =====================================================

def mostrar_resultado(score, fila, rank):
    db = DatabaseManager()
    cuenta, descripcion, fuente, confianza = db.obtener_digepres(
        fila["Código Familia"],
        descripcion_item=fila["Descripción"]
    )
    
    titulo = f"{score:.0f}% | {fila['Código UNSPSC']} | {fila['Descripción']}"
    
    with st.expander(titulo):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**📋 Código:**", fila["Código UNSPSC"])
            st.write("**📝 Descripción:**", fila["Descripción"])
            if fila.get("Definición") and str(fila["Definición"]) != "nan":
                st.write("**📖 Definición:**", fila["Definición"])
            st.write("**📂 Segmento:**", fila["Segmento"])
            st.write("**📁 Familia:**", fila["Familia"])
            st.write("**📄 Clase:**", fila["Clase"])
        
        with col2:
            st.write("**💰 Clasificación DIGEPRES**")
            if cuenta:
                st.success(f"**Cuenta:** {cuenta}")
                st.write(f"**Descripción:** {descripcion}")
                st.caption(f"🔍 Fuente: {fuente} | Confianza: {confianza:.0%}")
            else:
                st.warning("Sin clasificación DIGEPRES asignada")
        
        st.caption(f"📅 Versión: {fila.get('Fecha Versión', 'No disponible')}")

# =====================================================
# FUNCIÓN PRINCIPAL
# =====================================================

def main():
    """Función principal de la aplicación"""
    
    # =====================================================
    # INICIALIZAR SESSION STATE
    # =====================================================
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
    if "consulta_input" not in st.session_state:
        st.session_state.consulta_input = ""

    inject_custom_css()

    # =====================================================
    # SIDEBAR - LOGO + FILTROS
    # =====================================================
    with st.sidebar:
        # =====================================================
        # LOGO PNG COMO BASE64 (CARGADO EN TIEMPO REAL)
        # =====================================================
        try:
            logo_data_uri = obtener_logo_base64()
            
            if logo_data_uri:
                st.markdown(f"""
                <div class="sidebar-logo-container">
                    <div class="sidebar-logo-wrapper">
                        <img src="{logo_data_uri}" alt="Logo UNSPSC DGCP">
                    </div>
                    <div class="sidebar-logo-title">
                        Buscador de Bienes y Servicios
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Fallback con emoji
                st.markdown("""
                <div class="sidebar-logo-container">
                    <div style="
                        background: linear-gradient(135deg, #1a5276, #154360);
                        border-radius: 12px;
                        padding: 12px;
                        margin: 0 auto;
                        max-width: 130px;
                        box-shadow: 0 3px 5px rgba(0,0,0,0.25);
                    ">
                        <div style="font-size: 3rem; margin: 0;">🔎</div>
                        <div style="
                            font-size: 0.85rem;
                            font-weight: 700;
                            color: white;
                            margin: 3px 0 2px 0;
                        ">
                            UNSPSC DGCP
                        </div>
                    </div>
                    <div class="sidebar-logo-title">
                        Buscador de Bienes y Servicios
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.markdown("""
            <div class="sidebar-logo-container">
                <div style="
                    background: linear-gradient(135deg, #1a5276, #154360);
                    border-radius: 12px;
                    padding: 12px;
                    margin: 0 auto;
                    max-width: 130px;
                    box-shadow: 0 3px 5px rgba(0,0,0,0.25);
                ">
                    <div style="font-size: 3rem; margin: 0;">🔎</div>
                    <div style="
                        font-size: 0.85rem;
                        font-weight: 700;
                        color: white;
                        margin: 3px 0 2px 0;
                    ">
                        UNSPSC DGCP
                    </div>
                </div>
                <div class="sidebar-logo-title">
                    Buscador de Bienes y Servicios
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
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
    # ENCABEZADO - TÍTULO COMO BOTÓN DE INICIO
    # =====================================================
    
    home_url = "https://cataloconsultadgcp.streamlit.app"
    
    st.markdown(f"""
    <div class="main-header">
        <h1><a href="{home_url}" target="_self">🔎 BUSCADOR UNSPSC DGCP</a></h1>
        <p>Catálogo de Bienes y Servicios DGCP</p>
        <p class="credits">por Rudy Pérez</p>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # BARRA DE BÚSQUEDA
    # =====================================================
    
    consulta = st.text_input(
        "🔎 Describa el bien o servicio, ingrese un código UNSPSC o una cuenta DIGEPRES:",
        value=st.session_state.consulta,
        placeholder="Ej: perro, computadora, 10101502, 25101503, 2.3.9.4.01...",
        key="consulta_input"
    )

    # Si la consulta cambió, ejecutar búsqueda
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
                        sinonimos = sinonimos_dict.get(consulta, [])
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

    # Si no hay consulta, limpiar resultados
    elif not consulta:
        st.session_state.resultados = []
        st.session_state.sinonimos = []
        st.session_state.ultima_busqueda = ""

    # =====================================================
    # MOSTRAR RESULTADOS
    # =====================================================
    
    resultados = st.session_state.resultados
    sinonimos = st.session_state.sinonimos
    tipo_busqueda = st.session_state.get("tipo_busqueda", "texto")
    search_time_ms = st.session_state.get("search_time_ms", 0)

    if resultados:
        st.markdown(f"""
        <div style="max-width: 1280px; margin: 12px auto 8px auto; padding: 0 16px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <h2 style="font-size: 1.5rem; font-weight: 700; color: #1a5276; margin: 0;">
                    📋 Resultados encontrados: {len(resultados)}
                </h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_export, col_empty = st.columns([1, 5])
        with col_export:
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
            
            if export_data:
                df_export = pd.DataFrame(export_data)
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_export.to_excel(writer, index=False)
                excel_data = output.getvalue()
                
                st.download_button(
                    "📥 Exportar a Excel",
                    excel_data,
                    file_name=f"resultados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        items_por_pagina = 10
        total_items = len(resultados)
        total_paginas = (total_items + items_por_pagina - 1) // items_por_pagina
        
        if st.session_state.pagina_actual < 1:
            st.session_state.pagina_actual = 1
        if st.session_state.pagina_actual > total_paginas and total_paginas > 0:
            st.session_state.pagina_actual = total_paginas
        
        inicio = (st.session_state.pagina_actual - 1) * items_por_pagina
        fin = min(inicio + items_por_pagina, total_items)
        resultados_pagina = resultados[inicio:fin]
        
        if total_paginas > 1:
            col_prev, col_info, col_next = st.columns([1, 3, 1])
            with col_prev:
                if st.button("◀ Anterior", use_container_width=True, key="prev_top"):
                    if st.session_state.pagina_actual > 1:
                        st.session_state.pagina_actual -= 1
            with col_info:
                st.markdown(f"<p style='text-align:center;color:#6b7280;'>Página {st.session_state.pagina_actual} de {total_paginas} (mostrando {len(resultados_pagina)} de {total_items} ítems)</p>", unsafe_allow_html=True)
            with col_next:
                if st.button("Siguiente ▶", use_container_width=True, key="next_top"):
                    if st.session_state.pagina_actual < total_paginas:
                        st.session_state.pagina_actual += 1
        
        rank = inicio + 1
        for score, exacto, fila in resultados_pagina:
            mostrar_resultado(score, fila, rank)
            rank += 1
        
        if total_paginas > 1:
            st.divider()
            col_prev, col_info, col_next = st.columns([1, 3, 1])
            with col_prev:
                if st.button("◀ Anterior", use_container_width=True, key="prev_bottom"):
                    if st.session_state.pagina_actual > 1:
                        st.session_state.pagina_actual -= 1
            with col_info:
                st.markdown(f"<p style='text-align:center;color:#6b7280;'>Página {st.session_state.pagina_actual} de {total_paginas}</p>", unsafe_allow_html=True)
            with col_next:
                if st.button("Siguiente ▶", use_container_width=True, key="next_bottom"):
                    if st.session_state.pagina_actual < total_paginas:
                        st.session_state.pagina_actual += 1

    elif consulta:
        st.info("ℹ️ No se encontraron resultados para esta búsqueda.")
        st.caption("Sugerencias: prueba con sinónimos o términos más generales.")

    st.markdown("""
    <div class="footer">
        © 2026, todos los derechos reservados. | BUSCADOR UNSPSC DGCP
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# PUNTO DE ENTRADA
# =====================================================

if __name__ == "__main__":
    main()