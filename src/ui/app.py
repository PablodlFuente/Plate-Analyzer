"""
Módulo principal de la interfaz de usuario para la aplicación de análisis de placas.
"""
import os
import customtkinter as ctk
import webbrowser
import pandas as pd
import numpy as np
from src.models import PlateData
from src.ui.grid_view import PlateGridView
import importlib
from src.ui.legend import SectionLegend, WellStatusLegend
from src.analysis import analyze_plate, analyze_all_plates
from utils import save_masks_to_csv, load_masks_from_csv, save_neg_ctrl_masks_to_csv, load_neg_ctrl_masks_from_csv
from utils import save_grays_to_csv, load_grays_from_csv
from src.config import Config
from src.ui.menu import AppMenu
import tkinter as tk

class PlateMaskApp(ctk.CTk):
    """Clase principal de la aplicación de análisis de placas."""
    
    def __init__(self, df):
        """
        Inicializa la aplicación.
        
        Args:
            df (pandas.DataFrame, optional): DataFrame con los datos de las placas. Puede ser None.
        """
        super().__init__()
        self.title("Plate Masking Interface")
        self.geometry("1170x800")  # Aumentado en un 30%
        ctk.set_appearance_mode("system")

        # Initialize configuration
        self.config = Config()
        self.config.load()
        
        # Initialize empty data structures
        self.df = df
        self.plate_data = None
        self.keys = []
        self.mask_map = {}
        self.neg_ctrl_mask_map = {}
        self.section_grays = {}
        self.sections = []
        self.grid_sections = []
        self.buttons = []
        self.all_buttons = []
        self.section_colors = ['#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF', '#99FFFF']
        
        # Archivos para guardar/cargar datos
        self.mask_file = "last_masks.csv"
        self.neg_ctrl_mask_file = "last_neg_ctrl_masks.csv"
        self.gray_file = "section_grays.csv"
        
        # Initialize data if provided
        if df is not None:
            self._initialize_data(df)
        
        # Configurar la interfaz
        self._setup_ui()
        
        # Selección inicial
        self.selected_key = self.keys[0] if self.keys else None
        self.selected_hour_index = 0
        
        # Build grid if data is available
        if self.df is not None:
            self.build_grid()
        else:
            # Show welcome message if no data
            self._show_welcome_message()
        
        # Vincular eventos
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Configure>", self.on_resize)

    def _on_config_changed(self):
        """Handle configuration changes."""
        # Rebuild the grid to reflect any configuration changes
        if hasattr(self, 'grid_frame'):
            self.build_grid()
    
    def _edit_sections(self):
        """Open the section editor dialog."""
        self.menu.show_section_editor()
        
        # After editing sections, update the orphaned wells if auto-exclude is enabled
        if hasattr(self.config, 'auto_exclude_orphaned') and self.config.auto_exclude_orphaned:
            self._exclude_orphaned_wells()
            self.build_grid()  # Rebuild grid to show updated excluded wells
    
    def _initialize_data(self, df):
        """Initialize data structures with the provided DataFrame."""
        try:
            self.df = df
            self.plate_data = PlateData(df)
            
            # Ensure keys are valid strings
            self.keys = [str(k) for k in getattr(self.plate_data, 'keys', []) if k is not None]
            
            # Initialize section wells
            self.sections = []
            self.section_names = []
            self.section_wells = []
            
            # Load sections from config or use defaults
            if hasattr(self.config, 'sections') and self.config.sections:
                for s in self.config.sections:
                    try:
                        name = str(s.get('name', f'Section {len(self.sections) + 1}'))
                        wells = s.get('wells', [])
                        # Ensure wells is a list of tuples
                        if isinstance(wells, (list, tuple)):
                            valid_wells = []
                            for well in wells:
                                if isinstance(well, (list, tuple)) and len(well) >= 2:
                                    valid_wells.append((int(well[0]), int(well[1])))
                            
                            if valid_wells:  # Only add if we have valid wells
                                self.sections.append((name, valid_wells))
                                self.section_names.append(name)
                                self.section_wells.append(valid_wells)
                    except Exception as e:
                        print(f"Error processing section {s}: {e}")
                        continue
            
            # If no valid sections were loaded, use defaults
            if not self.sections:
                try:
                    default_limits = [
                        (0, 0, 3, 3), (0, 4, 3, 7), (0, 8, 3, 11),
                        (4, 0, 7, 3), (4, 4, 7, 7), (4, 8, 7, 11)
                    ]
                    default_names = [f"Section {i+1}" for i in range(6)]
                    
                    for i, (name, limits) in enumerate(zip(default_names, default_limits)):
                        try:
                            # Ensure limits is a 4-tuple of integers
                            if not isinstance(limits, (tuple, list)) or len(limits) != 4:
                                print(f"Invalid limits format for section {name}: {limits}")
                                continue
                                
                            r1, c1, r2, c2 = map(int, limits)
                            
                            # Generate well coordinates
                            wells = []
                            for row in range(min(r1, r2), max(r1, r2) + 1):
                                for col in range(min(c1, c2), max(c1, c2) + 1):
                                    wells.append((row, col))
                            
                            if wells:  # Only add if we have valid wells
                                self.sections.append((str(name), wells))
                                self.section_names.append(str(name))
                                self.section_wells.append(wells)
                                
                        except (ValueError, TypeError) as e:
                            print(f"Error creating default section {name} with limits {limits}: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Error initializing default sections: {e}")
                    import traceback
                    print(traceback.format_exc())
                    
                    # If we still don't have sections, create a single section with all wells
                    if not self.sections:
                        all_wells = [(i, j) for i in range(8) for j in range(12)]
                        self.sections = [("All Wells", all_wells)]
                        self.section_names = ["All Wells"]
                        self.section_wells = [all_wells]
            
            # Set section colors
            self.section_colors = getattr(self.plate_data, 'section_colors', 
                                       ['#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF', '#99FFFF'])
            
            # Initialize mask maps
            if not hasattr(self, 'mask_map'):
                self.mask_map = {}
            if not hasattr(self, 'neg_ctrl_mask_map'):
                self.neg_ctrl_mask_map = {}
            if not hasattr(self, 'section_grays'):
                self.section_grays = {}
            
            # Ensure default masks and gray values for all plate-assay keys
            for key in self.keys:
                self.mask_map.setdefault(key, np.ones((8, 12), dtype=float))
                self.neg_ctrl_mask_map.setdefault(key, np.zeros((8, 12), dtype=float))
                self.section_grays.setdefault(key, [0] * len(self.section_wells))
            
            # Handle orphaned wells if auto-exclude is enabled
            if hasattr(self.config, 'auto_exclude_orphaned') and self.config.auto_exclude_orphaned:
                self._exclude_orphaned_wells()
                
        except Exception as e:
            print(f"Error in _initialize_data: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise  # Re-raise the exception to be handled by the caller
    
    def _exclude_orphaned_wells(self):
        """Exclude wells that don't belong to any section."""
        try:
            # Ensure we have the required attributes
            if not hasattr(self, 'mask_map'):
                self.mask_map = {}
                
            if not hasattr(self, 'keys') or not self.keys:
                print("No plate keys found for excluding orphaned wells")
                return
                
            if not hasattr(self, 'section_wells') or not self.section_wells:
                print("No section wells defined for excluding orphaned wells")
                return
            
            # Create a set of all possible well coordinates (0-7 rows, 0-11 cols)
            all_wells = set((i, j) for i in range(8) for j in range(12))
            section_wells = set()
            
            # Get all wells that are in sections
            for well_list in self.section_wells:
                if not isinstance(well_list, (list, tuple)):
                    continue
                    
                for well in well_list:
                    try:
                        if isinstance(well, (list, tuple)) and len(well) >= 2:
                            # Convert to tuple of integers to make it hashable
                            row = int(well[0]) if hasattr(well, '__getitem__') else 0
                            col = int(well[1]) if hasattr(well, '__getitem__') and len(well) > 1 else 0
                            if 0 <= row < 8 and 0 <= col < 12:  # Validate coordinates
                                section_wells.add((row, col))
                    except (ValueError, TypeError, IndexError) as e:
                        print(f"Error processing well {well}: {e}")
                        continue
            
            # Find orphaned wells (not in any section)
            orphaned_wells = all_wells - section_wells
            
            if not orphaned_wells:
                print("No orphaned wells to exclude")
                return
                
            print(f"Found {len(orphaned_wells)} orphaned wells to exclude")
            
            # Exclude orphaned wells in all plates
            for key in list(self.keys):  # Create a copy of keys to avoid modification during iteration
                try:
                    if not isinstance(key, str):
                        print(f"Skipping invalid key (not a string): {key}")
                        continue
                        
                    if key not in self.mask_map:
                        self.mask_map[key] = np.ones((8, 12), dtype=float)
                    
                    mask = self.mask_map[key]
                    if not isinstance(mask, np.ndarray) or mask.shape != (8, 12):
                        print(f"Invalid mask for {key}, resetting to default")
                        self.mask_map[key] = np.ones((8, 12), dtype=float)
                        mask = self.mask_map[key]
                    
                    # Mark orphaned wells as excluded (0)
                    for i, j in orphaned_wells:
                        if 0 <= i < 8 and 0 <= j < 12:  # Double-check bounds
                            mask[i, j] = 0
                            
                except Exception as e:
                    print(f"Error processing plate {key}: {e}")
                    continue
                        
        except Exception as e:
            print(f"Error in _exclude_orphaned_wells: {str(e)}")
            import traceback
            print(traceback.format_exc())

        # Initialize masks and grays from config if available
        for key in self.keys:
            # Initialize mask map
            if key in self.config.masks:
                self.mask_map[key] = self.config.masks[key].copy()
            else:
                self.mask_map[key] = np.ones((8, 12), dtype=float)
            
            # Initialize negative control mask
            if key in self.config.neg_ctrl_masks:
                self.neg_ctrl_mask_map[key] = self.config.neg_ctrl_masks[key].copy()
            else:
                self.neg_ctrl_mask_map[key] = np.zeros((8, 12), dtype=float)
            
            # Initialize section grays
            if key in self.config.section_grays:
                self.section_grays[key] = self.config.section_grays[key].copy()
            else:
                # Default to 6 sections if not specified
                self.section_grays[key] = [0] * 6
            
            # Handle orphaned wells if auto-exclude is enabled
            if hasattr(self.config, 'auto_exclude_orphaned') and self.config.auto_exclude_orphaned:
                # Get all wells that are in sections
                section_wells = set()
                for wells in self.section_wells:
                    section_wells.update(wells)
                
                # Find orphaned wells (not in any section)
                all_wells = set((i, j) for i in range(8) for j in range(12))
                orphaned_wells = all_wells - section_wells
                
                # Exclude orphaned wells
                for i, j in orphaned_wells:
                    self.mask_map[key][i, j] = 0

    def _show_welcome_message(self):
        """Show welcome message when no data is loaded."""
        # Clear any existing content
        for w in self.grid_frame.winfo_children():
            w.destroy()
            
        for w in self.legend_frame.winfo_children():
            w.destroy()
        
        # Create welcome message
        welcome_frame = ctk.CTkFrame(self.grid_frame)
        welcome_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        welcome_label = ctk.CTkLabel(
            welcome_frame, 
            text="Welcome to Plate Analyzer",
            font=("Arial", 24, "bold")
        )
        welcome_label.pack(pady=(50, 20))
        
        instructions_label = ctk.CTkLabel(
            welcome_frame,
            text="Please use the File menu to load a data file.",
            font=("Arial", 16)
        )
        instructions_label.pack(pady=10)
        
        # Add a button to open file dialog
        load_button = ctk.CTkButton(
            welcome_frame,
            text="Load Data File",
            command=lambda: self.menu.load_file()
        )
        load_button.pack(pady=20)
        
        # Add section editor button
        section_btn = ctk.CTkButton(
            welcome_frame,
            text="Edit Sections",
            command=self.menu.show_section_editor,
            width=120
        )
        section_btn.pack(side=ctk.LEFT, padx=5, pady=5)
        
        # Add configuration button
        config_btn = ctk.CTkButton(
            welcome_frame,
            text="Configuration",
            command=self.menu.show_configuration,
            width=120
        )
        config_btn.pack(side=ctk.LEFT, padx=5, pady=5)
        
        # Show recent files if available
        if self.config.recent_files:
            recent_label = ctk.CTkLabel(
                welcome_frame,
                text="Recent Files:",
                font=("Arial", 16, "bold")
            )
            recent_label.pack(pady=(30, 10))
            
            recent_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
            recent_frame.pack(pady=10)
            
            for i, file_path in enumerate(self.config.recent_files[:5]):
                file_name = os.path.basename(file_path)
                recent_button = ctk.CTkButton(
                    recent_frame,
                    text=file_name,
                    command=lambda path=file_path: self.menu.load_specific_file(path)
                )
                recent_button.pack(pady=5)

    def _setup_ui(self):
        """Configura los elementos de la interfaz de usuario."""
        # Frame superior para controles
        self._setup_top_frame()
        
        # Initialize the menu
        self.menu = AppMenu(self, self.config, self.load_file)
        self.menu.on_config_changed = self._on_config_changed
        
        # Frame para modo avanzado
        self.advanced_mode = False
        self.advanced_frame = None
        
        # Frame principal de contenido
        self._setup_content_frame()
        
        # Frame para botones de control
        self._setup_button_frame()
        
        # Frame para opciones
        self._setup_options_frame()
        
        # Cuadro de texto para resultados
        self.result_box = ctk.CTkTextbox(self, width=800, height=200)
        self.result_box.pack(pady=10, fill="x", padx=10)
        
        # Frame de instrucciones
        self._setup_instructions_frame()

    def _setup_top_frame(self):
        """Configura el frame superior con controles de selección."""
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(pady=10, fill="x", padx=10)
        
        # Etiqueta para el dropdown
        self.combo_label = ctk.CTkLabel(self.top_frame, text="Select Plate-Assay:")
        self.combo_label.pack(side="left", padx=(0, 10))
        
        # Dropdown para seleccionar placa-ensayo
        self.combo = ctk.CTkComboBox(self.top_frame, values=self.keys, command=self.on_select, width=200)
        self.combo.pack(side="left", padx=10)
        
        # Botón de modo avanzado
        self.advanced_btn = ctk.CTkButton(self.top_frame, text="Advanced Mode", command=self.toggle_advanced_mode)
        self.advanced_btn.pack(side="right", padx=10)

    def _setup_content_frame(self):
        """Configura el frame principal de contenido."""
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(pady=10, fill="both", expand=True)
        
        # Contenedor para la cuadrícula con scrollbars
        self.grid_container = ctk.CTkFrame(self.content_frame)
        self.grid_container.pack(side="left", fill="both", expand=True)
        
        # Canvas con scrollbars para la cuadrícula
        self.grid_canvas = tk.Canvas(self.grid_container, highlightthickness=0)
        self.grid_scroll_y = ctk.CTkScrollbar(self.grid_container, orientation="vertical", command=self.grid_canvas.yview)
        self.grid_scroll_x = ctk.CTkScrollbar(self.grid_container, orientation="horizontal", command=self.grid_canvas.xview)
        self.grid_canvas.configure(yscrollcommand=self.grid_scroll_y.set, xscrollcommand=self.grid_scroll_x.set)
        
        # Posicionar elementos
        self.grid_canvas.grid(row=0, column=0, sticky="nsew")
        self.grid_scroll_y.grid(row=0, column=1, sticky="ns")
        self.grid_scroll_x.grid(row=1, column=0, sticky="ew")
        
        # Configurar el grid para que el canvas se expanda
        self.grid_container.grid_rowconfigure(0, weight=1)
        self.grid_container.grid_columnconfigure(0, weight=1)
        
        # Frame para la cuadrícula de pocillos dentro del canvas
        self.grid_frame = ctk.CTkFrame(self.grid_canvas)
        self.grid_window = self.grid_canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        
        # Configurar eventos
        self.grid_frame.bind("<Configure>", self._on_grid_configure)
        self.grid_canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Frame para la leyenda de secciones (lado derecho)
        self.legend_frame = ctk.CTkFrame(self.content_frame)
        self.legend_frame.pack(side="right", pady=10, padx=10, fill="y")

    def _on_grid_configure(self, event=None):
        # Ajustar el scrollregion del canvas cuando cambia el tamaño del frame
        self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        # Ajustar el tamaño del frame al canvas
        if event:
            canvas_width = max(event.width, self.grid_frame.winfo_reqwidth())
            self.grid_canvas.itemconfig(self.grid_window, width=canvas_width)
            # Asegurarse de que el canvas se actualiza
            self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all"))


    def _setup_button_frame(self):
        """Configura el frame de botones de control."""
        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.pack(pady=10, fill="x", padx=10)
        
        # Botones de control
        self.start_btn = ctk.CTkButton(self.btn_frame, text="Start Analysis", command=self.analyze_all)
        self.start_btn.pack(side="left", padx=5)
        
        self.copy_ab_btn = ctk.CTkButton(self.btn_frame, text="Copiar selección a todas las placas AB", 
                                        command=lambda: self.copy_to_assay('AB'))
        self.copy_ab_btn.pack(side="left", padx=5)
        
        self.copy_ros_btn = ctk.CTkButton(self.btn_frame, text="Copiar selección a todas las placas ROS", 
                                         command=lambda: self.copy_to_assay('ROS'))
        self.copy_ros_btn.pack(side="left", padx=5)
        
        # Botón para copiar a la misma placa
        self.copy_same_plate_btn = ctk.CTkButton(self.btn_frame, text="Copy to Same Plate", command=self.copy_to_same_plate)
        self.copy_same_plate_btn.pack(side="left", padx=5)
        
        self.analyze_all_btn = ctk.CTkButton(self.btn_frame, text="Analyze this plate", command=self.analyze_this_plate)
        self.analyze_all_btn.pack(side="left", padx=5)
        
        # Botón para editar secciones
        self.section_btn = ctk.CTkButton(
            self.btn_frame, 
            text="Edit Sections",
            command=self._edit_sections,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        self.section_btn.pack(side="left", padx=5)
        
        # Botón de configuración
        self.config_btn = ctk.CTkButton(
            self.btn_frame,
            text="Configuration",
            command=self.menu.show_configuration,
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.config_btn.pack(side="left", padx=5)
        
        # Disable buttons if no data is loaded
        if self.df is None:
            self._set_buttons_state(tk.DISABLED)

    def _set_buttons_state(self, state):
        """Set the state of all control buttons."""
        self.start_btn.configure(state=state)
        self.copy_ab_btn.configure(state=state)
        self.copy_ros_btn.configure(state=state)
        self.copy_same_plate_btn.configure(state=state)
        self.analyze_all_btn.configure(state=state)
        
        # Enable/disable section and config buttons based on data availability
        data_loaded = state != tk.DISABLED
        self.section_btn.configure(state=state)
        self.config_btn.configure(state=tk.NORMAL)  # Always enable config button

    def _setup_options_frame(self):
        """Configura el frame de opciones con checkboxes."""
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(pady=5, fill="x", padx=10)
        
        # Checkbox para porcentaje
        self.percent_var = ctk.BooleanVar(value=True)  # Por defecto seleccionado
        self.percent_check = ctk.CTkCheckBox(self.options_frame, text="%", variable=self.percent_var, 
                                            onvalue=True, offvalue=False)
        self.percent_check.pack(side="left", padx=10)
        
        # Checkbox para barras de error
        self.error_bars_var = ctk.BooleanVar(value=True)  # Por defecto seleccionado
        self.error_bars_check = ctk.CTkCheckBox(self.options_frame, text="Error Bars", variable=self.error_bars_var, 
                                               onvalue=True, offvalue=False)
        self.error_bars_check.pack(side="left", padx=10)
        
        # Checkbox para gráfico de barras
        self.bar_chart_var = ctk.BooleanVar(value=False)
        self.bar_chart_check = ctk.CTkCheckBox(self.options_frame, text="Bar Chart", variable=self.bar_chart_var, 
                                              onvalue=True, offvalue=False)
        self.bar_chart_check.pack(side="left", padx=10)
        
        # Checkbox para restar controles negativos
        self.subtract_neg_ctrl_var = ctk.BooleanVar(value=True)  # Por defecto seleccionado
        self.subtract_neg_ctrl_check = ctk.CTkCheckBox(self.options_frame, text="Subtract Neg. Controls", 
                                                      variable=self.subtract_neg_ctrl_var, 
                                                      onvalue=True, offvalue=False)
        self.subtract_neg_ctrl_check.pack(side="left", padx=10)

    def _setup_instructions_frame(self):
        """Configura el frame de instrucciones."""
        self.instructions_frame = ctk.CTkFrame(self)
        self.instructions_frame.pack(pady=5, fill="x", padx=10)
        
        instructions_text = "Instructions: Left-click to toggle well selection. Right-click to mark as negative control (purple)."
        self.instructions_label = ctk.CTkLabel(self.instructions_frame, text=instructions_text)
        self.instructions_label.pack(pady=5)

    def on_resize(self, event):
        """Maneja el evento de redimensionamiento de la ventana."""
        # Solo responder a eventos de redimensionamiento de la ventana principal, no de widgets hijos
        if event.widget == self:
            # Actualizar el layout si es necesario
            pass

    def toggle_advanced_mode(self):
        """Alterna entre modo simple y avanzado."""
        # Don't allow advanced mode if no data is loaded
        if self.df is None:
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, "Please load a data file first.")
            return
            
        self.advanced_mode = not self.advanced_mode
        
        # Actualizar texto del botón
        self.advanced_btn.configure(text="Simple Mode" if self.advanced_mode else "Advanced Mode")
        
        # Crear o destruir frame avanzado
        if self.advanced_mode:
            # Crear frame avanzado si no existe
            if not self.advanced_frame:
                self.advanced_frame = ctk.CTkFrame(self)
                self.advanced_frame.pack(before=self.content_frame, pady=10, fill="x", padx=10)
                
                # Crear selección de placa individual
                plate_label = ctk.CTkLabel(self.advanced_frame, text="Individual Plate:")
                plate_label.pack(side="left", padx=(0, 5))
                
                # Obtener lista de todas las placas individuales
                all_plates = self.plate_data.get_all_individual_plates()
                
                # Dropdown para selección de placa individual
                self.plate_combo = ctk.CTkComboBox(self.advanced_frame, values=all_plates, width=300)
                self.plate_combo.pack(side="left", padx=5)
                
                # Botón para cargar placa individual
                load_btn = ctk.CTkButton(self.advanced_frame, text="Load Plate", command=self.load_individual_plate)
                load_btn.pack(side="left", padx=5)
            else:
                self.advanced_frame.pack(before=self.content_frame, pady=10, fill="x", padx=10)
        else:
            # Ocultar frame avanzado
            if self.advanced_frame:
                self.advanced_frame.pack_forget()
        
        # Refrescar la cuadrícula
        self.build_grid()

    def load_individual_plate(self):
        """Carga una placa individual basada en la selección."""
        if not self.advanced_mode or not hasattr(self, 'plate_combo'):
            return
            
        selected = self.plate_combo.get()
        if not selected:
            return
            
        # Analizar la selección
        parts = selected.split('_')
        if len(parts) < 3:
            return
            
        plate_no = parts[0]
        assay = parts[1]
        hours = float(parts[2])
        
        # Encontrar la fila correspondiente en el DataFrame
        matching_rows = self.df[(self.df['plate_no'] == plate_no) & 
                               (self.df['assay'] == assay) & 
                               (self.df['hours'] == hours)]
        
        if matching_rows.empty:
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, "No matching plate found.")
            return
            
        # Establecer la clave seleccionada a la placa-ensayo
        self.selected_key = f"{plate_no}_{assay}"
        self.combo.set(self.selected_key)
        
        # Almacenar los datos de la placa individual
        self.current_individual_plate = matching_rows.iloc[0]
        
        # Actualizar la cuadrícula
        self.build_grid()
        
        # Mostrar información en el cuadro de resultados
        self.result_box.delete('1.0', ctk.END)
        self.result_box.insert(ctk.END, f"Loaded individual plate: {selected}\n")
        self.result_box.insert(ctk.END, f"Hours: {hours}\n")

    def on_select(self, choice):
        """Maneja la selección de una placa-ensayo diferente."""
        self.selected_key = choice
        self.selected_hour_index = 0
        # Limpiar selección de placa individual en modo avanzado
        if hasattr(self, 'current_individual_plate'):
            delattr(self, 'current_individual_plate')
        self.build_grid()

    def build_grid(self):
        """Construye la cuadrícula de pocillos y la leyenda."""
        # If no data is loaded, show welcome message
        if self.df is None:
            self._show_welcome_message()
            return
            
        # Limpiar frame de cuadrícula
        for w in self.grid_frame.winfo_children():
            w.destroy()
            
        # Limpiar frame de leyenda
        for w in self.legend_frame.winfo_children():
            w.destroy()

        if not self.selected_key:
            return
            
        plate, assay = self.selected_key.split("_")
        
        # Get all wells that are in sections
        section_wells_set = set()
        for wells in self.section_wells:
            section_wells_set.update(wells)
        
        # Find orphaned wells (not in any section)
        all_wells = set((i, j) for i in range(8) for j in range(12))
        orphaned_wells = all_wells - section_wells_set
        
        # If auto-exclude is enabled, update the mask for orphaned wells
        if hasattr(self.config, 'auto_exclude_orphaned') and self.config.auto_exclude_orphaned and orphaned_wells:
            if self.selected_key not in self.mask_map:
                self.mask_map[self.selected_key] = np.ones((8, 12), dtype=float)
            
            for i, j in orphaned_wells:
                self.mask_map[self.selected_key][i, j] = 0
        
        # Adaptar secciones a formato esperado por PlateGridView (bounding boxes)
        self.grid_sections = []
        for idx, wells in enumerate(self.section_wells):
            if wells:
                rows = [i for i, j in wells]
                cols = [j for i, j in wells]
                r1, r2 = min(rows), max(rows)
                c1, c2 = min(cols), max(cols)
                self.grid_sections.append((r1, c1, r2, c2))
            else:
                self.grid_sections.append((0, 0, 0, 0))
    
        n_sections = len(self.grid_sections)
        # Make sure we have enough colors for all sections
        while len(self.section_colors) < n_sections:
            self.section_colors.extend(self.section_colors[:n_sections - len(self.section_colors)])
        section_colors = self.section_colors[:n_sections]
        
        # Add a section for orphaned wells if auto-exclude is disabled
        if hasattr(self.config, 'auto_exclude_orphaned') and not self.config.auto_exclude_orphaned and orphaned_wells:
            rows = [i for i, j in orphaned_wells]
            cols = [j for i, j in orphaned_wells]
            if rows and cols:  # Only add if there are orphaned wells
                r1, r2 = min(rows), max(rows)
                c1, c2 = min(cols), max(cols)
                self.grid_sections.append((r1, c1, r2, c2))
                self.section_wells.append(list(orphaned_wells))
                self.section_names.append("Orphaned Wells")
        
        n_sections = len(self.grid_sections)
        section_colors = (self.section_colors * ((n_sections // len(self.section_colors)) + 1))[:n_sections]
        
        # Initialize section grays if not exists
        if self.selected_key not in self.section_grays:
            self.section_grays[self.selected_key] = [0] * n_sections
        
        # Ensure section_grays has the correct length
        current_grays = self.section_grays[self.selected_key]
        if len(current_grays) < n_sections:
            # Add zeros for new sections
            current_grays.extend([0] * (n_sections - len(current_grays)))
        elif len(current_grays) > n_sections:
            # Truncate if we have fewer sections now
            current_grays = current_grays[:n_sections]
        
        section_grays = current_grays
        # Crear vista de cuadrícula
        grid_view = PlateGridView(
            parent=self.grid_frame,
            plate=plate,
            assay=assay,
            mask=self.mask_map[self.selected_key],
            neg_ctrl_mask=self.neg_ctrl_mask_map[self.selected_key],
            sections=self.grid_sections,
            section_colors=section_colors,
            toggle_well_callback=self.toggle_well,
            toggle_negative_control_callback=self.toggle_negative_control,
            advanced_mode=self.advanced_mode,
            current_individual_plate=getattr(self, 'current_individual_plate', None)
        )
        # Crear leyendas con nombres personalizados


        self.section_legend = SectionLegend(
            parent=self.legend_frame,
            section_colors=section_colors,
            section_grays=section_grays,
            save_callback=self.save_single_gray_value,
            copy_callback=self.copy_grays_to_all_plates
        )
        self.section_legend.pack(pady=(0, 10), fill="x")
        # Añadir nombres de sección como etiquetas
        for idx, entry in enumerate(self.section_legend.gray_entries):
            if idx < len(self.section_names):
                entry.insert(0, f" ({self.section_names[idx]})")
        self.well_status_legend = WellStatusLegend(
            parent=self.legend_frame
        )
        self.well_status_legend.pack(pady=(10, 0), fill="x")
        # Almacenar referencias a los botones
        self.buttons = grid_view.buttons
        self.all_buttons = grid_view.all_buttons
        # Almacenar referencias a las entradas de grises
        self.gray_entries = self.section_legend.gray_entries
        


    def toggle_well(self, i, j):
        """Alterna el valor de máscara de un pocillo sin reconstruir toda la cuadrícula."""
        # Voltear máscara en la posición (i,j)
        m = self.mask_map[self.selected_key]
        neg_ctrl_m = self.neg_ctrl_mask_map[self.selected_key]
        
        # Alternar máscara normal (incluso si es un control negativo)
        m[i,j] = 0 if m[i,j] == 1 else 1
        print(f"DEBUG: toggle_well called with i={i}, j={j}")
        print(f"DEBUG: len(self.buttons) = {len(self.buttons)}")
        if len(self.buttons) > 0 and isinstance(self.buttons[0], list):
            print(f"DEBUG: len(self.buttons[0]) = {len(self.buttons[0])}")
        # Actualizar color del botón basado en ambas máscaras
        button = self.buttons[i][j]
        if neg_ctrl_m[i,j] == 1 and m[i,j] == 0:
            # Ambos control negativo y excluido
            button.configure(fg_color='#800080', border_color='#ff0000', border_width=2)
        elif neg_ctrl_m[i,j] == 1:
            # Solo control negativo
            button.configure(fg_color='#800080', border_width=0)
        elif m[i,j] == 0:
            # Solo excluido
            button.configure(fg_color='#ff0000', border_width=0)
        else:
            # Pocillo normal
            button.configure(fg_color='transparent', border_width=0)
        
        # Guardar máscaras en CSV después de cada cambio
        save_masks_to_csv(self.mask_file, self.mask_map)
        
        # Update the configuration
        self.config.update_masks(self.selected_key, self.mask_map[self.selected_key])

    def toggle_negative_control(self, i, j):
        """Alterna un pocillo como control negativo con clic derecho."""
        # Obtener máscaras
        m = self.mask_map[self.selected_key]
        neg_ctrl_m = self.neg_ctrl_mask_map[self.selected_key]
        
        # Alternar estado de control negativo
        neg_ctrl_m[i,j] = 0 if neg_ctrl_m[i,j] == 1 else 1
        print(f"DEBUG: toggle_negative_control called with i={i}, j={j}")
        print(f"DEBUG: len(self.buttons) = {len(self.buttons)}")
        if len(self.buttons) > 0 and isinstance(self.buttons[0], list):
            print(f"DEBUG: len(self.buttons[0]) = {len(self.buttons[0])}")
        # Actualizar color del botón basado en ambas máscaras
        button = self.buttons[i][j]
        if neg_ctrl_m[i,j] == 1 and m[i,j] == 0:
            # Ambos control negativo y excluido
            button.configure(fg_color='#800080', border_color='#ff0000', border_width=2)
        elif neg_ctrl_m[i,j] == 1:
            # Solo control negativo
            button.configure(fg_color='#800080', border_width=0)
        elif m[i,j] == 0:
            # Solo excluido
            button.configure(fg_color='#ff0000', border_width=0)
        else:
            # Pocillo normal
            button.configure(fg_color='transparent', border_width=0)
        
        # Guardar máscaras en CSV después de cada cambio
        save_neg_ctrl_masks_to_csv(self.neg_ctrl_mask_file, self.neg_ctrl_mask_map)
        
        # Update the configuration
        self.config.update_neg_ctrl_masks(self.selected_key, self.neg_ctrl_mask_map[self.selected_key])

    def copy_to_same_plate(self):
        """Copia la máscara actual a todos los puntos de tiempo de la misma placa."""
        if not self.selected_key:
            return
            
        plate, assay = self.selected_key.split("_")
        current_mask = self.mask_map[self.selected_key].copy()
        current_neg_ctrl_mask = self.neg_ctrl_mask_map[self.selected_key].copy()
        
        # Encontrar todas las placas con el mismo número de placa y ensayo
        for key in self.keys:
            key_plate, key_assay = key.split("_")
            if key_plate == plate and key_assay == assay:
                self.mask_map[key] = current_mask.copy()
                self.neg_ctrl_mask_map[key] = current_neg_ctrl_mask.copy()
        
        # Refrescar si se está viendo la misma placa
        self.build_grid()
        
        # Guardar máscaras en CSV después de copiar
        save_masks_to_csv(self.mask_file, self.mask_map)
        save_neg_ctrl_masks_to_csv(self.neg_ctrl_mask_file, self.neg_ctrl_mask_map)
        
        # Mostrar confirmación
        self.result_box.delete('1.0', ctk.END)
        self.result_box.insert(ctk.END, f"Selection copied to all time points of plate {plate}_{assay}\n")

    def analyze_all(self):
        """Analiza todas las placas y genera visualizaciones."""
        # Obtener opciones
        use_percentage = self.percent_var.get()
        show_error_bars = self.error_bars_var.get()
        use_bar_chart = self.bar_chart_var.get()
        subtract_neg_ctrl = self.subtract_neg_ctrl_var.get()
        
        # Convertir secciones al formato esperado (r1, c1, r2, c2)
        section_limits = []
        for section in self.sections:
            if isinstance(section, tuple) and len(section) == 2:
                # Si es una tupla (name, wells), obtener los límites
                name, wells = section
                if wells:  # Si hay pocillos en la sección
                    rows = [w[0] for w in wells]
                    cols = [w[1] for w in wells]
                    section_limits.append((min(rows), min(cols), max(rows), max(cols)))
            elif isinstance(section, dict) and 'wells' in section:
                # Si es un diccionario con clave 'wells'
                wells = section['wells']
                if wells:  # Si hay pocillos en la sección
                    rows = [w[0] for w in wells]
                    cols = [w[1] for w in wells]
                    section_limits.append((min(rows), min(cols), max(rows), max(cols)))
        
        # Si no hay secciones, usar la placa completa
        if not section_limits:
            section_limits = [(0, 0, 7, 11)]  # Toda la placa
        
        # Realizar análisis completo
        result_message, html_path = analyze_all_plates(
            df=self.df,
            keys=self.keys,
            mask_map=self.mask_map,
            neg_ctrl_mask_map=self.neg_ctrl_mask_map,
            section_grays=self.section_grays,
            sections=section_limits,  # Usar los límites convertidos
            section_colors=self.section_colors,
            use_percentage=use_percentage,
            show_error_bars=show_error_bars,
            use_bar_chart=use_bar_chart,
            subtract_neg_ctrl=subtract_neg_ctrl
        )
        
        # Mostrar mensaje de resultado
        self.result_box.delete('1.0', ctk.END)
        self.result_box.insert(ctk.END, result_message)
        
        # Abrir el archivo HTML en el navegador predeterminado
        if html_path:
            webbrowser.open('file://' + os.path.abspath(html_path))

    def copy_to_assay(self, target_assay):
        """Copia la máscara actual a todas las placas con el mismo ensayo."""
        if not self.selected_key:
            return
            
        current_mask = self.mask_map[self.selected_key].copy()
        current_neg_ctrl_mask = self.neg_ctrl_mask_map[self.selected_key].copy()
        
        for key in self.keys:
            _, assay = key.split("_")
            if assay == target_assay:
                self.mask_map[key] = current_mask.copy()
                self.neg_ctrl_mask_map[key] = current_neg_ctrl_mask.copy()
        
        # Refrescar si se está viendo el mismo ensayo
        if self.selected_key.split("_")[1] == target_assay:
            self.build_grid()
        
        # Guardar máscaras en CSV después de copiar
        save_masks_to_csv(self.mask_file, self.mask_map)
        save_neg_ctrl_masks_to_csv(self.neg_ctrl_mask_file, self.neg_ctrl_mask_map)
        
        # Mostrar confirmación
        self.result_box.delete('1.0', ctk.END)
        self.result_box.insert(ctk.END, f"Selection copied to all plates with assay {target_assay}\n")

    def save_section_grays(self):
        """Guarda los valores de grises actuales para la placa-ensayo seleccionada."""
        try:
            # Obtener valores de las entradas
            gray_values = []
            for entry in self.gray_entries:
                try:
                    value = float(entry.get())
                except ValueError:
                    value = 0
                gray_values.append(value)
            
            # Actualizar los valores de grises para la placa-ensayo actual
            self.section_grays[self.selected_key] = gray_values
            
            # Guardar en CSV
            save_grays_to_csv(self.gray_file, self.section_grays)
            
            # Mostrar confirmación
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, f"Gray values saved for {self.selected_key}\n")
            for i, value in enumerate(gray_values):
                self.result_box.insert(ctk.END, f"Section {i+1}: {value} Grays\n")
        except Exception as e:
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, f"Error saving gray values: {e}\n")

    def copy_grays_to_all_plates(self):
        """Copia los valores de grises actuales a todas las placas."""
        try:
            # Obtener valores de las entradas
            gray_values = []
            for entry in self.gray_entries:
                try:
                    value = float(entry.get())
                except ValueError:
                    value = 0
                gray_values.append(value)
            
            # Actualizar todas las placas con estos valores
            for key in self.keys:
                self.section_grays[key] = gray_values.copy()
            
            # Guardar en CSV
            save_grays_to_csv(self.gray_file, self.section_grays)
            
            # Mostrar confirmación
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, "Gray values copied to all plates\n")
            for i, value in enumerate(gray_values):
                self.result_box.insert(ctk.END, f"Section {i+1}: {value} Grays\n")
        except Exception as e:
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, f"Error copying gray values: {e}\n")

    def on_closing(self):
        """Maneja el evento de cierre de la ventana."""
        # Save configuration
        if self.df is not None and hasattr(self, 'keys') and self.keys:
            for key in list(self.keys):  # Create a copy of keys to avoid modification during iteration
                try:
                    if key in self.mask_map:
                        self.config.update_masks(key, self.mask_map[key])
                    else:
                        print(f"Warning: No mask data found for {key}, using default mask")
                        self.config.update_masks(key, np.ones((8, 12), dtype=float))
                    
                    if key in self.neg_ctrl_mask_map:
                        self.config.update_neg_ctrl_masks(key, self.neg_ctrl_mask_map[key])
                    else:
                        print(f"Warning: No negative control mask data found for {key}, using default")
                        self.config.update_neg_ctrl_masks(key, np.zeros((8, 12), dtype=float))
                    
                    if key in self.section_grays:
                        self.config.update_section_grays(key, self.section_grays[key])
                    else:
                        print(f"Warning: No section grays data found for {key}, using default")
                        self.config.update_section_grays(key, [0] * 6)
                except Exception as e:
                    print(f"Error saving data for {key}: {str(e)}")
        
        try:
            self.config.save()
        except Exception as e:
            print(f"Error saving configuration: {str(e)}")
        
        # Destroy the window
        self.destroy()
    
    def save_single_gray_value(self, index, value):
        """Save a single gray value when it changes."""
        if not self.selected_key:
            return
        
        # Update the value in the section_grays dictionary
        self.section_grays[self.selected_key][index] = value
        
        # Update the configuration
        self.config.update_section_grays(self.selected_key, self.section_grays[self.selected_key])
        
        # No need to rebuild the grid, just update the internal data
    
    def load_file(self, df, file_path):
        """Load a new file and initialize the application with it."""
        try:
            if df is None or df.empty:
                self.result_box.delete('1.0', ctk.END)
                self.result_box.insert(ctk.END, f"Error: No data found in file {file_path}\n")
                return
                
            # Store the new DataFrame
            self.df = df
            
            # Reinitialize the data
            self._initialize_data(df)
            
            if not self.keys:
                self.result_box.delete('1.0', ctk.END)
                self.result_box.insert(ctk.END, f"Error: No valid plate-assay combinations found in {file_path}\n")
                return
            
            # Update the combo box with new keys
            if hasattr(self, 'combo'):
                self.combo.configure(values=self.keys)
            
            # Select the first key
            if self.keys:
                self.selected_key = self.keys[0]
                if hasattr(self, 'combo'):
                    self.combo.set(self.selected_key)
            
            # Enable buttons
            self._set_buttons_state(tk.NORMAL)
            
            # Rebuild the grid
            self.build_grid()
            
            # Show confirmation
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, f"Successfully loaded file: {file_path}\n")
            self.result_box.insert(ctk.END, f"Found {len(self.keys)} plate-assay combinations\n")
            
        except Exception as e:
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, f"Error loading file {file_path}: {str(e)}\n")
            import traceback
            self.result_box.insert(ctk.END, f"Traceback: {traceback.format_exc()}\n")

    def analyze_this_plate(self):
        """Analyze current plate and show section summary table."""
        # Analyze only this plate using full analysis pipeline
        if not self.selected_key:
            return
        plate, assay = self.selected_key.split("_")
        mask = self.mask_map[self.selected_key]
        neg_ctrl_mask = self.neg_ctrl_mask_map[self.selected_key]
        sections = self.grid_sections
        use_percentage = self.percent_var.get()
        subtract_neg_ctrl = self.subtract_neg_ctrl_var.get()

        result_text = analyze_plate(
            self.df,
            plate,
            assay,
            mask,
            neg_ctrl_mask,
            sections,
            use_percentage,
            subtract_neg_ctrl,
            getattr(self, 'current_individual_plate', None)
        )

        # Show in result box
        self.result_box.delete('1.0', ctk.END)
        self.result_box.insert(tk.END, result_text)
