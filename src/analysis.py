"""
Module for plate data analysis.
"""
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from src.visualization import create_2d_figure, create_3d_figure, generate_html_content
import copy

def analyze_plate(df, plate, assay, mask, neg_ctrl_mask, sections, use_percentage=True, 
                 subtract_neg_ctrl=True, current_individual_plate=None):
    """
    Analyzes a specific plate and returns the results as text.

    Args:
        df (pandas.DataFrame): DataFrame with plate data.
        plate (str): Plate number.
        assay (str): Assay type.
        mask (numpy.ndarray): Well mask 
        neg_ctrl_mask (numpy.ndarray): Negative control mask 
        sections (list): List of tuples with the limits of each section.
        use_percentage (bool, optional): Whether to show results as percentage. Default is True.
        subtract_neg_ctrl (bool, optional): Whether to subtract negative controls. Default is True.
        current_individual_plate (pandas.Series, optional): Data of the selected individual plate.
    
    Returns:
        str: Analysis results as text.
    """
    result_text = ""
    
    # If in advanced mode and an individual plate is selected
    if current_individual_plate is not None:
        # Analyze only this individual plate
        # Analizar solo esta placa individual
        data = current_individual_plate['data'].copy()
        hours = current_individual_plate['hours']
        
        # Restar controles negativos si está habilitado
        neg_ctrl_avg = np.nan
        neg_ctrl_std = np.nan
        if subtract_neg_ctrl:
            # Calcular promedio y desviación estándar de controles negativos
            neg_ctrl_data = data * neg_ctrl_mask
            valid_neg_ctrls = neg_ctrl_data[neg_ctrl_data != 0]
            if len(valid_neg_ctrls) > 0:
                neg_ctrl_avg = np.nanmean(valid_neg_ctrls)
                neg_ctrl_std = np.nanstd(valid_neg_ctrls)
                # Restar de todos los pocillos
                data = data - neg_ctrl_avg
                # Establecer valores negativos a 0
                data[data < 0] = 0
        
        # Aplicar máscara
        mask_array = np.array(mask) if not isinstance(mask, np.ndarray) else mask
        masked_data = data * mask_array
        
        # Calcular medias y desviaciones estándar de secciones
        sec_means = {}
        sec_stds = {}
        
        # Para cada sección, calcular media y desviación estándar con propagación de error
        for i, (r1, c1, r2, c2) in enumerate(sections):
            section_data = masked_data[r1:r2+1, c1:c2+1]
            # Filtrar valores enmascarados (ceros)
            valid_data = section_data[section_data != 0]
            if len(valid_data) > 0:
                sec_means[f"S{i+1}"] = np.nanmean(valid_data)
                # Propagar error si se restaron controles negativos
                if subtract_neg_ctrl and not np.isnan(neg_ctrl_std):
                    # Fórmula de propagación de error para resta: sqrt(std1^2 + std2^2)
                    section_std = np.nanstd(valid_data)
                    # Error estándar: desviación estándar / raíz(n)
                    n = len(valid_data)
                    section_std = section_std / np.sqrt(n)
                    propagated_std = np.sqrt(section_std**2 + neg_ctrl_std**2)
                    sec_stds[f"S{i+1}_std"] = propagated_std
                else:
                    # Error estándar: desviación estándar / raíz(n)
                    n = len(valid_data)
                    sec_stds[f"S{i+1}_std"] = np.nanstd(valid_data) / np.sqrt(n)
            else:
                sec_means[f"S{i+1}"] = np.nan
                sec_stds[f"S{i+1}_std"] = np.nan
        
        # Generar texto de resultados
        result_text += f"Analysis for individual plate: {plate}_{assay} at {hours} hours\n\n"
        
        # Mostrar información de control negativo si se usó
        if subtract_neg_ctrl:
            neg_ctrl_count = np.sum(neg_ctrl_mask)
            if neg_ctrl_count > 0:
                result_text += f"Negative controls: {neg_ctrl_count} wells, avg value: {neg_ctrl_avg:.4f}, std: {neg_ctrl_std:.4f}\n\n"
            else:
                result_text += "No negative controls selected\n\n"
        
        for sec in sec_means.keys():
            result_text += f"{sec}: {sec_means[sec]:.4f} ± {sec_stds[sec]:.4f}\n"
        
        return result_text
    
    # Modo regular - analizar todos los puntos de tiempo para la placa-ensayo seleccionada
    sub = df[(df['plate_no']==plate) & (df['assay']==assay)].sort_values('hours')
    results = []
    
    # Procesar cada punto de tiempo
    for _, row in sub.iterrows():
        data = row['data'].copy()  # Hacer una copia para evitar modificar el original
        
        # Restar controles negativos si está habilitado
        neg_ctrl_avg = np.nan
        neg_ctrl_std = np.nan
        if subtract_neg_ctrl:
            # Calcular promedio y desviación estándar de controles negativos para este punto de tiempo
            neg_ctrl_data = data * neg_ctrl_mask
            valid_neg_ctrls = neg_ctrl_data[neg_ctrl_data != 0]
            if len(valid_neg_ctrls) > 0:
                neg_ctrl_avg = np.nanmean(valid_neg_ctrls)
                neg_ctrl_std = np.nanstd(valid_neg_ctrls)
                # Restar de todos los pocillos
                data = data - neg_ctrl_avg
                # Establecer valores negativos a 0
                data[data < 0] = 0
        
        # Aplicar máscara
        mask_array = np.array(mask) if not isinstance(mask, np.ndarray) else mask
        masked_data = data * mask_array
        
        sec_means = {}
        sec_stds = {}
        neg_ctrl_info = {'hours': row['hours'], 'neg_ctrl_avg': neg_ctrl_avg, 'neg_ctrl_std': neg_ctrl_std}
        
        # Para cada sección, calcular media y desviación estándar con propagación de error
        for i, (r1, c1, r2, c2) in enumerate(sections):
            section_data = masked_data[r1:r2+1, c1:c2+1]
            # Filtrar valores enmascarados (ceros)
            valid_data = section_data[section_data != 0]
            if len(valid_data) > 0:
                sec_means[f"S{i+1}"] = np.nanmean(valid_data)
                # Propagar error si se restaron controles negativos
                if subtract_neg_ctrl and not np.isnan(neg_ctrl_std):
                    # Fórmula de propagación de error para resta: sqrt(std1^2 + std2^2)
                    section_std = np.nanstd(valid_data)
                    # Error estándar: desviación estándar / raíz(n)
                    n = len(valid_data)
                    section_std = section_std / np.sqrt(n)
                    propagated_std = np.sqrt(section_std**2 + neg_ctrl_std**2)
                    sec_stds[f"S{i+1}_std"] = propagated_std
                else:
                    # Error estándar: desviación estándar / raíz(n)
                    n = len(valid_data)
                    sec_stds[f"S{i+1}_std"] = np.nanstd(valid_data) / np.sqrt(n)
            else:
                sec_means[f"S{i+1}"] = np.nan
                sec_stds[f"S{i+1}_std"] = np.nan
        
        # Combinar medias y desviaciones estándar
        combined_results = {**sec_means, **sec_stds, **neg_ctrl_info}
        results.append(combined_results)
    
    # Convertir a DataFrame
    res_df = pd.DataFrame(results)
    
    # Aplicar cálculo de porcentaje si está habilitado
    if use_percentage and len(res_df) > 0:
        # Obtener los valores de la primera fila para cada sección
        first_values = res_df.iloc[0].copy()
        
        # Calcular cambio porcentual para cada media de sección
        for col in [c for c in res_df.columns if c.startswith('S') and not c.endswith('_std')]:
            base_value = first_values[col]
            if base_value != 0:  # Evitar división por cero
                # También ajustar la desviación estándar para que sea relativa a la media
                std_col = f"{col}_std"
                res_df[std_col] = (res_df[std_col] / base_value) * 100
                res_df[col] = (res_df[col] / base_value - 1) * 100
            else:
                # Si el valor base es cero, establecer todos los valores a NaN
                std_col = f"{col}_std"
                res_df[col] = np.nan
                res_df[std_col] = np.nan
        
        # Añadir símbolo % a los nombres de columnas
        display_cols = {}
        for col in res_df.columns:
            if col.startswith('S') and not col.endswith('_std'):
                display_cols[col] = f"{col} (%)"
            elif col.endswith('_std'):
                display_cols[col] = f"{col[:-4]} Std (%)"
            elif col == 'neg_ctrl_avg':
                display_cols[col] = "Neg Ctrl Avg"
            elif col == 'neg_ctrl_std':
                display_cols[col] = "Neg Ctrl Std"
            else:
                display_cols[col] = col
        
        display_df = res_df.rename(columns=display_cols)
    else:
        # Solo renombrar columnas de desviación estándar para mostrar
        display_cols = {}
        for col in res_df.columns:
            if col.endswith('_std'):
                display_cols[col] = f"{col[:-4]} Std"
            elif col == 'neg_ctrl_avg':
                display_cols[col] = "Neg Ctrl Avg"
            elif col == 'neg_ctrl_std':
                display_cols[col] = "Neg Ctrl Std"
            else:
                display_cols[col] = col
        
        display_df = res_df.rename(columns=display_cols)
    
    # Generar texto de resultados
    result_text = ""
    
    # Mostrar información de control negativo
    if subtract_neg_ctrl:
        neg_ctrl_count = np.sum(neg_ctrl_mask)
        if neg_ctrl_count > 0:
            result_text += f"Negative controls: {neg_ctrl_count} wells\n\n"
        else:
            result_text += "No negative controls selected\n\n"
    
    result_text += display_df.to_string(index=False)
    
    return result_text

