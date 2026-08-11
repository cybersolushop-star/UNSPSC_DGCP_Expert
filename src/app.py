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

# Importar DatabaseManager desde database
from database import DatabaseManager

# Configuración de la página
st.set_page_config(
    page_title="UNSPSC DGCP BUSCADOR",
    page_icon="🔎",
    layout="wide"
)

# =====================================================
# ESTILOS CSS
# =====================================================

def inject_custom_css():
    """Inyecta CSS personalizado"""
    st.markdown("""
    <style>
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
        .sidebar-logo-container {
            text-align: center;
            padding: 5px 0 5px 0;
            border-bottom: 2px solid #334155;
            margin-bottom: 10px;
            cursor: pointer;
        }
        .sidebar-logo-wrapper {
            background: white;
            border-radius: 12px;
            padding: 6px;
            margin: 0 auto;
            max-width: 130px;
            box-shadow: 0 3px 5px rgba(0,0,0,0.25);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .sidebar-logo-wrapper:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 12px rgba(0,0,0,0.4);
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
            transition: color 0.2s ease;
            cursor: pointer;
        }
        .sidebar-logo-title:hover {
            color: #e2e8f0;
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
    
    resultado_exacto = df[df["Código"].astype(str) == consulta_limpia]
    if not resultado_exacto.empty:
        return resultado_exacto
    
    resultado_parcial = df[df["Código"].astype(str).str.startswith(consulta_limpia)]
    if not resultado_parcial.empty:
        return resultado_parcial
    
    resultado_contiene = df[df["Código"].astype(str).str.contains(consulta_limpia, na=False)]
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
# CARGAR DATOS DESDE EXCEL
# =====================================================

@st.cache_data
def cargar_catalogo_excel():
    """Carga el catálogo desde el archivo mapeo_completo.xlsx"""
    try:
        excel_path = Path("data/mapeo_completo.xlsx")
        if excel_path.exists():
            df = pd.read_excel(excel_path)
            # Asegurar nombres de columnas
            if 'Código' not in df.columns:
                if len(df.columns) > 0:
                    df.rename(columns={df.columns[0]: 'Código'}, inplace=True)
            if 'Descripción' not in df.columns:
                if len(df.columns) > 1:
                    df.rename(columns={df.columns[1]: 'Descripción'}, inplace=True)
            if 'Definición' not in df.columns:
                if len(df.columns) > 2:
                    df.rename(columns={df.columns[2]: 'Definición'}, inplace=True)
            if 'Sinónimos' not in df.columns:
                if len(df.columns) > 3:
                    df.rename(columns={df.columns[3]: 'Sinónimos'}, inplace=True)
            
            # Asegurar que las columnas necesarias existan
            columnas_necesarias = ['Código', 'Descripción', 'Definición', 'Sinónimos']
            for col in columnas_necesarias:
                if col not in df.columns:
                    df[col] = ''
            
            st.session_state.df_catalogo_excel = df
            return df
        else:
            st.warning("⚠️ No se encontró el archivo data/mapeo_completo.xlsx")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error cargando Excel: {e}")
        return pd.DataFrame()

@st.cache_data
def cargar_catalogo():
    """Carga el catálogo desde la base de datos SQLite (fallback)"""
    try:
        conn = sqlite3.connect("db/DGCP_UNSPSC.db")
        df = pd.read_sql("SELECT * FROM catalogo", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Error cargando base de datos: {e}")
        return pd.DataFrame()

# =====================================================
# BUSCADOR EN EXCEL (CON PESO SEMÁNTICO)
# =====================================================

def buscar_en_excel(df, consulta):
    """Busca la consulta en todas las columnas del DataFrame con peso semántico"""
    if df.empty:
        return pd.DataFrame()
    
    consulta_norm = normalizar(consulta)
    palabras = consulta_norm.split()
    
    resultados = []
    
    # Columnas a buscar (todas las columnas de texto)
    columnas_texto = [col for col in df.columns if df[col].dtype == 'object']
    
    # Columnas con mayor peso semántico (descripción y sinónimos)
    columnas_principales = ['Descripción', 'Sinónimos', 'Definición', 'Denominación']
    columnas_principales = [col for col in columnas_principales if col in df.columns]
    
    for idx, row in df.iterrows():
        score = 0
        coincidencias = []
        texto_completo = ""
        
        # Buscar en todas las columnas de texto
        for col in columnas_texto:
            valor = str(row[col]) if pd.notna(row[col]) else ""
            valor_norm = normalizar(valor)
            texto_completo += " " + valor_norm
            
            # Peso según la columna
            peso = 2.0 if col in columnas_principales else 0.5
            
            # Coincidencia exacta de la consulta completa
            if consulta_norm in valor_norm:
                score += 50 * peso
                coincidencias.append(f"{col}: '{consulta}' encontrado (peso {peso})")
            
            # Coincidencia de palabras individuales
            for palabra in palabras:
                if len(palabra) > 2 and palabra in valor_norm:
                    score += 10 * peso
                    coincidencias.append(f"{col}: '{palabra}' encontrado")
        
        # Bonus semántico: si la consulta está en el texto completo
        if consulta_norm in texto_completo:
            score += 30
        
        # Bonus por palabras clave específicas
        palabras_clave_negocio = {
            'construcción': 15,
            'instalación': 15,
            'reparación': 15,
            'mantenimiento': 12,
            'servicio': 10,
            'obra': 12,
            'muro': 10,
            'pared': 10,
            'perimetral': 8,
            'contención': 10,
            'infraestructura': 10
        }
        
        for palabra_clave, peso_extra in palabras_clave_negocio.items():
            if palabra_clave in consulta_norm:
                if palabra_clave in texto_completo:
                    score += peso_extra
        
        # Si tiene puntaje, agregar a resultados
        if score > 0:
            resultados.append({
                'fila': row,
                'score': score,
                'coincidencias': coincidencias,
                'descripcion': row.get('Descripción', 'Sin descripción')
            })
    
    # Ordenar por puntaje
    resultados.sort(key=lambda x: x['score'], reverse=True)
    
    # Devolver DataFrame con los resultados
    if resultados:
        return pd.DataFrame([r['fila'] for r in resultados])
    else:
        return pd.DataFrame()

# =====================================================
# BUSCADOR SEMÁNTICO CON EMBEDDINGS
# =====================================================

@st.cache_data
def cargar_embeddings():
    """Carga los embeddings pre-calculados"""
    try:
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
        return None
    except Exception as e:
        st.warning(f"No se pudieron cargar embeddings: {e}")
        return None

@st.cache_resource
def cargar_modelo():
    """Carga el modelo de SentenceTransformers para embeddings"""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def buscar_semantico(df, consulta, embeddings, modelo):
    """
    Busca usando embeddings semánticos (similitud de coseno)
    """
    from sentence_transformers import util
    import torch
    
    if embeddings is None or modelo is None:
        return []
    
    try:
        # Generar embedding de la consulta
        consulta_embedding = modelo.encode(consulta, convert_to_tensor=True, show_progress_bar=False)
        
        # Calcular similitud de coseno con todos los embeddings
        similitudes = util.cos_sim(consulta_embedding, embeddings)[0]
        
        # Obtener los top 200 resultados
        top_k = min(200, len(similitudes))
        top_scores, top_indices = torch.topk(similitudes, top_k)
        
        resultados = []
        for idx, score in zip(top_indices.cpu().numpy().tolist(), top_scores.cpu().numpy().tolist()):
            if score > 0.3:  # Umbral mínimo de similitud
                fila = df.iloc[idx]
                resultados.append({
                    'fila': fila,
                    'score': float(score) * 100,  # Escalar a porcentaje
                    'descripcion': fila.get('Descripción', 'Sin descripción'),
                    'semantico': True
                })
        
        return resultados
    except Exception as e:
        st.error(f"Error en búsqueda semántica: {e}")
        return []

# =====================================================
# BUSCADOR HÍBRIDO (TEXTO + SEMÁNTICO)
# =====================================================

def buscar_hibrido(df, consulta, embeddings, modelo):
    """
    Combina búsqueda por texto y búsqueda semántica
    """
    # 1. Búsqueda por texto (buscar_en_excel)
    resultados_texto = []
    try:
        df_texto = buscar_en_excel(df, consulta)
        if not df_texto.empty:
            for _, fila in df_texto.iterrows():
                resultados_texto.append({
                    'fila': fila,
                    'score': 100.0,  # Score alto para resultados de texto exacto
                    'descripcion': fila.get('Descripción', 'Sin descripción'),
                    'semantico': False
                })
    except Exception as e:
        pass
    
    # 2. Búsqueda semántica
    resultados_semanticos = buscar_semantico(df, consulta, embeddings, modelo)
    
    # 3. Combinar y deduplicar por código
    resultados_por_codigo = {}
    
    # Agregar resultados de texto
    for r in resultados_texto:
        codigo = r['fila'].get('Código', '')
        if codigo and codigo not in resultados_por_codigo:
            resultados_por_codigo[codigo] = r
    
    # Agregar resultados semánticos (con menor prioridad)
    for r in resultados_semanticos:
        codigo = r['fila'].get('Código', '')
        if codigo and codigo not in resultados_por_codigo:
            # Dar un pequeño bonus a los resultados semánticos si tienen buena similitud
            if r['score'] > 70:
                r['score'] = r['score'] * 0.9
            resultados_por_codigo[codigo] = r
    
    # Convertir a lista y ordenar por score
    resultados = list(resultados_por_codigo.values())
    resultados.sort(key=lambda x: x['score'], reverse=True)
    
    return resultados

# =====================================================
# FUNCIÓN PARA OBTENER JERARQUÍA DESDE SQLITE
# =====================================================

@st.cache_data
def obtener_jerarquia(codigo):
    """Obtiene Segmento, Familia y Clase desde la base de datos SQLite usando el código"""
    if not codigo or codigo == 'No disponible':
        return None, None, None
    
    try:
        conn = sqlite3.connect("db/DGCP_UNSPSC.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT Segmento, Familia, Clase 
            FROM catalogo 
            WHERE "Código UNSPSC" = ?
        """, (codigo,))
        resultado = cur.fetchone()
        conn.close()
        
        if resultado:
            return resultado[0], resultado[1], resultado[2]
        return None, None, None
    except Exception as e:
        return None, None, None

