# verificar_tabla_sinonimos.py
import sqlite3

def verificar_tabla():
    conn = sqlite3.connect("db/DGCP_UNSPSC.db")
    cur = conn.cursor()
    
    # Verificar si la tabla existe
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sinonimos'")
    tabla = cur.fetchone()
    
    if tabla:
        print("✅ La tabla 'sinonimos' existe")
        cur.execute("SELECT COUNT(*) FROM sinonimos")
        count = cur.fetchone()[0]
        print(f"📊 Total de relaciones: {count}")
        
        if count > 0:
            cur.execute("SELECT termino, sinonimo FROM sinonimos LIMIT 5")
            ejemplos = cur.fetchall()
            print("\n📋 Ejemplos de sinónimos:")
            for t, s in ejemplos:
                print(f"  • {t} ↔ {s}")
        else:
            print("⚠️ La tabla está vacía")
    else:
        print("❌ La tabla 'sinonimos' NO existe")
    
    conn.close()

if __name__ == "__main__":
    verificar_tabla()