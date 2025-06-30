import customtkinter as ctk
import tkinter as tk

class SectionSelectorDialog(ctk.CTkToplevel):
    """
    Dialog to select sections in a 96-well plate.
    Allows the user to select wells, group them as sections, and delete sections.
    """
    def __init__(self, parent, initial_sections=None, initial_colors=None, on_confirm=None):
        super().__init__(parent)
        self.title("Plate Section Selector")
        self.geometry("780x400")
        self.resizable(False, False)
        self.parent = parent
        self.on_confirm = on_confirm
        self.selected_wells = set()
        # Structure: [{'name':..., 'wells':[(i,j), ...]}, ...]
        # Ensure well coordinates are tuples (hashable)
        self.sections = []
        if initial_sections:
            for sec in initial_sections:
                # Clone the section to avoid mutating the original
                new_sec = sec.copy()
                new_sec['wells'] = [tuple(w) for w in sec.get('wells', [])]
                self.sections.append(new_sec)
        else:
            self.sections = []
        self.section_colors = initial_colors.copy() if initial_colors else [
            '#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF', '#99FFFF', '#FFA07A', '#90EE90', '#87CEFA', '#FFD700'
        ]
        self.current_section_index = 0
        self.section_entries = []  # Name entries
        self.selected_wells = set()
        self.selected_section_idx = None  # Initialize before _build_ui
        self._build_ui()
        self.bind("<space>", self.confirm_section)
        self.bind("<Delete>", self.delete_selected_section)
        self.bind("<BackSpace>", self.delete_selected_section)
        self.lift()
        self.focus_force()
        self.attributes('-topmost', True)

    # --- SectionSelectorDialog END ---

    def _build_ui(self):
        # Main left frame for the plate and instructions
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.pack(side="left", padx=20, pady=20, fill="both", expand=True)

        self.grid_frame = ctk.CTkFrame(left_frame)
        self.grid_frame.pack(pady=20) # Center the plate horizontally
        self._create_plate_grid()

        # Move instructions below the plate
        self.instructions = ctk.CTkLabel(left_frame, text="Select wells with left click.\nPress spacebar to confirm section.\nSelect a section and press Del to delete.\nDouble click to select a section.", font=("Arial", 10), justify=tk.LEFT)
        self.instructions.pack(side="bottom", pady=10, padx=5, fill="x")

        # Right sidebar
        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        self.sidebar.pack_propagate(False)

        self.sections_label = ctk.CTkLabel(self.sidebar, text="Current Sections:", font=("Arial", 12, "bold"))
        self.sections_label.pack(pady=5, padx=10, anchor="w")

        # Make the section list a scrollable frame
        self.sections_list = ctk.CTkScrollableFrame(self.sidebar)
        self.sections_list.pack(fill="both", expand=True, pady=5, padx=5)
        self._update_sections_list()

        # Frame for the bottom buttons
        bottom_button_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_button_frame.pack(side="bottom", fill="x", pady=5)

        self.restore_btn = ctk.CTkButton(bottom_button_frame, text="Restore Defaults", command=self.restore_defaults, width=160)
        self.restore_btn.pack(pady=5)
        self.confirm_btn = ctk.CTkButton(bottom_button_frame, text="Confirm Selection", command=self._confirm_all, width=160)
        self.confirm_btn.pack(pady=10)

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
        # Mark wells of existing sections
        for idx, section in enumerate(self.sections):
            wells = [tuple(w) for w in section['wells']]  # Ensure tuples
            color = self.section_colors[idx % len(self.section_colors)]
            for well in wells:
                if well in self.buttons:
                    self.buttons[well].configure(fg_color=color, text_color="black")
        # Mark selected wells for the new section
        for well in self.buttons:
            if well in self.selected_wells:
                self.buttons[well].configure(fg_color="#2222FF", text_color="white")
            elif not any(well in section['wells'] for section in self.sections):
                self.buttons[well].configure(fg_color="transparent", text_color="black")

    def confirm_section(self, event=None):
        if self.selected_wells:
            # Ask for section name or set automatically
            name = f"Section {len(self.sections)+1}"
            self.sections.append({'name': name, 'wells': list(self.selected_wells)})
            self.selected_wells.clear()
            self._update_grid_colors()
            self._update_sections_list()

    def _update_sections_list(self):
        # Clear widgets and entries
        for widget in self.sections_list.winfo_children():
            widget.destroy()
        self.section_entries = []
        
        for idx, section in enumerate(self.sections):
            color = self.section_colors[idx % len(self.section_colors)]
            
            # Main frame for the section
            frame = ctk.CTkFrame(self.sections_list, fg_color=color, corner_radius=4)
            
            # Editable entry for the name
            entry = ctk.CTkEntry(frame, width=100, corner_radius=4)
            entry.insert(0, section['name'])
            entry.pack(side="left", padx=5, pady=2)
            self.section_entries.append(entry)
            
            # Delete button with icon
            del_btn = ctk.CTkButton(
                frame,
                text="❌",
                width=28,
                height=28,
                fg_color="transparent",
                hover_color="#FF4444",
                text_color=("gray10", "gray90"),
                command=lambda i=idx: self._delete_section(i)
            )
            del_btn.pack(side="right", padx=5, pady=2)
            
            # Pack the frame
            frame.pack(fill="x", pady=2, padx=2, ipady=2)
            
            # Configure selection events
            def make_select_callback(i):
                return lambda e: self._select_section(i)
                
            # Select with single click
            frame.bind("<Button-1>", make_select_callback(idx))
            
            # Select when entry gets focus
            entry.bind("<FocusIn>", make_select_callback(idx))
        
        # Update highlight
        self._highlight_selected_section()

    def _select_section(self, idx):
        """Select a section by its index."""
        if 0 <= idx < len(self.sections):
            self.selected_section_idx = idx
            self._highlight_selected_section()
    
    def _delete_section(self, idx):
        """Delete the section at the given index."""
        if 0 <= idx < len(self.sections):
            # Confirm before deleting
            section_name = self.sections[idx]['name']
            if tk.messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete the section '{section_name}'?"
            ):
                del self.sections[idx]
                # Adjust selected index if needed
                if self.selected_section_idx == idx:
                    self.selected_section_idx = None
                elif self.selected_section_idx is not None and self.selected_section_idx > idx:
                    self.selected_section_idx -= 1
                # Update UI
                self._update_grid_colors()
                self._update_sections_list()

    def _confirm_all(self):
        # Update names from entries before returning
        for idx, entry in enumerate(self.section_entries):
            self.sections[idx]['name'] = entry.get()
        if self.on_confirm:
            self.on_confirm(self.sections)
        self.destroy()

    def delete_selected_section(self, event=None):
        """Delete the currently selected section."""
        if self.selected_section_idx is not None:
            self._delete_section(self.selected_section_idx)

    def _highlight_selected_section(self):
        """Highlight the selected section visually."""
        for i, frame in enumerate(self.sections_list.winfo_children()):
            if hasattr(self, 'selected_section_idx') and self.selected_section_idx == i:
                # Highlight selected section
                frame.configure(
                    border_color="#2222FF",
                    border_width=2,
                    corner_radius=6
                )
            else:
                # Restore default style
                frame.configure(
                    border_color="#CCCCCC",
                    border_width=1,
                    corner_radius=4
                )

    def restore_defaults(self):
        # Restore default sections
        default_limits = [
            (0, 0, 3, 3), (0, 4, 3, 7), (0, 8, 3, 11),
            (4, 0, 7, 3), (4, 4, 7, 7), (4, 8, 7, 11)
        ]
        default_names = [f"Section {i+1}" for i in range(6)]
        self.sections = []
        for name, (r1, c1, r2, c2) in zip(default_names, default_limits):
            wells = [(i, j) for i in range(r1, r2+1) for j in range(c1, c2+1)]
            self.sections.append({'name': name, 'wells': wells})
        self.selected_section_idx = None
        self._update_grid_colors()
        self._update_sections_list()
