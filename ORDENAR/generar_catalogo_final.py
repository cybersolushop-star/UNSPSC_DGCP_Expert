import pandas as pd
import os

print('='*70)
print('  🏛️ GENERACIÓN DE CATÁLOGO FINAL CON DIGEPRES')
print('='*70)

# Verificar que existe mapeo_completo.xlsx
if not os.path.exists('mapeo_completo.xlsx'):
    print('❌ Error: No se encuentra mapeo_completo.xlsx')
    print('   Asegúrate de tener el archivo en la carpeta actual')
    exit(1)

# Cargar archivos
print('\n📂 Cargando archivos...')

# Cargar catálogo original
catalogo = pd.read_csv('catalogo_bienes_servicios_tablas.csv')
print(f'   ✅ Catálogo DGCP: {len(catalogo)} ítems')

# Cargar mapeo DIGEPRES
mapeo = pd.read_excel('mapeo_completo.xlsx')
print(f'   ✅ Mapeo DIGEPRES: {len(mapeo)} ítems')

# Mostrar columnas para verificación
print(f'\n📋 Columnas en mapeo_completo.xlsx:')
print(f'   {mapeo.columns.tolist()}')

# Verificar que tiene las columnas necesarias
columnas_requeridas = ['Código', 'Auxiliar', 'Denominación']
for col in columnas_requeridas:
    if col not in mapeo.columns:
        print(f'❌ Error: No se encuentra la columna "{col}" en mapeo_completo.xlsx')
        exit(1)

# Crear DataFrame con solo las columnas necesarias del mapeo
mapeo_clean = mapeo[['Código', 'Auxiliar', 'Denominación']].copy()
mapeo_clean.columns = ['codigo_unspsc', 'cuenta_digepres', 'descripcion_digepres']

print(f'\n📋 Mapeo limpio: {len(mapeo_clean)} registros')

# Integrar con el catálogo
print('\n🔄 Integrando datos...')

catalogo_con_digepres = pd.merge(
    catalogo,
    mapeo_clean,
    left_on='Código',
    right_on='codigo_unspsc',
    how='left'
)

# Eliminar duplicados (si los hay)
catalogo_unique = catalogo_con_digepres.drop_duplicates(subset=['Código'])

# Generar estadísticas
total = len(catalogo_unique)
con_digepres = catalogo_unique['cuenta_digepres'].notna().sum()
sin_digepres = total - con_digepres
cuentas_unicas = catalogo_unique['cuenta_digepres'].nunique()

# Guardar archivos
print('\n💾 Guardando archivos...')

catalogo_unique.to_csv('catalogo_final.csv', index=False)
catalogo_unique.to_excel('catalogo_final.xlsx', index=False)

print('   ✅ catalogo_final.csv guardado')
print('   ✅ catalogo_final.xlsx guardado')

# Mostrar resultados
print('\n' + '='*70)
print('📊 RESULTADO FINAL')
print('='*70)
print(f'Total ítems únicos: {total:,}')
print(f'Con cuenta DIGEPRES: {con_digepres:,} ({con_digepres/total*100:.1f}%)')
print(f'Sin cuenta DIGEPRES: {sin_digepres:,} ({sin_digepres/total*100:.1f}%)')
print(f'Cuentas DIGEPRES únicas: {cuentas_unicas:,}')

# Mostrar top 10 cuentas
print('\n📋 TOP 10 CUENTAS DIGEPRES MÁS USADAS:')
print('-'*50)
top_cuentas = catalogo_unique['descripcion_digepres'].value_counts().head(10)
for i, (cuenta, count) in enumerate(top_cuentas.items(), 1):
    print(f'   {i:2}. {cuenta}: {count:,} ítems')

# Mostrar muestra
print('\n📋 MUESTRA DE 5 ÍTEMS:')
print('-'*70)
print(catalogo_unique[['Código', 'Descripción', 'Familia', 'cuenta_digepres', 'descripcion_digepres']].head(5).to_string(index=False))

print('\n' + '='*70)
print('✅ ¡PROCESO COMPLETADO CON ÉXITO!')
print('='*70)