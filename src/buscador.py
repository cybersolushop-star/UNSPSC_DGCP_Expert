"""
Módulo de búsqueda para UNSPSC DGCP Buscador
"""

import re
import torch
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer, util
import streamlit as st

# Configuración
SEMANTIC_WEIGHT = 0.20
FUZZY_WEIGHT = 0.80
MIN_SCORE = 70
PESO_DESCRIPCION = 0.75
PESO_CONTEXTO = 0.25
UMBRAL_FUZZY_EXACTO = 97

class Buscador:
    """Motor de búsqueda híbrido (semántico + fuzzy)"""
    
    def __init__(self):
        self.modelo = None
    
    @st.cache_resource
    def cargar_modelo(_self):
        """Carga el modelo de embeddings"""
        return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    
    def normalizar(self, texto):
        """Normaliza texto para búsqueda"""
        texto = str(texto).lower().strip()
        texto = re.sub(r"\s+", " ", texto)
        return texto
    
    def fuzzy_score(self, a, b):
        """Calcula el score fuzzy entre dos textos"""
        if not a or not b:
            return 0
        if len(a) < 5:
            return fuzz.token_sort_ratio(a, b)
        s1 = fuzz.token_set_ratio(a, b)
        s2 = fuzz.token_sort_ratio(a, b)
        s3 = fuzz.partial_ratio(a, b)
        if s3 > 80 and s1 < 60 and s2 < 60:
            return max(s1, s2)
        return max(s1, s2, s3)
    
    def fuzzy_score_avanzado(self, terminos, descripcion_keywords):
        """Calcula el score fuzzy avanzado considerando términos y keywords"""
        if not terminos or not descripcion_keywords:
            return 0
        mejor_score = 0
        for termino in terminos:
            score = self.fuzzy_score(termino, descripcion_keywords)
            mejor_score = max(mejor_score, score)
            for palabra in termino.split():
                if len(palabra) > 3:
                    score_palabra = self.fuzzy_score(palabra, descripcion_keywords)
                    mejor_score = max(mejor_score, score_palabra)
        return mejor_score
    
    def coincide_termino(self, termino, texto):
        """Verifica si un término aparece como palabra completa en el texto"""
        if not termino or not texto:
            return False
        variantes = {termino, termino + "s", termino + "es"}
        for variante in variantes:
            patron = r"(?<!\w)" + re.escape(variante) + r"(?!\w)"
            if re.search(patron, texto):
                return True
        return False
    
    def es_coincidencia_exacta(self, terminos, descripcion_norm, fuzzy_desc_max):
        """Determina si hay una coincidencia exacta real"""
        for termino in terminos:
            termino = termino.strip()
            if len(termino) < 4:
                if termino in descripcion_norm.split():
                    return True
                continue
            if self.coincide_termino(termino, descripcion_norm):
                return True
            patron = r"(?<![a-záéíóúñ])" + re.escape(termino) + r"(?![a-záéíóúñ])"
            if re.search(patron, descripcion_norm.lower()):
                return True
        return fuzzy_desc_max >= UMBRAL_FUZZY_EXACTO
    
    def extraer_palabras_clave(self, texto):
        """Extrae palabras clave de un texto"""
        texto_norm = self.normalizar(texto)
        return texto_norm.split()
    
    def buscar_hibrido(self, df, embeddings_catalogo, consulta, terminos_relacionados):
        """Realiza la búsqueda híbrida"""
        
        modelo = self.cargar_modelo()
        
        # Normalizar consulta
        consulta_norm = self.normalizar(consulta)
        
        # Crear lista de términos
        terminos = [consulta_norm]
        
        # Agregar palabras clave
        palabras_clave = self.extraer_palabras_clave(consulta)
        for palabra in palabras_clave:
            if len(palabra) > 3 and palabra not in terminos:
                terminos.append(palabra)
        
        # Agregar términos relacionados
        for t in terminos_relacionados:
            if t not in terminos:
                terminos.append(t)
        
        # Calcular similitud semántica
        mejor_similitud = None
        for termino in terminos:
            emb = modelo.encode(termino, convert_to_tensor=True, show_progress_bar=False)
            similitud = util.cos_sim(emb, embeddings_catalogo)[0]
            if mejor_similitud is None:
                mejor_similitud = similitud
            else:
                mejor_similitud = mejor_similitud.maximum(similitud)
        
        similitudes = mejor_similitud.cpu().numpy()
        
        # Evaluar cada fila
        resultados = []
        for idx, fila in df.iterrows():
            descripcion_norm = fila["descripcion_norm"]
            contexto_norm = fila["contexto_norm"]
            descripcion_keywords = descripcion_norm  # Simplificado
            
            # Fuzzy
            fuzzy_desc = self.fuzzy_score_avanzado(terminos, descripcion_keywords)
            fuzzy_contexto = 0
            if fuzzy_desc > 50:
                for termino in terminos:
                    fuzzy_contexto = max(fuzzy_contexto, self.fuzzy_score(termino, contexto_norm))
            
            # Ponderar fuzzy
            if fuzzy_desc > 50:
                fuzzy = (PESO_DESCRIPCION * fuzzy_desc) + (PESO_CONTEXTO * fuzzy_contexto)
            else:
                fuzzy = fuzzy_desc * 0.3
            
            # Score combinado
            semantico = float(similitudes[idx]) * 100
            score = (SEMANTIC_WEIGHT * semantico) + (FUZZY_WEIGHT * fuzzy)
            
            # Coincidencia exacta
            exacto = self.es_coincidencia_exacta(terminos, descripcion_norm, fuzzy_desc)
            
            # Filtrar
            if (score >= MIN_SCORE or exacto):
                resultados.append((score, exacto, fila))
        
        # Ordenar
        resultados.sort(key=lambda r: (not r[1], -r[0]))
        
        return resultados[:20]  # Límite de 20 resultados