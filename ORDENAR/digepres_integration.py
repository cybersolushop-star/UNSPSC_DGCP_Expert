"""
Módulo para integrar cuentas DIGEPRES al buscador
"""
import pandas as pd
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DigepresIntegration:
    """Clase para manejar la integración de cuentas DIGEPRES"""
    
    def __init__(self, csv_path='catalogo_final.csv', db_path='db/DGCP_UNSPSC.db'):
        self.csv_path = csv_path
        self.db_path = db_path
        self.df = None
        self._cargar_datos()
    
    def _cargar_datos(self):
        """Carga los datos DIGEPRES desde CSV"""
        try:
            # Intentar cargar desde CSV
            if Path(self.csv_path).exists():
                self.df = pd.read_csv(self.csv_path)
                logger.info(f"✅ DIGEPRES cargado desde CSV: {len(self.df)} ítems")
                return
            else:
                logger.warning(f"⚠️ Archivo {self.csv_path} no encontrado")
                self.df = None
        except Exception as e:
            logger.error(f"Error al cargar DIGEPRES: {e}")
            self.df = None
    
    def obtener_cuenta(self, codigo):
        """
        Obtiene la cuenta DIGEPRES para un código
        
        Args:
            codigo: Código UNSPSC del producto
            
        Returns:
            tuple: (cuenta_digepres, descripcion_digepres) o (None, None)
        """
        if self.df is None:
            return None, None
        
        codigo_str = str(codigo).strip()
        
        # Buscar en el DataFrame
        resultado = self.df[self.df['Código'].astype(str).str.strip() == codigo_str]
        
        if len(resultado) > 0:
            row = resultado.iloc[0]
            if 'cuenta_digepres' in row and pd.notna(row['cuenta_digepres']):
                return row['cuenta_digepres'], row.get('descripcion_digepres', '')
        
        return None, None
    
    def obtener_cuentas_multiples(self, codigos):
        """
        Obtiene cuentas DIGEPRES para múltiples códigos
        
        Args:
            codigos: Lista de códigos UNSPSC
            
        Returns:
            dict: {codigo: {'cuenta': cuenta, 'descripcion': desc}}
        """
        resultados = {}
        for codigo in codigos:
            cuenta, desc = self.obtener_cuenta(codigo)
            resultados[str(codigo)] = {'cuenta': cuenta, 'descripcion': desc}
        return resultados
    
    def agregar_digepres_a_df(self, df):
        """
        Agrega columnas DIGEPRES a un DataFrame de resultados
        
        Args:
            df: DataFrame con columna 'Código'
            
        Returns:
            DataFrame con columnas DIGEPRES agregadas
        """
        if df is None or len(df) == 0:
            return df
        
        if 'Código' not in df.columns:
            return df
        
        # Agregar columnas DIGEPRES
        codigos = df['Código'].tolist()
        cuentas = self.obtener_cuentas_multiples(codigos)
        
        df['cuenta_digepres'] = df['Código'].apply(
            lambda x: cuentas.get(str(x), {}).get('cuenta', None)
        )
        df['descripcion_digepres'] = df['Código'].apply(
            lambda x: cuentas.get(str(x), {}).get('descripcion', None)
        )
        
        return df
    
    def obtener_estadisticas(self):
        """
        Obtiene estadísticas de la integración DIGEPRES
        
        Returns:
            dict: Estadísticas
        """
        if self.df is None:
            return {
                'total': 0,
                'con_digepres': 0,
                'sin_digepres': 0,
                'cuentas_unicas': 0
            }
        
        total = len(self.df)
        con_digepres = self.df['cuenta_digepres'].notna().sum()
        sin_digepres = total - con_digepres
        cuentas_unicas = self.df['cuenta_digepres'].nunique() if 'cuenta_digepres' in self.df.columns else 0
        
        return {
            'total': total,
            'con_digepres': con_digepres,
            'sin_digepres': sin_digepres,
            'cuentas_unicas': cuentas_unicas
        }