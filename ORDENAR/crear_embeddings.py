"""
Script para crear el archivo de embeddings válido
"""

import torch
import numpy as np
import pandas as pd
import sqlite3
from pathlib import Path
from sentence_transformers import SentenceTransformer
import warnings
warnings.filterwarnings('ignore')

def crear_embeddings():
    """Crea el archivo de embeddings a partir de la base de datos"""
    
    print("=" * 70)
    print("CREANDO ARCHIVO DE EMBEDDINGS")
    print("=" * 70)
    
    # Conectar a la base de datos
    db_path = Path("db/DGCP_UNSPSC.db")
    if not db_path.exists():
        print(f"[ERROR] Base de datos no encontrada: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Cargar catálogo
        df = pd.read_sql("SELECT * FROM catalogo", conn)
        
        if df.empty:
            print("[ERROR] Catálogo vacío")
            return False
        
        print(f"[INFO] Catálogo cargado: {len(df)} registros")
        
        # Crear textos para embeddings (combinar descripción + definición)
        textos = []
        codigos = []
        
        for _, row in df.iterrows():
            texto = f"{row['Descripción']} {row['Definición']} {row['Segmento']} {row['Familia']} {row['Clase']}"
            textos.append(str(texto))
            codigos.append(str(row['Código UNSPSC']))
        
        print(f"[INFO] Generando embeddings para {len(textos)} textos...")
        
        # Cargar modelo
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # Generar embeddings en batches
        batch_size = 100
        embeddings_list = []
        
        for i in range(0, len(textos), batch_size):
            batch = textos[i:i+batch_size]
            batch_embeddings = model.encode(batch, convert_to_numpy=True)
            embeddings_list.append(batch_embeddings)
            print(f"   Procesados {min(i+batch_size, len(textos))} de {len(textos)}")
        
        # Combinar embeddings
        embeddings = np.vstack(embeddings_list)
        
        print(f"[INFO] Embeddings generados: {embeddings.shape}")
        
        # Guardar en formato compatible
        data = {
            'embeddings': torch.tensor(embeddings),
            'codigos': codigos
        }
        
        # Guardar
        torch.save(data, 'db/embeddings.pt')
        print(f"[OK] Embeddings guardados en db/embeddings.pt")
        
        # Verificar
        verify = torch.load('db/embeddings.pt', map_location='cpu')
        print(f"[VERIFICACION] Embeddings: {verify['embeddings'].shape}")
        print(f"[VERIFICACION] Códigos: {len(verify['codigos'])}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    crear_embeddings()