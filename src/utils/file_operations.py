"""
Módulo para operaciones de archivos, como guardar y cargar datos CSV.
"""
import os
import csv
import logging
import numpy as np
import pandas as pd

def save_masks_to_csv(file_path, mask_map):
    """
    Guarda todas las máscaras en un archivo CSV.
    
    Args:
        file_path (str): Ruta al archivo CSV.
        mask_map (dict): Diccionario de máscaras de pocillos.
    """
    try:
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['plate_assay', 'row', 'col', 'value'])
            for key, mask in mask_map.items():
                for i in range(8):
                    for j in range(12):
                        writer.writerow([key, i, j, mask[i, j]])
        logging.getLogger('plate_analyzer').info(f"Masks saved to {file_path}")
    except Exception as e:
        logging.getLogger('plate_analyzer').error(f"Error saving masks: {e}")

def load_masks_from_csv(file_path, mask_map):
    """
    Carga máscaras desde un archivo CSV si existe.
    
    Args:
        file_path (str): Ruta al archivo CSV.
        mask_map (dict): Diccionario de máscaras de pocillos a actualizar.
    """
    if not os.path.exists(file_path):
        logging.getLogger('plate_analyzer').info(f"Mask file {file_path} not found. Using default masks.")
        return
        
    try:
        df = pd.read_csv(file_path)
        for key, group in df.groupby('plate_assay'):
            if key not in mask_map:
                continue
            mask = np.ones((8, 12), dtype=float)
            for _, row in group.iterrows():
                i, j = int(row['row']), int(row['col'])
                mask[i, j] = row['value']
            mask_map[key] = mask
        logging.getLogger('plate_analyzer').info(f"Masks loaded from {file_path}")
    except Exception as e:
        logging.getLogger('plate_analyzer').error(f"Error loading masks: {e}")

def save_neg_ctrl_masks_to_csv(file_path, neg_ctrl_mask_map):
    """
    Guarda todas las máscaras de control negativo en un archivo CSV.
    
    Args:
        file_path (str): Ruta al archivo CSV.
        neg_ctrl_mask_map (dict): Diccionario de máscaras de controles negativos.
    """
    try:
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['plate_assay', 'row', 'col', 'value'])
            for key, mask in neg_ctrl_mask_map.items():
                for i in range(8):
                    for j in range(12):
                        writer.writerow([key, i, j, mask[i, j]])
        logging.getLogger('plate_analyzer').info(f"Negative control masks saved to {file_path}")
    except Exception as e:
        logging.getLogger('plate_analyzer').error(f"Error saving negative control masks: {e}")

def load_neg_ctrl_masks_from_csv(file_path, neg_ctrl_mask_map):
    """
    Carga máscaras de control negativo desde un archivo CSV si existe.
    
    Args:
        file_path (str): Ruta al archivo CSV.
        neg_ctrl_mask_map (dict): Diccionario de máscaras de controles negativos a actualizar.
    """
    if not os.path.exists(file_path):
        logging.getLogger('plate_analyzer').info(f"Negative control mask file {file_path} not found. Using default masks.")
        return
        
    try:
        df = pd.read_csv(file_path)
        for key, group in df.groupby('plate_assay'):
            if key not in neg_ctrl_mask_map:
                continue
            mask = np.zeros((8, 12), dtype=float)
            for _, row in group.iterrows():
                i, j = int(row['row']), int(row['col'])
                mask[i, j] = row['value']
            neg_ctrl_mask_map[key] = mask
        logging.getLogger('plate_analyzer').info(f"Negative control masks loaded from {file_path}")
    except Exception as e:
        logging.getLogger('plate_analyzer').error(f"Error loading negative control masks: {e}")

def save_grays_to_csv(file_path, section_grays):
    """
    Guarda todos los valores de grises en un archivo CSV.
    
    Args:
        file_path (str): Ruta al archivo CSV.
        section_grays (dict): Diccionario de valores de grises para cada sección.
    """
    try:
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['plate_assay', 'section', 'gray_value'])
            for key, values in section_grays.items():
                for i, value in enumerate(values):
                    writer.writerow([key, i+1, value])
        logging.getLogger('plate_analyzer').info(f"Gray values saved to {file_path}")
    except Exception as e:
        logging.getLogger('plate_analyzer').error(f"Error saving gray values: {e}")

def load_grays_from_csv(file_path, section_grays):
    """
    Carga valores de dosis desde un archivo CSV si existe.
    
    Args:
        file_path (str): Ruta al archivo CSV.
        section_grays (dict): Diccionario de valores de dosis para cada sección a actualizar.
    """
    if not os.path.exists(file_path):
        logging.getLogger('plate_analyzer').info(f"Gray file {file_path} not found. Using default values.")
        return
    
    try:
        df = pd.read_csv(file_path)
        for key, group in df.groupby('plate_assay'):
            if key not in section_grays:
                continue
            gray_values = [0, 0, 0, 0, 0, 0]
            for _, row in group.iterrows():
                section = int(row['section'])
                if 1 <= section <= 6:
                    gray_values[section-1] = float(row['gray_value'])
            section_grays[key] = gray_values
        logging.getLogger('plate_analyzer').info(f"Gray values loaded from {file_path}")
    except Exception as e:
        logging.getLogger('plate_analyzer').error(f"Error loading gray values: {e}")
