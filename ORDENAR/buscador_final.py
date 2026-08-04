import pandas as pd

try:
    df = pd.read_csv('catalogo_unique.csv')
except FileNotFoundError:
    print('⚠️ Ejecuta primero: python -c "import pandas as pd; df=pd.read_csv(\'catalogo_con_digepres_clean.csv\'); df_sin_duplicados=df.drop_duplicates(subset=[\'Código\']); df_sin_duplicados.to_csv(\'catalogo_unique.csv\', index=False); print(\'✅ Archivo creado\')"')
    exit()

print('🔍 BUSCADOR DE ÍTEMS CON DIGEPRES')
print('='*70)
print(f'Total: {len(df)} ítems únicos con DIGEPRES')
print(f'Cuentas DIGEPRES únicas: {df["cuenta_digepres"].nunique()}')
print('='*70)

while True:
    busqueda = input('\n📝 Ingresa código o descripción (o "salir"): ').strip()
    
    if busqueda.lower() in ['salir', 'exit', 'q']:
        print('👋 ¡Hasta luego!')
        break
    
    if len(busqueda) < 2:
        print('⚠️ Ingresa al menos 2 caracteres')
        continue
    
    resultado = df[
        df['Código'].astype(str).str.contains(busqueda, case=False, na=False) |
        df['Descripción'].astype(str).str.contains(busqueda, case=False, na=False)
    ]
    
    print(f'\n🔍 Resultados para "{busqueda}": {len(resultado)} ítems')
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