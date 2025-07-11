"""
Módulo para la visualización de la cuadrícula de placas.
"""
import customtkinter as ctk

class PlateGridView:
    """Class to display the well grid of a plate."""
    
    def __init__(self, parent, plate, assay, mask, neg_ctrl_mask, sections, section_colors, 
                toggle_well_callback, toggle_negative_control_callback, advanced_mode=False, 
                current_individual_plate=None):
        """
        Initialize the grid view.
        
        Args:
            parent: Parent widget where the grid will be displayed.
            plate (str): Plate number.
            assay (str): Assay type.
            mask (numpy.ndarray): Well mask (8x12).
            neg_ctrl_mask (numpy.ndarray): Negative control mask (8x12).
            sections (list): List of tuples with the limits of each section.
            section_colors (list): List of colors for each section.
            toggle_well_callback (callable): Function to toggle the state of a well.
            toggle_negative_control_callback (callable): Function to toggle the state of a negative control.
            advanced_mode (bool, optional): Whether it is in advanced mode. Defaults to False.
            current_individual_plate (pandas.Series, optional): Data of the selected individual plate.
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
        """Create the well grid."""
        # If in advanced mode and an individual plate is selected, use that data
        if self.advanced_mode and self.current_individual_plate is not None:
            # Show the individual plate
            hours = self.current_individual_plate['hours']
            plate_label = ctk.CTkLabel(self.parent, 
                                      text=f"Viewing: {self.plate}_{self.assay} at {hours} hours",
                                      font=("Arial", 14, "bold"))
            plate_label.grid(row=0, column=0, columnspan=13, pady=(0, 10))
            
            # Set initial row for the grid
            start_row = 1
        else:
            # Regular mode - just show the plate-assay
            plate_label = ctk.CTkLabel(self.parent, 
                                      text=f"Viewing: {self.plate}_{self.assay}",
                                      font=("Arial", 14, "bold"))
            plate_label.grid(row=0, column=0, columnspan=13, pady=(0, 10))
            start_row = 1

        # Add column headers (1-12)
        for j in range(12):
            col_label = ctk.CTkLabel(self.parent, text=f"{j+1}")
            col_label.grid(row=start_row, column=j+1, padx=2, pady=2)
            
        # Create section frames first
        section_frames = []
        for i, (r1, c1, r2, c2) in enumerate(self.sections):
            # Create a frame for this section with a colored border
            section_frame = ctk.CTkFrame(self.parent, fg_color="transparent", 
                                        border_color=self.section_colors[i], border_width=2)
            # Position the frame to cover the wells in this section
            section_frame.grid(row=r1+start_row+1, column=c1+1, rowspan=r2-r1+1, 
                              columnspan=c2-c1+1, padx=2, pady=2, sticky="nsew")
            
            # Add a label for the section
            section_label = ctk.CTkLabel(section_frame, text=f"S{i+1}", 
                                        fg_color=self.section_colors[i],
                                        text_color="black", corner_radius=5)
            section_label.place(x=5, y=5)
            
            section_frames.append(section_frame)
        
        # Add row headers (A-H) and buttons
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
