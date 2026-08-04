"""
Script para verificar un código específico en la base de datos
"""

import sqlite3
import sys

def verificar_codigo(codigo: str):
    """Verifica un código en la base de datos"""
    
    conn = sqlite3.connect('db/DGCP_UNSPSC.db')
    cursor = conn.cursor()
    
    print("=" * 70)
    print(f"VERIFICANDO CODIGO: {codigo}")
    print("=" * 70)
    
    # Buscar en imputaciones_presupuestarias
    cursor.execute("""
        SELECT codigo, descripcion, definicion, auxiliar, denominacion 
        FROM imputaciones_presupuestarias 
        WHERE codigo = ?
    """, (codigo,))
    
    row = cursor.fetchone()
    if row:
        print("\n[INFO] Datos en imputaciones_presupuestarias:")
        print(f"   Codigo: {row[0]}")
        print(f"   Descripcion: {row[1]}")
        print(f"   Definicion: {row[2]}")
        print(f"   Auxiliar (Cuenta): {row[3]}")
        print(f"   Denominacion: {row[4]}")
    else:
        print("\n[INFO] No encontrado en imputaciones_presupuestarias")
        
        # Buscar en catalogo_bienes
        cursor.execute("""
            SELECT codigo, descripcion, auxiliar, denominacion 
            FROM catalogo_bienes 
            WHERE codigo = ?
        """, (codigo,))
        
        row = cursor.fetchone()
        if row:
            print("\n[INFO] Datos en catalogo_bienes:")
            print(f"   Codigo: {row[0]}")
            print(f"   Descripcion: {row[1]}")
            print(f"   Auxiliar: {row[2]}")
            print(f"   Denominacion: {row[3]}")
        else:
            print("\n[INFO] No encontrado en catalogo_bienes")
    
    conn.close()

if __name__ == "__main__":
    codigo = sys.argv[1] if len(sys.argv) > 1 else "42262105"
    verificar_codigo(codigo)