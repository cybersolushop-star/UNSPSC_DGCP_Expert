"""
Módulo de exportación para UNSPSC DGCP
"""

import pandas as pd
from io import BytesIO

def generar_excel(df: pd.DataFrame) -> BytesIO:
    """
    Genera un archivo Excel a partir de un DataFrame
    
    Args:
        df: DataFrame con los datos a exportar
    
    Returns:
        BytesIO con el archivo Excel
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
        
        # Ajustar ancho de columnas
        for column in df.columns:
            column_width = max(df[column].astype(str).map(len).max(), len(column))
            column_width = min(column_width, 50)
            col_idx = df.columns.get_loc(column)
            writer.sheets['Resultados'].column_dimensions[chr(65 + col_idx)].width = column_width + 2
    
    output.seek(0)
    return output