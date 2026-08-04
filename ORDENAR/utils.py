"""
Módulo de utilidades para UNSPSC DGCP
"""

import re
import unicodedata
from typing import List, Set

def normalizar(texto: str) -> str:
    """
    Normaliza un texto eliminando acentos, caracteres especiales y convirtiendo a minúsculas
    """
    if not texto or not isinstance(texto, str):
        return ""
    
    texto = texto.lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def normalizar_avanzado(texto: str) -> str:
    """
    Normalización avanzada para búsquedas fuzzy
    """
    if not texto or not isinstance(texto, str):
        return ""
    
    texto = normalizar(texto)
    texto = re.sub(r'\b([a-z])[a-z]+\b', r'\1', texto)
    return texto

def tokenizar(texto: str) -> Set[str]:
    """Tokeniza un texto en palabras clave"""
    if not texto:
        return set()
    return set(normalizar(texto).split())

def extraer_palabras_clave(texto: str) -> List[str]:
    """Extrae palabras clave de un texto"""
    if not texto:
        return []
    palabras = normalizar(texto).split()
    return [p for p in palabras if len(p) > 2]