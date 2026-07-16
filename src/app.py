import streamlit as st
import sqlite3
import pandas as pd
import unicodedata
import re
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

SEMANTIC_WEIGHT = 0.20
FUZZY_WEIGHT = 0.80
MIN_SCORE = 70

# Pesos internos del fuzzy: la Descripción pesa mucho más que
# Segmento/Familia/Clase/Definición (contexto), para que categorías
# generales no le ganen al ítem exacto.
PESO_DESCRIPCION = 0.75
PESO_CONTEXTO = 0.25

# Umbral de fuzzy sobre la Descripción para considerar "exacto" aunque
# no haya coincidencia literal de palabra completa (respaldo).
UMBRAL_FUZZY_EXACTO = 95

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="UNSPSC DGCP BUSCADOR",
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
    texto = re.sub(r"\s+", " ", texto)
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

    # OJO: no usar reset_index aquí. Los embeddings en embeddings.pt
    # fueron generados en el mismo orden que "SELECT * FROM catalogo"
    # (ver generar_embeddings.py). drop_duplicates conserva las
    # etiquetas de índice originales, así que la posición sigue
    # coincidiendo con el vector correspondiente en embeddings.pt.
    df = df.drop_duplicates(subset=["Código UNSPSC"])

    # Descripción normalizada por separado: es el campo más importante
    # para decidir si una fila es "el ítem exacto".
    df["descripcion_norm"] = (
        df["Descripción"]
        .fillna("")
        .astype(str)
        .apply(normalizar)
    )

    # Contexto = todo lo demás. Sirve de apoyo, pero pesa menos.
    df["contexto_norm"] = (
        df["Definición"].fillna("") + " " +
        df["Segmento"].fillna("") + " " +
        df["Familia"].fillna("") + " " +
        df["Clase"].fillna("")
    )

    df["contexto_norm"] = (
        df["contexto_norm"]
        .astype(str)
        .apply(normalizar)
    )

    return df

# =====================================================
# SINONIMOS
# =====================================================

