"""
Module for parsing plate data from Excel files.
"""
import pandas as pd
import numpy as np
import re

def parse_spectro_excel(file_path):
    """
    Parse a spectrophotometry plate data Excel file.
    
    Args:
        file_path (str): Path to the Excel file.
        
    Returns:
        pandas.DataFrame: DataFrame with the parsed data.
    """
    raw = pd.read_excel(file_path, header=None)
    records = []
    nrows = raw.shape[0]
    i = 0
    
    # Regex patterns for plate number, assay, time and unit
    pat_plate = re.compile(r'(P\d+)', re.IGNORECASE)
    pat_assay = re.compile(r'(?:(?<=_)|^)(AB|ROS)(?:(?=_)|$)', re.IGNORECASE)
    pat_hours = re.compile(r'(\d+(?:\.\d+)?)(?=[hm])', re.IGNORECASE)
    pat_unit = re.compile(r'([hm])', re.IGNORECASE)

    while i < nrows:
        cell = str(raw.iat[i, 0]).strip()
        if cell.startswith("Plate"):  # Start of a plate block
            plate_full = str(raw.iat[i, 1]).strip()
            m_plate = pat_plate.search(plate_full)
            m_assay = pat_assay.search(plate_full)
            m_hours = pat_hours.search(plate_full)
            m_unit = pat_unit.search(plate_full)

            # Extract or use default values
            plate_no = m_plate.group(1).upper() if m_plate else np.nan
            assay = m_assay.group(1).upper() if m_assay else 'NaN'  # Default to 'NaN' for invalid assays
            if m_hours:
                val = float(m_hours.group(1))  # Convert to float to handle decimal hours
                hours = val / 60.0 if m_unit and m_unit.group(1).lower() == 'm' else val
            else:
                hours = np.nan

            data_list = []
            j = i + 2  # Skip header rows
            # Read until ~End marker
            while j < nrows and str(raw.iat[j, 0]).strip() != "~End":
                row = raw.iloc[j, 2:14].astype(float)
                if not row.isna().all():
                    data_list.extend(row.tolist())
                j += 1

            # Only keep complete plates
            if len(data_list) == 96:
                # Convert to list to ensure JSON serialization
                data_arr = np.array(data_list, dtype=float).reshape(8, 12).tolist()
                records.append({
                    'plate_no': str(plate_no),  # Ensure plate_no is a string
                    'assay': str(assay),        # Ensure assay is a string
                    'hours': float(hours),      # Ensure hours is a float
                    'data': data_arr            # This is now a list of lists
                })
            i = j + 1
        else:
            i += 1

    return pd.DataFrame(records)
