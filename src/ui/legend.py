"""
Legend module for the Plates Analyzer application.
"""
import customtkinter as ctk

class SectionLegend(ctk.CTkFrame):
    """Legend for plate sections."""
    
    def __init__(self, parent, section_colors, section_grays, save_callback=None, copy_callback=None):
        """Initialize the section legend.
        
        Args:
            parent: Parent widget.
            section_colors: List of colors for each section.
            section_grays: List of gray values for each section.
            save_callback: Callback for saving gray values.
            copy_callback: Callback for copying gray values to all plates.
        """
        import logging
        logging.getLogger('plate_analyzer').debug(f"DEBUG PRE-super: id(self)={id(self)}, Class id={id(SectionLegend)}")
        super().__init__(parent)
        logging.getLogger('plate_analyzer').debug(f"DEBUG POST-super: 'pack' in dir(self)? {'pack' in dir(self)}")
        self.section_colors = section_colors
        self.section_grays = section_grays
        self.save_callback = save_callback
        self.copy_callback = copy_callback
        self.gray_entries = []
        
        # Get section units from config
        self.section_units = getattr(parent.master.master, 'config', None)
        if self.section_units:
            self.section_units = getattr(self.section_units, 'section_units', "grays")
        else:
            self.section_units = "grays"
        
        self._create_legend()
    
    def _create_legend(self):
        """Create the legend UI."""
        # Title
        title = ctk.CTkLabel(self, text="Section Legend", font=("Arial", 14, "bold"))
        title.pack(pady=(0, 10))
        
        # Create a row for each section
        num_sections = len(self.section_grays)
        
        for i in range(num_sections):
            row_frame = ctk.CTkFrame(self)
            row_frame.pack(fill="x", pady=2)
            
            # Color indicator
            color_frame = ctk.CTkFrame(row_frame, fg_color=self.section_colors[i % len(self.section_colors)], width=20, height=20, corner_radius=0)
            color_frame.pack(side="left", padx=5)
            
            # Section label
            section_label = ctk.CTkLabel(row_frame, text=f"S{i+1}")
            section_label.pack(side="left", padx=5)
            
            # Gray value entry
            gray_entry = ctk.CTkEntry(row_frame, width=60)
            gray_entry.insert(0, str(self.section_grays[i]))
            gray_entry.pack(side="left", padx=5)
            self.gray_entries.append(gray_entry)
            
            # Units label
            units_label = ctk.CTkLabel(row_frame, text=self.section_units)
            units_label.pack(side="left", padx=5)
            
            # Add callback to update when entry changes
            gray_entry.bind("<FocusOut>", lambda event, idx=i, entry=gray_entry: self._on_entry_change(idx, entry))
            gray_entry.bind("<Return>", lambda event, idx=i, entry=gray_entry: self._on_entry_change(idx, entry))
        
        # Add buttons at the bottom
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", pady=(10, 0))
        
        if self.copy_callback:
            copy_btn = ctk.CTkButton(
                button_frame, 
                text="Copy to All Plates", 
                command=self.copy_callback,
                fg_color="#4CAF50",
                hover_color="#45a049"
            )
            copy_btn.pack(pady=5)
    
    def _on_entry_change(self, index, entry):
        """Handle entry value change.
        
        Args:
            index: Index of the entry.
            entry: Entry widget.
        """
        try:
            value = float(entry.get())
            if self.save_callback:
                self.save_callback(index, value)
        except ValueError:
            # Reset to previous value if invalid
            entry.delete(0, ctk.END)
            entry.insert(0, str(self.section_grays[index]))

class WellStatusLegend(ctk.CTkFrame):
    """Legend for well status."""
    
    def __init__(self, parent):
        """Initialize the well status legend.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._create_legend()
    
    def _create_legend(self):
        """Create the legend UI."""
        # Title
        title = ctk.CTkLabel(self, text="Well Status", font=("Arial", 14, "bold"))
        title.pack(pady=(10, 10))
        
        # Normal well
        normal_frame = ctk.CTkFrame(self)
        normal_frame.pack(fill="x", pady=2)
        
        normal_indicator = ctk.CTkFrame(normal_frame, fg_color="transparent", width=20, height=20, corner_radius=0, border_width=1, border_color="gray")
        normal_indicator.pack(side="left", padx=5)
        
        normal_label = ctk.CTkLabel(normal_frame, text="Normal Well")
        normal_label.pack(side="left", padx=5)
        
        # Excluded well
        excluded_frame = ctk.CTkFrame(self)
        excluded_frame.pack(fill="x", pady=2)
        
        excluded_indicator = ctk.CTkFrame(excluded_frame, fg_color="#ff0000", width=20, height=20, corner_radius=0)
        excluded_indicator.pack(side="left", padx=5)
        
        excluded_label = ctk.CTkLabel(excluded_frame, text="Excluded Well")
        excluded_label.pack(side="left", padx=5)
        
        # Negative control
        neg_ctrl_frame = ctk.CTkFrame(self)
        neg_ctrl_frame.pack(fill="x", pady=2)
        
        neg_ctrl_indicator = ctk.CTkFrame(neg_ctrl_frame, fg_color="#800080", width=20, height=20, corner_radius=0)
        neg_ctrl_indicator.pack(side="left", padx=5)
        
        neg_ctrl_label = ctk.CTkLabel(neg_ctrl_frame, text="Negative Control")
        neg_ctrl_label.pack(side="left", padx=5)
        
        # Excluded negative control
        excluded_neg_frame = ctk.CTkFrame(self)
        excluded_neg_frame.pack(fill="x", pady=2)
        
        excluded_neg_indicator = ctk.CTkFrame(excluded_neg_frame, fg_color="#800080", width=20, height=20, corner_radius=0, border_width=2, border_color="#ff0000")
        excluded_neg_indicator.pack(side="left", padx=5)
        
        excluded_neg_label = ctk.CTkLabel(excluded_neg_frame, text="Excluded Neg. Control")
        excluded_neg_label.pack(side="left", padx=5)
