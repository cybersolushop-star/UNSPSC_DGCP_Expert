import pandas as pd
import sys

try:
    df = pd.read_csv('catalogo_final.csv')
except FileNotFoundError:
    print('⚠️ Ejecuta primero: python integrar_final.py')
    exit()

print('🔍 BUSCADOR CATÁLOGO + DIGEPRES')
print('='*70)
print(f'Total: {len(df)} ítems')
print(f'Con DIGEPRES: {df["cuenta_digepres"].notna().sum()}')
print(f'Sin DIGEPRES: {df["cuenta_digepres"].isna().sum()}')
print('='*70)

def buscar(termino):
    resultado = df[
        df['Código'].astype(str).str.contains(termino, case=False, na=False) |
        df['Descripción'].astype(str).str.contains(termino, case=False, na=False)
    ]
    return resultado

if len(sys.argv) > 1:
    termino = sys.argv[1]
    resultado = buscar(termino)
    print(f'\n🔍 Resultados para "{termino}": {len(resultado)} ítems')
    print('-'*70)
    
    if len(resultado) == 0:
        print('❌ No se encontraron ítems')
    else:
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
    print('\n📋 Uso: python buscador_app.py <código o descripción>')
    print('Ejemplo: python buscador_app.py 10101501')
    print('Ejemplo: python buscador_app.py Gatos')