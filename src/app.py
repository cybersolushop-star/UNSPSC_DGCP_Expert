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
        /* Barra de búsqueda */
        .search-container {
            max-width: 896px;
            margin: 16px auto 8px auto;
            padding: 0 16px;
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
            padding-right: 16px;
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
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }
        .search-btn:hover {
            box-shadow: 0 4px 12px rgba(26, 82, 118, 0.3);
            transform: translateY(-1px);
        }
        .search-btn svg {
            width: 20px;
            height: 20px;
        }
        
        /* Ocultar el filtro de nivel "Todos" */
        .filter-container {
            display: none !important;
        }
        
        /* Ajustes generales */
        .main-header {
            text-align: center;
            padding: 20px 0 10px 0;
        }
        .main-header h1 {
            color: #1a5276;
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
        }
        .main-header p {
            color: #5d6d7e;
            font-size: 1.1rem;
            margin: 4px 0 0 0;
        }
        .main-header .credits {
            color: #5d6d7e;
            font-size: 0.9rem;
            font-style: italic;
            margin: 4px 0 0 0;
        }
        
        /* Resultados */
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
        
        /* Métricas */
        .metrics-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            max-width: 1280px;
            margin: 16px auto;
            padding: 0 16px;
        }
        .metric-card {
            background: white;
            border-radius: 8px;
            padding: 12px 16px;
            border: 1px solid #e8e8e8;
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
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 20px 16px;
            border-top: 1px solid #e8e8e8;
            margin-top: 24px;
            color: #6b7280;
            font-size: 14px;
        }
        
        /* Ajustes de formulario */
        .stForm {
            padding: 0 !important;
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
# MOSTRAR RESULTADO
# =====================================================

def mostrar_resultado(score, fila, rank):
    db = DatabaseManager()
    cuenta, descripcion, fuente, confianza = db.obtener_digepres(
        fila["Código Familia"],
        descripcion_item=fila["Descripción"]
    )
    
    html = f"""
    <div class="result-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:14px;color:#6b7280;">Código: <strong>{fila['Código UNSPSC']}</strong></span>
            <span style="background:#1a5276;color:white;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-weight:bold;">{rank}</span>
        </div>
        <div class="title">{fila['Descripción']}</div>
        <div class="hierarchy">
            <div><span class="label">Segmento:</span> {fila['Segmento']}</div>
            <div><span class="label">Familia:</span> {fila['Familia']}</div>
            <div><span class="label">Clase:</span> {fila['Clase']}</div>
        </div>
        <div class="digepres">
            <div><span class="label">💰 Clasificación DIGEPRES</span></div>
            <div><span class="label">Cuenta:</span> {cuenta if cuenta else 'No asignada'}</div>
            <div><span class="label">Descripción:</span> {descripcion if descripcion else 'Sin descripción'}</div>
            <div style="font-size:12px;color:#6b7280;margin-top:4px;">Confianza: {int(score)}% | Score: {score:.1f}</div>
        </div>
        <div style="font-size:14px;color:#4a4a4a;margin-top:8px;font-style:italic;">
            {fila.get('Definición', 'No hay definición disponible')[:200]}{'...' if len(str(fila.get('Definición', ''))) > 200 else ''}
        </div>
        <div style="margin-top:8px;font-size:12px;color:#6b7280;">
            Versión: {fila.get('Fecha Versión', 'No disponible')}
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

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
# ENCABEZADO
# =====================================================

st.markdown("""
<div class="main-header">
    <h1>🔎 BUSCADOR UNSPSC DGCP</h1>
    <p>Catálogo de Bienes y Servicios DGCP</p>
    <p class="credits">por Rudy Pérez</p>
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
# BARRA DE BÚSQUEDA CON st.form (FUNCIONAL)
# =====================================================

with st.form(key="search_form", clear_on_submit=False):
    col1, col2 = st.columns([5, 1])
    
    with col1:
        consulta = st.text_input(
            "Buscar",
            value=st.session_state.consulta,
            placeholder="Buscar productos por nombre, código o descripción...",
            key="search_input",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Espaciado para alinear
        submitted = st.form_submit_button("🔍 Buscar", use_container_width=True)

# Actualizar consulta si se envió el formulario
if submitted and consulta:
    st.session_state.consulta = consulta
    st.session_state.ultima_busqueda = consulta
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

# Si no hay consulta, limpiar resultados
elif not consulta:
    st.session_state.resultados = []
    st.session_state.sinonimos = []

# =====================================================
# MOSTRAR RESULTADOS
# =====================================================

resultados = st.session_state.resultados
sinonimos = st.session_state.sinonimos
tipo_busqueda = st.session_state.get("tipo_busqueda", "texto")
search_time_ms = st.session_state.get("search_time_ms", 0)

if resultados:
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📊 Resultados", len(resultados))
    col2.metric("🔍 Método", "Híbrido")
    col3.metric("🔗 Sinónimos", len(sinonimos))
    col4.metric("⏱️ Tiempo", f"{search_time_ms:.0f} ms" if search_time_ms > 0 else "< 100 ms")
    
    # Exportar
    if st.button("📥 Exportar a Excel"):
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
    
    st.subheader(f"📋 Resultados encontrados: {len(resultados)}")
    
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
    
    # Controles de paginación
    if total_paginas > 1:
        col_prev, col_info, col_next = st.columns([1, 3, 1])
        with col_prev:
            if st.button("◀ Anterior", use_container_width=True):
                if st.session_state.pagina_actual > 1:
                    st.session_state.pagina_actual -= 1
        with col_info:
            st.write(f"Página {st.session_state.pagina_actual} de {total_paginas} (mostrando {len(resultados_pagina)} de {total_items} ítems)")
        with col_next:
            if st.button("Siguiente ▶", use_container_width=True):
                if st.session_state.pagina_actual < total_paginas:
                    st.session_state.pagina_actual += 1
    
    # Mostrar resultados
    rank = inicio + 1
    for score, exacto, fila in resultados_pagina:
        mostrar_resultado(score, fila, rank)
        rank += 1
    
    # Controles de paginación abajo
    if total_paginas > 1:
        st.divider()
        col_prev, col_info, col_next = st.columns([1, 3, 1])
        with col_prev:
            if st.button("◀ Anterior", use_container_width=True):
                if st.session_state.pagina_actual > 1:
                    st.session_state.pagina_actual -= 1
        with col_info:
            st.write(f"Página {st.session_state.pagina_actual} de {total_paginas}")
        with col_next:
            if st.button("Siguiente ▶", use_container_width=True):
                if st.session_state.pagina_actual < total_paginas:
                    st.session_state.pagina_actual += 1

elif consulta:
    st.info("ℹ️ No se encontraron resultados para esta búsqueda.")
    st.caption("Sugerencias: prueba con sinónimos o términos más generales.")

# =====================================================
# FOOTER
# =====================================================

st.markdown("""
<div class="footer">
    © 2026, todos los derechos reservados. | BUSCADOR UNSPSC DGCP
</div>
""", unsafe_allow_html=True)