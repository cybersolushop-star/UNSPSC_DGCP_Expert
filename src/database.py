"""
Módulo de base de datos para UNSPSC DGCP Buscador
"""

import sqlite3
import pandas as pd
import unicodedata
import re
import torch
from pathlib import Path
from datetime import datetime
import streamlit as st

class DatabaseManager:
    """Gestiona todas las operaciones de base de datos"""
    
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.db_file = self.base_dir / "db" / "DGCP_UNSPSC.db"
        self.conn = None
        self.catalogo = None
        self.equivalencias_digepres = None
        self.cargar_datos()
    
    def conectar(self):
        """Establece conexión con la base de datos"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_file)
        return self.conn
    
    def cerrar(self):
        """Cierra la conexión con la base de datos"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def cargar_datos(self):
        """Carga los datos principales en memoria"""
        self.catalogo = self.cargar_catalogo()
        self.equivalencias_digepres = self.cargar_equivalencias_digepres()
    
    def normalizar(self, texto):
        """Normaliza texto: minúsculas, sin tildes, sin espacios extra"""
        texto = str(texto)
        texto = texto.lower().strip()
        texto = "".join(
            c for c in unicodedata.normalize("NFD", texto)
            if unicodedata.category(c) != "Mn"
        )
        texto = re.sub(r"\s+", " ", texto)
        return texto
    
    @st.cache_data
    def cargar_catalogo(_self):
        """Carga el catálogo desde la base de datos"""
        conn = _self.conectar()
        df = pd.read_sql("SELECT * FROM catalogo", conn)
        
        # Limpiar y preparar
        df = df.drop_duplicates(subset=["Código UNSPSC"])
        df["descripcion_norm"] = df["Descripción"].fillna("").astype(str).apply(_self.normalizar)
        df["contexto_norm"] = (
            df["Definición"].fillna("") + " " +
            df["Segmento"].fillna("") + " " +
            df["Familia"].fillna("") + " " +
            df["Clase"].fillna("")
        ).apply(_self.normalizar)
        
        return df
    
    @st.cache_data
    def cargar_equivalencias_digepres(_self):
        """Carga las equivalencias DIGEPRES"""
        try:
            conn = _self.conectar()
            df = pd.read_sql("SELECT * FROM equivalencias_digepres", conn)
            df['codigo_familia'] = df['codigo_familia'].astype(str)
            return df
        except:
            return pd.DataFrame(columns=['codigo_familia', 'familia_unspsc', 'cuenta_digepres', 'descripcion_digepres'])
    
    @st.cache_data
    def cargar_embeddings(_self):
        """Carga los embeddings del catálogo"""
        archivo = _self.base_dir / "db" / "embeddings.pt"
        data = torch.load(archivo, map_location="cpu")
        
        # Extraer el tensor del diccionario
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
    
    @st.cache_data
    def cargar_sinonimos(_self):
        """Carga los sinónimos de la base de datos"""
        try:
            conn = _self.conectar()
            df = pd.read_sql("SELECT termino, sinonimo FROM sinonimos", conn)
            conn.close()
            dic = {}
            for _, row in df.iterrows():
                t = _self.normalizar(row["termino"])
                s = _self.normalizar(row["sinonimo"])
                if t not in dic:
                    dic[t] = []
                if s not in dic[t]:
                    dic[t].append(s)
            return dic
        except:
            return {}
    
    def obtener_digepres(self, codigo_familia, descripcion_item=None):
        """
        Obtiene la cuenta DIGEPRES para un ítem.
        Prioriza búsqueda por código UNSPSC en equivalencias_por_item.
        """
        conn = self.conectar()
        cur = conn.cursor()
        
        # 1. BUSCAR POR CÓDIGO FAMILIA (que en este caso es el código UNSPSC)
        if codigo_familia:
            try:
                # Buscar en equivalencias_por_item (por código UNSPSC)
                cur.execute("""
                    SELECT cuenta_digepres, descripcion_digepres 
                    FROM equivalencias_por_item 
                    WHERE codigo_unspsc = ?
                """, (str(codigo_familia).strip(),))
                resultado = cur.fetchone()
                if resultado:
                    return resultado[0], resultado[1], 'item', 1.0
            except:
                pass
            
            try:
                # Si no encuentra, buscar en equivalencias_digepres (por familia)
                cur.execute("""
                    SELECT cuenta_digepres, descripcion_digepres 
                    FROM equivalencias_digepres 
                    WHERE codigo_familia = ?
                """, (str(codigo_familia).strip(),))
                resultado = cur.fetchone()
                if resultado:
                    return resultado[0], resultado[1], 'familia', 1.0
            except:
                pass
        
        # 2. BUSCAR POR DESCRIPCIÓN DEL ÍTEM (si se proporcionó)
        if descripcion_item:
            try:
                cur.execute("""
                    SELECT "Código UNSPSC" FROM catalogo 
                    WHERE "Descripción" = ? 
                    LIMIT 1
                """, (descripcion_item,))
                resultado = cur.fetchone()
                if resultado:
                    codigo_unspsc = resultado[0]
                    cur.execute("""
                        SELECT cuenta_digepres, descripcion_digepres 
                        FROM equivalencias_por_item 
                        WHERE codigo_unspsc = ?
                    """, (codigo_unspsc,))
                    item_result = cur.fetchone()
                    if item_result:
                        return item_result[0], item_result[1], 'item', 1.0
            except:
                pass
        
        return None, None, 'ninguna', 0.0
    
    def registrar_busqueda(self, consulta, cantidad):
        """Registra una búsqueda en el historial"""
        try:
            conn = self.conectar()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS consultas(
                    id INTEGER PRIMARY KEY,
                    fecha TEXT,
                    consulta TEXT,
                    resultados INTEGER
                )
            """)
            conn.execute("""
                INSERT INTO consultas (fecha, consulta, resultados)
                VALUES (?, ?, ?)
            """, (datetime.now().isoformat(), consulta, cantidad))
            conn.commit()
        except:
            pass