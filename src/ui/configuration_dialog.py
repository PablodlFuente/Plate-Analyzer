"""
Configuration dialog for the Plates Analyzer application.
"""
import customtkinter as ctk
from src.modules import database as db
from tkinter import ttk, messagebox

class ConfigurationDialog(ctk.CTkToplevel):
    """Dialog for application configuration."""
    
    def __init__(self, parent, config, on_config_saved):
        """Initialize the configuration dialog.
        
        Args:
            parent: Parent window.
            config: Configuration object.
            on_config_saved: Callback when configuration is saved.
        """
        super().__init__(parent)
        self.title("Configuration")
        self.geometry("400x600")
        self.resizable(False, True)
        
        self.config = config
        self.on_config_saved = on_config_saved
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Section units configuration
        units_label = ctk.CTkLabel(self.main_frame, text="Section Units:")
        units_label.pack(pady=(0, 5), anchor="w")
        
        # Get the current section units or default to "grays"
        current_units = getattr(self.config, 'section_units', "grays")
        self.section_units_var = ctk.StringVar(value=current_units)
        
        # Create an entry for section units
        self.section_units_entry = ctk.CTkEntry(
            self.main_frame, 
            textvariable=self.section_units_var,
            width=200
        )
        self.section_units_entry.pack(pady=5, anchor="w")
        
        # Help text for section units
        units_help = ctk.CTkLabel(
            self.main_frame, 
            text="Enter the units to display for section values (e.g., grays, units, etc.)",
            font=("Arial", 10),
            text_color="gray"
        )
        units_help.pack(pady=(0, 15), anchor="w")
        
        # Auto-exclude orphaned wells
        self.auto_exclude_var = ctk.BooleanVar(value=config.auto_exclude_orphaned)
        auto_exclude_check = ctk.CTkCheckBox(
            self.main_frame,
            text="Auto-exclude wells not in any section",
            variable=self.auto_exclude_var
        )
        auto_exclude_check.pack(pady=15, anchor="w")

        # Log level configuration
        log_level_label = ctk.CTkLabel(self.main_frame, text="Log Level:")
        log_level_label.pack(pady=(15, 5), anchor="w")

        self.log_level_var = ctk.StringVar(value=self.config.log_level)
        log_level_combo = ctk.CTkComboBox(
            self.main_frame,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            variable=self.log_level_var,
            width=200
        )
        log_level_combo.pack(pady=5, anchor="w")

        # Separator
        sep = ctk.CTkLabel(self.main_frame, text="", height=2)
        sep.pack(fill="x", pady=10)

        # Delete all database button
        delete_btn = ctk.CTkButton(
            self.main_frame,
            text="Delete ALL Database Records",
            fg_color="red",
            hover_color="#aa0000",
            command=self._on_delete_db
        )
        delete_btn.pack(pady=10, anchor="center")
        

        
        # Center the dialog
        self.update_idletasks()
        self.geometry(f"+{parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2}+{parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2}")

        # Bind the closing event
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_delete_db(self):
        """Prompt confirmation and delete all records from the database."""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete ALL records from the database? This action cannot be undone."):
            try:
                db.delete_all_records()
                messagebox.showinfo("Success", "All records have been deleted from the database.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete records: {e}")

    def _on_close(self):
        """Handle save button click."""
        # Save the section units
        self.config.section_units = self.section_units_var.get()
        
        # Save other settings
        self.config.auto_exclude_orphaned = self.auto_exclude_var.get()
        self.config.log_level = self.log_level_var.get()
        
        # Save to file
        self.config.save()
        
        # Notify parent
        if self.on_config_saved:
            self.on_config_saved()
        
        # Close dialog
        self.destroy()
