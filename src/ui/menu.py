"""
Menu module for the Plates Analyzer application.
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
import customtkinter as ctk
from src.ui.section_selector import SectionSelectorDialog
from src.ui.configuration_dialog import ConfigurationDialog
from src.parser import parse_spectro_excel

class AppMenu:
    """Class to manage application menus."""
    
    def __init__(self, parent, config, load_callback):
        """Initialize the menu.
        
        Args:
            parent: Parent window.
            config: Configuration object.
            load_callback: Callback for loading files.
        """
        self.parent = parent
        self.config = config
        self.load_callback = load_callback
        self.on_config_changed = None

        # Create menu
        self.menu = tk.Menu(parent)
        parent.configure(menu=self.menu)

        # File menu
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Load Data File...", command=self.load_file)

        # Recent files submenu
        self.recent_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self._update_recent_files_menu()

        self.file_menu.add_separator()

        # Export submenu
        self.export_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="Export DB into", menu=self.export_menu)
        self.export_menu.add_command(label="GraphPad XML...", command=lambda: self.parent.export_to_graphpad_xml_action())

        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=parent.on_closing)

        # Tools menu
        self.tools_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Tools", menu=self.tools_menu)
        self.tools_menu.add_command(label="Section Editor", command=self.show_section_editor)
        self.tools_menu.add_command(label="Configuration", command=self.show_configuration)
    
    def _update_recent_files_menu(self):
        """Update the recent files submenu."""
        # Clear existing items
        self.recent_menu.delete(0, tk.END)
        
        # Add recent files
        if self.config.recent_files:
            for file_path in self.config.recent_files:
                file_name = os.path.basename(file_path)
                self.recent_menu.add_command(
                    label=file_name,
                    command=lambda path=file_path: self.load_specific_file(path)
                )
        else:
            self.recent_menu.add_command(label="No recent files", state=tk.DISABLED)
    
    def load_file(self):
        """Open file dialog and load selected file."""
        initial_dir = self.config.default_directory if self.config.default_directory else os.getcwd()
        file_path = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=initial_dir
        )
        
        if file_path:
            self.load_specific_file(file_path)
    
    def load_specific_file(self, file_path):
        """Load a specific file.
        
        Args:
            file_path: Path to the file to load.
        """
        try:
            # Update default directory
            self.config.default_directory = os.path.dirname(file_path)
            
            # Parse the data
            df = parse_spectro_excel(file_path)
            
            # Convert numpy arrays to lists to avoid unhashable type issues
            if not df.empty and 'data' in df.columns:
                df['data'] = df['data'].apply(lambda x: x.tolist() if hasattr(x, 'tolist') else x)
            
            # Add to recent files
            self.config.add_recent_file(file_path)
            self._update_recent_files_menu()
            
            # Call the load callback with the modified DataFrame
            self.load_callback(df, file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
    
    def show_section_editor(self):
        """Show the section editor dialog."""
        # Get initial sections from config if available
        initial_sections = self.config.sections if hasattr(self.config, 'sections') and self.config.sections else None
        
        # Get section colors
        section_colors = getattr(self.parent, 'section_colors', None)
        
        # Create and show the dialog
        dialog = SectionSelectorDialog(
            self.parent,
            initial_sections=initial_sections,
            initial_colors=section_colors,
            on_confirm=self.on_sections_confirmed
        )
    
    def on_sections_confirmed(self, sections):
        """Handle confirmed sections from the section editor.
        
        Args:
            sections: List of section dictionaries.
        """
        # Update the parent's sections
        self.parent.sections = sections
        
        # Extract section names and wells
        self.parent.section_names = [s['name'] for s in sections]
        self.parent.section_wells = [s['wells'] for s in sections]
        
        # Save sections to config
        self.config.update_sections(sections)
        
        # Rebuild the grid
        self.parent.build_grid()
    
    def show_configuration(self):
        """Show the configuration dialog."""
        dialog = ConfigurationDialog(
            self.parent,
            self.config,
            self._on_config_saved
        )
    
    def _on_config_saved(self):
        """Handle configuration saved event."""
        if self.on_config_changed:
            self.on_config_changed()
