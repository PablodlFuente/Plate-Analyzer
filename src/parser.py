"""
Módulo para analizar archivos Excel de datos de placas.
"""
import pandas as pd
import numpy as np
import re

def parse_spectro_excel(file_path):
    """
    Analiza un archivo Excel con datos de espectrofotometría de placas.
    
    Args:
        file_path (str): Ruta al archivo Excel.
        
    Returns:
        pandas.DataFrame: DataFrame con los datos analizados.
    """
    raw = pd.read_excel(file_path, header=None)
    records = []
    nrows = raw.shape[0]
    i = 0
    
    # Patrones regex para número de placa, ensayo, tiempo y unidad
    pat_plate = re.compile(r'(P\d+)', re.IGNORECASE)
    pat_assay = re.compile(r'(?:(?<=_)|^)(AB|ROS)(?:(?=_)|$)', re.IGNORECASE)
    pat_hours = re.compile(r'(\d+(?:\.\d+)?)(?=[hm])', re.IGNORECASE)
    pat_unit = re.compile(r'([hm])', re.IGNORECASE)

    while i < nrows:
        cell = str(raw.iat[i, 0]).strip()
        if cell.startswith("Plate"):  # Inicio de un bloque de placa
            plate_full = str(raw.iat[i, 1]).strip()
            m_plate = pat_plate.search(plate_full)
            m_assay = pat_assay.search(plate_full)
            m_hours = pat_hours.search(plate_full)
            m_unit = pat_unit.search(plate_full)

            # Extraer o usar NaN por defecto
            plate_no = m_plate.group(1).upper() if m_plate else np.nan
            assay = m_assay.group(1).upper() if m_assay else 'NaN'  # Default to 'NaN' for invalid assays
            if m_hours:
                val = float(m_hours.group(1))  # Convert to float to handle decimal hours
                hours = val / 60.0 if m_unit and m_unit.group(1).lower() == 'm' else val
            else:
                hours = np.nan

            data_list = []
            j = i + 2  # Saltar filas de encabezado
            # Leer hasta el marcador ~End
            while j < nrows and str(raw.iat[j, 0]).strip() != "~End":
                row = raw.iloc[j, 2:14].astype(float)
                if not row.isna().all():
                    data_list.extend(row.tolist())
                j += 1

            # Solo mantener placas completas
            if len(data_list) == 96:
                data_arr = np.array(data_list, dtype=float).reshape(8, 12)
                records.append({
                    'plate_no': plate_no,
                    'assay': assay,
                    'hours': hours,
                    'data': data_arr
                })
            i = j + 1
        else:
            i += 1

    return pd.DataFrame(records)
