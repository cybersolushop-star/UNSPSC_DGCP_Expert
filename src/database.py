# -*- coding: utf-8 -*-
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
        print(f"📊 Equivalencias cargadas: {len(self.equivalencias_digepres) if self.equivalencias_digepres is not None else 0}")
    
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
        """Carga las equivalencias DIGEPRES desde catalogo_final.csv"""
        try:
            csv_path = _self.base_dir / "data" / "catalogo_final.csv"
            print(f"📂 Buscando archivo: {csv_path}")
            
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                print(f"✅ Archivo cargado: {len(df)} filas")
                print(f"📋 Columnas: {list(df.columns)}")
                
                # Usar la columna 'Código' como identificador
                df['codigo_familia'] = df['Código'].astype(str).str.strip()
                
                # Las columnas ya se llaman 'cuenta_digepres' y 'descripcion_digepres'
                if 'cuenta_digepres' in df.columns and 'descripcion_digepres' in df.columns:
                    # Limpiar datos
                    df_clean = df[['codigo_familia', 'cuenta_digepres', 'descripcion_digepres']].copy()
                    df_clean = df_clean.dropna(subset=['codigo_familia', 'cuenta_digepres'])
                    df_clean = df_clean.drop_duplicates(subset=['codigo_familia'])
                    print(f"✅ Datos limpios: {len(df_clean)} registros")
                    return df_clean
            
            # Fallback: intentar cargar desde la base de datos
            conn = _self.conectar()
            df = pd.read_sql("SELECT * FROM equivalencias_digepres", conn)
            df['codigo_familia'] = df['codigo_familia'].astype(str)
            return df
        except Exception as e:
            print(f"❌ Error cargando equivalencias: {e}")
            return pd.DataFrame(columns=['codigo_familia', 'cuenta_digepres', 'descripcion_digepres'])
    
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
        Busca en equivalencias_digepres (cargado desde CSV).
        """
        # 1. BUSCAR EN equivalencias_digepres (cargado desde CSV)
        if codigo_familia and self.equivalencias_digepres is not None and not self.equivalencias_digepres.empty:
            try:
                # Buscar por código (que es el Código UNSPSC)
                fila = self.equivalencias_digepres[
                    self.equivalencias_digepres['codigo_familia'].astype(str).str.strip() == str(codigo_familia).strip()
                ]
                if not fila.empty:
                    cuenta = fila.iloc[0]['cuenta_digepres']
                    desc = fila.iloc[0]['descripcion_digepres']
                    if cuenta and len(str(cuenta)) > 0:
                        return cuenta, desc, 'familia', 1.0
            except Exception as e:
                print(f"⚠️ Error buscando en equivalencias: {e}")
        
        # 2. SI NO ENCUENTRA, BUSCAR POR DESCRIPCIÓN
        if descripcion_item:
            try:
                conn = self.conectar()
                cur = conn.cursor()
                cur.execute("""
                    SELECT "Código UNSPSC" FROM catalogo 
                    WHERE "Descripción" = ? 
                    LIMIT 1
                """, (descripcion_item,))
                resultado = cur.fetchone()
                if resultado:
                    codigo_unspsc = resultado[0]
                    if self.equivalencias_digepres is not None and not self.equivalencias_digepres.empty:
                        fila = self.equivalencias_digepres[
                            self.equivalencias_digepres['codigo_familia'].astype(str).str.strip() == str(codigo_unspsc).strip()
                        ]
                        if not fila.empty:
                            return fila.iloc[0]['cuenta_digepres'], fila.iloc[0]['descripcion_digepres'], 'item', 1.0
            except Exception as e:
                print(f"⚠️ Error buscando por descripción: {e}")
        
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