"""
Module for plate data analysis.
"""
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import copy
from src.core.visualization.plots import create_2d_figure, create_3d_figure
from src.core.visualization.html_generator import generate_html_content

def analyze_plate(df, plate, assay, mask, neg_ctrl_mask, sections, use_percentage=True, 
                 subtract_neg_ctrl=True, current_individual_plate=None):
    """
    Analyze a specific plate and return results as text.
    
    Args:
        df (pandas.DataFrame): DataFrame with plate data.
        plate (str): Plate number.
        assay (str): Assay type.
        mask (numpy.ndarray): Well mask (8x12).
        neg_ctrl_mask (numpy.ndarray): Negative control mask (8x12).
        sections (list): List of tuples with section boundaries.
        use_percentage (bool, optional): Whether to show results as percentage. Default True.
        subtract_neg_ctrl (bool, optional): Whether to subtract negative controls. Default True.
        current_individual_plate (pandas.Series, optional): Data for the selected individual plate.
        
    Returns:
        str: Text with analysis results.
    """
    result_text = ""
    
    # If in advanced mode and an individual plate is selected
    if current_individual_plate is not None:
        # Analyze only this individual plate
        data = current_individual_plate['data'].copy()
        hours = current_individual_plate['hours']
        
        # Subtract negative controls if enabled
        neg_ctrl_avg = np.nan
        neg_ctrl_std = np.nan
        if subtract_neg_ctrl:
            # Calculate average and standard deviation of negative controls
            neg_ctrl_data = data * neg_ctrl_mask
            valid_neg_ctrls = neg_ctrl_data[neg_ctrl_data != 0]
            if len(valid_neg_ctrls) > 0:
                neg_ctrl_avg = np.nanmean(valid_neg_ctrls)
                neg_ctrl_std = np.nanstd(valid_neg_ctrls)
                # Subtract from all wells
                data = data - neg_ctrl_avg
                # Set negative values to 0
                data[data < 0] = 0
        
        # Apply mask
        masked_data = data * mask
        
        # Calculate means and standard deviations of sections
        sec_means = {}
        sec_stds = {}
        
        # For each section, calculate mean and standard deviation with error propagation
        for i, (r1, c1, r2, c2) in enumerate(sections):
            section_data = masked_data[r1:r2+1, c1:c2+1]
            # Filter masked values (zeros)
            valid_data = section_data[section_data != 0]
            if len(valid_data) > 0:
                sec_means[f"S{i+1}"] = np.nanmean(valid_data)
                # Propagate error if negative controls were subtracted
                if subtract_neg_ctrl and not np.isnan(neg_ctrl_std):
                    # Error propagation formula for subtraction: sqrt(std1^2 + std2^2)
                    section_std = np.nanstd(valid_data)
                    # Standard error: standard deviation / sqrt(n)
                    n = len(valid_data)
                    section_std = section_std / np.sqrt(n)
                    propagated_std = np.sqrt(section_std**2 + neg_ctrl_std**2)
                    sec_stds[f"S{i+1}_std"] = propagated_std
                else:
                    # Standard error: standard deviation / sqrt(n)
                    n = len(valid_data)
                    sec_stds[f"S{i+1}_std"] = np.nanstd(valid_data) / np.sqrt(n)
            else:
                sec_means[f"S{i+1}"] = np.nan
                sec_stds[f"S{i+1}_std"] = np.nan
        
        # Generate results text
        result_text += f"Analysis for individual plate: {plate}_{assay} at {hours} hours\n\n"
        
        # Show negative control information if used
        if subtract_neg_ctrl:
            neg_ctrl_count = np.sum(neg_ctrl_mask)
            if neg_ctrl_count > 0:
                result_text += f"Negative controls: {neg_ctrl_count} wells, avg value: {neg_ctrl_avg:.4f}, std: {neg_ctrl_std:.4f}\n\n"
            else:
                result_text += "No negative controls selected\n\n"
        
        for sec in sec_means.keys():
            result_text += f"{sec}: {sec_means[sec]:.4f} ± {sec_stds[sec]:.4f}\n"
        
        return result_text
    
    # Regular mode - analyze all time points for the selected plate-assay
    sub = df[(df['plate_no']==plate) & (df['assay']==assay)].sort_values('hours')
    results = []
    
    # Process each time point
    for _, row in sub.iterrows():
        data = row['data'].copy()  # Make a copy to avoid modifying the original
        
        # Subtract negative controls if enabled
        neg_ctrl_avg = np.nan
        neg_ctrl_std = np.nan
        if subtract_neg_ctrl:
            # Calculate average and standard deviation of negative controls for this time point
            neg_ctrl_data = data * neg_ctrl_mask
            valid_neg_ctrls = neg_ctrl_data[neg_ctrl_data != 0]
            if len(valid_neg_ctrls) > 0:
                neg_ctrl_avg = np.nanmean(valid_neg_ctrls)
                neg_ctrl_std = np.nanstd(valid_neg_ctrls)
                # Subtract from all wells
                data = data - neg_ctrl_avg
                # Set negative values to 0
                data[data < 0] = 0
        
        # Apply mask
        masked_data = data * mask
        
        sec_means = {}
        sec_stds = {}
        neg_ctrl_info = {'hours': row['hours'], 'neg_ctrl_avg': neg_ctrl_avg, 'neg_ctrl_std': neg_ctrl_std}
        
        # For each section, calculate mean and standard deviation with error propagation
        for i, (r1, c1, r2, c2) in enumerate(sections):
            section_data = masked_data[r1:r2+1, c1:c2+1]
            # Filter masked values (zeros)
            valid_data = section_data[section_data != 0]
            if len(valid_data) > 0:
                sec_means[f"S{i+1}"] = np.nanmean(valid_data)
                # Propagate error if negative controls were subtracted
                if subtract_neg_ctrl and not np.isnan(neg_ctrl_std):
                    # Error propagation formula for subtraction: sqrt(std1^2 + std2^2)
                    section_std = np.nanstd(valid_data)
                    # Standard error: standard deviation / sqrt(n)
                    n = len(valid_data)
                    section_std = section_std / np.sqrt(n)
                    propagated_std = np.sqrt(section_std**2 + neg_ctrl_std**2)
                    sec_stds[f"S{i+1}_std"] = propagated_std
                else:
                    # Standard error: standard deviation / sqrt(n)
                    n = len(valid_data)
                    sec_stds[f"S{i+1}_std"] = np.nanstd(valid_data) / np.sqrt(n)
            else:
                sec_means[f"S{i+1}"] = np.nan
                sec_stds[f"S{i+1}_std"] = np.nan
        
        # Combine means and standard deviations
        combined_results = {**sec_means, **sec_stds, **neg_ctrl_info}
        results.append(combined_results)
    
    # Convert to DataFrame
    res_df = pd.DataFrame(results)
    
    # Apply percentage calculation if enabled
    if use_percentage and len(res_df) > 0:
        # Get values from the first row for each section
        first_values = res_df.iloc[0].copy()
        
        # Calculate percentage change for each section mean
        for col in [c for c in res_df.columns if c.startswith('S') and not c.endswith('_std')]:
            base_value = first_values[col]
            if base_value != 0:  # Avoid division by zero
                # Also adjust standard deviation to be relative to the mean
                std_col = f"{col}_std"
                res_df[std_col] = (res_df[std_col] / base_value) * 100
                res_df[col] = (res_df[col] / base_value - 1) * 100
            else:
                # If base value is zero, set all values to NaN
                std_col = f"{col}_std"
                res_df[col] = np.nan
                res_df[std_col] = np.nan
        
        # Add % symbol to column names
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
        # Just rename standard deviation columns for display
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
    
    # Generate results text
    result_text = ""
    
    # Show negative control information
    if subtract_neg_ctrl:
        neg_ctrl_count = np.sum(neg_ctrl_mask)
        if neg_ctrl_count > 0:
            result_text += f"Negative controls: {neg_ctrl_count} wells\n\n"
        else:
            result_text += "No negative controls selected\n\n"
    
    result_text += display_df.to_string(index=False)
    
    return result_text

