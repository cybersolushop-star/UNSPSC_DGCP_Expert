import pandas as pd

# Cargar el archivo integrado
df = pd.read_csv('catalogo_con_digepres.csv')
print(f'📊 Total antes: {len(df)} ítems')

# Filtrar solo los que tienen cuenta DIGEPRES
df_clean = df[df['cuenta_digepres'].notna()]
print(f'📊 Total después: {len(df_clean)} ítems')
print(f'🗑️ Eliminados: {len(df) - len(df_clean)} ítems sin DIGEPRES')

# Guardar el archivo limpio
df_clean.to_csv('catalogo_con_digepres_clean.csv', index=False)
print('✅ Archivo guardado: catalogo_con_digepres_clean.csv')