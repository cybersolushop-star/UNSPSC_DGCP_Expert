import torch
import numpy as np
from pathlib import Path

embeddings_file = Path("db/embeddings.pt")

print(f"Verificando archivo: {embeddings_file}")
print(f"¿Existe? {embeddings_file.exists()}")

if embeddings_file.exists():
    try:
        data = torch.load(embeddings_file, map_location='cpu')
        print(f"\nTipo de datos: {type(data)}")
        
        if isinstance(data, dict):
            print(f"Claves: {list(data.keys())}")
            
            if 'embeddings' in data:
                emb = data['embeddings']
                print(f"\nEmbeddings:")
                print(f"  Tipo: {type(emb)}")
                if isinstance(emb, torch.Tensor):
                    print(f"  Dimensiones: {emb.shape}")
                    print(f"  Número de elementos: {emb.numel()}")
                    print(f"  dtype: {emb.dtype}")
                    print(f"  device: {emb.device}")
                else:
                    print(f"  Shape: {np.array(emb).shape}")
            
            if 'codigos' in data:
                codigos = data['codigos']
                print(f"\nCódigos:")
                print(f"  Tipo: {type(codigos)}")
                print(f"  Longitud: {len(codigos)}")
                print(f"  Primeros 5: {codigos[:5]}")
        else:
            print(f"Contenido: {data}")
            
    except Exception as e:
        print(f"Error al cargar: {e}")