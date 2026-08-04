"""
Importador de la Guía Alfabética de Imputaciones Presupuestarias
Para el proyecto UNSPSC DGCP Buscador
Version independiente (no requiere DatabaseManager)
"""

import sqlite3
import pandas as pd
from pathlib import Path

class ImportadorGuiaAlfabetica:
    """Clase para importar la Guia Alfabetica de Imputaciones"""
    
    def __init__(self, db_path='db/DGCP_UNSPSC.db'):
        self.db_path = db_path
        
    def conectar_db(self):
        """Conecta a la base de datos"""
        Path('db').mkdir(exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"[OK] Conectado a: {self.db_path}")
        
    def cerrar_db(self):
        """Cierra la conexion a la base de datos"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            print("[OK] Conexion cerrada")
    
    def crear_tablas(self):
        """Crea las tablas necesarias si no existen"""
        
        # Tabla: catalogo_bienes
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS catalogo_bienes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                descripcion TEXT NOT NULL,
                clase TEXT,
                familia TEXT,
                segmento TEXT,
                definicion TEXT,
                auxiliar TEXT,
                denominacion TEXT,
                fecha_importacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla: imputaciones_presupuestarias
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS imputaciones_presupuestarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                descripcion TEXT NOT NULL,
                definicion TEXT,
                auxiliar TEXT,
                denominacion TEXT,
                clase TEXT,
                familia TEXT,
                segmento TEXT,
                fecha_importacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Indices
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_cb_codigo ON catalogo_bienes(codigo)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_cb_descripcion ON catalogo_bienes(descripcion)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_cb_auxiliar ON catalogo_bienes(auxiliar)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_cb_denominacion ON catalogo_bienes(denominacion)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_ip_codigo ON imputaciones_presupuestarias(codigo)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_ip_descripcion ON imputaciones_presupuestarias(descripcion)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_ip_auxiliar ON imputaciones_presupuestarias(auxiliar)")
        
        self.conn.commit()
        print("[OK] Tablas creadas/verificadas")
    
    def importar_catalogo_bienes(self, archivo_excel):
        """Importa el catalogo de bienes y servicios desde Excel"""
        
        if not Path(archivo_excel).exists():
            print(f"[ERROR] Archivo no encontrado: {archivo_excel}")
            return False
        
        print(f"\n[INFO] Importando catalogo desde: {archivo_excel}")
        
        try:
            df = pd.read_excel(archivo_excel)
            print(f"[INFO] Registros en archivo: {len(df)}")
            print(f"[INFO] Columnas: {list(df.columns)}")
            
            if 'Código' not in df.columns:
                print("[ERROR] Columna 'Codigo' no encontrada")
                return False
            
            df = df.drop_duplicates(subset=['Código'])
            df = df[df['Código'].astype(str).str.match(r'^\d{8}$')]
            print(f"[INFO] Registros despues de limpieza: {len(df)}")
            
            registros_importados = 0
            for _, row in df.iterrows():
                try:
                    codigo = str(row['Código']).strip()
                    descripcion = str(row.get('Descripción', '')).strip()
                    clase = str(row.get('Clase', '')).strip()
                    familia = str(row.get('Familia', '')).strip()
                    segmento = str(row.get('Segmento', '')).strip()
                    definicion = str(row.get('Definición', '')).strip()
                    auxiliar = str(row.get('Auxiliar', '')).strip()
                    denominacion = str(row.get('Denominación', '')).strip()
                    
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO catalogo_bienes 
                        (codigo, descripcion, clase, familia, segmento, definicion, auxiliar, denominacion)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (codigo, descripcion, clase, familia, segmento, definicion, auxiliar, denominacion))
                    
                    registros_importados += 1
                    
                    if registros_importados % 1000 == 0:
                        print(f"   Importados {registros_importados} registros...")
                        
                except Exception as e:
                    print(f"   [WARN] Error al importar {row['Código']}: {e}")
                    continue
            
            self.conn.commit()
            print(f"[OK] Importados {registros_importados} registros en catalogo_bienes")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error al importar: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def importar_imputaciones_presupuestarias(self, archivo_excel):
        """Importa las imputaciones presupuestarias desde Excel"""
        
        if not Path(archivo_excel).exists():
            print(f"[ERROR] Archivo no encontrado: {archivo_excel}")
            return False
        
        print(f"\n[INFO] Importando imputaciones desde: {archivo_excel}")
        
        try:
            df = pd.read_excel(archivo_excel)
            print(f"[INFO] Registros en archivo: {len(df)}")
            print(f"[INFO] Columnas: {list(df.columns)}")
            
            if 'Código' not in df.columns:
                print("[ERROR] Columna 'Codigo' no encontrada")
                return False
            
            df = df.drop_duplicates(subset=['Código'])
            df = df[df['Código'].astype(str).str.match(r'^\d{8}$')]
            print(f"[INFO] Registros despues de limpieza: {len(df)}")
            
            registros_importados = 0
            for _, row in df.iterrows():
                try:
                    codigo = str(row['Código']).strip()
                    descripcion = str(row.get('Descripción', row.get('Descripcion', ''))).strip()
                    definicion = str(row.get('Definición', row.get('Definicion', ''))).strip()
                    auxiliar = str(row.get('Auxiliar', '')).strip()
                    denominacion = str(row.get('Denominación', row.get('Denominacion', ''))).strip()
                    clase = str(row.get('Clase', '')).strip()
                    familia = str(row.get('Familia', '')).strip()
                    segmento = str(row.get('Segmento', '')).strip()
                    
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO imputaciones_presupuestarias 
                        (codigo, descripcion, definicion, auxiliar, denominacion, clase, familia, segmento)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (codigo, descripcion, definicion, auxiliar, denominacion, clase, familia, segmento))
                    
                    registros_importados += 1
                    
                    if registros_importados % 1000 == 0:
                        print(f"   Importados {registros_importados} registros...")
                        
                except Exception as e:
                    print(f"   [WARN] Error al importar {row['Código']}: {e}")
                    continue
            
            self.conn.commit()
            print(f"[OK] Importados {registros_importados} registros en imputaciones_presupuestarias")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error al importar: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verificar_importacion(self):
        """Verifica los datos importados"""
        
        total_catalogo = self.cursor.execute("SELECT COUNT(*) FROM catalogo_bienes").fetchone()[0]
        total_imputaciones = self.cursor.execute("SELECT COUNT(*) FROM imputaciones_presupuestarias").fetchone()[0]
        
        print(f"\n[INFO] Total en catalogo_bienes: {total_catalogo}")
        print(f"[INFO] Total en imputaciones_presupuestarias: {total_imputaciones}")
        
        if total_catalogo > 0:
            muestras = self.cursor.execute(
                "SELECT codigo, descripcion FROM catalogo_bienes LIMIT 5"
            ).fetchall()
            print("\n[INFO] Muestras del catalogo:")
            for codigo, desc in muestras:
                print(f"   {codigo}: {desc[:50]}...")
        
        if total_imputaciones > 0:
            muestras = self.cursor.execute(
                "SELECT codigo, descripcion, auxiliar FROM imputaciones_presupuestarias LIMIT 5"
            ).fetchall()
            print("\n[INFO] Muestras de imputaciones:")
            for codigo, desc, aux in muestras:
                print(f"   {codigo}: {desc[:40]}... | {aux}")
        
        return total_catalogo > 0 or total_imputaciones > 0

def main():
    """Funcion principal"""
    
    print("=" * 70)
    print("IMPORTADOR DE GUIA ALFABETICA - UNSPSC DGCP")
    print("=" * 70)
    
    importador = ImportadorGuiaAlfabetica()
    
    try:
        importador.conectar_db()
        importador.crear_tablas()
        
        archivos = [
            'catalogo_bienes_servicios_tablas.xlsx',
            'guia_alfabetica_imputaciones.xlsx',
            'BASE_DATOS_CUENTAS_DGCP.xlsx'
        ]
        
        print("\n[INFO] Archivos disponibles:")
        for archivo in archivos:
            existe = "[OK]" if Path(archivo).exists() else "[NO]"
            print(f"   {existe} {archivo}")
        
        for archivo in archivos:
            if Path(archivo).exists():
                if 'catalogo' in archivo.lower():
                    print(f"\n[INFO] Procesando: {archivo}")
                    importador.importar_catalogo_bienes(archivo)
                elif 'guia' in archivo.lower() or 'imputacion' in archivo.lower():
                    print(f"\n[INFO] Procesando: {archivo}")
                    importador.importar_imputaciones_presupuestarias(archivo)
                elif 'cuentas' in archivo.lower():
                    print(f"\n[INFO] Procesando: {archivo}")
                    importador.importar_imputaciones_presupuestarias(archivo)
            else:
                print(f"[INFO] Archivo no encontrado: {archivo}")
        
        print("\n" + "=" * 70)
        print("VERIFICANDO IMPORTACION")
        print("=" * 70)
        importador.verificar_importacion()
        
        print("\n" + "=" * 70)
        print("IMPORTACION COMPLETADA")
        print("=" * 70)
        print(f"Base de datos: {importador.db_path}")
        print("\nPara ejecutar la aplicacion:")
        print("   python -m streamlit run app.py")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        importador.cerrar_db()

if __name__ == "__main__":
    main()