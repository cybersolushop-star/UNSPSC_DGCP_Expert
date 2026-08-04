import torch

embeddings = torch.load("db/embeddings.pt", map_location="cpu")

print("📊 Tipo:", type(embeddings))
print("📊 Claves:", embeddings.keys() if isinstance(embeddings, dict) else "No es diccionario")

if isinstance(embeddings, dict):
    for key, value in embeddings.items():
        print(f"   - {key}: {type(value)}")
        if isinstance(value, torch.Tensor):
            print(f"     Shape: {value.shape}")
else:
    print(f"📊 Shape: {embeddings.shape}")
    print(f"📊 Primeros 5 valores: {embeddings[:5]}")