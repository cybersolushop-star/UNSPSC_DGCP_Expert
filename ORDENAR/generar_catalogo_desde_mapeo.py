import pandas as pd
import os

print('='*70)
print('  🏛️ GENERACIÓN DE CATÁLOGO DESDE MAPEO_COMPLETO.XLSX')
print('='*70)

# Verificar que existe mapeo_completo.xlsx
if not os.path.exists('mapeo_completo.xlsx'):
    print('❌ Error: No se encuentra mapeo_completo.xlsx')
    exit(1)

# Cargar mapeo_completo.xlsx (este es tu catálogo completo)
mapeo = pd.read_excel('mapeo_completo.xlsx')
print(f'✅ Mapeo DIGEPRES (catálogo completo): {len(mapeo)} ítems')
print(f'Columnas: {mapeo.columns.tolist()}')

# El archivo ya tiene todas las columnas necesarias:
# - Código: Código UNSPSC
# - Descripción: Descripción del ítem
# - Definición: Definición del ítem
# - Auxiliar: Cuenta DIGEPRES
# - Denominación: Descripción de la cuenta DIGEPRES

# Renombrar columnas para consistencia
mapeo.rename(columns={
    'Código': 'Código',
    'Descripción': 'Descripción',
    'Definición': 'Definición',
    'Auxiliar': 'cuenta_digepres',
    'Denominación': 'descripcion_digepres'
}, inplace=True)

# Guardar como catalogo_final.csv
mapeo.to_csv('catalogo_final.csv', index=False)
mapeo.to_excel('catalogo_final.xlsx', index=False)

print('\n📊 RESULTADO FINAL')
print('='*70)
print(f'Total ítems en catálogo: {len(mapeo)}')
print(f'Con cuenta DIGEPRES: {mapeo["cuenta_digepres"].notna().sum()}')
print(f'Sin cuenta DIGEPRES: {mapeo["cuenta_digepres"].isna().sum()}')
print(f'Cuentas DIGEPRES únicas: {mapeo["cuenta_digepres"].nunique()}')

print('\n✅ Archivos generados:')
print('  - catalogo_final.csv (con todos los ítems)')
print('  - catalogo_final.xlsx (con todos los ítems)')

print('\n📋 MUESTRA DE 5 ÍTEMS:')
print(mapeo[['Código', 'Descripción', 'cuenta_digepres', 'descripcion_digepres']].head(5).to_string(index=False))

print('\n' + '='*70)
print('✅ ¡PROCESO COMPLETADO CON ÉXITO!')