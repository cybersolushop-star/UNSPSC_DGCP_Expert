import streamlit as st
import sqlite3
import pandas as pd
import unicodedata
import time

from io import BytesIO
from datetime import datetime
from pathlib import Path

from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer, util

# =====================================================
# CONFIG
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "db" / "DGCP_UNSPSC.db"

SEMANTIC_WEIGHT = 0.70
FUZZY_WEIGHT = 0.30
MIN_SCORE = 45

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="UNSPSC DGCP Expert",
    page_icon="🔎",
    layout="wide"
)

# =====================================================
# NORMALIZACION
# =====================================================

def normalizar(texto):
    texto = str(texto)
    texto = texto.lower().strip()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return texto

# =====================================================
# MODELO IA
# =====================================================

@st.cache_resource
def cargar_modelo():
    return SentenceTransformer(
        "paraphrase-multilingual-MiniLM-L12-v2"
    )

# =====================================================
# CATALOGO
# =====================================================

@st.cache_data
def cargar_catalogo():
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql("SELECT * FROM catalogo", conn)

    df = df.drop_duplicates(subset=["Código UNSPSC"])

    df["texto_busqueda"] = (
        df["Descripción"].fillna("") + " " +
        df["Definición"].fillna("") + " " +
        df["Segmento"].fillna("") + " " +
        df["Familia"].fillna("") + " " +
        df["Clase"].fillna("")
    )

    df["texto_busqueda"] = (
        df["texto_busqueda"]
        .astype(str)
        .apply(normalizar)
    )

    return df

# =====================================================
# SINONIMOS
# =====================================================

@st.cache_data
def cargar_sinonimos():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            df = pd.read_sql(
                "SELECT termino, sinonimo FROM sinonimos",
                conn
            )

        diccionario = {}

        for _, fila in df.iterrows():
            termino = normalizar(fila["termino"])
            sinonimo = normalizar(fila["sinonimo"])

            diccionario.setdefault(
                termino,
                []
            ).append(sinonimo)

        return diccionario

    except Exception:
        return {}

# =====================================================
# EMBEDDINGS
# =====================================================

import torch

@st.cache_resource
def cargar_embeddings():

    archivo = BASE_DIR / "db" / "embeddings.pt"

    return torch.load(
        archivo,
        map_location="cpu"
    )

# =====================================================
# RAPIDFUZZ
# =====================================================

def fuzzy_score(a, b):
    s1 = fuzz.token_set_ratio(a, b)
    s2 = fuzz.token_sort_ratio(a, b)
    s3 = fuzz.partial_ratio(a, b)
    return max(s1, s2, s3)

# =====================================================
# LOG
# =====================================================

