import pandas as pd

print('📊 INTEGRACIÓN FINAL - CATÁLOGO + DIGEPRES')
print('='*60)

# Cargar archivos
catalogo = pd.read_csv('catalogo_bienes_servicios_tablas.csv')
print(f'✅ Catálogo: {len(catalogo)} ítems')

mapeo = pd.read_excel('mapeo_completo.xlsx')
print(f'✅ Mapeo DIGEPRES: {len(mapeo)} ítems')

# Renombrar columnas del mapeo
mapeo.rename(columns={
    'Código': 'codigo_unspsc',
    'Auxiliar': 'cuenta_digepres',
    'Denominación': 'descripcion_digepres'
}, inplace=True)

# Integrar
catalogo_con_digepres = pd.merge(
    catalogo,
    mapeo[['codigo_unspsc', 'cuenta_digepres', 'descripcion_digepres']],
    left_on='Código',
    right_on='codigo_unspsc',
    how='left'
)

# Eliminar duplicados
catalogo_unique = catalogo_con_digepres.drop_duplicates(subset=['Código'])

# Guardar archivo final
catalogo_unique.to_csv('catalogo_final.csv', index=False)
catalogo_unique.to_excel('catalogo_final.xlsx', index=False)

print('\n📊 RESULTADO FINAL')
print('='*60)
print(f'Total ítems únicos: {len(catalogo_unique)}')
print(f'Con cuenta DIGEPRES: {catalogo_unique["cuenta_digepres"].notna().sum()}')
print(f'Sin cuenta DIGEPRES: {catalogo_unique["cuenta_digepres"].isna().sum()}')
print(f'Cuentas DIGEPRES únicas: {catalogo_unique["cuenta_digepres"].nunique()}')

print('\n✅ Archivos generados:')
print('  - catalogo_final.csv')
print('  - catalogo_final.xlsx')

print('\n📋 TOP 10 CUENTAS DIGEPRES MÁS USADAS:')
print(catalogo_unique['descripcion_digepres'].value_counts().head(10))