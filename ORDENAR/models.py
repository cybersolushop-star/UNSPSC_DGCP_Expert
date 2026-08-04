"""
Módulo de modelos para UNSPSC DGCP
"""

import streamlit as st
import pandas as pd
import numpy as np
import torch
from pathlib import Path
from typing import Optional, Tuple
from src.config import EMBEDDINGS_FILE, MODEL_NAME, DEVICE

class EmbeddingManager:
    """Gestor de embeddings para el catálogo UNSPSC"""
    
    def __init__(self):
        self.model = None
        self.embeddings = None
        self.codigos = None
    
    @st.cache_resource
    def cargar_embeddings(_self):
        """Carga los embeddings desde el archivo .pt"""
        try:
            # Intentar cargar el modelo
            try:
                from sentence_transformers import SentenceTransformer
                _self.model = SentenceTransformer(MODEL_NAME, device=DEVICE)
            except ImportError:
                _self._crear_embeddings_vacios()
                return None
            
            # Verificar si existe el archivo de embeddings
            if Path(EMBEDDINGS_FILE).exists():
                try:
                    data = torch.load(EMBEDDINGS_FILE, map_location=DEVICE)
                    
                    if isinstance(data, dict) and 'embeddings' in data and 'codigos' in data:
                        embeddings = data['embeddings']
                        codigos = data['codigos']
                        
                        if isinstance(embeddings, torch.Tensor):
                            if embeddings.dim() == 1:
                                embeddings = embeddings.unsqueeze(0)
                            elif embeddings.dim() > 2:
                                embeddings = embeddings.view(embeddings.size(0), -1)
                            
                            _self.embeddings = embeddings.numpy()
                        else:
                            _self.embeddings = np.array(embeddings)
                            if _self.embeddings.ndim == 1:
                                _self.embeddings = _self.embeddings.reshape(1, -1)
                        
                        _self.codigos = codigos
                        
                        # Solo imprimir en consola, no mostrar en la interfaz
                        print(f"✅ Embeddings cargados: {len(_self.codigos)} elementos")
                        return _self.embeddings
                    else:
                        _self._crear_embeddings_vacios()
                        return None
                        
                except Exception as e:
                    print(f"Error al cargar embeddings: {e}")
                    _self._crear_embeddings_vacios()
                    return None
            else:
                _self._crear_embeddings_vacios()
                return None
                
        except Exception as e:
            print(f"Error al cargar modelo de embeddings: {e}")
            return None
    
    def _crear_embeddings_vacios(_self):
        """Crea embeddings vacíos para evitar errores"""
        _self.embeddings = np.array([]).reshape(0, 0)
        _self.codigos = []
    
    def generar_embedding(self, texto: str) -> Optional[np.ndarray]:
        """Genera un embedding para un texto dado"""
        try:
            if self.model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    self.model = SentenceTransformer(MODEL_NAME, device=DEVICE)
                except ImportError:
                    return None
            embedding = self.model.encode(texto, convert_to_numpy=True)
            return embedding
        except Exception as e:
            print(f"Error al generar embedding: {e}")
            return None
    
    def buscar_similares(self, embedding: np.ndarray, top_k: int = 10) -> list:
        """Busca los embeddings más similares"""
        if self.embeddings is None or self.codigos is None:
            return []
        
        if isinstance(self.embeddings, np.ndarray) and self.embeddings.size == 0:
            return []
        
        if embedding.ndim > 1:
            embedding = embedding.flatten()
        
        try:
            if isinstance(self.embeddings, torch.Tensor):
                embeddings_np = self.embeddings.numpy()
            else:
                embeddings_np = np.array(self.embeddings)
            
            if embeddings_np.ndim == 1:
                embeddings_np = embeddings_np.reshape(1, -1)
            
            norm_embeddings = np.linalg.norm(embeddings_np, axis=1, keepdims=True)
            norm_embeddings = np.where(norm_embeddings == 0, 1, norm_embeddings)
            embeddings_norm = embeddings_np / norm_embeddings
            
            norm_embedding = np.linalg.norm(embedding)
            if norm_embedding == 0:
                return []
            embedding_norm = embedding / norm_embedding
            
            similitudes = np.dot(embeddings_norm, embedding_norm)
            
            if len(similitudes) > 0:
                indices = np.argsort(similitudes)[-top_k:][::-1]
                resultados = []
                for idx in indices:
                    if similitudes[idx] > 0.1:
                        resultados.append((self.codigos[idx], float(similitudes[idx])))
                return resultados
            
            return []
            
        except Exception as e:
            print(f"Error en búsqueda semántica: {e}")
            return []