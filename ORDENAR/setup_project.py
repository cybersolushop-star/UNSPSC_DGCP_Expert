"""
Script de configuración inicial del proyecto
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_project():
    """Configura el proyecto completo."""
    
    print("🚀 Configurando proyecto UNSPSC DGCP...")
    
    # Crear estructura de directorios
    directorios = ["db", "logs", "cache", "backup"]
    for dir_name in directorios:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"📁 Directorio creado: {dir_name}")
    
    # Verificar archivos necesarios
    archivos_requeridos = ["app.py", "requirements.txt", ".env"]
    for archivo in archivos_requeridos:
        if not Path(archivo).exists():
            print(f"⚠️ Archivo no encontrado: {archivo}")
    
    # Verificar base de datos
    db_path = Path("db/DGCP_UNSPSC.db")
    if not db_path.exists():
        print("❌ Base de datos no encontrada. Asegúrate de tener DGCP_UNSPSC.db en la carpeta db/")
    else:
        print(f"✅ Base de datos encontrada: {db_path}")
    
    # Verificar embeddings
    embeddings_path = Path("db/embeddings.pt")
    if not embeddings_path.exists():
        print("⚠️ Archivo de embeddings no encontrado. Se generará automáticamente al iniciar.")
    else:
        print(f"✅ Embeddings encontrados: {embeddings_path}")
    
    # Instalar dependencias
    print("\n📦 Instalando dependencias...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencias instaladas correctamente")
    except Exception as e:
        print(f"❌ Error al instalar dependencias: {e}")
    
    print("\n✨ Configuración completada!")
    print("\nPara iniciar la aplicación:")
    print("  streamlit run app.py")
    print("\nO con Makefile (si lo tienes):")
    print("  make run")

if __name__ == "__main__":
    setup_project()