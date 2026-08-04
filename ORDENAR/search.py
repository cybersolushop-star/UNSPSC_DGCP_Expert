"""
Módulo de búsqueda para UNSPSC DGCP
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
from src.utils import normalizar, normalizar_avanzado
from src.config import MIN_SCORE, MAX_RESULTS

class SearchEngine:
    """Motor de búsqueda para el catálogo UNSPSC"""
    
    def __init__(self, catalogo: pd.DataFrame, embeddings: pd.DataFrame):
        self.catalogo = catalogo
        self.embeddings = embeddings
        self.max_results = MAX_RESULTS
        self.min_score = MIN_SCORE / 100
    
    def buscar(self, consulta: str, sinonimos: List[str] = None) -> List[Tuple[float, bool, pd.Series]]:
        """Busca en el catálogo usando múltiples estrategias"""
        resultados = []
        consulta_norm = normalizar(consulta)
        consulta_keywords = normalizar_avanzado(consulta)
        
        # 1. Búsqueda exacta por código
        if consulta_norm.isdigit() and len(consulta_norm) == 8:
            exactos = self._buscar_por_codigo(consulta_norm)
            if exactos:
                resultados.extend(exactos)
        
        # 2. Búsqueda por texto exacto
        exactos = self._buscar_por_texto_exacto(consulta_norm)
        if exactos:
            resultados.extend(exactos)
        
        # 3. Búsqueda por texto con sinónimos
        if sinonimos:
            sinonimos_resultados = self._buscar_por_sinonimos(sinonimos)
            resultados.extend(sinonimos_resultados)
        
        # 4. Búsqueda por coincidencia aproximada (fuzzy)
        fuzzy_resultados = self._buscar_fuzzy(consulta, consulta_keywords)
        resultados.extend(fuzzy_resultados)
        
        # 5. Búsqueda semántica (si hay embeddings)
        if self.embeddings is not None:
            # Verificar si embeddings no está vacío correctamente
            if isinstance(self.embeddings, np.ndarray):
                if self.embeddings.size > 0:
                    semanticos = self._buscar_semantico(consulta)
                    resultados.extend(semanticos)
            elif hasattr(self.embeddings, 'shape'):
                if self.embeddings.shape[0] > 0:
                    semanticos = self._buscar_semantico(consulta)
                    resultados.extend(semanticos)
        
        # Limpiar y ordenar resultados
        resultados = self._limpiar_resultados(resultados)
        resultados = sorted(resultados, key=lambda x: x[0], reverse=True)
        
        return resultados[:self.max_results]
    
    def _buscar_por_codigo(self, codigo: str) -> List[Tuple[float, bool, pd.Series]]:
        """Busca por código exacto"""
        try:
            fila = self.catalogo[self.catalogo["Código UNSPSC"].astype(str) == codigo]
            if not fila.empty:
                return [(100.0, True, fila.iloc[0])]
        except:
            pass
        return []
    
    def _buscar_por_texto_exacto(self, texto: str) -> List[Tuple[float, bool, pd.Series]]:
        """Busca por texto exacto en descripción"""
        try:
            filtro = self.catalogo["descripcion_norm"].str.contains(texto, case=False, na=False)
            filas = self.catalogo[filtro]
            if not filas.empty:
                return [(95.0, True, fila) for _, fila in filas.iterrows()]
        except:
            pass
        return []
    
    def _buscar_por_sinonimos(self, sinonimos: List[str]) -> List[Tuple[float, bool, pd.Series]]:
        """Busca usando sinónimos"""
        resultados = []
        for sinonimo in sinonimos:
            try:
                filtro = self.catalogo["descripcion_norm"].str.contains(sinonimo, case=False, na=False)
                filas = self.catalogo[filtro]
                for _, fila in filas.iterrows():
                    resultados.append((85.0, False, fila))
            except:
                pass
        return resultados
    
    def _buscar_fuzzy(self, consulta: str, consulta_keywords: str) -> List[Tuple[float, bool, pd.Series]]:
        """Busca usando fuzzy matching"""
        resultados = []
        
        try:
            from fuzzywuzzy import fuzz, process
            
            # Buscar en descripciones
            descripciones = self.catalogo["descripcion_keywords"].fillna("").tolist()
            if descripciones:
                matches = process.extract(consulta_keywords, descripciones, scorer=fuzz.token_sort_ratio, limit=20)
                
                for match_text, score in matches:
                    if score >= 60:
                        filtro = self.catalogo["descripcion_keywords"] == match_text
                        filas = self.catalogo[filtro]
                        for _, fila in filas.iterrows():
                            resultados.append((score / 100, False, fila))
            
            # Buscar en contexto
            contextos = self.catalogo["contexto_norm"].fillna("").tolist()
            if contextos:
                matches = process.extract(consulta_keywords, contextos, scorer=fuzz.token_sort_ratio, limit=20)
                
                for match_text, score in matches:
                    if score >= 60:
                        filtro = self.catalogo["contexto_norm"] == match_text
                        filas = self.catalogo[filtro]
                        for _, fila in filas.iterrows():
                            resultados.append((score / 100 * 0.8, False, fila))
                        
        except Exception as e:
            print(f"Error en búsqueda fuzzy: {e}")
        
        return resultados
    
    def _buscar_semantico(self, consulta: str) -> List[Tuple[float, bool, pd.Series]]:
        """Busca usando embeddings semánticos"""
        try:
            from src.models import EmbeddingManager
            embed_manager = EmbeddingManager()
            embedding = embed_manager.generar_embedding(consulta)
            
            if embedding is not None:
                similares = embed_manager.buscar_similares(embedding, top_k=20)
                resultados = []
                for codigo, score in similares:
                    if score >= 0.3:
                        fila = self.catalogo[self.catalogo["Código UNSPSC"].astype(str) == codigo]
                        if not fila.empty:
                            resultados.append((score, False, fila.iloc[0]))
                return resultados
        except Exception as e:
            print(f"Error en búsqueda semántica: {e}")
        
        return []
    
    def _limpiar_resultados(self, resultados: List) -> List:
        """Limpia y deduplica resultados"""
        vistos = set()
        limpios = []
        
        for score, exacto, fila in resultados:
            codigo = fila.get("Código UNSPSC", "")
            if codigo not in vistos:
                vistos.add(codigo)
                limpios.append((score, exacto, fila))
        
        return limpios