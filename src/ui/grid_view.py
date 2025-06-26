"""
Módulo para la visualización de la cuadrícula de placas.
"""
import customtkinter as ctk

class PlateGridView:
    """Clase para mostrar la cuadrícula de pocillos de una placa."""
    
    def __init__(self, parent, plate, assay, mask, neg_ctrl_mask, sections, section_colors, 
                toggle_well_callback, toggle_negative_control_callback, advanced_mode=False, 
                current_individual_plate=None):
        """
        Inicializa la vista de cuadrícula.
        
        Args:
            parent: Widget padre donde se mostrará la cuadrícula.
            plate (str): Número de placa.
            assay (str): Tipo de ensayo.
            mask (numpy.ndarray): Máscara de pocillos (8x12).
            neg_ctrl_mask (numpy.ndarray): Máscara de controles negativos (8x12).
            sections (list): Lista de tuplas con los límites de cada sección.
            section_colors (list): Lista de colores para cada sección.
            toggle_well_callback (callable): Función para alternar el estado de un pocillo.
            toggle_negative_control_callback (callable): Función para alternar el estado de control negativo.
            advanced_mode (bool, optional): Si está en modo avanzado. Por defecto False.
            current_individual_plate (pandas.Series, optional): Datos de la placa individual seleccionada.
        """
        self.parent = parent
        self.plate = plate
        self.assay = assay
        self.mask = mask
        self.neg_ctrl_mask = neg_ctrl_mask
        self.sections = sections
        self.section_colors = section_colors
        self.toggle_well_callback = toggle_well_callback
        self.toggle_negative_control_callback = toggle_negative_control_callback
        self.advanced_mode = advanced_mode
        self.current_individual_plate = current_individual_plate
        
        self.buttons = []
        self.all_buttons = {}
        
        self._create_grid()
    
    def _create_grid(self):
        """Crea la cuadrícula de pocillos."""
        # Si en modo avanzado y una placa individual está seleccionada, usar esos datos
        if self.advanced_mode and self.current_individual_plate is not None:
            # Mostrar la placa individual
            hours = self.current_individual_plate['hours']
            plate_label = ctk.CTkLabel(self.parent, 
                                      text=f"Viewing: {self.plate}_{self.assay} at {hours} hours",
                                      font=("Arial", 14, "bold"))
            plate_label.grid(row=0, column=0, columnspan=13, pady=(0, 10))
            
            # Ajustar fila inicial para la cuadrícula
            start_row = 1
        else:
            # Modo regular - solo mostrar la placa-ensayo
            plate_label = ctk.CTkLabel(self.parent, 
                                      text=f"Viewing: {self.plate}_{self.assay}",
                                      font=("Arial", 14, "bold"))
            plate_label.grid(row=0, column=0, columnspan=13, pady=(0, 10))
            start_row = 1

        # Añadir encabezados de columna (1-12)
        for j in range(12):
            col_label = ctk.CTkLabel(self.parent, text=f"{j+1}")
            col_label.grid(row=start_row, column=j+1, padx=2, pady=2)
            
        # Crear frames de sección primero
        section_frames = []
        for i, (r1, c1, r2, c2) in enumerate(self.sections):
            # Crear un frame para esta sección con un borde coloreado
            section_frame = ctk.CTkFrame(self.parent, fg_color="transparent", 
                                        border_color=self.section_colors[i], border_width=2)
            # Posicionar el frame para cubrir los pocillos en esta sección
            section_frame.grid(row=r1+start_row+1, column=c1+1, rowspan=r2-r1+1, 
                              columnspan=c2-c1+1, padx=2, pady=2, sticky="nsew")
            
            # Añadir una etiqueta para la sección
            section_label = ctk.CTkLabel(section_frame, text=f"S{i+1}", 
                                        fg_color=self.section_colors[i],
                                        text_color="black", corner_radius=5)
            section_label.place(x=5, y=5)
            
            section_frames.append(section_frame)
        
        # Añadir encabezados de fila (A-H) y botones
        for i in range(8):  # filas A-H
            row_btns = []
            # Encabezado de fila
            row_label = ctk.CTkLabel(self.parent, text=f"{chr(ord('A')+i)}")
            row_label.grid(row=i+start_row+1, column=0, padx=(0, 5), sticky="e")
            
            for j in range(12):  # columnas 1-12
                # Crear etiqueta de pocillo (1A, 2A, etc.)
                well_label = f"{j+1}{chr(ord('A')+i)}"
                
                # Determinar a qué sección pertenece este pocillo
                section_idx = -1
                for idx, (r1, c1, r2, c2) in enumerate(self.sections):
                    if r1 <= i <= r2 and c1 <= j <= c2:
                        section_idx = idx
                        break
                
                # Determinar color del botón basado en máscara y estado de control negativo
                if self.neg_ctrl_mask[i,j] == 1 and self.mask[i,j] == 0:
                    # Ambos control negativo y excluido - púrpura con borde rojo
                    btn = ctk.CTkButton(
                        self.parent,
                        text=well_label,
                        width=40,
                        height=30,
                        fg_color='#800080',  # Púrpura para control negativo
                        border_color='#ff0000',
                        border_width=2,
                        command=lambda x=i, y=j: self.toggle_well_callback(x, y)
                    )
                elif self.neg_ctrl_mask[i,j] == 1:
                    # Control negativo - púrpura
                    btn = ctk.CTkButton(
                        self.parent,
                        text=well_label,
                        width=40,
                        height=30,
                        fg_color='#800080',  # Púrpura para control negativo
                        command=lambda x=i, y=j: self.toggle_well_callback(x, y)
                    )
                elif self.mask[i,j] == 0:
                    # Pocillo excluido - rojo
                    btn = ctk.CTkButton(
                        self.parent,
                        text=well_label,
                        width=40,
                        height=30,
                        fg_color='#ff0000',
                        command=lambda x=i, y=j: self.toggle_well_callback(x, y)
                    )
                else:
                    # Pocillo normal - por defecto
                    btn = ctk.CTkButton(
                        self.parent,
                        text=well_label,
                        width=40,
                        height=30,
                        fg_color='transparent',
                        command=lambda x=i, y=j: self.toggle_well_callback(x, y)
                    )
                btn.grid(row=i+start_row+1, column=j+1, padx=2, pady=2)
                
                # Vincular clic derecho para marcar como control negativo
                btn.bind("<Button-3>", lambda event, x=i, y=j: self.toggle_negative_control_callback(x, y))
                
                row_btns.append(btn)
            self.buttons.append(row_btns)
        
        # Almacenar referencias a todos los botones para acceso rápido
        for i in range(8):
            for j in range(12):
                self.all_buttons[(i, j)] = self.buttons[i][j]