# Modificar la función analyze_all_plates para incluir la normalización con S1
def analyze_all_plates(df, keys, mask_map, neg_ctrl_mask_map, section_grays, sections, section_colors,
                      use_percentage=True, show_error_bars=True, use_bar_chart=False, subtract_neg_ctrl=True):
    """
    Analiza todas las placas, guarda resultados en Excel y genera visualizaciones HTML.
    
    Args:
        df (pandas.DataFrame): DataFrame con los datos de las placas.
        keys (list): Lista de claves placa-ensayo.
        mask_map (dict): Diccionario de máscaras de pocillos.
        neg_ctrl_mask_map (dict): Diccionario de máscaras de controles negativos.
        section_grays (dict): Diccionario de valores de grises para cada sección.
        sections (list): Lista de tuplas con los límites de cada sección.
        section_colors (list): Lista de colores para cada sección.
        use_percentage (bool, optional): Si se deben mostrar los resultados como porcentaje. Por defecto True.
        show_error_bars (bool, optional): Si se deben mostrar barras de error. Por defecto True.
        use_bar_chart (bool, optional): Si se debe usar gráfico de barras en lugar de líneas. Por defecto False.
        subtract_neg_ctrl (bool, optional): Si se deben restar los controles negativos. Por defecto True.
        
    Returns:
        tuple: (mensaje de resultado, ruta al archivo HTML)
    """
    out_dir = "analysis_output"
    os.makedirs(out_dir, exist_ok=True)
    
    # Archivo de diagnóstico para depuración
    debug_file = os.path.join(out_dir, "debug_info.txt")
    with open(debug_file, 'w') as f_debug:
        f_debug.write("Información de diagnóstico para análisis de placas\n")
        f_debug.write("=" * 50 + "\n\n")
    
    try:
        writer = pd.ExcelWriter(os.path.join(out_dir, "all_results.xlsx"), engine='xlsxwriter')
    except ImportError:
        writer = pd.ExcelWriter(os.path.join(out_dir, "all_results.xlsx"), engine='openpyxl')

    # Crear figuras 2D y 3D para todas las placas
    figures_2d = {}
    figures_2d_norm = {}  # Para las gráficas normalizadas con S1
    figures_3d = {}
    figures_3d_norm = {}  # Para las gráficas 3D normalizadas con S1
    
    for key in keys:
        plate, assay = key.split("_")
        
        # Añadir información de diagnóstico
        with open(debug_file, 'a') as f_debug:
            f_debug.write(f"\nProcesando placa: {key}\n")
            f_debug.write("-" * 30 + "\n")
        
        sub = df[(df['plate_no']==plate) & (df['assay']==assay)].sort_values('hours')
        
        # Verificar si hay datos para esta placa
        if sub.empty:
            with open(debug_file, 'a') as f_debug:
                f_debug.write(f"No hay datos para la placa {key}\n")
            continue
        
        # Añadir información sobre los datos encontrados
        with open(debug_file, 'a') as f_debug:
            f_debug.write(f"Encontrados {len(sub)} puntos de tiempo para {key}\n")
            f_debug.write(f"Horas disponibles: {sub['hours'].tolist()}\n")
            
        mask = mask_map[key]
        neg_ctrl_mask = neg_ctrl_mask_map[key]
        
        # Verificar las máscaras
        with open(debug_file, 'a') as f_debug:
            f_debug.write(f"Máscara: {np.sum(mask)} pocillos activos de 96\n")
            f_debug.write(f"Máscara de controles negativos: {np.sum(neg_ctrl_mask)} pocillos marcados de 96\n")
        
        results = []
        gray_values = section_grays[key]
        
        # Verificar valores de grises
        with open(debug_file, 'a') as f_debug:
            f_debug.write(f"Valores de grises: {gray_values}\n")
        
        # Procesar cada punto de tiempo
        for _, row in sub.iterrows():
            data = row['data'].copy()
            hours = row['hours']
            
            # Convert data to numpy array if it's a list
            data_array = np.array(data) if isinstance(data, list) else data
            
            # Inicializar para evitar errores cuando no se usa la resta de controles
            valid_neg_ctrls = np.array([])
            
            # Verificar datos brutos
            with open(debug_file, 'a') as f_debug:
                f_debug.write(f"\nPunto de tiempo: {hours} horas\n")
                f_debug.write(f"Tipo de datos: {type(data_array)}, Forma: {data_array.shape if hasattr(data_array, 'shape') else 'N/A'}\n")
                f_debug.write(f"Rango de datos brutos: {np.nanmin(data_array)} a {np.nanmax(data_array)}\n")
                f_debug.write(f"Media de datos brutos: {np.nanmean(data_array)}\n")
                f_debug.write(f"NaNs en datos brutos: {np.isnan(data_array).sum()} de {data_array.size}\n")
            
            # Restar controles negativos si está habilitado
            neg_ctrl_avg = np.nan
            neg_ctrl_std = np.nan
            if subtract_neg_ctrl and neg_ctrl_mask is not None:
                # Ensure both data and mask are numpy arrays
                mask_array = np.array(neg_ctrl_mask) if not isinstance(neg_ctrl_mask, np.ndarray) else neg_ctrl_mask
                neg_ctrl_data = data_array * mask_array
                valid_neg_ctrls = neg_ctrl_data[neg_ctrl_data != 0]
                
                with open(debug_file, 'a') as f_debug:
                    f_debug.write(f"Controles negativos válidos: {len(valid_neg_ctrls)}\n")
                
                if valid_neg_ctrls.size > 0:
                    neg_ctrl_avg = np.nanmean(valid_neg_ctrls)
                    neg_ctrl_std = np.nanstd(valid_neg_ctrls) / np.sqrt(len(valid_neg_ctrls))  # Error estándar
                    
                    with open(debug_file, 'a') as f_debug:
                        f_debug.write(f"Media de controles negativos: {neg_ctrl_avg}\n")
                        f_debug.write(f"Error estándar de controles negativos: {neg_ctrl_std}\n")
                    
                    # Restar de todos los pocillos
                    data_array = data_array.astype(float) - neg_ctrl_avg
                    
                    with open(debug_file, 'a') as f_debug:
                        f_debug.write("Valores negativos NO forzados a 0 tras la resta de controles\n")
            

            
            # Aplicar máscara: excluir solo pocillos marcados como excluidos (controles negativos incluidos si no están excluidos)
            mask_array = np.array(mask) if not isinstance(mask, np.ndarray) else mask
            masked_data = data_array * mask_array
            
            with open(debug_file, 'a') as f_debug:
                non_zero = masked_data[masked_data != 0]
                non_zero_count = np.sum(masked_data != 0)
                f_debug.write(f"Datos después de aplicar máscara - Valores no cero: {non_zero_count}\n")
                if non_zero_count > 0:
                    non_zero_array = np.array(non_zero) if not isinstance(non_zero, np.ndarray) else non_zero
                    f_debug.write(f"Rango de valores no cero: {np.nanmin(non_zero_array)} a {np.nanmax(non_zero_array)}\n")
                    f_debug.write(f"Media de valores no cero: {np.nanmean(non_zero_array)}\n")
                else:
                    f_debug.write("No hay valores no cero después de aplicar la máscara\n")
            
            # Calcular medias y desviaciones estándar para cada sección
            sec_means = {}
            sec_stds = {}
            neg_ctrl_info = {'hours': row['hours'], 'neg_ctrl_avg': neg_ctrl_avg, 'neg_ctrl_std': neg_ctrl_std}
            
            # Use the actual number of sections available
            num_sections = len(sections)
            
            for i in range(num_sections):
                if i >= len(sections):
                    continue
                    
                r1, c1, r2, c2 = map(int, sections[i])  # Asegurarse de que son enteros
                # Asegurarse de que los índices estén dentro de los límites
                r1, r2 = max(0, min(r1, 7)), max(0, min(r2, 7))
                c1, c2 = max(0, min(c1, 11)), max(0, min(c2, 11))
                
                section_data = masked_data[r1:r2+1, c1:c2+1]
                valid_data = section_data[section_data != 0]
                if not isinstance(valid_data, np.ndarray):
                    valid_data = np.array(valid_data)
                
                with open(debug_file, 'a') as f_debug:
                    f_debug.write(f"Sección {i+1}: {len(valid_data)} valores válidos\n")
                
                if len(valid_data) > 0:
                    sec_means[f"S{i+1}"] = np.nanmean(valid_data)
                    
                    with open(debug_file, 'a') as f_debug:
                        f_debug.write(f"  Media: {sec_means[f'S{i+1}']}\n")
                    
                    if subtract_neg_ctrl and not np.isnan(neg_ctrl_std):
                        section_std = np.nanstd(valid_data) / np.sqrt(len(valid_data))  # Error estándar
                        propagated_std = np.sqrt(section_std**2 + neg_ctrl_std**2)
                        sec_stds[f"S{i+1}_std"] = propagated_std
                        
                        with open(debug_file, 'a') as f_debug:
                            f_debug.write(f"  Desviación estándar (propagada): {propagated_std}\n")
                    else:
                        sec_stds[f"S{i+1}_std"] = np.nanstd(valid_data) / np.sqrt(len(valid_data))  # Error estándar
                        
                        with open(debug_file, 'a') as f_debug:
                            f_debug.write(f"  Desviación estándar: {sec_stds[f'S{i+1}_std']}\n")
                else:
                    sec_means[f"S{i+1}"] = np.nan
                    sec_stds[f"S{i+1}_std"] = np.nan
                    
                    with open(debug_file, 'a') as f_debug:
                        f_debug.write("  No hay datos válidos para esta sección\n")
            

            
            # Combinar resultados
            combined_results = {**sec_means, **sec_stds, **neg_ctrl_info}
            results.append(combined_results)
        
        # Convertir a DataFrame
        res_df = pd.DataFrame(results)
        
        with open(debug_file, 'a') as f_debug:
            f_debug.write("\nResultados procesados:\n")
            f_debug.write(f"DataFrame shape: {res_df.shape}\n")
            f_debug.write(f"Columnas: {res_df.columns.tolist()}\n")
            f_debug.write("Primeras filas:\n")
            f_debug.write(str(res_df.head()) + "\n")
        
        # Guardar valores originales para graficar
        orig_df = res_df.copy()
        
        # Crear DataFrame normalizado con S1 como control
        norm_df = res_df.copy()
        
        # Para cada punto de tiempo, normalizar todas las secciones dividiendo por el valor de S1
        for i, row in norm_df.iterrows():
            s1_value = row.get('S1', np.nan)  # Use .get() to safely access S1
            
            with open(debug_file, 'a') as f_debug:
                f_debug.write(f"\nNormalización para tiempo {row['hours']} horas:\n")
                f_debug.write(f"Valor de S1: {s1_value}\n")
            
            if not np.isnan(s1_value) and s1_value != 0:  # Evitar división por cero
                # Get all available section columns
                available_sections = [c for c in norm_df.columns if c.startswith('S') and not c.endswith('_std')]
                
                for col in available_sections:
                    if col != 'S1':  # No normalizar S1 consigo misma
                        # Normalizar el valor
                        if col in row:
                            norm_df.at[i, col] = row[col] / s1_value
                            
                            with open(debug_file, 'a') as f_debug:
                                f_debug.write(f"  {col}: {row[col]} / {s1_value} = {norm_df.at[i, col]}\n")
                            
                            # También ajustar la desviación estándar para mantener la proporción
                            std_col = f"{col}_std"
                            if std_col in row:
                                norm_df.at[i, std_col] = row[std_col] / s1_value
                
                # También necesitamos crear la incertidumbre para S1 (que ahora es 1)
                norm_df.at[i, 'S1'] = 1.0
                s1_std = row.get('S1_std', np.nan)
                if not np.isnan(s1_std):
                    # Error relativo: std/value
                    norm_df.at[i, 'S1_std'] = s1_std / s1_value
            else:
                with open(debug_file, 'a') as f_debug:
                    f_debug.write("  No se puede normalizar: S1 es NaN o cero\n")
        
        # Aplicar cálculo de porcentaje si está habilitado
        if use_percentage and len(res_df) > 0:
            first_values = res_df.iloc[0].copy()
            
            with open(debug_file, 'a') as f_debug:
                f_debug.write("\nCálculo de porcentajes:\n")
                f_debug.write(f"Valores iniciales: {first_values[first_values.index.str.startswith('S')].to_dict()}\n")
            
            for col in [c for c in res_df.columns if c.startswith('S') and not c.endswith('_std')]:
                base_value = first_values[col]
                
                with open(debug_file, 'a') as f_debug:
                    f_debug.write(f"Columna {col}, valor base: {base_value}\n")
                
                if base_value != 0 and not np.isnan(base_value):  # Evitar división por cero y NaN
                    std_col = f"{col}_std"
                    res_df[std_col] = (res_df[std_col] / base_value) * 100
                    res_df[col] = (res_df[col] / base_value - 1) * 100
                    
                    with open(debug_file, 'a') as f_debug:
                        f_debug.write(f"  Convertido a porcentaje. Nuevos valores: {res_df[col].tolist()}\n")
                else:
                    std_col = f"{col}_std"
                    res_df[col] = np.nan
                    res_df[std_col] = np.nan
                    
                    with open(debug_file, 'a') as f_debug:
                        f_debug.write(f"  No se puede calcular porcentaje: valor base es {base_value}\n")
            
            # Renombrar columnas para mostrar
            display_cols = {}
            for col in res_df.columns:
                if col.startswith('S') and not col.endswith('_std'):
                    display_cols[col] = f"{col} (%)"
                elif col.endswith('_std'):
                    display_cols[col] = f"{col[:-4]} Std (%)"
                elif col == 'neg_ctrl_avg':
                    display_cols[col] = "Neg Ctrl Avg"
                elif col == 'neg_ctrl_std':
                    display_cols[col] = "Neg Ctrl Std"
                else:
                    display_cols[col] = col
            
            display_df = res_df.rename(columns=display_cols)
            
            # Guardar en Excel con nombres de columnas de porcentaje
            sheet_name = key
            display_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # También guardar la versión normalizada en otra hoja
            norm_display_cols = {}
            for col in norm_df.columns:
                if col.startswith('S') and not col.endswith('_std'):
                    norm_display_cols[col] = f"{col} (norm)"
                elif col.endswith('_std'):
                    norm_display_cols[col] = f"{col[:-4]} Std (norm)"
                elif col == 'neg_ctrl_avg':
                    norm_display_cols[col] = "Neg Ctrl Avg"
                elif col == 'neg_ctrl_std':
                    norm_display_cols[col] = "Neg Ctrl Std"
                else:
                    norm_display_cols[col] = col
            
            norm_display_df = norm_df.rename(columns=norm_display_cols)
            norm_sheet_name = f"{key}_norm"
            norm_display_df.to_excel(writer, sheet_name=norm_sheet_name, index=False)
        else:
            # Solo renombrar columnas de desviación estándar para mostrar
            display_cols = {}
            for col in res_df.columns:
                if col.endswith('_std'):
                    display_cols[col] = f"{col[:-4]} Std"
                elif col == 'neg_ctrl_avg':
                    display_cols[col] = "Neg Ctrl Avg"
                elif col == 'neg_ctrl_std':
                    display_cols[col] = "Neg Ctrl Std"
                else:
                    display_cols[col] = col
            
            display_df = res_df.rename(columns=display_cols)
            
            # Guardar valores originales en Excel
            sheet_name = key
            display_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # También guardar la versión normalizada en otra hoja
            norm_display_cols = {}
            for col in norm_df.columns:
                if col.endswith('_std'):
                    norm_display_cols[col] = f"{col[:-4]} Std (norm)"
                elif col == 'neg_ctrl_avg':
                    norm_display_cols[col] = "Neg Ctrl Avg"
                elif col == 'neg_ctrl_std':
                    norm_display_cols[col] = "Neg Ctrl Std"
                elif col.startswith('S'):
                    norm_display_cols[col] = f"{col} (norm)"
                else:
                    norm_display_cols[col] = col
            
            norm_display_df = norm_df.rename(columns=norm_display_cols)
            norm_sheet_name = f"{key}_norm"
            norm_display_df.to_excel(writer, sheet_name=norm_sheet_name, index=False)
        
        # Verificar si hay datos válidos para graficar
        has_valid_data = False
        for col in [c for c in res_df.columns if c.startswith('S') and not c.endswith('_std')]:
            if not res_df[col].isna().all():
                has_valid_data = True
                break
        
        with open(debug_file, 'a') as f_debug:
            f_debug.write(f"\n¿Tiene datos válidos para graficar? {has_valid_data}\n")
            if not has_valid_data:
                f_debug.write("ADVERTENCIA: No hay datos válidos para graficar esta placa\n")
                # Mostrar más detalles sobre los datos
                f_debug.write("Detalles de los datos:\n")
                for col in [c for c in res_df.columns if c.startswith('S') and not c.endswith('_std')]:
                    f_debug.write(f"  {col}: {res_df[col].tolist()}\n")
                    f_debug.write(f"  NaNs: {res_df[col].isna().sum()} de {len(res_df[col])}\n")
        
        if not has_valid_data:
            # Si no hay datos válidos, crear una figura vacía con mensaje
            import copy
            # Crear una figura vacía con mensaje
            empty_fig = go.Figure()
            empty_fig.add_annotation(
                text="No hay datos válidos para esta placa",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            empty_fig.update_layout(
                title=f"No hay datos válidos para {key}",
                height=600,
                width=900
            )
            figures_2d[key] = empty_fig
            figures_2d_norm[key] = copy.deepcopy(empty_fig)
            figures_3d[key] = copy.deepcopy(empty_fig)
            figures_3d_norm[key] = copy.deepcopy(empty_fig)
            continue
        
        # Crear figura 2D para esta placa-ensayo
        plot_df = res_df if use_percentage else orig_df
        
        with open(debug_file, 'a') as f_debug:
            f_debug.write("\nCreando gráficas 2D:\n")
            f_debug.write(f"DataFrame para graficar shape: {plot_df.shape}\n")
            f_debug.write(f"Columnas: {plot_df.columns.tolist()}\n")
            f_debug.write("Primeras filas:\n")
            f_debug.write(str(plot_df.head()) + "\n")
        
        fig_2d = create_2d_figure(
            plot_df=plot_df,
            key=key,
            use_percentage=use_percentage,
            show_error_bars=show_error_bars,
            use_bar_chart=use_bar_chart,
            subtract_neg_ctrl=subtract_neg_ctrl,
            title_prefix="Original",
            gray_values=gray_values  # Asegurarse de pasar los valores de grays
        )
        figures_2d[key] = fig_2d
        
        # Crear figura 2D normalizada con S1
        with open(debug_file, 'a') as f_debug:
            f_debug.write("\nCreando gráficas 2D normalizadas:\n")
            f_debug.write(f"DataFrame normalizado shape: {norm_df.shape}\n")
            f_debug.write(f"Columnas: {norm_df.columns.tolist()}\n")
            f_debug.write("Primeras filas:\n")
            f_debug.write(str(norm_df.head()) + "\n")
        
        fig_2d_norm = create_2d_figure(
            plot_df=norm_df,
            key=key,
            use_percentage=False,  # Ya está normalizado
            show_error_bars=show_error_bars,
            use_bar_chart=use_bar_chart,
            subtract_neg_ctrl=subtract_neg_ctrl,
            title_prefix="Normalized to S1",
            is_normalized=True,
            gray_values=gray_values  # Asegurarse de pasar los valores de grays
        )
        figures_2d_norm[key] = fig_2d_norm
        
        # Crear figura 3D para esta placa-ensayo
        with open(debug_file, 'a') as f_debug:
            f_debug.write("\nCreando gráficas 3D:\n")
            f_debug.write(f"Usando {len(sub)} puntos de tiempo\n")
            f_debug.write(f"Valores de grises: {gray_values}\n")
        
        gray_values = section_grays[key]
        fig_3d = create_3d_figure(
            df=df,
            plate=plate,
            assay=assay,
            mask=mask,
            neg_ctrl_mask=neg_ctrl_mask,
            sections=sections,
            section_colors=section_colors,
            gray_values=gray_values,
            use_percentage=use_percentage,
            show_error_bars=show_error_bars,
            use_bar_chart=use_bar_chart,
            subtract_neg_ctrl=subtract_neg_ctrl,
            title_prefix="Original",
            debug_file=debug_file  # Pasar el archivo de depuración
        )
        figures_3d[key] = fig_3d
        
        # Crear figura 3D normalizada con S1
        fig_3d_norm = create_3d_figure(
            df=df,
            plate=plate,
            assay=assay,
            mask=mask,
            neg_ctrl_mask=neg_ctrl_mask,
            sections=sections,
            section_colors=section_colors,
            gray_values=gray_values,
            use_percentage=False,  # Ya está normalizado
            show_error_bars=show_error_bars,
            use_bar_chart=use_bar_chart,
            subtract_neg_ctrl=subtract_neg_ctrl,
            title_prefix="Normalized to S1",
            normalized_df=norm_df,
            debug_file=debug_file  # Pasar el archivo de depuración
        )
        figures_3d_norm[key] = fig_3d_norm

    writer.close()
    
    # Generar contenido HTML
    html_content = generate_html_content(figures_2d, figures_2d_norm, figures_3d, figures_3d_norm)
    
    # Verificar que html_content no sea None antes de escribirlo
    if html_content is None:
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error en la generación de gráficos</title>
        </head>
        <body>
            <h1>Error en la generación de gráficos</h1>
            <p>No se pudieron generar los gráficos correctamente. Por favor, revise los datos e intente nuevamente.</p>
        </body>
        </html>
        """

    # Guardar el archivo HTML
    html_path = os.path.join(out_dir, "all_plots.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Generar mensaje de resultado
    mode_text = "percentage change" if use_percentage else "absolute values"
    chart_type = "bar charts" if use_bar_chart else "line charts"
    error_bars = "with error bars" if show_error_bars else "without error bars"
    neg_ctrl_text = "with negative controls subtracted" if subtract_neg_ctrl else "without negative control subtraction"

    result_message = f"Results saved to {out_dir}/all_results.xlsx (showing {mode_text})\n"
    result_message += f"Plots saved to {html_path} and opened in browser ({chart_type} {error_bars}, {neg_ctrl_text})\n"
    result_message += f"3D plots added with Gray values as the third dimension\n"
    result_message += f"Log scale option added to the plot interface\n"
    result_message += f"Plots are responsive and will adjust to window size\n"
    result_message += f"Added normalized plots (dividing by S1 control values)\n"
    result_message += f"Debug information saved to {debug_file}\n"
    
    return result_message, html_path
