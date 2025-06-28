"""
Utility module for file operations.
"""
import os
import csv
import numpy as np
import pandas as pd
import logging

def save_masks_to_csv(file_path, mask_map):
    """
    Save all masks to a CSV file.
    
    Args:
        file_path (str): Path to the CSV file.
        mask_map (dict): Dictionary of well masks.
    """
    try:
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['plate_assay', 'row', 'col', 'value'])
            
            # Write each mask
            for key, mask in mask_map.items():
                for i in range(8):
                    for j in range(12):
                        writer.writerow([key, i, j, mask[i, j]])
        
        logging.getLogger('plate_analyzer').info(f"Masks saved to {file_path}")
    except Exception as e:
        logging.getLogger('plate_analyzer').error(f"Error saving masks: {e}")

def load_masks_from_csv(file_path, mask_map):
    """
    Load masks from a CSV file if it exists.
    
    Args:
        file_path (str): Path to the CSV file.
        mask_map (dict): Dictionary of well masks to update.
    """
    if not os.path.exists(file_path):
        logging.getLogger('plate_analyzer').warning(f"Mask file {file_path} not found. Using default masks.")
        return
        
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Group by plate_assay
        for key, group in df.groupby('plate_assay'):
            # Skip if the key is not in our current keys
            if key not in mask_map:
                continue
                
            # Initialize a new mask
            mask = np.ones((8, 12), dtype=float)
            
            # Fill in mask values
            for _, row in group.iterrows():
                i, j = int(row['row']), int(row['col'])
                mask[i, j] = row['value']
            
            # Update the mask map
            mask_map[key] = mask
            
        logging.getLogger('plate_analyzer').info(f"Masks loaded from {file_path}")
    except Exception as e:
        logging.getLogger('plate_analyzer').error(f"Error loading masks: {e}")

def save_neg_ctrl_masks_to_csv(file_path, neg_ctrl_mask_map):
    """
    Save all negative control masks to a CSV file.
    
    Args:
        file_path (str): Path to the CSV file.
        neg_ctrl_mask_map (dict): Dictionary of negative control masks.
    """
    try:
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['plate_assay', 'row', 'col', 'value'])
            
            # Write each mask
            for key, mask in neg_ctrl_mask_map.items():
                for i in range(8):
                    for j in range(12):
                        writer.writerow([key, i, j, mask[i, j]])
        
        logging.getLogger('plate_analyzer').info(f"Negative control masks saved to {file_path}")
    except Exception as e:
        logging.getLogger('plate_analyzer').error(f"Error saving negative control masks: {e}")

def load_neg_ctrl_masks_from_csv(file_path, neg_ctrl_mask_map):
    """
    Load negative control masks from a CSV file if it exists.
    
    Args:
        file_path (str): Path to the CSV file.
        neg_ctrl_mask_map (dict): Dictionary of negative control masks to update.
    """
    if not os.path.exists(file_path):
        logging.getLogger('plate_analyzer').warning(f"Negative control mask file {file_path} not found. Using default masks.")
        return
        
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Group by plate_assay
        for key, group in df.groupby('plate_assay'):
            # Skip if the key is not in our current keys
            if key not in neg_ctrl_mask_map:
                continue
                
            # Initialize a new mask
            mask = np.zeros((8, 12), dtype=float)
            
            # Fill in mask values
            for _, row in group.iterrows():
                i, j = int(row['row']), int(row['col'])
                mask[i, j] = row['value']
            
            # Update the mask map
            neg_ctrl_mask_map[key] = mask
            
        logging.getLogger('plate_analyzer').info(f"Negative control masks loaded from {file_path}")
    except Exception as e:
        logging.getLogger('plate_analyzer').error(f"Error loading negative control masks: {e}")

def save_grays_to_csv(file_path, section_grays):
    """
    Save all gray values to a CSV file.
    
    Args:
        file_path (str): Path to the CSV file.
        section_grays (dict): Dictionary of gray values for each section.
    """
    try:
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['plate_assay', 'section', 'gray_value'])
        
            # Write each gray value
            for key, values in section_grays.items():
                for i, value in enumerate(values):
                    writer.writerow([key, i+1, value])
    
        logging.getLogger('plate_analyzer').info(f"Gray values saved to {file_path}")
    except Exception as e:
        logging.getLogger('plate_analyzer').error(f"Error saving gray values: {e}")

def load_grays_from_csv(file_path, section_grays):
    """
    Load gray values from a CSV file if it exists.
    
    Args:
        file_path (str): Path to the CSV file.
        section_grays (dict): Dictionary of gray values for each section to update.
    """
    if not os.path.exists(file_path):
        logging.getLogger('plate_analyzer').warning(f"Gray file {file_path} not found. Using default values.")
        return
    
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
    
        # Group by plate_assay
        for key, group in df.groupby('plate_assay'):
            # Skip if the key is not in our current keys
            if key not in section_grays:
                continue
            
            # Initialize a new array for gray values
            gray_values = [0, 0, 0, 0, 0, 0]
        
            # Fill in gray values
            for _, row in group.iterrows():
                section = int(row['section'])
                if 1 <= section <= 6:
                    gray_values[section-1] = float(row['gray_value'])
        
            # Update gray values
            section_grays[key] = gray_values
        
        logging.getLogger('plate_analyzer').info(f"Gray values loaded from {file_path}")
    except Exception as e:
        logging.getLogger('plate_analyzer').error(f"Error loading gray values: {e}")
