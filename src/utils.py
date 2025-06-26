"""
Módulo de utilidades para la aplicación de análisis de placas.
"""
import os
import csv
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
            # Escribir encabezado
            writer.writerow(['plate_assay', 'row', 'col', 'value'])
            
            # Escribir cada máscara
            for key, mask in mask_map.items():
                for i in range(8):
                    for j in range(12):
                        writer.writerow([key, i, j, mask[i, j]])
        
        print(f"Masks saved to {file_path}")
    except Exception as e:
        print(f"Error saving masks: {e}")

def load_masks_from_csv(file_path, mask_map):
    """
    Carga máscaras desde un archivo CSV si existe.
    
    Args:
        file_path (str): Ruta al archivo CSV.
        mask_map (dict): Diccionario de máscaras de pocillos a actualizar.
    """
    if not os.path.exists(file_path):
        print(f"Mask file {file_path} not found. Using default masks.")
        return
        
    try:
        # Leer el archivo CSV
        df = pd.read_csv(file_path)
        
        # Agrupar por plate_assay
        for key, group in df.groupby('plate_assay'):
            # Saltar si la clave no está en nuestras claves actuales
            if key not in mask_map:
                continue
                
            # Inicializar una nueva máscara
            mask = np.ones((8, 12), dtype=float)
            
            # Llenar los valores de la máscara
            for _, row in group.iterrows():
                i, j = int(row['row']), int(row['col'])
                mask[i, j] = row['value']
            
            # Actualizar el mapa de máscaras
            mask_map[key] = mask
            
        print(f"Masks loaded from {file_path}")
    except Exception as e:
        print(f"Error loading masks: {e}")

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
            # Escribir encabezado
            writer.writerow(['plate_assay', 'row', 'col', 'value'])
            
            # Escribir cada máscara
            for key, mask in neg_ctrl_mask_map.items():
                for i in range(8):
                    for j in range(12):
                        writer.writerow([key, i, j, mask[i, j]])
        
        print(f"Negative control masks saved to {file_path}")
    except Exception as e:
        print(f"Error saving negative control masks: {e}")

def load_neg_ctrl_masks_from_csv(file_path, neg_ctrl_mask_map):
    """
    Carga máscaras de control negativo desde un archivo CSV si existe.
    
    Args:
        file_path (str): Ruta al archivo CSV.
        neg_ctrl_mask_map (dict): Diccionario de máscaras de controles negativos a actualizar.
    """
    if not os.path.exists(file_path):
        print(f"Negative control mask file {file_path} not found. Using default masks.")
        return
        
    try:
        # Leer el archivo CSV
        df = pd.read_csv(file_path)
        
        # Agrupar por plate_assay
        for key, group in df.groupby('plate_assay'):
            # Saltar si la clave no está en nuestras claves actuales
            if key not in neg_ctrl_mask_map:
                continue
                
            # Inicializar una nueva máscara
            mask = np.zeros((8, 12), dtype=float)
            
            # Llenar los valores de la máscara
            for _, row in group.iterrows():
                i, j = int(row['row']), int(row['col'])
                mask[i, j] = row['value']
            
            # Actualizar el mapa de máscaras
            neg_ctrl_mask_map[key] = mask
            
        print(f"Negative control masks loaded from {file_path}")
    except Exception as e:
        print(f"Error loading negative control masks: {e}")

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
            # Escribir encabezado
            writer.writerow(['plate_assay', 'section', 'gray_value'])
        
            # Escribir cada valor de gris
            for key, values in section_grays.items():
                for i, value in enumerate(values):
                    writer.writerow([key, i+1, value])
    
        print(f"Gray values saved to {file_path}")
    except Exception as e:
        print(f"Error saving gray values: {e}")

def load_grays_from_csv(file_path, section_grays):
    """
    Carga valores de grises desde un archivo CSV si existe.
    
    Args:
        file_path (str): Ruta al archivo CSV.
        section_grays (dict): Diccionario de valores de grises para cada sección a actualizar.
    """
    if not os.path.exists(file_path):
        print(f"Gray file {file_path} not found. Using default values.")
        return
    
    try:
        # Leer el archivo CSV
        df = pd.read_csv(file_path)
    
        # Agrupar por plate_assay
        for key, group in df.groupby('plate_assay'):
            # Saltar si la clave no está en nuestras claves actuales
            if key not in section_grays:
                continue
            
            # Inicializar un nuevo array para valores de grises
            gray_values = [0, 0, 0, 0, 0, 0]
        
            # Llenar los valores de grises
            for _, row in group.iterrows():
                section = int(row['section'])
                if 1 <= section <= 6:
                    gray_values[section-1] = float(row['gray_value'])
        
            # Actualizar los valores de grises
            section_grays[key] = gray_values
        
        print(f"Gray values loaded from {file_path}")
    except Exception as e:
        print(f"Error loading gray values: {e}")
