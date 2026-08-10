# verificar_pdf.py
import pdfplumber
from pathlib import Path

def verificar_pdf():
    ruta_pdf = Path("data/CATALOGO DIGEPRES SIN CUENTAS.pdf")
    
    if not ruta_pdf.exists():
        print(f"❌ No se encontró el archivo: {ruta_pdf}")
        print(f"📁 Buscando en: {ruta_pdf.absolute()}")
        return
    
    print(f"📄 Verificando: {ruta_pdf}")
    print("="*60)
    
    with pdfplumber.open(ruta_pdf) as pdf:
        for i, pagina in enumerate(pdf.pages[:3]):  # Solo primeras 3 páginas
            print(f"\n📄 Página {i+1}:")
            tablas = pagina.extract_tables()
            if tablas:
                for tabla in tablas:
                    if tabla:
                        print(f"  Tabla encontrada con {len(tabla)} filas")
                        # Mostrar primeras 5 filas
                        for j, fila in enumerate(tabla[:5]):
                            if fila:
                                print(f"    Fila {j+1}: {fila}")
                        break
            else:
                print("  No se encontraron tablas en esta página")

if __name__ == "__main__":
    verificar_pdf()