def analyze_all_plates(df, keys, mask_map, neg_ctrl_mask_map, section_grays, sections, section_colors,
                      use_percentage=True, show_error_bars=True, use_bar_chart=False, subtract_neg_ctrl=True):
    """
    Analyze all plates, save results to Excel and generate HTML visualizations.
    
    Args:
        df (pandas.DataFrame): DataFrame with plate data.
        keys (list): List of plate-assay keys.
        mask_map (dict): Dictionary of well masks.
        neg_ctrl_mask_map (dict): Dictionary of negative control masks.
        section_grays (dict): Dictionary of gray values for each section.
        sections (list): List of tuples with section boundaries.
        section_colors (list): List of colors for each section.
        use_percentage (bool, optional): Whether to show results as percentage. Default True.
        show_error_bars (bool, optional): Whether to show error bars. Default True.
        use_bar_chart (bool, optional): Whether to use bar chart instead of lines. Default False.
        subtract_neg_ctrl (bool, optional): Whether to subtract negative controls. Default True.
        
    Returns:
        tuple: (result message, path to HTML file)
    """
    out_dir = "analysis_output"
    os.makedirs(out_dir, exist_ok=True)

    # Get logger for this module
    import logging
    logger = logging.getLogger('plate_analyzer')
    
    try:
        writer = pd.ExcelWriter(os.path.join(out_dir, "all_results.xlsx"), engine='xlsxwriter')
    except ImportError:
        writer = pd.ExcelWriter(os.path.join(out_dir, "all_results.xlsx"), engine='openpyxl')

    # Create 2D and 3D figures for all plates
    figures_2d = {}
    figures_2d_norm = {}  # For plots normalized with S1
    figures_3d = {}
    figures_3d_norm = {}  # For 3D plots normalized with S1
    
    for key in keys:
        plate, assay = key.split("_")
        
        # Add diagnostic information
        logger.debug(f"\nProcessing plate: {key}\n")
        logger.debug("-" * 30 + "\n")
        
        sub = df[(df['plate_no']==plate) & (df['assay']==assay)].sort_values('hours')
        
        # Check if there's data for this plate
        if sub.empty:
            logger.warning(f"No data for plate {key}")
            continue
        
        logger.debug(f"Found {len(sub)} time points for {key}")
        logger.debug(f"Available hours: {sub['hours'].tolist()}")
            
        mask = mask_map[key]
        neg_ctrl_mask = neg_ctrl_mask_map[key]
        
        logger.debug(f"Mask: {np.sum(mask)} active wells out of 96")
        logger.debug(f"Negative control mask: {np.sum(neg_ctrl_mask)} marked wells out of 96")
        
        results = []
        gray_values = section_grays[key]
        
        logger.debug(f"Gray values: {gray_values}")
        
        # Process each time point
        for _, row in sub.iterrows():
            data = row['data'].copy()
            hours = row['hours']
            
            logger.debug(f"\nTime point: {hours} hours")
            logger.debug(f"Raw data range: {np.nanmin(data)} to {np.nanmax(data)}")
            logger.debug(f"Raw data mean: {np.nanmean(data)}")
            logger.debug(f"NaNs in raw data: {np.isnan(data).sum()} of {data.size}")
            
            # Subtract negative controls if enabled
            neg_ctrl_avg = np.nan
            neg_ctrl_std = np.nan
            if subtract_neg_ctrl:
                neg_ctrl_data = data * neg_ctrl_mask
                valid_neg_ctrls = neg_ctrl_data[neg_ctrl_data != 0]
                
                logger.debug(f"Valid negative controls: {len(valid_neg_ctrls)}")
                
                if len(valid_neg_ctrls) > 0:
                    neg_ctrl_avg = np.nanmean(valid_neg_ctrls)
                    neg_ctrl_std = np.nanstd(valid_neg_ctrls) / np.sqrt(len(valid_neg_ctrls))  # Standard error
                    
                    logger.debug(f"Negative control mean: {neg_ctrl_avg}")
                    logger.debug(f"Negative control standard error: {neg_ctrl_std}")
                    
                    # Subtract from all wells
                    data = data - neg_ctrl_avg
                    # Set negative values to 0
                    neg_count = np.sum(data < 0)
                    data[data < 0] = 0
                    
                    logger.debug(f"Negative values after subtracting controls: {neg_count}")
            
            # Apply mask
            masked_data = data * mask
            
            logger.debug(f"Data after applying mask - Non-zero values: {np.sum(masked_data != 0)}")
            non_zero = masked_data[masked_data != 0]
            if len(non_zero) > 0:
                logger.debug(f"Non-zero value range: {np.nanmin(non_zero)} to {np.nanmax(non_zero)}")
                logger.debug(f"Non-zero value mean: {np.nanmean(non_zero)}")
            else:
                logger.debug("No non-zero values after applying mask")
            
            # Calculate means and standard deviations for each section
            sec_means = {}
            sec_stds = {}
            neg_ctrl_info = {'hours': row['hours'], 'neg_ctrl_avg': neg_ctrl_avg, 'neg_ctrl_std': neg_ctrl_std}
            
            for i, (r1, c1, r2, c2) in enumerate(sections):
                section_data = masked_data[r1:r2+1, c1:c2+1]
                valid_data = section_data[section_data != 0]
                
                logger.debug(f"Section {i+1}: {len(valid_data)} valid values")
                
                if len(valid_data) > 0:
                    sec_means[f"S{i+1}"] = np.nanmean(valid_data)
                    
                    logger.debug(f"  Mean: {sec_means[f'S{i+1}']}")
                    
                    if subtract_neg_ctrl and not np.isnan(neg_ctrl_std):
                        section_std = np.nanstd(valid_data) / np.sqrt(len(valid_data))  # Standard error
                        propagated_std = np.sqrt(section_std**2 + neg_ctrl_std**2)
                        sec_stds[f"S{i+1}_std"] = propagated_std
                        
                        logger.debug(f"  Standard deviation (propagated): {propagated_std}")
                    else:
                        sec_stds[f"S{i+1}_std"] = np.nanstd(valid_data) / np.sqrt(len(valid_data))  # Standard error
                        
                        logger.debug(f"  Standard deviation: {sec_stds[f'S{i+1}_std']}")
                else:
                    sec_means[f"S{i+1}"] = np.nan
                    sec_stds[f"S{i+1}_std"] = np.nan
                    
                    logger.debug("  No valid data for this section")
            
            # Combine results
            combined_results = {**sec_means, **sec_stds, **neg_ctrl_info}
            results.append(combined_results)
        
        # Convert to DataFrame
        res_df = pd.DataFrame(results)
        
        logger.debug("\nProcessed results:")
        logger.debug(f"DataFrame shape: {res_df.shape}")
        logger.debug(f"Columns: {res_df.columns.tolist()}")
        logger.debug("First rows:")
        logger.debug(str(res_df.head()))
        
        # Save the DataFrame to Excel
        res_df.to_excel(writer, sheet_name='All Results', index=False)
        
        # Debugging: Log final DataFrame
        logger.debug("\nFinal DataFrame (res_df) saved to Excel:")
        logger.debug(str(res_df.head()))
        
        # Save original values for plotting
        orig_df = res_df.copy()
        
        # Create normalized DataFrame with S1 as control
        norm_df = res_df.copy()
        
        # For each time point, normalize all sections by dividing by S1 value
        for i, row in norm_df.iterrows():
            s1_value = row['S1']
            
            logger.debug(f"\nNormalization for time {row['hours']} hours:")
            logger.debug(f"S1 value: {s1_value}")
            
            if not np.isnan(s1_value) and s1_value != 0:  # Avoid division by zero
                for col in [c for c in norm_df.columns if c.startswith('S') and not c.endswith('_std')]:
                    if col != 'S1':  # Don't normalize S1 with itself
                        # Normalize the value
                        norm_df.at[i, col] = row[col] / s1_value
                        
                        logger.debug(f"  {col}: {row[col]} / {s1_value} = {norm_df.at[i, col]}")
                        
                        # Also adjust standard deviation to maintain proportion
                        std_col = f"{col}_std"
                        norm_df.at[i, std_col] = row[std_col] / s1_value
                
                # Also need to create uncertainty for S1 (which is now 1)
                norm_df.at[i, 'S1'] = 1.0
                s1_std = row['S1_std']
                if not np.isnan(s1_std):
                    # Relative error: std/value
                    norm_df.at[i, 'S1_std'] = s1_std / s1_value
            else:
                logger.debug("  Cannot normalize: S1 is NaN or zero")
        
        # Apply percentage calculation if enabled
        if use_percentage and len(res_df) > 0:
            first_values = res_df.iloc[0].copy()
            
            logger.debug("\nPercentage calculation:")
            logger.debug(f"Initial values: {first_values[first_values.index.str.startswith('S')].to_dict()}")
            
            for col in [c for c in res_df.columns if c.startswith('S') and not c.endswith('_std')]:
                base_value = first_values[col]
                
                logger.debug(f"Column {col}, base value: {base_value}")
                
                if base_value != 0 and not np.isnan(base_value):  # Avoid division by zero and NaN
                    std_col = f"{col}_std"
                    res_df[std_col] = (res_df[std_col] / base_value) * 100
                    res_df[col] = (res_df[col] / base_value - 1) * 100
                    
                    logger.debug(f"  Converted to percentage. New values: {res_df[col].tolist()}")
                else:
                    std_col = f"{col}_std"
                    res_df[col] = np.nan
                    res_df[std_col] = np.nan
                    
                    logger.debug(f"  Cannot calculate percentage: base value is {base_value}")
            
            # Rename columns for display
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
            
            # Save to Excel with percentage column names
            sheet_name = key
            display_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Also save normalized version in another sheet
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
            # Just rename standard deviation columns for display
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
            
            # Save original values to Excel
            sheet_name = key
            display_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Also save normalized version in another sheet
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
        
        # Check if there's valid data for plotting
        has_valid_data = False
        for col in [c for c in res_df.columns if c.startswith('S') and not c.endswith('_std')]:
            if not res_df[col].isna().all():
                has_valid_data = True
                break
        
        logger.debug(f"\nHas valid data for plotting? {has_valid_data}")
        if not has_valid_data:
            logger.debug("WARNING: No valid data for plotting this plate")
            # Show more details about the data
            logger.debug("Data details:")
            for col in [c for c in res_df.columns if c.startswith('S') and not c.endswith('_std')]:
                logger.debug(f"  {col}: {res_df[col].tolist()}")
                logger.debug(f"  NaNs: {res_df[col].isna().sum()} of {len(res_df[col])}")
        
        if not has_valid_data:
            # If there's no valid data, create an empty figure with message
            import copy
            # Create an empty figure with message
            empty_fig = go.Figure()
            empty_fig.add_annotation(
                text="No valid data for this plate",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            empty_fig.update_layout(
                title=f"No valid data for {key}",
                height=600,
                width=900
            )
            figures_2d[key] = empty_fig
            figures_2d_norm[key] = copy.deepcopy(empty_fig)
            figures_3d[key] = copy.deepcopy(empty_fig)
            figures_3d_norm[key] = copy.deepcopy(empty_fig)
            continue
        
        # Create 2D figure for this plate-assay
        plot_df = res_df if use_percentage else orig_df
        
        logger.debug("\nCreating 2D plots:")
        logger.debug(f"DataFrame for plotting shape: {plot_df.shape}")
        logger.debug(f"Columns: {plot_df.columns.tolist()}")
        logger.debug("First rows:")
        logger.debug(str(plot_df.head()))
        
        fig_2d = create_2d_figure(
            plot_df=plot_df,
            key=key,
            use_percentage=use_percentage,
            show_error_bars=show_error_bars,
            use_bar_chart=use_bar_chart,
            subtract_neg_ctrl=subtract_neg_ctrl,
            title_prefix="Original",
            gray_values=gray_values)
        figures_2d[key] = fig_2d
        
        # Create normalized 2D figure with S1
        logger.debug("\nCreating normalized 2D plots:")
        logger.debug(f"Normalized DataFrame shape: {norm_df.shape}")
        logger.debug(f"Columns: {norm_df.columns.tolist()}")
        logger.debug("First rows:")
        logger.debug(str(norm_df.head()))
        
        fig_2d_norm = create_2d_figure(
            plot_df=norm_df,
            key=key,
            use_percentage=False,  # Already normalized
            show_error_bars=show_error_bars,
            use_bar_chart=use_bar_chart,
            subtract_neg_ctrl=subtract_neg_ctrl,
            title_prefix="Normalized to S1",
            is_normalized=True,
            gray_values=gray_values  # Make sure to pass gray values
        )
        figures_2d_norm[key] = fig_2d_norm
        
        # Create 3D figure for this plate-assay
        logger.debug("\nCreating 3D plots:")
        logger.debug(f"Using {len(sub)} time points")
        logger.debug(f"Gray values: {gray_values}")
        
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
            title_prefix="Original"
        )
        figures_3d[key] = fig_3d
        
        # Create normalized 3D figure with S1
        fig_3d_norm = create_3d_figure(
            df=df,
            plate=plate,
            assay=assay,
            mask=mask,
            neg_ctrl_mask=neg_ctrl_mask,
            sections=sections,
            section_colors=section_colors,
            gray_values=gray_values,
            use_percentage=False,  # Already normalized
            show_error_bars=show_error_bars,
            use_bar_chart=use_bar_chart,
            subtract_neg_ctrl=subtract_neg_ctrl,
            title_prefix="Normalized to S1",
            normalized_df=norm_df
        )
        figures_3d_norm[key] = fig_3d_norm

    writer.close()
    
    # Generate HTML content
    html_content = generate_html_content(figures_2d, figures_2d_norm, figures_3d, figures_3d_norm)
    
    # Verify that html_content is not None before writing it
    if html_content is None:
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error in plot generation</title>
        </head>
        <body>
            <h1>Error in plot generation</h1>
            <p>Plots could not be generated correctly. Please check the data and try again.</p>
        </body>
        </html>
        """

    # Save HTML file
    html_path = os.path.join(out_dir, "all_plots.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Generate result message
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

    
    return result_message, html_path
