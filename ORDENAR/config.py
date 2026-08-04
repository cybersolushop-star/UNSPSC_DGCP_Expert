"""
Módulo de configuración para UNSPSC DGCP
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Directorios
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "db"
MODELS_DIR = BASE_DIR / "models"

# Archivos
DB_FILE = DB_DIR / "DGCP_UNSPSC.db"
EMBEDDINGS_FILE = DB_DIR / "embeddings.pt"
SINONIMOS_FILE = DATA_DIR / "sinonimos.csv"
EQUIVALENCIAS_FILE = DATA_DIR / "equivalencias_digepres.csv"

# Configuración del modelo
MODEL_NAME = os.getenv("MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2")
DEVICE = os.getenv("DEVICE", "cpu")

# Configuración de búsqueda
MIN_SCORE = int(os.getenv("MIN_SCORE", 50))
MAX_RESULTS = int(os.getenv("MAX_RESULTS", 30))

def get_config():
    """Retorna la configuración como diccionario"""
    return {
        "MODEL_NAME": MODEL_NAME,
        "DEVICE": DEVICE,
        "MIN_SCORE": MIN_SCORE,
        "MAX_RESULTS": MAX_RESULTS,
        "DB_FILE": str(DB_FILE),
        "EMBEDDINGS_FILE": str(EMBEDDINGS_FILE),
    }