"""
Module for plate data visualization.
"""
import numpy as np
import plotly.graph_objects as go
from scipy import interpolate

def create_2d_figure(plot_df, key, use_percentage=True, show_error_bars=True, use_bar_chart=False, subtract_neg_ctrl=True, 
                    title_prefix="", is_normalized=False, gray_values=None):
    """
    Create a 2D figure for a plate-assay.
    
    Args:
        plot_df (pandas.DataFrame): DataFrame with data to plot.
        key (str): Plate-assay key.
        use_percentage (bool, optional): Whether to show results as percentage. Default True.
        show_error_bars (bool, optional): Whether to show error bars. Default True.
        use_bar_chart (bool, optional): Whether to use bar chart instead of lines. Default False.
        subtract_neg_ctrl (bool, optional): Whether negative controls were subtracted. Default True.
        title_prefix (str, optional): Prefix for the title. Default "".
        is_normalized (bool, optional): Whether data is normalized. Default False.
        gray_values (list, optional): List of gray values for each section. Default None.
        
    Returns:
        plotly.graph_objects.Figure: 2D figure.
    """
    fig = go.Figure()
    
    # Sort columns by gray value if provided
    if gray_values is not None:
        # Create a mapping of section to gray value
        section_to_gray = {f"S{i+1}": gray_values[i] for i in range(len(gray_values))}
        
        # Get section columns and sort them by gray value
        section_cols = [c for c in plot_df.columns if c.startswith('S') and not c.endswith('_std')]
        section_cols.sort(key=lambda x: section_to_gray.get(x, 0))
    else:
        # If no gray values, use default order
        section_cols = [c for c in plot_df.columns if c.startswith('S') and not c.endswith('_std')]
    
    # Determine chart type based on checkbox
    if use_bar_chart:
        # Bar chart mode
        # For bar charts, we need to organize data differently
        # Each section will be a group, and each time point will be a bar within that group
        
        # Get unique time points and sort them
        time_points = sorted(plot_df['hours'].unique())
        num_sections = len(section_cols)

        # Calculate adaptive bar width based on number of time points
        # and number of sections
        if len(time_points) > 1:
            # Calculate minimum distance between time points
            min_distance = min([time_points[i+1] - time_points[i] for i in range(len(time_points)-1)])

            # Adjust bar width based on number of time points
            if len(time_points) <= 3:
                # For few time points, use narrower bars
                bar_width = min_distance / (num_sections * 2)
                bargap = 0.4  # More space between groups
                bargroupgap = 0.1  # Moderate space between bars in the same group
            elif len(time_points) >= 6:
                # For many time points, use wider bars
                bar_width = min_distance / (num_sections * 1.2)
                bargap = 0.1  # Less space between groups
                bargroupgap = 0.02  # Minimum space between bars in the same group
            else:
                # Intermediate case
                bar_width = min_distance / (num_sections * 1.5)
                bargap = 0.2  # Moderate space between groups
                bargroupgap = 0.05  # Small space between bars in the same group
        else:
            # Default value if only one time point
            bar_width = 0.15
            bargap = 0.2
            bargroupgap = 0.05

        # For each section, create a bar trace
        for i, col in enumerate(section_cols):
            # Extract section number (e.g., S1 -> 1)
            section_num = int(col[1:])

            # Determine y-axis label based on percentage mode
            if is_normalized:
                if gray_values is not None:
                    y_label = f"{col}({gray_values[section_num-1]})"
                else:
                    y_label = f"{col} (norm)"
            else:
                if gray_values is not None:
                    y_label = f"{col}({gray_values[section_num-1]})" + (" (%)" if use_percentage else "")
                else:
                    y_label = f"{col} (%)" if use_percentage else col

            # Get corresponding standard deviation column
            std_col = f"{col}_std"

            # Create error bars if enabled
            error_y = dict(
                type='data',
                array=plot_df[std_col] if show_error_bars else None,
                visible=show_error_bars
            )

            # Filter data for this trace
            trace_data = plot_df.sort_values('hours')

            # Add bar trace with explicit width
            fig.add_trace(go.Bar(
                x=trace_data['hours'],
                y=trace_data[col],
                name=y_label,
                error_y=error_y,
                width=bar_width  # Adaptive width
            ))

        # Update layout for bar chart with adaptive spacing
        fig.update_layout(
            barmode='group',  # Group bars by time point
            bargap=bargap,    # Adaptive space between different x values (time points)
            bargroupgap=bargroupgap  # Adaptive space between bars in the same group
        )
    else:
        # Line chart mode (default)
        for col in section_cols:
            # Extract section number (e.g., S1 -> 1)
            section_num = int(col[1:])

            # Get corresponding standard deviation column
            std_col = f"{col}_std"

            # Determine y-axis label based on percentage mode
            if is_normalized:
                if gray_values is not None:
                    y_label = f"{col}({gray_values[section_num-1]})"
                else:
                    y_label = f"{col} (norm)"
            else:
                if gray_values is not None:
                    y_label = f"{col}({gray_values[section_num-1]})" + (" (%)" if use_percentage else "")
                else:
                    y_label = f"{col} (%)" if use_percentage else col

            # Add trace with error bars if enabled
            fig.add_trace(go.Scatter(
                x=plot_df['hours'],
                y=plot_df[col],
                mode='lines+markers',
                name=y_label,
                error_y=dict(
                    type='data',
                    array=plot_df[std_col] if show_error_bars else None,
                    visible=show_error_bars
                )
            ))

    # Set appropriate title and axis labels
    if is_normalized:
        title_suffix = " (normalized to S1)"
        y_axis_label = "Normalized value"
    else:
        title_suffix = " (% change from initial value)" if use_percentage else ""
        y_axis_label = "% Change" if use_percentage else "Mean value"

    chart_type = "Bar Chart" if use_bar_chart else "Line Chart"
    neg_ctrl_text = " (Neg Ctrl Subtracted)" if subtract_neg_ctrl else ""

    title_text = f"{title_prefix}: " if title_prefix else ""
    title_text += f"Evolution {key}{title_suffix}{neg_ctrl_text} - {chart_type}"

    # Make plots larger and responsive
    fig.update_layout(
        title=title_text,
        xaxis_title='Hours',
        yaxis_title=y_axis_label,
        height=700,  # Increase height
        width=1000,  # Increase width
        autosize=True,  # Allow auto-sizing
        margin=dict(l=50, r=50, t=80, b=50)  # Adjust margins
    )

    return fig

