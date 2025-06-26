import customtkinter as ctk
import tkinter as tk

class SectionSelectorDialog(ctk.CTkToplevel):
    """
    Diálogo para seleccionar secciones en una placa de 96 pocillos.
    Permite al usuario seleccionar pocillos, agruparlos como secciones, y borrar secciones.
    """
    def __init__(self, parent, initial_sections=None, initial_colors=None, on_confirm=None):
        super().__init__(parent)
        self.title("Selector de Secciones de Placa")
        self.geometry("700x600")
        self.resizable(False, False)
        self.parent = parent
        self.on_confirm = on_confirm
        self.selected_wells = set()
        # Estructura: [{'name':..., 'wells':[(i,j), ...]}, ...]
        # Asegurar que las coordenadas de los pocillos sean tuplas (hashables)
        self.sections = []
        if initial_sections:
            for sec in initial_sections:
                # Clonar la sección para no mutar el original
                new_sec = sec.copy()
                new_sec['wells'] = [tuple(w) for w in sec.get('wells', [])]
                self.sections.append(new_sec)
        else:
            self.sections = []
        self.section_colors = initial_colors.copy() if initial_colors else [
            '#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF', '#99FFFF', '#FFA07A', '#90EE90', '#87CEFA', '#FFD700'
        ]
        self.current_section_index = 0
        self.section_entries = []  # Entradas de nombre
        self.selected_wells = set()
        self.selected_section_idx = None  # Inicializar antes de _build_ui
        self._build_ui()
        self.bind("<space>", self.confirm_section)
        self.bind("<Delete>", self.delete_selected_section)
        self.bind("<BackSpace>", self.delete_selected_section)
        self.lift()
        self.focus_force()
        self.attributes('-topmost', True)

    def _build_ui(self):
        self.grid_frame = ctk.CTkFrame(self)
        self.grid_frame.pack(side="left", padx=20, pady=20)
        self._create_plate_grid()

        self.sidebar = ctk.CTkFrame(self)
        self.sidebar.pack(side="right", fill="y", padx=10, pady=10)
        self.sections_label = ctk.CTkLabel(self.sidebar, text="Secciones actuales:", font=("Arial", 12, "bold"))
        self.sections_label.pack(pady=5)
        self.sections_list = ctk.CTkFrame(self.sidebar)
        self.sections_list.pack(fill="y", expand=True)
        self._update_sections_list()
        self.restore_btn = ctk.CTkButton(self.sidebar, text="Restaurar por defecto", command=self.restore_defaults)
        self.restore_btn.pack(pady=5)
        self.confirm_btn = ctk.CTkButton(self.sidebar, text="Confirmar selección", command=self._confirm_all)
        self.confirm_btn.pack(pady=10)
        self.instructions = ctk.CTkLabel(self.sidebar, text="Selecciona pocillos con clic izquierdo.\nBarra espaciadora para confirmar sección.\nSelecciona una sección y presiona Supr/Del para borrar.\nHaz doble clic para seleccionar una sección.", font=("Arial", 10))
        self.instructions.pack(pady=5)

    def _create_plate_grid(self):
        self.buttons = {}
        for i in range(8):
            for j in range(12):
                well = (i, j)
                btn = ctk.CTkButton(self.grid_frame, text=f"{chr(65+i)}{j+1}", width=40, height=30,
                                    fg_color="transparent", command=lambda w=well: self._toggle_well(w))
                btn.grid(row=i, column=j, padx=2, pady=2)
                self.buttons[well] = btn
        self._update_grid_colors()

    def _toggle_well(self, well):
        if well in self.selected_wells:
            self.selected_wells.remove(well)
        else:
            self.selected_wells.add(well)
        self._update_grid_colors()

    def _update_grid_colors(self):
        # Marcar los pocillos de secciones existentes
        for idx, section in enumerate(self.sections):
            wells = [tuple(w) for w in section['wells']]  # Garantizar tuplas
            color = self.section_colors[idx % len(self.section_colors)]
            for well in wells:
                if well in self.buttons:
                    self.buttons[well].configure(fg_color=color, text_color="black")
        # Marcar los seleccionados para la nueva sección
        for well in self.buttons:
            if well in self.selected_wells:
                self.buttons[well].configure(fg_color="#2222FF", text_color="white")
            elif not any(well in section['wells'] for section in self.sections):
                self.buttons[well].configure(fg_color="transparent", text_color="black")

    def confirm_section(self, event=None):
        if self.selected_wells:
            # Preguntar nombre de sección o poner uno automático
            name = f"Sección {len(self.sections)+1}"
            self.sections.append({'name': name, 'wells': list(self.selected_wells)})
            self.selected_wells.clear()
            self._update_grid_colors()
            self._update_sections_list()

    def _update_sections_list(self):
        # Limpiar widgets y entradas
        for widget in self.sections_list.winfo_children():
            widget.destroy()
        self.section_entries = []
        
        for idx, section in enumerate(self.sections):
            color = self.section_colors[idx % len(self.section_colors)]
            wells_str = ", ".join([f"{chr(65+i)}{j+1}" for (i, j) in sorted(section['wells'])])
            
            # Frame principal de la sección
            frame = ctk.CTkFrame(self.sections_list, fg_color=color, corner_radius=4)
            
            # Entrada editable para el nombre
            entry = ctk.CTkEntry(frame, width=100, corner_radius=4)
            entry.insert(0, section['name'])
            entry.pack(side="left", padx=5, pady=2)
            self.section_entries.append(entry)
            
            # Label con los pocillos
            label = ctk.CTkLabel(frame, text=f": {wells_str}", text_color="black", anchor="w")
            label.pack(side="left", padx=5, fill="x", expand=True)
            
            # Botón de borrar
            del_btn = ctk.CTkButton(
                frame, 
                text="Borrar", 
                width=60, 
                fg_color="#FF4444",
                hover_color="#CC0000",
                corner_radius=4,
                command=lambda i=idx: self._delete_section(i)
            )
            del_btn.pack(side="right", padx=5, pady=2)
            
            # Empaquetar el frame
            frame.pack(fill="x", pady=2, padx=2, ipady=2)
            
            # Configurar eventos de selección
            def make_select_callback(i):
                return lambda e: self._select_section(i)
                
            # Selección con clic simple
            frame.bind("<Button-1>", make_select_callback(idx))
            label.bind("<Button-1>", make_select_callback(idx))
            
            # Selección al hacer foco en la entrada
            entry.bind("<FocusIn>", make_select_callback(idx))
        
        # Actualizar resaltado
        self._highlight_selected_section()

    def _select_section(self, idx):
        """Selecciona una sección por su índice."""
        if 0 <= idx < len(self.sections):
            self.selected_section_idx = idx
            self._highlight_selected_section()
    
    def _delete_section(self, idx):
        """Elimina la sección en el índice dado."""
        if 0 <= idx < len(self.sections):
            # Confirmar antes de borrar
            section_name = self.sections[idx]['name']
            if tk.messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Estás seguro de que quieres eliminar la sección '{section_name}'?"
            ):
                del self.sections[idx]
                # Ajustar el índice seleccionado si es necesario
                if self.selected_section_idx == idx:
                    self.selected_section_idx = None
                elif self.selected_section_idx is not None and self.selected_section_idx > idx:
                    self.selected_section_idx -= 1
                # Actualizar la interfaz
                self._update_grid_colors()
                self._update_sections_list()

    def _confirm_all(self):
        # Actualizar nombres desde las entradas antes de devolver
        for idx, entry in enumerate(self.section_entries):
            self.sections[idx]['name'] = entry.get()
        if self.on_confirm:
            self.on_confirm(self.sections)
        self.destroy()

    def delete_selected_section(self, event=None):
        """Elimina la sección actualmente seleccionada."""
        if self.selected_section_idx is not None:
            self._delete_section(self.selected_section_idx)

    def _highlight_selected_section(self):
        """Resalta visualmente la sección seleccionada."""
        for i, frame in enumerate(self.sections_list.winfo_children()):
            if hasattr(self, 'selected_section_idx') and self.selected_section_idx == i:
                # Resaltar la sección seleccionada
                frame.configure(
                    border_color="#2222FF",
                    border_width=2,
                    corner_radius=6
                )
            else:
                # Restaurar el estilo por defecto
                frame.configure(
                    border_color="#CCCCCC",
                    border_width=1,
                    corner_radius=4
                )

    def restore_defaults(self):
        # Restaurar secciones por defecto
        default_limits = [
            (0, 0, 3, 3), (0, 4, 3, 7), (0, 8, 3, 11),
            (4, 0, 7, 3), (4, 4, 7, 7), (4, 8, 7, 11)
        ]
        default_names = [f"Sección {i+1}" for i in range(6)]
        self.sections = []
        for name, (r1, c1, r2, c2) in zip(default_names, default_limits):
            wells = [(i, j) for i in range(r1, r2+1) for j in range(c1, c2+1)]
            self.sections.append({'name': name, 'wells': wells})
        self.selected_section_idx = None
        self._update_grid_colors()
        self._update_sections_list()
