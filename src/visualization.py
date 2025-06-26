"""
Módulo para la visualización de datos de placas.
"""
import numpy as np
import plotly.graph_objects as go
from scipy import interpolate

# Modificar la función create_2d_figure para añadir argumentos para título personalizado
def create_2d_figure(plot_df, key, use_percentage=True, show_error_bars=True, use_bar_chart=False, subtract_neg_ctrl=True, 
                    title_prefix="", is_normalized=False, gray_values=None, section_units="grays"):
    """
    Crea una figura 2D para una placa-ensayo.
    
    Args:
        plot_df (pandas.DataFrame): DataFrame con los datos a graficar.
        key (str): Clave placa-ensayo.
        use_percentage (bool, optional): Si se deben mostrar los resultados como porcentaje. Por defecto True.
        show_error_bars (bool, optional): Si se deben mostrar barras de error. Por defecto True.
        use_bar_chart (bool, optional): Si se debe usar gráfico de barras en lugar de líneas. Por defecto False.
        subtract_neg_ctrl (bool, optional): Si se restaron los controles negativos. Por defecto True.
        title_prefix (str, optional): Prefijo para el título. Por defecto "".
        is_normalized (bool, optional): Si los datos están normalizados. Por defecto False.
        gray_values (list, optional): Lista de valores de grises para cada sección. Por defecto None.
        section_units (str, optional): Unidades para los valores de sección. Por defecto "grays".
        
    Returns:
        plotly.graph_objects.Figure: Figura 2D.
    """
    fig = go.Figure()
    
    # Ordenar las columnas por valor de grays si se proporciona
    if gray_values is not None:
        # Crear un mapeo de sección a valor de gray
        section_to_gray = {f"S{i+1}": gray_values[i] for i in range(len(gray_values))}
        
        # Obtener las columnas de sección y ordenarlas por valor de gray
        section_cols = [c for c in plot_df.columns if c.startswith('S') and not c.endswith('_std')]
        section_cols.sort(key=lambda x: section_to_gray.get(x, 0))
    else:
        # Si no hay valores de gray, usar el orden predeterminado
        section_cols = [c for c in plot_df.columns if c.startswith('S') and not c.endswith('_std')]
    
    # Determinar tipo de gráfico basado en checkbox
    if use_bar_chart:
        # Modo gráfico de barras
        # Para gráficos de barras, necesitamos organizar los datos de manera diferente
        # Cada sección será un grupo, y cada punto de tiempo será una barra dentro de ese grupo
        
        # Obtener puntos de tiempo únicos y ordenarlos
        time_points = sorted(plot_df['hours'].unique())
        num_sections = len(section_cols)

        # Calcular el ancho de barra adaptativo basado en el número de puntos de tiempo
        # y el número de secciones
        if len(time_points) > 1:
            # Calcular la distancia mínima entre puntos de tiempo
            min_distance = min([time_points[i+1] - time_points[i] for i in range(len(time_points)-1)])

            # Ajustar el ancho de barra según el número de puntos de tiempo
            if len(time_points) <= 3:
                # Para pocos puntos de tiempo, usar barras más estrechas
                bar_width = min_distance / (num_sections * 2)
                bargap = 0.4  # Mayor espacio entre grupos
                bargroupgap = 0.1  # Espacio moderado entre barras del mismo grupo
            elif len(time_points) >= 6:
                # Para muchos puntos de tiempo, usar barras más anchas
                bar_width = min_distance / (num_sections * 1.2)
                bargap = 0.1  # Menor espacio entre grupos
                bargroupgap = 0.02  # Espacio mínimo entre barras del mismo grupo
            else:
                # Caso intermedio
                bar_width = min_distance / (num_sections * 1.5)
                bargap = 0.2  # Espacio moderado entre grupos
                bargroupgap = 0.05  # Espacio pequeño entre barras del mismo grupo
        else:
            # Valor por defecto si solo hay un punto de tiempo
            bar_width = 0.15
            bargap = 0.2
            bargroupgap = 0.05

        # Para cada sección, crear un trazo de barra
        for i, col in enumerate(section_cols):
            # Extraer el número de sección (por ejemplo, S1 -> 1)
            section_num = int(col[1:])

            # Determinar etiqueta del eje y basada en modo porcentaje
            if is_normalized:
                if gray_values is not None:
                    y_label = f"{col}({gray_values[section_num-1]} {section_units})"
                else:
                    y_label = f"{col} (norm)"
            else:
                if gray_values is not None:
                    y_label = f"{col}({gray_values[section_num-1]} {section_units})" + (" (%)" if use_percentage else "")
                else:
                    y_label = f"{col} (%)" if use_percentage else col

            # Obtener columna de desviación estándar correspondiente
            std_col = f"{col}_std"

            # Crear barras de error si están habilitadas
            error_y = dict(
                type='data',
                array=plot_df[std_col] if show_error_bars else None,
                visible=show_error_bars
            )

            # Filtrar los datos para este trazo
            trace_data = plot_df.sort_values('hours')

            # Añadir trazo de barra con width explícito
            fig.add_trace(go.Bar(
                x=trace_data['hours'],
                y=trace_data[col],
                name=y_label,
                error_y=error_y,
                width=bar_width  # Ancho adaptativo
            ))

        # Update layout for bar chart with adaptive spacing
        fig.update_layout(
            barmode='group',  # Group bars by time point
            bargap=bargap,    # Espacio adaptativo entre diferentes valores x (puntos de tiempo)
            bargroupgap=bargroupgap  # Espacio adaptativo entre barras en el mismo grupo
        )
    else:
        # Modo gráfico de líneas (por defecto)
        for col in section_cols:
            # Extraer el número de sección (por ejemplo, S1 -> 1)
            section_num = int(col[1:])

            # Obtener columna de desviación estándar correspondiente
            std_col = f"{col}_std"

            # Determinar etiqueta del eje y basada en modo porcentaje
            if is_normalized:
                if gray_values is not None:
                    y_label = f"{col}({gray_values[section_num-1]} {section_units})"
                else:
                    y_label = f"{col} (norm)"
            else:
                if gray_values is not None:
                    y_label = f"{col}({gray_values[section_num-1]} {section_units})" + (" (%)" if use_percentage else "")
                else:
                    y_label = f"{col} (%)" if use_percentage else col

            # Añadir trazo con barras de error si están habilitadas
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

    # Establecer título y etiquetas de ejes apropiados
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

    # Hacer que las gráficas sean más grandes y responsivas
    fig.update_layout(
        title=title_text,
        xaxis_title='Hours',
        yaxis_title=y_axis_label,
        height=700,  # Aumentar altura
        width=1000,  # Aumentar ancho
        autosize=True,  # Permitir ajuste automático
        margin=dict(l=50, r=50, t=80, b=50)  # Ajustar márgenes
    )

    return fig

