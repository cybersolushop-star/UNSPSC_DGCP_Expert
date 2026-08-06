"""
Aplicación principal UNSPSC DGCP Buscador - Punto de entrada desde raíz
"""

import sys
import os
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar la aplicación desde src
from src.app import main

if __name__ == "__main__":
    main()