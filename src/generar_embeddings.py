from pathlib import Path
import sqlite3
import pandas as pd
import torch

from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent

DB_FILE = BASE_DIR / "db" / "DGCP_UNSPSC.db"

OUTPUT_FILE = BASE_DIR / "db" / "embeddings.pt"


print("Cargando catálogo...")


with sqlite3.connect(DB_FILE) as conn:

    df = pd.read_sql(
        "SELECT * FROM catalogo",
        conn
    )


print(f"Registros encontrados: {len(df)}")


def normalizar(texto):

    return str(texto).lower().strip()


df["texto_busqueda"] = (

    df["Descripción"].fillna("")
    + " "
    + df["Definición"].fillna("")
    + " "
    + df["Segmento"].fillna("")
    + " "
    + df["Familia"].fillna("")
    + " "
    + df["Clase"].fillna("")

)


df["texto_busqueda"] = (
    df["texto_busqueda"]
    .apply(normalizar)
)


print("Cargando modelo...")


modelo = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2"
)


print("Generando embeddings...")


embeddings = modelo.encode(
    df["texto_busqueda"].tolist(),
    convert_to_tensor=True,
    show_progress_bar=True
)


print("Guardando embeddings...")


torch.save(
    embeddings,
    OUTPUT_FILE
)


print("Proceso terminado:")
print(OUTPUT_FILE)