def registrar_busqueda(consulta, cantidad):
    try:
        with sqlite3.connect(DB_FILE) as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS consultas(
                    id INTEGER PRIMARY KEY,
                    fecha TEXT,
                    consulta TEXT,
                    resultados INTEGER
                )
            """)

            conn.execute("""
                INSERT INTO consultas
                (fecha, consulta, resultados)
                VALUES (?, ?, ?)
            """, (
                datetime.now().isoformat(),
                consulta,
                cantidad
            ))

            conn.commit()

    except Exception:
        pass

# =====================================================
# EXPORTAR EXCEL
# =====================================================

def generar_excel(df):
    salida = BytesIO()

    with pd.ExcelWriter(
        salida,
        engine="openpyxl"
    ) as writer:
        df.to_excel(
            writer,
            index=False
        )

    return salida.getvalue()

# =====================================================
# BUSQUEDA HIBRIDA
# =====================================================

def buscar_hibrido(
    df,
    embeddings_catalogo,
    consulta,
    sinonimos
):

    modelo = cargar_modelo()

    consulta_norm = normalizar(consulta)

    terminos = [consulta_norm]
    terminos.extend(sinonimos)

    mejor_similitud = None

    for termino in terminos:

        emb = modelo.encode(
            termino,
            convert_to_tensor=True,
            show_progress_bar=False
        )

        similitud = util.cos_sim(
            emb,
            embeddings_catalogo
        )[0]

        if mejor_similitud is None:
            mejor_similitud = similitud
        else:
            mejor_similitud = mejor_similitud.maximum(
                similitud
            )

    similitudes = (
        mejor_similitud
        .cpu()
        .numpy()
    )

    resultados = []

    for idx, fila in df.iterrows():

        texto = fila["texto_busqueda"]

        fuzzy = fuzzy_score(
            consulta_norm,
            texto
        )

        semantico = float(
            similitudes[idx]
        ) * 100

        score = (
            SEMANTIC_WEIGHT * semantico +
            FUZZY_WEIGHT * fuzzy
        )

        if score >= MIN_SCORE:
            resultados.append(
                (score, fila)
            )

    resultados.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    return resultados[:50]

# =====================================================
# TITULO
# =====================================================

st.title("🔎 UNSPSC DGCP Expert")
st.write("Catálogo Oficial de Bienes y Servicios DGCP")

# =====================================================
# CARGA DATOS
# =====================================================

catalogo = cargar_catalogo()
dic_sinonimos = cargar_sinonimos()

with st.spinner(
    "Cargando embeddings..."
):

    embeddings_catalogo = (
        cargar_embeddings()
    )

# =====================================================
# FILTROS
# =====================================================

st.sidebar.header("Filtros")

segmentos = sorted(
    catalogo["Segmento"]
    .dropna()
    .unique()
)

segmento = st.sidebar.selectbox(
    "Segmento",
    ["Todos"] + list(segmentos)
)

if segmento != "Todos":
    catalogo = catalogo[
        catalogo["Segmento"] == segmento
    ]

familias = sorted(
    catalogo["Familia"]
    .dropna()
    .unique()
)

familia = st.sidebar.selectbox(
    "Familia",
    ["Todas"] + list(familias)
)

if familia != "Todas":
    catalogo = catalogo[
        catalogo["Familia"] == familia
    ]

clases = sorted(
    catalogo["Clase"]
    .dropna()
    .unique()
)

clase = st.sidebar.selectbox(
    "Clase",
    ["Todas"] + list(clases)
)

if clase != "Todas":
    catalogo = catalogo[
        catalogo["Clase"] == clase
    ]

# =====================================================
# BUSQUEDA
# =====================================================

consulta = st.text_input(
    "Describa el bien o servicio:"
)

if consulta:

    inicio = time.time()

    consulta_norm = normalizar(
        consulta
    )

    sinonimos = dic_sinonimos.get(
        consulta_norm,
        []
    )

    if sinonimos:
        st.info(
            "Sinónimos detectados: " +
            ", ".join(sinonimos)
        )

    resultados = buscar_hibrido(
        catalogo,
        embeddings_catalogo,
        consulta,
        sinonimos
    )

    registrar_busqueda(
        consulta,
        len(resultados)
    )

    tiempo = round(
        time.time() - inicio,
        2
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Resultados",
        len(resultados)
    )

    c2.metric(
        "Sinónimos",
        len(sinonimos)
    )

    c3.metric(
        "Tiempo (s)",
        tiempo
    )

    exportar = []

    for score, fila in resultados:
        exportar.append({
            "Score": round(score, 2),
            "Código UNSPSC": fila["Código UNSPSC"],
            "Descripción": fila["Descripción"],
            "Definición": fila["Definición"],
            "Segmento": fila["Segmento"],
            "Familia": fila["Familia"],
            "Clase": fila["Clase"]
        })

    df_exportar = pd.DataFrame(
        exportar
    )

    if not df_exportar.empty:

        archivo = generar_excel(
            df_exportar
        )

        st.download_button(
            "📥 Exportar Excel",
            archivo,
            file_name="resultados_unspsc.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.subheader(
        f"Resultados encontrados: {len(resultados)}"
    )

    for score, fila in resultados:

        with st.expander(
            f"{score:.0f}% | {fila['Código UNSPSC']} | {fila['Descripción']}"
        ):

            st.write("**Código:**", fila["Código UNSPSC"])
            st.write("**Descripción:**", fila["Descripción"])
            st.write("**Definición:**", fila["Definición"])
            st.write("**Segmento:**", fila["Segmento"])
            st.write("**Familia:**", fila["Familia"])
            st.write("**Clase:**", fila["Clase"])
            st.write("**Versión:**", fila["Fecha Versión"])