# =====================================================
# MOSTRAR RESULTADO
# =====================================================

def mostrar_resultado(score, fila, rank, es_semantico=False):
    db = DatabaseManager()
    
    # Obtener datos de la fila del Excel
    codigo = str(fila.get('Código', 'No disponible')) if pd.notna(fila.get('Código', 'No disponible')) else 'No disponible'
    descripcion = str(fila.get('Descripción', 'Sin descripción')) if pd.notna(fila.get('Descripción', 'Sin descripción')) else 'Sin descripción'
    definicion = str(fila.get('Definición', '')) if pd.notna(fila.get('Definición', '')) else ''
    sinonimos = str(fila.get('Sinónimos', '')) if pd.notna(fila.get('Sinónimos', '')) else ''
    
    # Buscar Segmento, Familia, Clase desde la base de datos SQLite usando el código
    segmento, familia, clase = obtener_jerarquia(codigo)
    
    # Etiqueta de tipo de búsqueda
    etiqueta = "🔍 Semántica" if es_semantico else "📌 Exacta"
    
    titulo = f"{etiqueta} | {score:.0f}% | {codigo} | {descripcion[:50]}..."
    
    with st.expander(titulo):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**📋 Código:**", codigo)
            st.write("**📝 Descripción:**", descripcion)
            if definicion and definicion != 'nan':
                st.write("**📖 Definición:**", definicion)
            if sinonimos and sinonimos != 'nan':
                st.write("**🔗 Sinónimos:**", sinonimos)
            st.write("**📂 Segmento:**", segmento if segmento else "No disponible")
            st.write("**📁 Familia:**", familia if familia else "No disponible")
            st.write("**📄 Clase:**", clase if clase else "No disponible")
            if es_semantico:
                st.caption("🔍 Este resultado fue encontrado por similitud semántica")
        
        with col2:
            st.write("**💰 Clasificación DIGEPRES**")
            try:
                # Buscar DIGEPRES por código
                cuenta, descripcion_cuenta, fuente, confianza = db.obtener_digepres(
                    codigo[:2] if codigo != 'No disponible' and len(codigo) >= 2 else "",
                    descripcion_item=descripcion
                )
                
                if cuenta:
                    st.success(f"**Cuenta:** {cuenta}")
                    if descripcion_cuenta:
                        st.write(f"**Descripción:** {descripcion_cuenta}")
                    st.caption(f"🔍 Fuente: {fuente or 'N/A'} | Confianza: {confianza:.0%}")
                else:
                    st.warning("Sin clasificación DIGEPRES asignada")
            except Exception as e:
                st.warning("Sin clasificación DIGEPRES asignada")
                st.caption(f"⚠️ Error: {e}")

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
    # DETECTAR CLICK EN EL LOGO (RESET)
    # =====================================================
    try:
        query_params = st.query_params
        if query_params.get("reset") == "true":
            st.session_state.consulta = ""
            st.session_state.resultados = []
            st.session_state.sinonimos = []
            st.session_state.tipo_busqueda = "texto"
            st.session_state.pagina_actual = 1
            st.session_state.ultima_busqueda = ""
            st.session_state.search_time_ms = 0
            st.session_state.consulta_input = ""
            st.query_params.clear()
            st.rerun()
    except AttributeError:
        try:
            query_params = st.experimental_get_query_params()
            if query_params.get("reset", [""])[0] == "true":
                st.session_state.consulta = ""
                st.session_state.resultados = []
                st.session_state.sinonimos = []
                st.session_state.tipo_busqueda = "texto"
                st.session_state.pagina_actual = 1
                st.session_state.ultima_busqueda = ""
                st.session_state.search_time_ms = 0
                st.session_state.consulta_input = ""
                st.experimental_set_query_params()
                st.rerun()
        except:
            pass

    # =====================================================
    # SIDEBAR
    # =====================================================
    with st.sidebar:
        # Logo
        try:
            logo_url = "https://raw.githubusercontent.com/cybersolushop-star/UNSPSC_DGCP_Expert/6df141cc0e6021de921153b1d343128bc6e35290/data/logo.png"
            st.markdown(f"""
            <div class="sidebar-logo-container" onclick="window.location.href = window.location.pathname + '?reset=true';">
                <div class="sidebar-logo-wrapper">
                    <img src="{logo_url}" alt="Logo UNSPSC DGCP - Ir al inicio">
                </div>
                <div class="sidebar-logo-title">🏠 Buscador de Bienes y Servicios</div>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown("### 🔎 UNSPSC DGCP")
        
        st.divider()
        st.header("📂 Filtros")
        
        # Cargar catálogo desde Excel
        df_catalogo = cargar_catalogo_excel()
        
        if not df_catalogo.empty:
            st.session_state.df_catalogo_excel = df_catalogo
            st.session_state.df_filtrado = df_catalogo
            st.caption(f"📊 {len(df_catalogo)} ítems disponibles")
        else:
            # Fallback a SQLite
            df_catalogo = cargar_catalogo()
            if not df_catalogo.empty:
                st.session_state.df_filtrado = df_catalogo
                st.caption(f"📊 {len(df_catalogo)} ítems disponibles (SQLite)")
            else:
                st.warning("⚠️ No se pudo cargar el catálogo")
                st.session_state.df_filtrado = pd.DataFrame()
        
        st.divider()
        
        # Opción para usar búsqueda semántica
        usar_semantica = st.checkbox("🧠 Usar búsqueda semántica", value=True, 
                                       help="Permite encontrar ítems relacionados por significado, no solo por palabras exactas")
        
        st.divider()
        if st.button("🧹 Limpiar Búsqueda", use_container_width=True):
            st.session_state.consulta = ""
            st.session_state.resultados = []
            st.session_state.sinonimos = []
            st.session_state.tipo_busqueda = "texto"
            st.session_state.pagina_actual = 1
            st.session_state.ultima_busqueda = ""
            st.session_state.search_time_ms = 0
            st.session_state.consulta_input = ""
            st.rerun()
        
        st.divider()
        st.caption("🔎 UNSPSC DGCP Expert v2.0")

    # =====================================================
    # ENCABEZADO
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
        placeholder="Ej: Construcción de verja perimetral, perro, computadora, 10101502, 2.3.9.4.01...",
        key="consulta_input"
    )

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
                    df = cargar_catalogo_excel()
                    if df.empty:
                        df = cargar_catalogo()
                
                if df is not None and not df.empty:
                    # Verificar si es búsqueda por código
                    if es_busqueda_por_codigo(consulta):
                        resultados_codigo = buscar_por_codigo(df, consulta)
                        if not resultados_codigo.empty:
                            resultados = []
                            for _, fila in resultados_codigo.iterrows():
                                resultados.append((100.0, True, fila, False))
                            st.session_state.resultados = resultados
                            st.session_state.tipo_busqueda = "código"
                        else:
                            st.session_state.resultados = []
                    else:
                        # Verificar si el usuario quiere usar búsqueda semántica
                        if usar_semantica:
                            # Cargar embeddings y modelo
                            embeddings = cargar_embeddings()
                            modelo = cargar_modelo()
                            
                            if embeddings is not None and modelo is not None:
                                # Búsqueda híbrida
                                resultados_hibridos = buscar_hibrido(df, consulta, embeddings, modelo)
                                if resultados_hibridos:
                                    resultados = []
                                    for r in resultados_hibridos:
                                        fila = r['fila']
                                        score = r['score']
                                        es_semantico = r.get('semantico', False)
                                        resultados.append((score, True, fila, es_semantico))
                                    st.session_state.resultados = resultados
                                    st.session_state.tipo_busqueda = "hibrida"
                                else:
                                    st.session_state.resultados = []
                            else:
                                # Fallback a búsqueda en Excel
                                resultados_df = buscar_en_excel(df, consulta)
                                if not resultados_df.empty:
                                    resultados = []
                                    for _, fila in resultados_df.iterrows():
                                        resultados.append((100.0, True, fila, False))
                                    st.session_state.resultados = resultados
                                    st.session_state.tipo_busqueda = "excel"
                                else:
                                    st.session_state.resultados = []
                        else:
                            # Solo búsqueda en Excel
                            resultados_df = buscar_en_excel(df, consulta)
                            if not resultados_df.empty:
                                resultados = []
                                for _, fila in resultados_df.iterrows():
                                    resultados.append((100.0, True, fila, False))
                                st.session_state.resultados = resultados
                                st.session_state.tipo_busqueda = "excel"
                            else:
                                st.session_state.resultados = []
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
        st.session_state.ultima_busqueda = ""

    # =====================================================
    # MOSTRAR RESULTADOS
    # =====================================================
    resultados = st.session_state.resultados

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
        
        # Exportar
        col_export, col_empty = st.columns([1, 5])
        with col_export:
            export_data = []
            for score, exacto, fila, es_semantico in resultados:
                export_data.append({
                    "Tipo": "Semántico" if es_semantico else "Exacta",
                    "Score": round(score, 2),
                    "Código": fila.get("Código", ""),
                    "Descripción": fila.get("Descripción", ""),
                    "Sinónimos": fila.get("Sinónimos", ""),
                    "Segmento": fila.get("Segmento", ""),
                    "Familia": fila.get("Familia", ""),
                    "Clase": fila.get("Clase", "")
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
        
        # Paginación
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
                st.markdown(f"<p style='text-align:center;color:#6b7280;'>Página {st.session_state.pagina_actual} de {total_paginas}</p>", unsafe_allow_html=True)
            with col_next:
                if st.button("Siguiente ▶", use_container_width=True, key="next_top"):
                    if st.session_state.pagina_actual < total_paginas:
                        st.session_state.pagina_actual += 1
        
        rank = inicio + 1
        for score, exacto, fila, es_semantico in resultados_pagina:
            mostrar_resultado(score, fila, rank, es_semantico)
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
