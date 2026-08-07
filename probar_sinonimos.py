"""
Script para probar la carga de sinónimos desde database.py
"""

import sys
sys.path.insert(0, 'src')
from database import DatabaseManager

db = DatabaseManager()
sinonimos = db.cargar_sinonimos()

print(f"📊 Sinónimos cargados: {len(sinonimos)}")
print(f"¿refrigerio en sinonimos? {'refrigerio' in sinonimos}")

if 'Servicios de cáterin' in sinonimos:
    print(f"✅ 'Servicios de cáterin' encontrado")
    print(f"   Sinónimos: {sinonimos['Servicios de cáterin'][:5]}")
else:
    print("❌ 'Servicios de cáterin' NO encontrado")