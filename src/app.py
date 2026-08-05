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

# Importar DatabaseManager desde database
from database import DatabaseManager

# Configuración de la página
st.set_page_config(
    page_title="UNSPSC DGCP BUSCADOR",
    page_icon="🔎",
    layout="wide"
)

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
            # Asegurar que las columnas sean strings
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
# BUSCADOR HÍBRIDO OPTIMIZADO
# =====================================================

def buscar_hibrido(df, embeddings, consulta, sinonimos):
    from rapidfuzz import fuzz
    from sentence_transformers import util
    import torch
    
    modelo = cargar_modelo()
    
    consulta_norm = normalizar(consulta)
    terminos = [consulta_norm] + sinonimos
    
    emb_consulta = modelo.encode(consulta_norm, convert_to_tensor=True, show_progress_bar=False)
    
    if not isinstance(embeddings, torch.Tensor):
        embeddings = torch.tensor(embeddings)
    
    similitudes = util.cos_sim(emb_consulta, embeddings)[0]
    
    top_k = min(200, len(similitudes))
    top_scores, top_indices = torch.topk(similitudes, top_k)
    
    top_indices_list = top_indices.cpu().numpy().tolist()
    top_scores_list = top_scores.cpu().numpy().tolist()
    
    resultados = []
    for idx, sem_score in zip(top_indices_list, top_scores_list):
        fila = df.iloc[idx]
        desc = normalizar(fila["Descripción"])
        contexto = normalizar(f"{fila['Segmento']} {fila['Familia']} {fila['Clase']}")
        
        fuzzy_desc = 0
        fuzzy_ctx = 0
        for t in terminos:
            fs = fuzz.token_set_ratio(t, desc)
            if fs > fuzzy_desc:
                fuzzy_desc = fs
            fc = fuzz.token_set_ratio(t, contexto)
            if fc > fuzzy_ctx:
                fuzzy_ctx = fc
        
        fuzzy = (fuzzy_desc * 0.7) + (fuzzy_ctx * 0.3)
        semantico = float(sem_score) * 100
        score = (semantico * 0.3) + (fuzzy * 0.7)
        
        exacto = any(t in desc for t in terminos)
        
        if score >= 55 or exacto:
            resultados.append((score, exacto, fila))
    
    if len(resultados) < 10:
        top_indices_set = set(top_indices_list)
        for idx, fila in df.iterrows():
            if idx in top_indices_set:
                continue
            desc = normalizar(fila["Descripción"])
            fuzzy_desc = 0
            for t in terminos:
                fs = fuzz.token_set_ratio(t, desc)
                if fs > fuzzy_desc:
                    fuzzy_desc = fs
            if fuzzy_desc > 60:
                resultados.append((fuzzy_desc, False, fila))
    
    resultados.sort(key=lambda x: (-x[1], -x[0]))
    return resultados[:200]  # Limitamos a 200 para no sobrecargar la paginación

# =====================================================
# MOSTRAR RESULTADO
# =====================================================

def mostrar_resultado(score, fila, tipo_busqueda="texto"):
    db = DatabaseManager()
    cuenta, descripcion, fuente, confianza = db.obtener_digepres(
        fila["Código Familia"],
        descripcion_item=fila["Descripción"]
    )
    
    if tipo_busqueda == "código":
        etiqueta = "🎯 Coincidencia por código"
    elif tipo_busqueda == "cuenta":
        etiqueta = "💰 Coincidencia por cuenta DIGEPRES"
    else:
        etiqueta = ""
    
    titulo = f"{score:.0f}% | {fila['Código UNSPSC']} | {fila['Descripción']}"
    if etiqueta:
        titulo = f"{etiqueta} - {titulo}"
    
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
# PAGINACIÓN
# =====================================================

def paginar_resultados(resultados, pagina, items_por_pagina=20):
    """
    Divide los resultados en páginas.
    """
    total_items = len(resultados)
    total_paginas = (total_items + items_por_pagina - 1) // items_por_pagina
    
    if pagina < 1:
        pagina = 1
    if pagina > total_paginas and total_paginas > 0:
        pagina = total_paginas
    
    inicio = (pagina - 1) * items_por_pagina
    fin = min(inicio + items_por_pagina, total_items)
    
    return resultados[inicio:fin], total_paginas, pagina

# =====================================================
# INTERFAZ PRINCIPAL
# =====================================================

st.title("🔎 BUSCADOR UNSPSC DGCP")
st.caption("Catálogo Oficial de Bienes y Servicios DGCP")
st.markdown("*por Rudy Pérez*")

# =====================================================
# SIDEBAR - FILTROS CON BOTÓN LIMPIAR
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
    
    # =====================================================
    # BOTÓN LIMPIAR
    # =====================================================
    st.divider()
    if st.button("🧹 Limpiar Búsqueda", use_container_width=True):
        st.session_state.consulta = ""
        st.session_state.resultados = []
        st.session_state.sinonimos = []
        st.session_state.tipo_busqueda = "texto"
        st.session_state.pagina_actual = 1
        st.rerun()
    
    st.divider()
    st.caption("🔎 UNSPSC DGCP Expert v2.0")

# =====================================================
# ÁREA PRINCIPAL - BÚSQUEDA
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