@st.cache_data
def cargar_sinonimos():
    """
    Construye un diccionario BIDIRECCIONAL de términos relacionados.

    La tabla 'sinonimos' guarda filas (termino, sinonimo, capa), por
    ejemplo ("automovil", "carro", 3). Si sólo se indexa por 'termino'
    (como antes), buscar "carro" nunca encuentra nada, porque "carro"
    jamás es una llave del diccionario, sólo un valor.

    Aquí se agregan ambas direcciones: termino -> sinonimo y
    sinonimo -> termino, para que buscar por cualquiera de los dos
    términos encuentre al otro (y a sus hermanos).
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            df = pd.read_sql(
                "SELECT termino, sinonimo, capa FROM sinonimos",
                conn
            )
    except Exception:
        try:
            with sqlite3.connect(DB_FILE) as conn:
                df = pd.read_sql(
                    "SELECT termino, sinonimo FROM sinonimos",
                    conn
                )
            df["capa"] = 1
        except Exception:
            return {}

    diccionario = {}

    def agregar(clave, valor, capa):
        clave = normalizar(clave)
        valor = normalizar(valor)

        if not clave or not valor or clave == valor:
            return

        lista = diccionario.setdefault(clave, [])

        if not any(v == valor for v, _ in lista):
            lista.append((valor, capa))

    for _, fila in df.iterrows():
        termino = fila["termino"]
        sinonimo = fila["sinonimo"]

        try:
            capa = int(fila["capa"]) if pd.notna(fila["capa"]) else 1
        except Exception:
            capa = 1

        agregar(termino, sinonimo, capa)
        agregar(sinonimo, termino, capa)

    # Dentro de cada llave, ordenar por capa (menor capa = relación
    # más fuerte / oficial primero).
    for clave in diccionario:
        diccionario[clave].sort(key=lambda x: x[1])

    return diccionario

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
    if not a or not b:
        return 0
    s1 = fuzz.token_set_ratio(a, b)
    s2 = fuzz.token_sort_ratio(a, b)
    s3 = fuzz.partial_ratio(a, b)
    return max(s1, s2, s3)

# =====================================================
# COINCIDENCIA EXACTA
# =====================================================

def coincide_termino(termino, texto):
    """
    True si 'termino' aparece como palabra/frase completa dentro de
    'texto' (contempla plurales simples: carro/carros,
    automovil/automoviles).
    """
    if not termino or not texto:
        return False

    variantes = {termino, termino + "s", termino + "es"}

    for variante in variantes:
        patron = r"(?<!\w)" + re.escape(variante) + r"(?!\w)"
        if re.search(patron, texto):
            return True

    return False


def es_coincidencia_exacta(terminos, descripcion_norm, fuzzy_desc_max):
    for termino in terminos:
        termino = termino.strip()
        if coincide_termino(termino, descripcion_norm):
            return True

    # Respaldo: si la Descripción es casi idéntica al término buscado
    # (diferencias mínimas de redacción), también se considera exacta.
    return fuzzy_desc_max >= UMBRAL_FUZZY_EXACTO

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
    terminos_relacionados
):

    modelo = cargar_modelo()

    consulta_norm = normalizar(consulta)

    terminos = [consulta_norm]
    for t in terminos_relacionados:
        if t not in terminos:
            terminos.append(t)

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

        descripcion_norm = fila["descripcion_norm"]
        contexto_norm = fila["contexto_norm"]

        fuzzy_desc = 0
        fuzzy_contexto = 0

        for termino in terminos:
            fuzzy_desc = max(
                fuzzy_desc,
                fuzzy_score(termino, descripcion_norm)
            )
            fuzzy_contexto = max(
                fuzzy_contexto,
                fuzzy_score(termino, contexto_norm)
            )

        fuzzy = (
            (PESO_DESCRIPCION * fuzzy_desc) +
            (PESO_CONTEXTO * fuzzy_contexto)
        )

        semantico = float(
            similitudes[idx]
        ) * 100

        score = (
            SEMANTIC_WEIGHT * semantico +
            FUZZY_WEIGHT * fuzzy
        )

        exacto = es_coincidencia_exacta(
            terminos,
            descripcion_norm,
            fuzzy_desc
        )

        if score >= MIN_SCORE or exacto:
            resultados.append(
                (score, exacto, fila)
            )

    # Orden: primero coincidencias exactas, luego por score descendente.
    resultados.sort(
        key=lambda r: (not r[1], -r[0])
    )

    return resultados[:10]


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
# INICIALIZAR SESSION STATE
# =====================================================

# Inicializar estado de limpieza
if "limpiar" not in st.session_state:
    st.session_state.limpiar = False

# =====================================================
# FILTROS
# =====================================================

st.sidebar.header("Filtros")

segmentos = sorted(
    catalogo["Segmento"]
    .dropna()
    .unique()
)

# Si se solicitó limpiar, usar valores por defecto
if st.session_state.limpiar:
    valor_segmento = "Todos"
    valor_familia = "Todas"
    valor_clase = "Todas"
else:
    valor_segmento = st.session_state.get("segmento", "Todos")
    valor_familia = st.session_state.get("familia", "Todas")
    valor_clase = st.session_state.get("clase", "Todas")

segmento = st.sidebar.selectbox(
    "Segmento",
    ["Todos"] + list(segmentos),
    index=0 if valor_segmento == "Todos" else list(segmentos).index(valor_segmento) if valor_segmento in segmentos else 0,
    key="segmento_select"
)

if segmento != "Todos":
    catalogo_filtrado = catalogo[catalogo["Segmento"] == segmento]
else:
    catalogo_filtrado = catalogo

familias = sorted(
    catalogo_filtrado["Familia"]
    .dropna()
    .unique()
)

familia = st.sidebar.selectbox(
    "Familia",
    ["Todas"] + list(familias),
    index=0 if valor_familia == "Todas" else list(familias).index(valor_familia) if valor_familia in familias else 0,
    key="familia_select"
)

if familia != "Todas":
    catalogo_filtrado = catalogo_filtrado[catalogo_filtrado["Familia"] == familia]

clases = sorted(
    catalogo_filtrado["Clase"]
    .dropna()
    .unique()
)

clase = st.sidebar.selectbox(
    "Clase",
    ["Todas"] + list(clases),
    index=0 if valor_clase == "Todas" else list(clases).index(valor_clase) if valor_clase in clases else 0,
    key="clase_select"
)

if clase != "Todas":
    catalogo_filtrado = catalogo_filtrado[catalogo_filtrado["Clase"] == clase]

# Guardar valores actuales en session_state
st.session_state.segmento = segmento
st.session_state.familia = familia
st.session_state.clase = clase

# =====================================================
# BOTÓN LIMPIAR BÚSQUEDA
# =====================================================

if st.sidebar.button("🧹 Limpiar Búsqueda", use_container_width=True):
    # Activar bandera de limpieza
    st.session_state.limpiar = True
    # Limpiar consulta
    st.session_state.consulta = ""
    # Forzar recarga
    st.rerun()

# =====================================================
# BUSQUEDA
# =====================================================

# Si se limpió, desactivar la bandera después de la recarga
if st.session_state.limpiar:
    st.session_state.limpiar = False

# Usar session_state para el campo de búsqueda
consulta_val = st.session_state.get("consulta", "")
consulta = st.text_input(
    "Describa el bien o servicio:",
    value=consulta_val,
    key="consulta_input"
)

# Actualizar session_state cuando cambia la consulta
if consulta != st.session_state.get("consulta", ""):
    st.session_state.consulta = consulta

if consulta:

    inicio = time.time()

    consulta_norm = normalizar(
        consulta
    )

    relacionados_info = dic_sinonimos.get(
        consulta_norm,
        []
    )

    sinonimos = [t for t, _ in relacionados_info]

    if sinonimos:
        st.info(
            "Términos relacionados detectados: " +
            ", ".join(sinonimos)
        )

    resultados = buscar_hibrido(
        catalogo_filtrado,
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

    for score, exacto, fila in resultados:
        exportar.append({
            "Tipo": "Exacta" if exacto else "Relacionada",
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

    if not resultados:
        st.warning("No se encontraron resultados para esta búsqueda.")

    exactos = [r for r in resultados if r[1]]
    relacionados_res = [r for r in resultados if not r[1]]

    def mostrar_resultado(score, fila):
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

    if exactos:
        st.markdown("### 🎯 Coincidencia exacta")
        for score, exacto, fila in exactos:
            mostrar_resultado(score, fila)

    if relacionados_res:
        st.markdown("### 🔍 Resultados relacionados")
        for score, exacto, fila in relacionados_res:
            mostrar_resultado(score, fila)