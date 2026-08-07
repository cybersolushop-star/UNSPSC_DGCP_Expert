# guardar_logo.py
from logosvg import generar_logo
from pathlib import Path

def guardar_logo():
    """Guarda el logo en la carpeta data como logo.png"""
    # Crear el directorio data si no existe
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Generar el logo
    logo_buffer = generar_logo()
    
    # Guardar el logo como archivo
    logo_path = data_dir / "logo.png"
    with open(logo_path, "wb") as f:
        f.write(logo_buffer.getvalue())
    
    print(f"✅ Logo guardado en: {logo_path}")

if __name__ == "__main__":
    guardar_logo()