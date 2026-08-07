# logosvg.py
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon
import matplotlib.transforms as transforms
import io

def generar_logo():
    """Genera el logo y devuelve los datos de la imagen en un buffer"""
    # Crear figura
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Colores
    azul = "#052A66"
    gris = "#D9D9D9"
    gris_oscuro = "#BFC3C7"
    verde = "#BFDCCF"
    rojo = "#D70F1A"
    
    # -----------------------
    # LUPA
    # -----------------------
    # Aro exterior
    ax.add_patch(
        Circle((45, 55), 30, fill=False, linewidth=8, edgecolor=azul)
    )
    
    # Mango de la lupa
    mango = Rectangle((66, 28), 20, 8,
                      facecolor=rojo,
                      edgecolor='white',
                      linewidth=1.5)
    t = transforms.Affine2D().rotate_deg_around(66, 28, -45)
    mango.set_transform(t + ax.transData)
    ax.add_patch(mango)
    
    # -----------------------
    # SUELO VERDE
    # -----------------------
    suelo = Polygon(
        [(30, 33), (40, 36), (55, 36), (63, 33), (58, 31), (34, 31)],
        closed=True,
        facecolor=verde,
        edgecolor='none'
    )
    ax.add_patch(suelo)
    
    # -----------------------
    # EDIFICIO IZQUIERDO OSCURO
    # -----------------------
    ax.add_patch(Rectangle((25, 35), 7, 28,
                           facecolor=azul,
                           edgecolor='white'))
    
    # -----------------------
    # EDIFICIO IZQUIERDO CLARO
    # -----------------------
    ax.add_patch(Rectangle((32, 35), 7, 20,
                           facecolor=gris,
                           edgecolor='white'))
    
    for y in [40, 44, 48]:
        ax.add_patch(Rectangle((33, y), 5, 1.2,
                               facecolor='white',
                               edgecolor='white'))
    
    # -----------------------
    # TORRE CENTRAL
    # -----------------------
    frente = Polygon(
        [(39, 35), (50, 35), (50, 70), (39, 63)],
        closed=True,
        facecolor=azul,
        edgecolor='white'
    )
    
    lado = Polygon(
        [(50, 35), (56, 35), (56, 63), (50, 70)],
        closed=True,
        facecolor=gris,
        edgecolor='white'
    )
    
    ax.add_patch(frente)
    ax.add_patch(lado)
    
    for x in [42, 44, 46, 48]:
        ax.plot([x, x], [40, 58], color='white', linewidth=1.8)
    
    # -----------------------
    # EDIFICIO CENTRAL DERECHO
    # -----------------------
    frente = Polygon(
        [(50, 35), (59, 35), (59, 52), (50, 58)],
        closed=True,
        facecolor=azul,
        edgecolor='white'
    )
    
    lado = Polygon(
        [(59, 35), (65, 35), (65, 52), (59, 58)],
        closed=True,
        facecolor=gris,
        edgecolor='white'
    )
    
    ax.add_patch(frente)
    ax.add_patch(lado)
    
    for y in [39, 43, 47, 51]:
        ax.add_patch(Rectangle((51.5, y), 5, 1,
                               facecolor='white',
                               edgecolor='white'))
    
    # -----------------------
    # EDIFICIO DERECHO
    # -----------------------
    ax.add_patch(Rectangle((60, 35), 6, 16,
                           facecolor=gris,
                           edgecolor='white'))
    
    for x in [62, 64]:
        for y in [39, 43, 47]:
            ax.add_patch(Rectangle((x, y), 0.8, 0.8,
                                   facecolor='white',
                                   edgecolor='white'))
    
    plt.tight_layout()
    
    # Guardar en un buffer de memoria en lugar de archivo
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                facecolor='white', transparent=False)
    buf.seek(0)
    plt.close()
    
    return buf