def create_3d_figure(df, plate, assay, mask, neg_ctrl_mask, sections, section_colors, gray_values,
                    use_percentage=True, show_error_bars=True, use_bar_chart=False, subtract_neg_ctrl=True,
                    title_prefix="", normalized_df=None, debug_file=None):
    """
    Create a 3D figure for a plate-assay.

    Args:
        df (pandas.DataFrame): DataFrame with plate data.
        plate (str): Plate number.
        assay (str): Assay type.
        mask (numpy.ndarray): Well mask (8x12).
        neg_ctrl_mask (numpy.ndarray): Negative control mask (8x12).
        sections (list): List of tuples with section boundaries.
        section_colors (list): List of colors for each section.
        gray_values (list): List of gray values for each section.
        use_percentage (bool, optional): Whether to show results as percentage. Default True.
        show_error_bars (bool, optional): Whether to show error bars. Default True.
        use_bar_chart (bool, optional): Whether to use bar chart instead of surface. Default False.
        subtract_neg_ctrl (bool, optional): Whether to subtract negative controls. Default True.
        title_prefix (str, optional): Prefix for the title. Default "".
        normalized_df (pandas.DataFrame, optional): DataFrame with normalized data. Default None.
        debug_file (str, optional): Path to debug file. Default None.

    Returns:
        plotly.graph_objects.Figure: 3D figure.
    """
    # Function to write to debug file
    def write_debug(message):
        if debug_file:
            with open(debug_file, 'a') as f:
                f.write(message + "\n")

    write_debug(f"\nCreating 3D figure for {plate}_{assay}")

    sub = df[(df['plate_no']==plate) & (df['assay']==assay)].sort_values('hours')

    # Skip if no data
    if sub.empty:
        write_debug("No data for this plate")
        return go.Figure()

    write_debug(f"Found {len(sub)} time points")
    write_debug(f"Available hours: {sub['hours'].tolist()}")

    # Create 3D figure
    fig3d = go.Figure()

    # Collect all data points for a unified surface
    all_hours = []
    all_grays = []
    all_values = []
    all_stds = []
    all_sections = []

    # If we have normalized data, use it directly
    if normalized_df is not None:
        write_debug("Using provided normalized data")

        # For each section, get normalized values
        for i in range(6):
            section_column = f"S{i+1}"
            std_column = f"{section_column}_std"

            for _, row in normalized_df.iterrows():
                # Check if value is NaN
                if not np.isnan(row[section_column]):
                    all_hours.append(row['hours'])
                    all_grays.append(gray_values[i])
                    all_values.append(row[section_column])
                    all_stds.append(row[std_column])
                    all_sections.append(i+1)
    else:
        write_debug("Calculating data from scratch")

        # First pass: collect all raw data
        for i in range(6):
            # Get section boundaries
            r1, c1, r2, c2 = sections[i]

            # Get gray value for this section
            gray = gray_values[i]

            # Process each time point
            for _, row in sub.iterrows():
                data = row['data'].copy()
                hours = row['hours']

                # Subtract negative controls if enabled
                if subtract_neg_ctrl:
                    neg_ctrl_data = data * neg_ctrl_mask
                    valid_neg_ctrls = neg_ctrl_data[neg_ctrl_data != 0]
                    if len(valid_neg_ctrls) > 0:
                        neg_ctrl_avg = np.nanmean(valid_neg_ctrls)
                        # Subtract from all wells
                        data = data - neg_ctrl_avg
                        # Set negative values to 0
                        data[data < 0] = 0

                # Apply mask
                masked_data = data * mask

                # Get section data
                section_data_array = masked_data[r1:r2+1, c1:c2+1]
                valid_data = section_data_array[section_data_array != 0]

                if len(valid_data) > 0:
                    mean_value = np.nanmean(valid_data)
                    std_value = np.nanstd(valid_data) / np.sqrt(len(valid_data))

                    # Store data for this section and time point
                    all_hours.append(hours)
                    all_grays.append(gray)
                    all_values.append(mean_value)
                    all_stds.append(std_value)
                    all_sections.append(i+1)

        # Second pass: apply percentage calculation if needed
        if use_percentage:
            write_debug("Applying percentage calculation")

            # Group by section
            section_data = {}
            for i, section in enumerate(all_sections):
                if section not in section_data:
                    section_data[section] = []
                section_data[section].append({
                    'index': i,
                    'hours': all_hours[i],
                    'value': all_values[i],
                    'std': all_stds[i]
                })

            # For each section, calculate percentage
            for section, data_points in section_data.items():
                # Sort by hours
                data_points.sort(key=lambda x: x['hours'])

                # Get base value (first time point)
                if data_points:
                    baseline = data_points[0]['value']

                    if baseline != 0 and not np.isnan(baseline):
                        for point in data_points:
                            idx = point['index']
                            all_values[idx] = ((all_values[idx] / baseline) - 1) * 100
                            all_stds[idx] = (all_stds[idx] / baseline) * 100

    # Skip if no valid data
    if not all_hours:
        write_debug("No valid data to create 3D figure")
        fig3d = go.Figure()
        fig3d.add_annotation(
            text="No valid data for this plate",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig3d.update_layout(
            title=f"No valid data for {plate}_{assay}",
            height=600,
            width=900
        )
        return fig3d

    # Determine whether to use bar chart or surface
    if use_bar_chart:
        write_debug("Creating 3D bar chart")

        # Get unique time points and sort them
        unique_hours = sorted(list(set(all_hours)))
        num_sections = len(set(all_sections))

        # Calculate adaptive bar width
        if len(unique_hours) > 1:
            # Calculate minimum distance between time points
            min_distance = min([unique_hours[i+1] - unique_hours[i] for i in range(len(unique_hours)-1)])

            # Adjust bar width based on number of time points
            if len(unique_hours) <= 3:
                # For few time points, use narrower bars
                bar_width = min_distance / (num_sections * 2)
            elif len(unique_hours) >= 6:
                # For many time points, use wider bars
                bar_width = min_distance / (num_sections * 1.2)
            else:
                # Intermediate case
                bar_width = min_distance / (num_sections * 1.5)
        else:
            # Default value if only one time point
            bar_width = 0.15

        # Create a 3D bar chart using Scatter3d with markers
        for section in sorted(set(all_sections)):
            # Filter data for this section
            indices = [i for i, s in enumerate(all_sections) if s == section]
            section_hours = [all_hours[i] for i in indices]
            section_grays = [all_grays[i] for i in indices]
            section_values = [all_values[i] for i in indices]
            section_stds = [all_stds[i] for i in indices]

            # Use section index to get color (section ranges from 1 to 6)
            section_color = section_colors[section-1]

            # Calculate offset for each bar within the group
            # so they're centered around the time point
            section_idx = section - 1  # Convert to 0-based index
            offset = (section_idx - (num_sections - 1) / 2) * bar_width * 1.2  # Add a bit more space
    else:
        write_debug("Creating 3D surface plot")

        # FIXED: Create a single unified surface for all data points

        # First, add scatter points for all data
        for section in sorted(set(all_sections)):
            # Filter data for this section
            indices = [i for i, s in enumerate(all_sections) if s == section]
            section_hours = [all_hours[i] for i in indices]
            section_grays = [all_grays[i] for i in indices]
            section_values = [all_values[i] for i in indices]

            # Use section index to get color (section ranges from 1 to 6)
            section_color = section_colors[section-1]

            # Add scatter points for this section
            fig3d.add_trace(go.Scatter3d(
                x=section_hours,
                y=section_grays,
                z=section_values,
                mode='markers',
                name=f'S{section}',
                marker=dict(
                    size=5,
                    color=section_color,
                    opacity=0.8
                )
            ))

            # Add error bars if enabled
            if show_error_bars:
                section_stds = [all_stds[i] for i in indices]
                for h, g, v, s in zip(section_hours, section_grays, section_values, section_stds):
                    fig3d.add_trace(go.Scatter3d(
                        x=[h, h],
                        y=[g, g],
                        z=[v-s, v+s],
                        mode='lines',
                        line=dict(color='red', width=2),
                        showlegend=False
                    ))

        # Now create a single unified surface
        if len(all_hours) >= 4:  # Need at least 4 points for interpolation
            try:
                # Create a grid for interpolation
                unique_hours = sorted(list(set(all_hours)))
                unique_grays = sorted(list(set(all_grays)))

                if len(unique_hours) >= 2 and len(unique_grays) >= 2:
                    # Create a grid for interpolation
                    grid_x, grid_y = np.meshgrid(
                        np.linspace(min(unique_hours), max(unique_hours), 30),
                        np.linspace(min(unique_grays), max(unique_grays), 30)
                    )

                    # Prepare points for interpolation
                    points = np.array(list(zip(all_hours, all_grays)))
                    values = np.array(all_values)

                    # Use griddata for interpolation
                    grid_z = interpolate.griddata(
                        points,
                        values,
                        (grid_x, grid_y),
                        method='linear',
                        fill_value=np.nan
                    )

                    # Create a colorscale that transitions through all section colors
                    colorscale = []
                    for i, color in enumerate(section_colors):
                        colorscale.append([i/len(section_colors), color])
                        colorscale.append([(i+1)/len(section_colors), color])

                    # Add surface with custom colorscale
                    fig3d.add_trace(go.Surface(
                        z=grid_z,
                        x=grid_x,
                        y=grid_y,
                        colorscale='Viridis',  # Use a standard colorscale for better visualization
                        opacity=0.8,
                        name='Surface',
                        showscale=False
                    ))
            except Exception as e:
                write_debug(f"Error creating unified surface: {e}")

    # Update layout
    key = f"{plate}_{assay}"
    if normalized_df is not None:
        title_suffix = " (normalized to S1)"
        y_axis_label = "Normalized value"
    else:
        title_suffix = " (% change from initial value)" if use_percentage else ""
        y_axis_label = "% Change" if use_percentage else "Value"

    neg_ctrl_text = " (with Neg Ctrl Subtracted)" if subtract_neg_ctrl else ""
    chart_type = "3D Bar Chart" if use_bar_chart else "3D Surface"
    error_text = " with Error Bars" if show_error_bars else ""

    title_text = f"{title_prefix}: " if title_prefix else ""
    title_text += f"3D View: {key}{title_suffix}{neg_ctrl_text} - {chart_type}{error_text}"

    # Move legend to bottom
    fig3d.update_layout(
        title=title_text,
        scene=dict(
            xaxis_title='Hours',
            yaxis_title='Grays',
            zaxis_title=y_axis_label,
            aspectmode='auto'  # Allow axes to adjust automatically
        ),
        height=700,  # Increase height
        width=1000,  # Increase width
        autosize=True,  # Allow auto-sizing
        margin=dict(l=50, r=50, t=80, b=50),  # Adjust margins
        legend=dict(
            x=0.5,  # Center horizontally
            y=0,    # Place at bottom
            xanchor='center',
            yanchor='bottom',
            orientation='h',  # Horizontal orientation
            bgcolor='rgba(255,255,255,0.8)'  # Semi-transparent background
        )
    )

    write_debug("3D figure created successfully")
    return fig3d
