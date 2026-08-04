import pandas as pd
import sys

# Cargar el catálogo
catalogo = pd.read_csv('catalogo_bienes_servicios_tablas.csv')
print(f'📊 Catálogo: {len(catalogo)} ítems')

# Cargar el mapeo completo (usando mapeo_completo.xlsx)
mapeo = pd.read_excel('mapeo_completo.xlsx')
print(f'📊 Mapeo: {len(mapeo)} ítems')

# Renombrar columnas del mapeo para claridad
mapeo.rename(columns={
    'Código': 'codigo_unspsc',
    'Auxiliar': 'cuenta_digepres',
    'Denominación': 'descripcion_digepres'
}, inplace=True)

# Unir los datos
catalogo_con_digepres = pd.merge(
    catalogo,
    mapeo[['codigo_unspsc', 'cuenta_digepres', 'descripcion_digepres']],
    left_on='Código',
    right_on='codigo_unspsc',
    how='left'
)

# Guardar
catalogo_con_digepres.to_csv('catalogo_con_digepres.csv', index=False)
print('✅ Archivo integrado: catalogo_con_digepres.csv')
print(f'Total: {len(catalogo_con_digepres)} ítems')
print(f'Con cuenta DIGEPRES: {catalogo_con_digepres["cuenta_digepres"].notna().sum()}')
print(f'Sin cuenta DIGEPRES: {catalogo_con_digepres["cuenta_digepres"].isna().sum()}')

# Eliminar duplicados
catalogo_unique = catalogo_con_digepres.drop_duplicates(subset=['Código'])
catalogo_unique.to_csv('catalogo_unique.csv', index=False)
print(f'✅ Sin duplicados: {len(catalogo_unique)} ítems únicos')

def buscar_item(termino):
    resultado = catalogo_unique[
        catalogo_unique['Código'].astype(str).str.contains(termino, case=False, na=False) |
        catalogo_unique['Descripción'].astype(str).str.contains(termino, case=False, na=False)
    ]
    return resultado

if len(sys.argv) > 1:
    termino = sys.argv[1]
    resultado = buscar_item(termino)
    print(f'\n🔍 Resultados para "{termino}": {len(resultado)} ítems')
    print('='*70)
    if len(resultado) > 0:
        columnas = ['Código', 'Descripción', 'Familia', 'cuenta_digepres', 'descripcion_digepres']
        for _, row in resultado.head(20).iterrows():
            print(f"📌 {row['Código']} - {row['Descripción']}")
            if pd.notna(row['cuenta_digepres']):
                print(f"   DIGEPRES: {row['cuenta_digepres']} - {row['descripcion_digepres']}")
            else:
                print("   DIGEPRES: ⚠️ Sin asignar")
            print()
        if len(resultado) > 20:
            print(f'... y {len(resultado)-20} más')
    else:
        print('❌ No se encontraron ítems')
else:
    print('\n📋 Uso: python integrar_codificacion_por_item.py <código o descripción>')
    print('Ejemplo: python integrar_codificacion_por_item.py 10101501')
    print('Ejemplo: python integrar_codificacion_por_item.py Gatos')
    print('Ejemplo: python integrar_codificacion_por_item.py computadora')