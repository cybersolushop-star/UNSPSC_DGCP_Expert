"""
Script para guardar el logo como SVG
"""
from pathlib import Path

# El código SVG de tu logo (lo extraemos de matplotlib)
SVG_LOGO = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="200" height="200">
    <!-- Fondo redondo -->
    <circle cx="50" cy="50" r="48" fill="#052A66" stroke="white" stroke-width="2"/>
    
    <!-- Lupa - Aro -->
    <circle cx="45" cy="45" r="25" fill="none" stroke="white" stroke-width="5"/>
    
    <!-- Lupa - Mango -->
    <line x1="65" y1="65" x2="85" y2="85" stroke="#D70F1A" stroke-width="8" stroke-linecap="round"/>
    
    <!-- Suelo verde -->
    <polygon points="30,70 40,75 55,75 63,70 58,67 34,67" fill="#BFDCCF"/>
    
    <!-- Edificio izquierdo oscuro -->
    <rect x="25" y="45" width="7" height="25" fill="#052A66" stroke="white" stroke-width="1"/>
    
    <!-- Edificio izquierdo claro -->
    <rect x="32" y="45" width="7" height="20" fill="#D9D9D9" stroke="white" stroke-width="1"/>
    <rect x="33" y="48" width="5" height="2" fill="white"/>
    <rect x="33" y="52" width="5" height="2" fill="white"/>
    <rect x="33" y="56" width="5" height="2" fill="white"/>
    
    <!-- Torre central - Frente -->
    <polygon points="39,45 50,45 50,70 39,63" fill="#052A66" stroke="white" stroke-width="1"/>
    
    <!-- Torre central - Lado -->
    <polygon points="50,45 56,45 56,63 50,70" fill="#D9D9D9" stroke="white" stroke-width="1"/>
    
    <!-- Ventanas torre central -->
    <line x1="42" y1="48" x2="42" y2="60" stroke="white" stroke-width="2"/>
    <line x1="44" y1="48" x2="44" y2="60" stroke="white" stroke-width="2"/>
    <line x1="46" y1="48" x2="46" y2="60" stroke="white" stroke-width="2"/>
    <line x1="48" y1="48" x2="48" y2="60" stroke="white" stroke-width="2"/>
    
    <!-- Edificio central derecho -->
    <polygon points="50,45 59,45 59,58 50,62" fill="#052A66" stroke="white" stroke-width="1"/>
    <polygon points="59,45 65,45 65,58 59,62" fill="#D9D9D9" stroke="white" stroke-width="1"/>
    
    <!-- Ventanas edificio central derecho -->
    <rect x="52" y="48" width="4" height="2" fill="white"/>
    <rect x="52" y="52" width="4" height="2" fill="white"/>
    <rect x="52" y="56" width="4" height="2" fill="white"/>
    
    <!-- Edificio derecho -->
    <rect x="60" y="45" width="6" height="16" fill="#D9D9D9" stroke="white" stroke-width="1"/>
    
    <!-- Ventanas edificio derecho -->
    <rect x="62" y="48" width="2" height="2" fill="white"/>
    <rect x="64" y="48" width="2" height="2" fill="white"/>
    <rect x="62" y="52" width="2" height="2" fill="white"/>
    <rect x="64" y="52" width="2" height="2" fill="white"/>
    <rect x="62" y="56" width="2" height="2" fill="white"/>
    <rect x="64" y="56" width="2" height="2" fill="white"/>
</svg>
"""

def guardar_svg():
    """Guarda el logo como SVG en la carpeta data"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    svg_path = data_dir / "logo.svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(SVG_LOGO)
    
    print(f"✅ Logo SVG guardado en: {svg_path}")
    
    # También guardamos una versión HTML para copiar directamente
    html_path = data_dir / "logo_html.txt"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(SVG_LOGO)
    
    print(f"✅ Versión HTML guardada en: {html_path}")
    print(f"\n📋 Para usarlo en Streamlit, copia el código de:")
    print(f"   {html_path}")

if __name__ == "__main__":
    guardar_svg()