# Modificar la función create_3d_figure para añadir soporte para normalización con S1
def create_3d_figure(df, plate, assay, mask, neg_ctrl_mask, sections, section_colors, gray_values,
                    use_percentage=True, show_error_bars=True, use_bar_chart=False, subtract_neg_ctrl=True,
                    title_prefix="", normalized_df=None, debug_file=None, section_units="grays"):
    """
    Crea una figura 3D para una placa-ensayo.

    Args:
        df (pandas.DataFrame): DataFrame con los datos de las placas.
        plate (str): Número de placa.
        assay (str): Tipo de ensayo.
        mask (numpy.ndarray): Máscara de pocillos (8x12).
        neg_ctrl_mask (numpy.ndarray): Máscara de controles negativos (8x12).
        sections (list): Lista de tuplas con los límites de cada sección.
        section_colors (list): Lista de colores para cada sección.
        gray_values (list): Lista de valores de grises para cada sección.
        use_percentage (bool, optional): Si se deben mostrar los resultados como porcentaje. Por defecto True.
        show_error_bars (bool, optional): Si se deben mostrar barras de error. Por defecto True.
        use_bar_chart (bool, optional): Si se debe usar gráfico de barras en lugar de superficie. Por defecto False.
        subtract_neg_ctrl (bool, optional): Si se deben restar los controles negativos. Por defecto True.
        title_prefix (str, optional): Prefijo para el título. Por defecto "".
        normalized_df (pandas.DataFrame, optional): DataFrame con datos normalizados. Por defecto None.
        debug_file (str, optional): Ruta al archivo de depuración. Por defecto None.
        section_units (str, optional): Unidades para los valores de sección. Por defecto "grays".

    Returns:
        plotly.graph_objects.Figure: Figura 3D.
    """
    # Función para escribir en el archivo de depuración
    def write_debug(message):
        if debug_file:
            with open(debug_file, 'a') as f:
                f.write(message + "\n")

    write_debug(f"\nCreando figura 3D para {plate}_{assay}")

    sub = df[(df['plate_no']==plate) & (df['assay']==assay)].sort_values('hours')

    # Saltar si no hay datos
    if sub.empty:
        write_debug("No hay datos para esta placa")
        return go.Figure()

    write_debug(f"Encontrados {len(sub)} puntos de tiempo")
    write_debug(f"Horas disponibles: {sub['hours'].tolist()}")

    # Crear figura 3D
    fig3d = go.Figure()

    # Recopilar todos los puntos de datos para una superficie unificada
    all_hours = []
    all_grays = []
    all_values = []
    all_stds = []
    all_sections = []

    # Si tenemos datos normalizados, usarlos directamente
    if normalized_df is not None:
        write_debug("Usando datos normalizados proporcionados")

        # Get the actual section columns that exist in the normalized dataframe
        available_sections = [col for col in normalized_df.columns if col.startswith('S') and not col.endswith('_std')]
        
        # Para cada sección disponible, obtener los valores normalizados
        for section_col in available_sections:
            std_column = f"{section_col}_std"
            
            # Extract section number for gray values
            section_num = int(section_col[1:]) - 1  # Convert S1->0, S2->1, etc.
            
            for _, row in normalized_df.iterrows():
                # Verificar si el valor es NaN
                if section_col in row and not np.isnan(row[section_col]):
                    all_hours.append(row['hours'])
                    # Use gray value if available, otherwise use 0
                    gray_value = gray_values[section_num] if section_num < len(gray_values) else 0
                    all_grays.append(gray_value)
                    all_values.append(row[section_col])
                    if std_column in row:
                        all_stds.append(row[std_column])
                    else:
                        all_stds.append(0)
                    all_sections.append(section_num + 1)  # Convert back to 1-based
    else:
        write_debug("Calculando datos desde cero")

        # Primera pasada: recopilar todos los datos brutos
        # Use the actual number of sections available
        num_sections = len(sections)
        
        for i in range(num_sections):
            # Obtener límites de sección
            if i < len(sections):
                r1, c1, r2, c2 = sections[i]
            else:
                # Skip this section if it doesn't exist
                continue

            # Obtener valor de gris para esta sección
            gray = gray_values[i] if i < len(gray_values) else 0

            # Procesar cada punto de tiempo
            for _, row in sub.iterrows():
                data = row['data'].copy()
                hours = row['hours']

                # Restar controles negativos si está habilitado
                if subtract_neg_ctrl:
                    neg_ctrl_data = data * neg_ctrl_mask
                    valid_neg_ctrls = neg_ctrl_data[neg_ctrl_data != 0]
                    if len(valid_neg_ctrls) > 0:
                        neg_ctrl_avg = np.nanmean(valid_neg_ctrls)
                        # Restar de todos los pocillos
                        data = data - neg_ctrl_avg
                        # Establecer valores negativos a 0
                        data[data < 0] = 0

                # Aplicar máscara
                masked_data = data * mask

                # Obtener datos de sección
                section_data_array = masked_data[r1:r2+1, c1:c2+1]
                valid_data = section_data_array[section_data_array != 0]

                if len(valid_data) > 0:
                    mean_value = np.nanmean(valid_data)
                    std_value = np.nanstd(valid_data) / np.sqrt(len(valid_data))

                    # Almacenar datos para esta sección y punto de tiempo
                    all_hours.append(hours)
                    all_grays.append(gray)
                    all_values.append(mean_value)
                    all_stds.append(std_value)
                    all_sections.append(i+1)

        # Segunda pasada: aplicar cálculo de porcentaje si es necesario
        if use_percentage:
            write_debug("Aplicando cálculo de porcentaje")

            # Agrupar por sección
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

            # Para cada sección, calcular porcentaje
            for section, data_points in section_data.items():
                # Ordenar por horas
                data_points.sort(key=lambda x: x['hours'])

                # Obtener valor base (primer punto de tiempo)
                if data_points:
                    baseline = data_points[0]['value']

                    if baseline != 0 and not np.isnan(baseline):
                        for point in data_points:
                            idx = point['index']
                            all_values[idx] = ((all_values[idx] / baseline) - 1) * 100
                            all_stds[idx] = (all_stds[idx] / baseline) * 100

    # Saltar si no hay datos válidos
    if not all_hours:
        write_debug("No hay datos válidos para crear la figura 3D")
        fig3d = go.Figure()
        fig3d.add_annotation(
            text="No hay datos válidos para esta placa",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig3d.update_layout(
            title=f"No hay datos válidos para {plate}_{assay}",
            height=600,
            width=900
        )
        return fig3d

    # Determinar si se debe usar gráfico de barras o superficie
    if use_bar_chart:
        write_debug("Creando gráfico de barras 3D")

        # Obtener puntos de tiempo únicos y ordenarlos
        unique_hours = sorted(list(set(all_hours)))
        num_sections = len(set(all_sections))

        # Calcular el ancho de barra adaptativo
        if len(unique_hours) > 1:
            # Calcular la distancia mínima entre puntos de tiempo
            min_distance = min([unique_hours[i+1] - unique_hours[i] for i in range(len(unique_hours)-1)])

            # Ajustar el ancho de barra según el número de puntos de tiempo
            if len(unique_hours) <= 3:
                # Para pocos puntos de tiempo, usar barras más estrechas
                bar_width = min_distance / (num_sections * 2)
            elif len(unique_hours) >= 6:
                # Para muchos puntos de tiempo, usar barras más anchas
                bar_width = min_distance / (num_sections * 1.2)
            else:
                # Caso intermedio
                bar_width = min_distance / (num_sections * 1.5)
        else:
            # Valor por defecto si solo hay un punto de tiempo
            bar_width = 0.15

        # Crear un gráfico de barras 3D usando Scatter3d con marcadores
        for section in sorted(set(all_sections)):
            # Filtrar datos para esta sección
            indices = [i for i, s in enumerate(all_sections) if s == section]
            section_hours = [all_hours[i] for i in indices]
            section_grays = [all_grays[i] for i in indices]
            section_values = [all_values[i] for i in indices]
            section_stds = [all_stds[i] for i in indices]

            # Usar el índice de sección para obtener el color (section va de 1 a 6)
            section_color = section_colors[section-1]

            # Calcular el desplazamiento para cada barra dentro del grupo
            # para que estén centradas alrededor del punto de tiempo
            section_idx = section - 1  # Convertir a índice base 0
            offset = (section_idx - (num_sections - 1) / 2) * bar_width * 1.2  # Añadir un poco más de espacio
    else:
        write_debug("Creating 3D surface plot")

        # FIXED: Create a single unified surface for all data points

        # First, add scatter points for all data
        for section in sorted(set(all_sections)):
            # Filtrar datos para esta sección
            indices = [i for i, s in enumerate(all_sections) if s == section]
            section_hours = [all_hours[i] for i in indices]
            section_grays = [all_grays[i] for i in indices]
            section_values = [all_values[i] for i in indices]

            # Usar el índice de sección para obtener el color (section va de 1 a 6)
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

    # Actualizar layout
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

    # Mover la leyenda a la parte inferior
    fig3d.update_layout(
        title=title_text,
        scene=dict(
            xaxis_title='Hours',
            yaxis_title=section_units.capitalize(),  # Use the configured section units
            zaxis_title=y_axis_label,
            aspectmode='auto'  # Permitir que los ejes se ajusten automáticamente
        ),
        height=700,  # Aumentar altura
        width=1000,  # Aumentar ancho
        autosize=True,  # Permitir ajuste automático
        margin=dict(l=50, r=50, t=80, b=50),  # Ajustar márgenes
        legend=dict(
            x=0.5,  # Centrar horizontalmente
            y=0,    # Colocar en la parte inferior
            xanchor='center',
            yanchor='bottom',
            orientation='h',  # Orientación horizontal
            bgcolor='rgba(255,255,255,0.8)'  # Fondo semi-transparente
        )
    )

    write_debug("Figura 3D creada exitosamente")
    return fig3d

# Modificar la función generate_html_content para soportar las gráficas normalizadas
def generate_html_content(figures_2d, figures_2d_norm, figures_3d, figures_3d_norm):
    """
    Genera contenido HTML para visualizar figuras 2D y 3D, originales y normalizadas.

    Args:
        figures_2d (dict): Diccionario de figuras 2D originales.
        figures_2d_norm (dict): Diccionario de figuras 2D normalizadas.
        figures_3d (dict): Diccionario de figuras 3D originales.
        figures_3d_norm (dict): Diccionario de figuras 3D normalizadas.

    Returns:
        str: Contenido HTML.
    """
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Plate Analysis Results</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 100%; margin: 0 auto; }
        select { padding: 8px; margin-bottom: 20px; width: 300px; }
        .plot-container { 
            width: 100%; 
            height: 85vh; 
            min-height: 700px; 
        }
        .stacked-container {
            width: 100%;
            display: flex;
            flex-direction: column;
        }
        .plot-wrapper {
            width: 100%;
            height: 700px;
            margin-bottom: 30px;
        }
        .plot-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            text-align: center;
        }
        .export-btn { 
            padding: 8px 16px; 
            background-color: #4CAF50; 
            color: white; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            margin-left: 10px;
        }
        .export-btn:hover { background-color: #45a049; }
        .checkbox-container {
            margin-left: 10px;
            display: inline-block;
        }
        .checkbox-label {
            margin-left: 5px;
            cursor: pointer;
        }
        .tab {
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
            margin-bottom: 10px;
        }
        .tab button {
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
            font-size: 16px;
        }
        .tab button:hover {
            background-color: #ddd;
        }
        .tab button.active {
            background-color: #ccc;
        }
        .tabcontent {
            display: none;
            padding: 6px 12px;
            border: 1px solid #ccc;
            border-top: none;
            overflow-y: auto;
            max-height: calc(100vh - 150px);
        }
        .tabcontent.active {
            display: block;
        }
        .slider-container {
            width: 100%;
            padding: 10px 0;
            position: sticky;
            top: 0;
            background-color: white;
            z-index: 100;
            border-bottom: 1px solid #ddd;
        }
        .slider {
            width: 100%;
            height: 25px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Plate Analysis Results</h1>
        <div style="display: flex; align-items: center;">
            <label for="plot-selector">Select Plate:</label>
            <select id="plot-selector" onchange="showPlot(this.value)">
"""

    # Añadir opciones para cada figura
    for i, key in enumerate(figures_2d.keys()):
        selected = "selected" if i == 0 else ""
        html_content += f'<option value="{key}" {selected}>{key}</option>\n'

    html_content += """
            </select>
            <button class="export-btn" onclick="exportCurrentPlot()">Export as PNG</button>
            <div class="checkbox-container">
                <input type="checkbox" id="log-scale-checkbox" onchange="toggleLogScale()">
                <label for="log-scale-checkbox" class="checkbox-label">Log Scale (Y-axis)</label>
            </div>
        </div>
        
        <!-- Tab links -->
        <div class="tab">
            <button class="tablinks active" onclick="openTab(event, '2D')">2D View</button>
            <button class="tablinks" onclick="openTab(event, '3D')">3D View</button>
        </div>
        
        <!-- Tab content -->
        <div id="2D" class="tabcontent active">
            <div class="slider-container">
                <input type="range" min="0" max="100" value="0" class="slider" id="slider-2d">
                <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                    <span>Original</span>
                    <span>Normalized</span>
                </div>
            </div>
            <div class="stacked-container">
                <div class="plot-wrapper">
                    <div class="plot-title">Original 2D Plot</div>
                    <div id="plot-container-2d" style="width: 100%; height: 100%;"></div>
                </div>
                <div class="plot-wrapper">
                    <div class="plot-title">Normalized 2D Plot</div>
                    <div id="plot-container-2d-norm" style="width: 100%; height: 100%;"></div>
                </div>
            </div>
        </div>
        
        <div id="3D" class="tabcontent">
            <div class="slider-container">
                <input type="range" min="0" max="100" value="0" class="slider" id="slider-3d">
                <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                    <span>Original</span>
                    <span>Normalized</span>
                </div>
            </div>
            <div class="stacked-container">
                <div class="plot-wrapper">
                    <div class="plot-title">Original 3D Plot</div>
                    <div id="plot-container-3d" style="width: 100%; height: 100%;"></div>
                </div>
                <div class="plot-wrapper">
                    <div class="plot-title">Normalized 3D Plot</div>
                    <div id="plot-container-3d-norm" style="width: 100%; height: 100%;"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Store all the figures
        const figures2D = {};
        const figures2DNorm = {};
        const figures3D = {};
        const figures3DNorm = {};
        
        // Track log scale state
        let useLogScale = false;
        
        // Function to handle window resize
        function handleResize() {
            const currentKey = document.getElementById('plot-selector').value;
            showPlot(currentKey);
        }
        
        // Add resize event listener
        window.addEventListener('resize', handleResize);
"""

    # Añadir cada figura 2D original como JSON
    for key, fig in figures_2d.items():
        fig_json = fig.to_json()
        html_content += f'figures2D["{key}"] = {fig_json};\n'

    # Añadir cada figura 2D normalizada como JSON
    for key, fig in figures_2d_norm.items():
        fig_json = fig.to_json()
        html_content += f'figures2DNorm["{key}"] = {fig_json};\n'

    # Añadir cada figura 3D original como JSON
    for key, fig3d in figures_3d.items():
        fig3d_json = fig3d.to_json()
        html_content += f'figures3D["{key}"] = {fig3d_json};\n'

    # Añadir cada figura 3D normalizada como JSON
    for key, fig3d_norm in figures_3d_norm.items():
        fig3d_json = fig3d_norm.to_json()
        html_content += f'figures3DNorm["{key}"] = {fig3d_json};\n'

    html_content += """
        // Function to show the selected plot
        function showPlot(key) {
            // Get active tab
            const activeTab = document.querySelector('.tablinks.active');
            const tabName = activeTab.textContent.trim();
            
            if (tabName === '2D View') {
                // Show 2D plot (original)
                const currentFigure = JSON.parse(JSON.stringify(figures2D[key]));
                
                // Apply log scale if checkbox is checked
                if (useLogScale) {
                    currentFigure.layout.yaxis = currentFigure.layout.yaxis || {};
                    currentFigure.layout.yaxis.type = 'log';
                } else {
                    currentFigure.layout.yaxis = currentFigure.layout.yaxis || {};
                    currentFigure.layout.yaxis.type = 'linear';
                }
                
                // Make sure the layout is responsive
                currentFigure.layout.autosize = true;
                currentFigure.layout.height = 650;
                
                Plotly.react('plot-container-2d', currentFigure.data, currentFigure.layout);
                
                // Show 2D plot (normalized)
                const currentFigureNorm = JSON.parse(JSON.stringify(figures2DNorm[key]));
                
                // Apply log scale if checkbox is checked
                if (useLogScale) {
                    currentFigureNorm.layout.yaxis = currentFigureNorm.layout.yaxis || {};
                    currentFigureNorm.layout.yaxis.type = 'log';
                } else {
                    currentFigureNorm.layout.yaxis = currentFigureNorm.layout.yaxis || {};
                    currentFigureNorm.layout.yaxis.type = 'linear';
                }
                
                // Make sure the layout is responsive
                currentFigureNorm.layout.autosize = true;
                currentFigureNorm.layout.height = 650;
                
                Plotly.react('plot-container-2d-norm', currentFigureNorm.data, currentFigureNorm.layout);
                
                // Update slider visibility based on scroll position
                updateSliderVisibility('2D');
            } else {
                // Show 3D plot (original)
                const currentFigure = JSON.parse(JSON.stringify(figures3D[key]));
                
                // Make sure the layout is responsive
                currentFigure.layout.autosize = true;
                currentFigure.layout.height = 650;
                
                Plotly.react('plot-container-3d', currentFigure.data, currentFigure.layout);
                
                // Show 3D plot (normalized)
                const currentFigureNorm = JSON.parse(JSON.stringify(figures3DNorm[key]));
                
                // Make sure the layout is responsive
                currentFigureNorm.layout.autosize = true;
                currentFigureNorm.layout.height = 650;
                
                Plotly.react('plot-container-3d-norm', currentFigureNorm.data, currentFigureNorm.layout);
                
                // Update slider visibility based on scroll position
                updateSliderVisibility('3D');
            }
        }
        
        // Function to toggle log scale
        function toggleLogScale() {
            useLogScale = document.getElementById('log-scale-checkbox').checked;
            showPlot(document.getElementById('plot-selector').value);
        }
        
        // Function to export the current plot as PNG
        function exportCurrentPlot() {
            const currentKey = document.getElementById('plot-selector').value;
            const activeTab = document.querySelector('.tablinks.active');
            const tabName = activeTab.textContent.trim();
            
            // Create a new window to show combined image
            const w = window.open();
            w.document.write('<html><head><title>Export Plots</title></head><body>');
            w.document.write('<h2>Exporting plots...</h2>');
            w.document.write('<p>Right-click on the images to save them.</p>');
            
            if (tabName === '2D View') {
                // Export both 2D plots
                Plotly.toImage('plot-container-2d', {
                    format: 'png',
                    width: 1200,
                    height: 800
                }).then(function(dataUrl) {
                    w.document.write('<h3>Original 2D Plot</h3>');
                    w.document.write('<img src="' + dataUrl + '" alt="Original 2D Plot"/>');
                });
                
                Plotly.toImage('plot-container-2d-norm', {
                    format: 'png',
                    width: 1200,
                    height: 800
                }).then(function(dataUrl) {
                    w.document.write('<h3>Normalized 2D Plot</h3>');
                    w.document.write('<img src="' + dataUrl + '" alt="Normalized 2D Plot"/>');
                    w.document.write('</body></html>');
                });
            } else {
                // Export both 3D plots
                Plotly.toImage('plot-container-3d', {
                    format: 'png',
                    width: 1200,
                    height: 800
                }).then(function(dataUrl) {
                    w.document.write('<h3>Original 3D Plot</h3>');
                    w.document.write('<img src="' + dataUrl + '" alt="Original 3D Plot"/>');
                });
                
                Plotly.toImage('plot-container-3d-norm', {
                    format: 'png',
                    width: 1200,
                    height: 800
                }).then(function(dataUrl) {
                    w.document.write('<h3>Normalized 3D Plot</h3>');
                    w.document.write('<img src="' + dataUrl + '" alt="Normalized 3D Plot"/>');
                    w.document.write('</body></html>');
                });
            }
        }
        
        // Function to open tab
        function openTab(evt, tabName) {
            // Declare all variables
            var i, tabcontent, tablinks;
            
            // Get all elements with class="tabcontent" and hide them
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].className = tabcontent[i].className.replace(" active", "");
            }
            
            // Get all elements with class="tablinks" and remove the class "active"
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            
            // Show the current tab, and add an "active" class to the button that opened the tab
            document.getElementById(tabName).className += " active";
            evt.currentTarget.className += " active";
            
            // Update the plot
            showPlot(document.getElementById('plot-selector').value);
        }
        
        // Function to update slider visibility based on scroll position
        function updateSliderVisibility(tabName) {
            const tabContent = document.getElementById(tabName);
            const slider = document.querySelector(`#${tabName} .slider-container`);
            
            tabContent.addEventListener('scroll', function() {
                if (tabContent.scrollTop > 10) {
                    slider.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
                } else {
                    slider.style.boxShadow = 'none';
                }
            });
        }
        
        // Setup sliders to control scroll position
        document.getElementById('slider-2d').addEventListener('input', function(e) {
            const container = document.getElementById('2D');
            const maxScroll = container.scrollHeight - container.clientHeight;
            container.scrollTop = (e.target.value / 100) * maxScroll;
        });
        
        document.getElementById('slider-3d').addEventListener('input', function(e) {
            const container = document.getElementById('3D');
            const maxScroll = container.scrollHeight - container.clientHeight;
            container.scrollTop = (e.target.value / 100) * maxScroll;
        });
        
        // Show the first plot by default
        showPlot(document.getElementById('plot-selector').value);
    </script>
</body>
</html>
"""

    return html_content
