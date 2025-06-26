"""
Main entry point for the Plate Analyzer application.
"""
import sys
import os
import customtkinter as ctk
from src.ui.app import PlateMaskApp
from src.core.data.parser import parse_spectro_excel
import tkinter as tk
from tkinter import filedialog, messagebox

def main():
    """Main function to start the application."""
    # Set appearance mode
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    
    # Initialize app with no data
    app = PlateMaskApp(None)
    
    # Check if a file was provided as command line argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path) and file_path.endswith(('.xls', '.xlsx')):
            try:
                df = parse_spectro_excel(file_path)
                if not df.empty:
                    app.load_file(df, file_path)
                else:
                    messagebox.showerror("Error", "No valid data found in the file.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
    
    # Start the main loop
    app.mainloop()

if __name__ == "__main__":
    main()
