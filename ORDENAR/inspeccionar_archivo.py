import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ARCHIVO = BASE_DIR / "data" / "codificacion_digepres.xlsx"

df = pd.read_excel(ARCHIVO)

print("📊 ESTADÍSTICAS DEL ARCHIVO:")
print(f"   Total de filas: {len(df)}")
print(f"\n📋 Columnas: {list(df.columns)}")
print(f"\n🔍 Tipos de datos:")
print(df.dtypes)

# Verificar valores nulos en 'Auxiliar'
nulos = df['Auxiliar'].isna().sum()
print(f"\n📌 Valores nulos en 'Auxiliar': {nulos}")

# Verificar valores vacíos en 'Auxiliar'
vacios = (df['Auxiliar'] == '').sum()
print(f"📌 Valores vacíos en 'Auxiliar': {vacios}")

# Mostrar algunos ejemplos de valores en 'Auxiliar'
print(f"\n📋 Ejemplos de valores en 'Auxiliar' (primeros 10):")
print(df['Auxiliar'].head(10).tolist())

# Verificar cuántos valores únicos en 'Auxiliar'
print(f"\n📌 Valores únicos en 'Auxiliar': {df['Auxiliar'].nunique()}")

# Mostrar la distribución de valores en 'Auxiliar'
print(f"\n📊 Distribución de valores en 'Auxiliar' (top 5):")
print(df['Auxiliar'].value_counts().head(5))