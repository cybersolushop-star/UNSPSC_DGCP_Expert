import base64
from pathlib import Path

def convertir_logo_a_base64():
    """Convierte el logo a Base64 para incrustarlo en el código"""
    logo_path = Path("data/logo.png")
    
    if not logo_path.exists():
        print(f"❌ Logo no encontrado en: {logo_path}")
        return None
    
    with open(logo_path, "rb") as f:
        logo_bytes = f.read()
        logo_base64 = base64.b64encode(logo_bytes).decode()
    
    # Guardar el Base64 en un archivo
    output_path = Path("data/logo_base64.txt")
    with open(output_path, "w") as f:
        f.write(logo_base64)
    
    print(f"✅ Logo convertido a Base64")
    print(f"📁 Guardado en: {output_path}")
    print(f"📏 Longitud: {len(logo_base64)} caracteres")
    
    # Mostrar los primeros 100 caracteres
    print(f"\n🔑 Primeros 100 caracteres:")
    print(logo_base64[:100] + "...")
    
    return logo_base64

if __name__ == "__main__":
    convertir_logo_a_base64()