# Barra de búsqueda
consulta = st.text_input(
    "🔎 Describa el bien o servicio, ingrese un código UNSPSC o una cuenta DIGEPRES (ej: 2.3.9.4.01):",
    value=st.session_state.consulta,
    placeholder="Ej: perro, computadora, 10101502, 25101503, 2.3.9.4.01...",
    key="input_busqueda"
)

# Ejecutar búsqueda (si hay consulta y es diferente a la anterior)
if consulta and consulta != st.session_state.consulta:
    st.session_state.consulta = consulta
    st.session_state.pagina_actual = 1  # Resetear página al hacer nueva búsqueda
    
    with st.spinner("🔍 Buscando..."):
        try:
            df = st.session_state.df_filtrado
            if df.empty:
                df = cargar_catalogo()
            
            if df is not None and not df.empty:
                if es_busqueda_por_cuenta(consulta):
                    # Búsqueda por cuenta DIGEPRES (usando catalogo_final.csv)
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
                                    # Si no está en el catálogo, usar los datos del CSV
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
                    # Búsqueda por código UNSPSC
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
                    # Búsqueda híbrida por texto
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

# Si no hay consulta, limpiar resultados
elif not consulta:
    st.session_state.resultados = []
    st.session_state.sinonimos = []

# =====================================================
# MOSTRAR RESULTADOS CON PAGINACIÓN (CORREGIDA)
# =====================================================

resultados = st.session_state.resultados
sinonimos = st.session_state.sinonimos
tipo_busqueda = st.session_state.get("tipo_busqueda", "texto")

if resultados:
    # Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("📊 Resultados", len(resultados))
    
    if tipo_busqueda == "código":
        c2.metric("🔢 Tipo", "Búsqueda por código")
    elif tipo_busqueda == "cuenta":
        c2.metric("💰 Tipo", "Búsqueda por cuenta DIGEPRES")
    else:
        c2.metric("🔗 Sinónimos", len(sinonimos))
    c3.metric("⏱️ Tiempo", "< 1s")
    
    # Exportar (si hay resultados)
    col_export, col_empty = st.columns([1, 5])
    with col_export:
        if st.button("📥 Exportar a Excel", use_container_width=True):
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
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    st.subheader(f"📋 Resultados encontrados: {len(resultados)}")
    
    # =====================================================
    # PAGINACIÓN (CORREGIDA - SIN st.rerun())
    # =====================================================
    items_por_pagina = 20
    total_items = len(resultados)
    total_paginas = (total_items + items_por_pagina - 1) // items_por_pagina
    
    # Asegurar que la página actual sea válida
    if st.session_state.pagina_actual < 1:
        st.session_state.pagina_actual = 1
    if st.session_state.pagina_actual > total_paginas and total_paginas > 0:
        st.session_state.pagina_actual = total_paginas
    
    # Obtener los resultados de la página actual
    inicio = (st.session_state.pagina_actual - 1) * items_por_pagina
    fin = min(inicio + items_por_pagina, total_items)
    resultados_pagina = resultados[inicio:fin]
    
    # Controles de paginación (arriba) - SIN st.rerun()
    if total_paginas > 1:
        col_prev, col_info, col_next = st.columns([1, 3, 1])
        
        with col_prev:
            if st.button("◀ Anterior", use_container_width=True, key="prev_top"):
                if st.session_state.pagina_actual > 1:
                    st.session_state.pagina_actual -= 1
        
        with col_info:
            st.markdown(f"<div style='text-align: center;'>Página {st.session_state.pagina_actual} de {total_paginas} (mostrando {len(resultados_pagina)} de {total_items} ítems)</div>", unsafe_allow_html=True)
        
        with col_next:
            if st.button("Siguiente ▶", use_container_width=True, key="next_top"):
                if st.session_state.pagina_actual < total_paginas:
                    st.session_state.pagina_actual += 1
    
    # Mostrar resultados de la página actual
    exactos = [r for r in resultados_pagina if r[1]]
    relacionados = [r for r in resultados_pagina if not r[1]]
    
    if exactos:
        st.markdown("### 🎯 Coincidencias exactas")
        for score, _, fila in exactos:
            mostrar_resultado(score, fila, tipo_busqueda)
    
    if relacionados:
        st.markdown("### 🔍 Resultados relacionados")
        for score, _, fila in relacionados:
            mostrar_resultado(score, fila, tipo_busqueda)
    
    # Controles de paginación (abajo) - SIN st.rerun()
    if total_paginas > 1:
        st.divider()
        col_prev, col_info, col_next = st.columns([1, 3, 1])
        
        with col_prev:
            if st.button("◀ Anterior", use_container_width=True, key="prev_bottom"):
                if st.session_state.pagina_actual > 1:
                    st.session_state.pagina_actual -= 1
        
        with col_info:
            st.markdown(f"<div style='text-align: center;'>Página {st.session_state.pagina_actual} de {total_paginas}</div>", unsafe_allow_html=True)
        
        with col_next:
            if st.button("Siguiente ▶", use_container_width=True, key="next_bottom"):
                if st.session_state.pagina_actual < total_paginas:
                    st.session_state.pagina_actual += 1

elif consulta:
    st.info("ℹ️ No se encontraron resultados para esta búsqueda.")
    st.caption("Sugerencias: prueba con sinónimos o términos más generales.")