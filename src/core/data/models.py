"""
Module containing data classes and structures for plate analysis.
"""
import numpy as np
import pandas as pd
import logging

class PlateData:
    """Class to store and manage plate data."""
    
    def __init__(self, df):
        """
        Initialize the class with a pandas DataFrame.
        
        Args:
            df (pandas.DataFrame): DataFrame with plate data. Can be None.
        """
        if df is None or df.empty:
            # Initialize with empty data
            self.df = pd.DataFrame()
            self.unique_plates = pd.DataFrame()
            self.keys = []
        else:
            # Make a deep copy of the input dataframe
            self.df = df.copy(deep=True).reset_index(drop=True)
            
            # Ensure data is in the correct format
            if 'data' in self.df.columns:
                # Convert any numpy arrays to lists
                self.df['data'] = self.df['data'].apply(
                    lambda x: x.tolist() if hasattr(x, 'tolist') else x
                )
            
            self.unique_plates = self._get_unique_plates()
            self.keys = self._get_keys()
        
        # Define section colors - using more vibrant colors for better visibility
        self.section_colors = ['#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF', '#99FFFF']
        
        # Define section boundaries
        self.sections = [
            (0, 0, 3, 3),  # Section 1: rows 0-3, cols 0-3
            (0, 4, 3, 7),  # Section 2: rows 0-3, cols 4-7
            (0, 8, 3, 11), # Section 3: rows 0-3, cols 8-11
            (4, 0, 7, 3),  # Section 4: rows 4-7, cols 0-3
            (4, 4, 7, 7),  # Section 5: rows 4-7, cols 4-7
            (4, 8, 7, 11)  # Section 6: rows 4-7, cols 8-11
        ]
    
    def _get_unique_plates(self):
        """Get unique plates from the DataFrame."""
        if self.df.empty:
            return pd.DataFrame()
        return self.df[['plate_no', 'assay']].drop_duplicates().reset_index(drop=True)
    
    def _get_keys(self):
        """Generate unique keys for each plate-assay combination."""
        if self.df.empty or self.unique_plates.empty:
            return []
            
        keys = []
        for _, row in self.unique_plates.iterrows():
            try:
                # Ensure both plate_no and assay are strings
                plate_no = str(row['plate_no']) if pd.notna(row['plate_no']) else ''
                assay = str(row['assay']) if pd.notna(row['assay']) else ''
                if plate_no and assay:  # Only add if both are non-empty
                    keys.append(f"{plate_no}_{assay}")
            except Exception as e:
                logging.getLogger('plate_analyzer').error(f"Error generating key for row {row}: {e}")
                continue
                
        return list(dict.fromkeys(keys))  # Remove duplicates while preserving order
    
    def get_plate_data(self, plate_no, assay, hours=None):
        """
        Get data for a specific plate.
        
        Args:
            plate_no (str): Plate number.
            assay (str): Assay type.
            hours (float, optional): Specific hours. If None, returns all time points.
            
        Returns:
            pandas.DataFrame: Filtered DataFrame with plate data.
        """
        if self.df.empty:
            return pd.DataFrame()
            
        if hours is None:
            return self.df[(self.df['plate_no'] == plate_no) & 
                          (self.df['assay'] == assay)].sort_values('hours')
        else:
            return self.df[(self.df['plate_no'] == plate_no) & 
                          (self.df['assay'] == assay) & 
                          (self.df['hours'] == hours)]
    
    def get_all_individual_plates(self):
        """
        Get a list of all individual plates.
        
        Returns:
            list: List of strings with format 'plate_no_assay_hours'.
        """
        if self.df.empty:
            return []
            
        all_plates = []
        for _, row in self.df.iterrows():
            plate_id = f"{row['plate_no']}_{row['assay']}_{row['hours']}"
            if plate_id not in all_plates:
                all_plates.append(plate_id)
        return all_plates
