"""
Módulo que contiene las clases de datos y estructuras para el análisis de placas.
"""
import numpy as np
import pandas as pd

class PlateData:
    """Clase para almacenar y gestionar datos de placas."""
    
    def __init__(self, df):
        """
        Inicializa la clase con un DataFrame de pandas.
        
        Args:
            df (pandas.DataFrame): DataFrame con los datos de las placas. Puede ser None.
        """
        if df is None:
            # Initialize with empty data
            self.df = pd.DataFrame()
            self.unique_plates = pd.DataFrame()
            self.keys = []
        else:
            self.df = df.copy().reset_index(drop=True)
            self.unique_plates = self._get_unique_plates()
            self.keys = self._get_keys()
        
        # Definir colores de sección - usando colores más vibrantes para mejor visibilidad
        self.section_colors = ['#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF', '#99FFFF']
        
        # Definir límites de secciones
        self.sections = [
            (0, 0, 3, 3),  # Sección 1: filas 0-3, cols 0-3
            (0, 4, 3, 7),  # Sección 2: filas 0-3, cols 4-7
            (0, 8, 3, 11), # Sección 3: filas 0-3, cols 8-11
            (4, 0, 7, 3),  # Sección 4: filas 4-7, cols 0-3
            (4, 4, 7, 7),  # Sección 5: filas 4-7, cols 4-7
            (4, 8, 7, 11)  # Sección 6: filas 4-7, cols 8-11
        ]
    
    def _get_unique_plates(self):
        """Obtiene las placas únicas del DataFrame."""
        if self.df.empty:
            return pd.DataFrame()
        return self.df[['plate_no', 'assay']].drop_duplicates().reset_index(drop=True)
    
    def _get_keys(self):
        """Genera claves únicas para cada combinación placa-ensayo."""
        if self.df.empty:
            return []
        return [f"{r.plate_no}_{r.assay}" for _, r in self.unique_plates.iterrows()]
    
    def get_plate_data(self, plate_no, assay, hours=None):
        """
        Obtiene los datos de una placa específica.
        
        Args:
            plate_no (str): Plate number.
            assay (str): Tipo de ensayo.
            hours (float, optional): Horas específicas. Si es None, devuelve todos los tiempos.
            
        Returns:
            pandas.DataFrame: DataFrame filtrado con los datos de la placa.
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
        Obtiene una lista de todas las placas individuales.
        
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
