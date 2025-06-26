import pandas as pd
import re
import numpy as np
import customtkinter as ctk
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import webbrowser
import tempfile
import json
import csv

# Parser function to extract plate data from an Excel file
def parse_spectro_excel(file_path):
    raw = pd.read_excel(file_path, header=None)
    records = []
    nrows = raw.shape[0]
    i = 0
    # Regex patterns for plate number, assay, time and unit
    pat_plate = re.compile(r'(P\d+)', re.IGNORECASE)
    pat_assay = re.compile(r'(?:(?<=_)|^)(AB|ROS)(?:(?=_)|$)', re.IGNORECASE)
    pat_hours = re.compile(r'(\d+)(?=[hm])', re.IGNORECASE)
    pat_unit = re.compile(r'([hm])', re.IGNORECASE)

    while i < nrows:
        cell = str(raw.iat[i, 0]).strip()
        if cell.startswith("Plate"):  # Start of a plate block
            plate_full = str(raw.iat[i, 1]).strip()
            m_plate = pat_plate.search(plate_full)
            m_assay = pat_assay.search(plate_full)
            m_hours = pat_hours.search(plate_full)
            m_unit = pat_unit.search(plate_full)

            # Extract or default to NaN
            plate_no = m_plate.group(1).upper() if m_plate else np.nan
            assay = m_assay.group(1).upper() if m_assay else np.nan
            if m_hours:
                val = int(m_hours.group(1))
                hours = val / 60.0 if m_unit and m_unit.group(1).lower() == 'm' else float(val)
            else:
                hours = np.nan

            data_list = []
            j = i + 2  # Skip header rows
            # Read until ~End marker
            while j < nrows and str(raw.iat[j, 0]).strip() != "~End":
                row = raw.iloc[j, 2:14].astype(float)
                if not row.isna().all():
                    data_list.extend(row.tolist())
                j += 1

            # Only keep complete plates
            if len(data_list) == 96:
                data_arr = np.array(data_list, dtype=float).reshape(8, 12)
                records.append({
                    'plate_no': plate_no,
                    'assay': assay,
                    'hours': hours,
                    'data': data_arr
                })
            i = j + 1
        else:
            i += 1

    return pd.DataFrame(records)

# GUI application class for interacting with plate data
class PlateMaskApp(ctk.CTk):
    def __init__(self, df):
        super().__init__()
        self.title("Plate Masking Interface")
        self.geometry("900x800")
        ctk.set_appearance_mode("system")

        # Prepare data and mask structures
        self.df = df.copy().reset_index(drop=True)
        uniq = self.df[['plate_no','assay']].drop_duplicates().reset_index(drop=True)
        self.keys = [f"{r.plate_no}_{r.assay}" for _, r in uniq.iterrows()]
        
        # Initialize mask for each plate-assay key (8x12 of ones)
        self.mask_map = {key: np.ones((8,12), dtype=float) for key in self.keys}
        
        # Initialize negative control mask for each plate-assay key (8x12 of zeros)
        self.neg_ctrl_mask_map = {key: np.zeros((8,12), dtype=float) for key in self.keys}
        
        # Initialize gray values for each section (default to 0)
        self.section_grays = {key: [0, 0, 0, 0, 0, 0] for key in self.keys}
        # Try to load gray values from CSV if it exists
        self.gray_file = "section_grays.csv"
        self.load_grays_from_csv()
        
        # Define section colors - using more vibrant colors for better visibility
        self.section_colors = ['#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF', '#99FFFF']
        
        # Define section boundaries
        self.sections = [
            (0, 0, 3, 3),  # Section 1: rows 0-3, cols 0-3
            (0, 4, 3, 7),  # Section 2: rows 0-3, cols 4-7
            (0, 8, 3, 11), # Section 3: rows 0-3, cols 8-11
            (4, 0, 7, 3),  # Section 4: rows 4-7, cols 0-3
            (4, 4, 7, 7),  # Section 5: rows 4-7, cols 4-7
            (4, 8, 7, 11)  # Section 6: rows 4-7, cols 8-11
        ]
        
        # Try to load masks from CSV if it exists
        self.mask_file = "last_masks.csv"
        self.neg_ctrl_mask_file = "last_neg_ctrl_masks.csv"
        self.load_masks_from_csv()
        self.load_neg_ctrl_masks_from_csv()

        # Create a frame for the top controls
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(pady=10, fill="x", padx=10)
        
        # Label for the dropdown
        self.combo_label = ctk.CTkLabel(self.top_frame, text="Select Plate-Assay:")
        self.combo_label.pack(side="left", padx=(0, 10))
        
        # Dropdown to select plate-assay
        self.combo = ctk.CTkComboBox(self.top_frame, values=self.keys, command=self.on_select, width=200)
        self.combo.pack(side="left", padx=10)
        
        # Advanced mode button
        self.advanced_btn = ctk.CTkButton(self.top_frame, text="Advanced Mode", command=self.toggle_advanced_mode)
        self.advanced_btn.pack(side="right", padx=10)
        
        # Advanced mode state and UI elements
        self.advanced_mode = False
        self.advanced_frame = None
        self.individual_plates = []
        
        # Main content frame with grid and legend side by side
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(pady=10, fill="both", expand=True)
        
        # Frame to hold the 8x12 grid of wells (left side)
        self.grid_frame = ctk.CTkFrame(self.content_frame)
        self.grid_frame.pack(side="left", pady=10, padx=10, fill="both", expand=True)
        
        # Frame for section legend (right side)
        self.legend_frame = ctk.CTkFrame(self.content_frame)
        self.legend_frame.pack(side="right", pady=10, padx=10, fill="y")

        # Control buttons frame
        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.pack(pady=10, fill="x", padx=10)
        
        # Control buttons
        self.start_btn = ctk.CTkButton(self.btn_frame, text="Start Analysis", command=self.on_start)
        self.start_btn.pack(side="left", padx=5)
        self.copy_ab_btn = ctk.CTkButton(self.btn_frame, text="Copiar selección a todas las placas AB", command=lambda: self.copy_to_assay('AB'))
        self.copy_ab_btn.pack(side="left", padx=5)
        self.copy_ros_btn = ctk.CTkButton(self.btn_frame, text="Copiar selección a todas las placas ROS", command=lambda: self.copy_to_assay('ROS'))
        self.copy_ros_btn.pack(side="left", padx=5)
        # New button: copy to same plate
        self.copy_same_plate_btn = ctk.CTkButton(self.btn_frame, text="Copiar selección para la misma placa", command=self.copy_to_same_plate)
        self.copy_same_plate_btn.pack(side="left", padx=5)
        # Analyze all button
        self.analyze_all_btn = ctk.CTkButton(self.btn_frame, text="Analizar todo", command=self.analyze_all)
        self.analyze_all_btn.pack(side="left", padx=5)
        
        # Options frame for checkboxes
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(pady=5, fill="x", padx=10)
        
        # Add percentage checkbox
        self.percent_var = ctk.BooleanVar(value=True)  # Default to selected
        self.percent_check = ctk.CTkCheckBox(self.options_frame, text="%", variable=self.percent_var, 
                                            onvalue=True, offvalue=False)
        self.percent_check.pack(side="left", padx=10)
        
        # Add error bars checkbox
        self.error_bars_var = ctk.BooleanVar(value=True)  # Default to selected
        self.error_bars_check = ctk.CTkCheckBox(self.options_frame, text="Error Bars", variable=self.error_bars_var, 
                                               onvalue=True, offvalue=False)
        self.error_bars_check.pack(side="left", padx=10)
        
        # Add bar chart checkbox
        self.bar_chart_var = ctk.BooleanVar(value=False)  # Default to line chart
        self.bar_chart_check = ctk.CTkCheckBox(self.options_frame, text="Bar Chart", variable=self.bar_chart_var, 
                                              onvalue=True, offvalue=False)
        self.bar_chart_check.pack(side="left", padx=10)
        
        # Add subtract negative controls checkbox
        self.subtract_neg_ctrl_var = ctk.BooleanVar(value=True)  # Default to selected
        self.subtract_neg_ctrl_check = ctk.CTkCheckBox(self.options_frame, text="Subtract Neg. Controls", 
                                                      variable=self.subtract_neg_ctrl_var, 
                                                      onvalue=True, offvalue=False)
        self.subtract_neg_ctrl_check.pack(side="left", padx=10)

        # Textbox to show results for single plate
        self.result_box = ctk.CTkTextbox(self, width=800, height=200)
        self.result_box.pack(pady=10, fill="x", padx=10)
        
        # Add instructions for negative controls
        self.instructions_frame = ctk.CTkFrame(self)
        self.instructions_frame.pack(pady=5, fill="x", padx=10)
        
        instructions_text = "Instructions: Left-click to toggle well selection. Right-click to mark as negative control (purple)."
        self.instructions_label = ctk.CTkLabel(self.instructions_frame, text=instructions_text)
        self.instructions_label.pack(pady=5)

        # Initial selection and draw
        self.selected_key = self.keys[0] if self.keys else None
        self.selected_hour_index = 0
        self.build_grid()
        
        # Bind the close event to save masks
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Bind resize event to update layout
        self.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        """Handle window resize event"""
        # Only respond to actual window resize events, not child widget events
        if event.widget == self:
            # Update layout if needed
            pass

    def toggle_advanced_mode(self):
        """Toggle between simple and advanced mode"""
        self.advanced_mode = not self.advanced_mode
        
        # Update button text
        self.advanced_btn.configure(text="Simple Mode" if self.advanced_mode else "Advanced Mode")
        
        # Create or destroy advanced frame
        if self.advanced_mode:
            # Create advanced frame if it doesn't exist
            if not self.advanced_frame:
                self.advanced_frame = ctk.CTkFrame(self)
                self.advanced_frame.pack(before=self.content_frame, pady=10, fill="x", padx=10)
                
                # Get unique plates and assays
                unique_plates = self.df['plate_no'].unique()
                unique_assays = self.df['assay'].unique()
                
                # Create individual plate selection
                plate_label = ctk.CTkLabel(self.advanced_frame, text="Individual Plate:")
                plate_label.pack(side="left", padx=(0, 5))
                
                # Create a list of all individual plates
                all_plates = []
                for _, row in self.df.iterrows():
                    plate_id = f"{row['plate_no']}_{row['assay']}_{row['hours']}"
                    if plate_id not in all_plates:
                        all_plates.append(plate_id)
                
                # Dropdown for individual plate selection
                self.plate_combo = ctk.CTkComboBox(self.advanced_frame, values=all_plates, width=300)
                self.plate_combo.pack(side="left", padx=5)
                
                # Button to load individual plate
                load_btn = ctk.CTkButton(self.advanced_frame, text="Load Plate", command=self.load_individual_plate)
                load_btn.pack(side="left", padx=5)
            else:
                self.advanced_frame.pack(before=self.content_frame, pady=10, fill="x", padx=10)
        else:
            # Hide advanced frame
            if self.advanced_frame:
                self.advanced_frame.pack_forget()
        
        # Refresh the grid
        self.build_grid()

    def load_individual_plate(self):
        """Load an individual plate based on the selection"""
        if not self.advanced_mode or not hasattr(self, 'plate_combo'):
            return
            
        selected = self.plate_combo.get()
        if not selected:
            return
            
        # Parse the selection
        parts = selected.split('_')
        if len(parts) < 3:
            return
            
        plate_no = parts[0]
        assay = parts[1]
        hours = float(parts[2])
        
        # Find the matching row in the dataframe
        matching_rows = self.df[(self.df['plate_no'] == plate_no) & 
                               (self.df['assay'] == assay) & 
                               (self.df['hours'] == hours)]
        
        if matching_rows.empty:
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, "No matching plate found.")
            return
            
        # Set the selected key to the plate-assay
        self.selected_key = f"{plate_no}_{assay}"
        self.combo.set(self.selected_key)
        
        # Store the individual plate data
        self.current_individual_plate = matching_rows.iloc[0]
        
        # Update the grid
        self.build_grid()
        
        # Show info in result box
        self.result_box.delete('1.0', ctk.END)
        self.result_box.insert(ctk.END, f"Loaded individual plate: {selected}\n")
        self.result_box.insert(ctk.END, f"Hours: {hours}\n")

    def on_select(self, choice):
        # When user selects a different plate-assay
        self.selected_key = choice
        self.selected_hour_index = 0
        # Clear individual plate selection in advanced mode
        if hasattr(self, 'current_individual_plate'):
            delattr(self, 'current_individual_plate')
        self.build_grid()

    def build_grid(self):
        # Clear grid frame
        for w in self.grid_frame.winfo_children():
            w.destroy()
            
        # Clear legend frame
        for w in self.legend_frame.winfo_children():
            w.destroy()

        if not self.selected_key:
            return
            
        plate, assay = self.selected_key.split("_")
        
        # If in advanced mode and an individual plate is selected, use that data
        if self.advanced_mode and hasattr(self, 'current_individual_plate'):
            # Display the individual plate data
            data = self.current_individual_plate['data']
            # Create a label to show which individual plate is being viewed
            hours = self.current_individual_plate['hours']
            plate_label = ctk.CTkLabel(self.grid_frame, 
                                      text=f"Viewing: {plate}_{assay} at {hours} hours",
                                      font=("Arial", 14, "bold"))
            plate_label.grid(row=0, column=0, columnspan=13, pady=(0, 10))
            
            # Adjust starting row for the grid
            start_row = 1
        else:
            # Regular mode - just show the plate-assay
            plate_label = ctk.CTkLabel(self.grid_frame, 
                                      text=f"Viewing: {plate}_{assay}",
                                      font=("Arial", 14, "bold"))
            plate_label.grid(row=0, column=0, columnspan=13, pady=(0, 10))
            start_row = 1

        # Draw grid labeled by well (1A..12H)
        mask = self.mask_map[self.selected_key]
        neg_ctrl_mask = self.neg_ctrl_mask_map[self.selected_key]
        self.buttons = []
        
        # Add column headers (1-12)
        for j in range(12):
            col_label = ctk.CTkLabel(self.grid_frame, text=f"{j+1}")
            col_label.grid(row=start_row, column=j+1, padx=2, pady=2)
            
        # Create section frames first
        section_frames = []
        for i, (r1, c1, r2, c2) in enumerate(self.sections):
            # Create a frame for this section with a colored border
            section_frame = ctk.CTkFrame(self.grid_frame, fg_color="transparent", 
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
        for i in range(8):  # rows A-H
            row_btns = []
            # Row header
            row_label = ctk.CTkLabel(self.grid_frame, text=f"{chr(ord('A')+i)}")
            row_label.grid(row=i+start_row+1, column=0, padx=(0, 5), sticky="e")
            
            for j in range(12):  # columns 1-12
                # Create well label (1A, 2A, etc.)
                well_label = f"{j+1}{chr(ord('A')+i)}"
                
                # Determine which section this well belongs to
                section_idx = -1
                for idx, (r1, c1, r2, c2) in enumerate(self.sections):
                    if r1 <= i <= r2 and c1 <= j <= c2:
                        section_idx = idx
                        break
                
                # Determine button color based on mask and negative control status
                if neg_ctrl_mask[i,j] == 1 and mask[i,j] == 0:
                    # Both negative control and excluded - purple with red border
                    btn = ctk.CTkButton(
                        self.grid_frame,
                        text=well_label,
                        width=40,
                        height=30,
                        fg_color='#800080',  # Purple for negative control
                        border_color='#ff0000',
                        border_width=2,
                        command=lambda x=i, y=j: self.toggle_well(x, y)
                    )
                elif neg_ctrl_mask[i,j] == 1:
                    # Negative control - purple
                    btn = ctk.CTkButton(
                        self.grid_frame,
                        text=well_label,
                        width=40,
                        height=30,
                        fg_color='#800080',  # Purple for negative control
                        command=lambda x=i, y=j: self.toggle_well(x, y)
                    )
                elif mask[i,j] == 0:
                    # Excluded well - red
                    btn = ctk.CTkButton(
                        self.grid_frame,
                        text=well_label,
                        width=40,
                        height=30,
                        fg_color='#ff0000',
                        command=lambda x=i, y=j: self.toggle_well(x, y)
                    )
                else:
                    # Normal well - default
                    btn = ctk.CTkButton(
                        self.grid_frame,
                        text=well_label,
                        width=40,
                        height=30,
                        fg_color='transparent',
                        command=lambda x=i, y=j: self.toggle_well(x, y)
                    )
                btn.grid(row=i+start_row+1, column=j+1, padx=2, pady=2)
                
                # Bind right-click to mark as negative control
                btn.bind("<Button-3>", lambda event, x=i, y=j: self.toggle_negative_control(x, y))
                
                row_btns.append(btn)
            self.buttons.append(row_btns)
        
        # Add section legend to the right frame
        self.add_section_legend()
        
        # Add well status legend to the right frame
        self.add_well_status_legend()
        
        # Store references to all buttons for quick access
        self.all_buttons = {}
        for i in range(8):
            for j in range(12):
                self.all_buttons[(i, j)] = self.buttons[i][j]

    def add_section_legend(self):
        """Add a legend for the sections with input fields for gray values"""
        # Create a frame for section indicators
        section_frame = ctk.CTkFrame(self.legend_frame)
        section_frame.pack(pady=10, padx=10, fill="x")
        
        # Add section legend title
        section_label = ctk.CTkLabel(section_frame, text="Sections:", font=("Arial", 12, "bold"))
        section_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Add color indicators and input fields for each section
        self.gray_entries = []
        for i in range(6):
            # Section row
            row_frame = ctk.CTkFrame(section_frame)
            row_frame.grid(row=i+1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
            
            # Color indicator
            color_frame = ctk.CTkFrame(row_frame, fg_color=self.section_colors[i], width=20, height=20, corner_radius=0)
            color_frame.pack(side="left", padx=5)
            
            # Section label
            section_text = ctk.CTkLabel(row_frame, text=f"S{i+1}")
            section_text.pack(side="left", padx=5)
            
            # Gray label
            gray_label = ctk.CTkLabel(row_frame, text="Grays:", font=("Arial", 10))
            gray_label.pack(side="left", padx=5)
            
            # Gray entry
            gray_value = self.section_grays[self.selected_key][i]
            gray_entry = ctk.CTkEntry(row_frame, width=60, height=25)
            gray_entry.insert(0, str(gray_value))
            gray_entry.pack(side="left", padx=5)
            self.gray_entries.append(gray_entry)
        
        # Add buttons for gray values
        button_frame = ctk.CTkFrame(section_frame)
        button_frame.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Save gray values button
        save_grays_btn = ctk.CTkButton(button_frame, text="Save Gray Values", 
                                      command=self.save_section_grays)
        save_grays_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        # Copy gray values button
        copy_grays_btn = ctk.CTkButton(button_frame, text="Copy Gray Values to All Plates", 
                                      command=self.copy_grays_to_all_plates)
        copy_grays_btn.pack(side="left", padx=5, fill="x", expand=True)

    def add_well_status_legend(self):
        """Add a legend for well status"""
        # Create a frame for well status
        status_frame = ctk.CTkFrame(self.legend_frame)
        status_frame.pack(pady=10, padx=10, fill="x")
        
        # Add well status title
        status_label = ctk.CTkLabel(status_frame, text="Well Status:", font=("Arial", 12, "bold"))
        status_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Normal well
        normal_row = ctk.CTkFrame(status_frame)
        normal_row.grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky="ew")
        normal_frame = ctk.CTkFrame(normal_row, fg_color=None, width=20, height=20, corner_radius=0)
        normal_frame.pack(side="left", padx=5)
        normal_text = ctk.CTkLabel(normal_row, text="Normal Well")
        normal_text.pack(side="left", padx=5)
        
        # Excluded well
        excluded_row = ctk.CTkFrame(status_frame)
        excluded_row.grid(row=2, column=0, columnspan=2, padx=5, pady=2, sticky="ew")
        excluded_frame = ctk.CTkFrame(excluded_row, fg_color='#ff0000', width=20, height=20, corner_radius=0)
        excluded_frame.pack(side="left", padx=5)
        excluded_text = ctk.CTkLabel(excluded_row, text="Excluded Well")
        excluded_text.pack(side="left", padx=5)
        
        # Negative control
        neg_ctrl_row = ctk.CTkFrame(status_frame)
        neg_ctrl_row.grid(row=3, column=0, columnspan=2, padx=5, pady=2, sticky="ew")
        neg_ctrl_frame = ctk.CTkFrame(neg_ctrl_row, fg_color='#800080', width=20, height=20, corner_radius=0)
        neg_ctrl_frame.pack(side="left", padx=5)
        neg_ctrl_text = ctk.CTkLabel(neg_ctrl_row, text="Negative Control")
        neg_ctrl_text.pack(side="left", padx=5)

        # Combined state
        combined_row = ctk.CTkFrame(status_frame)
        combined_row.grid(row=4, column=0, columnspan=2, padx=5, pady=2, sticky="ew")
        combined_frame = ctk.CTkFrame(combined_row, fg_color='#800080', width=20, height=20, corner_radius=0, border_color='#ff0000', border_width=2)
        combined_frame.pack(side="left", padx=5)
        combined_text = ctk.CTkLabel(combined_row, text="Neg. Control + Excluded")
        combined_text.pack(side="left", padx=5)

    def toggle_well(self, i, j):
        """Toggle a well's mask value without rebuilding the entire grid"""
        # Flip mask at position (i,j)
        m = self.mask_map[self.selected_key]
        neg_ctrl_m = self.neg_ctrl_mask_map[self.selected_key]
        
        # Toggle normal mask (even if it's a negative control)
        m[i,j] = 0 if m[i,j] == 1 else 1
        
        # Update button color based on both masks
        button = self.buttons[i][j]
        if neg_ctrl_m[i,j] == 1 and m[i,j] == 0:
            # Both negative control and excluded
            button.configure(fg_color='#800080', border_color='#ff0000', border_width=2)
        elif neg_ctrl_m[i,j] == 1:
            # Just negative control
            button.configure(fg_color='#800080', border_width=0)
        elif m[i,j] == 0:
            # Just excluded
            button.configure(fg_color='#ff0000', border_width=0)
        else:
            # Normal well
            button.configure(fg_color='transparent', border_width=0)
        
        # Save masks to CSV after each change
        self.save_masks_to_csv()

    def toggle_negative_control(self, i, j):
        """Toggle a well as negative control with right-click"""
        # Get masks
        m = self.mask_map[self.selected_key]
        neg_ctrl_m = self.neg_ctrl_mask_map[self.selected_key]
        
        # Toggle negative control status
        neg_ctrl_m[i,j] = 0 if neg_ctrl_m[i,j] == 1 else 1
        
        # Update button color based on both masks
        button = self.buttons[i][j]
        if neg_ctrl_m[i,j] == 1 and m[i,j] == 0:
            # Both negative control and excluded
            button.configure(fg_color='#800080', border_color='#ff0000', border_width=2)
        elif neg_ctrl_m[i,j] == 1:
            # Just negative control
            button.configure(fg_color='#800080', border_width=0)
        elif m[i,j] == 0:
            # Just excluded
            button.configure(fg_color='#ff0000', border_width=0)
        else:
            # Normal well
            button.configure(fg_color='transparent', border_width=0)
        
        # Save masks to CSV after each change
        self.save_neg_ctrl_masks_to_csv()

    def copy_to_same_plate(self):
        """Copy current mask to all time points of the same plate"""
        if not self.selected_key:
            return
            
        plate, assay = self.selected_key.split("_")
        current_mask = self.mask_map[self.selected_key].copy()
        current_neg_ctrl_mask = self.neg_ctrl_mask_map[self.selected_key].copy()
        
        # Find all plates with the same plate number and assay
        for key in self.keys:
            key_plate, key_assay = key.split("_")
            if key_plate == plate and key_assay == assay:
                self.mask_map[key] = current_mask.copy()
                self.neg_ctrl_mask_map[key] = current_neg_ctrl_mask.copy()
        
        # Refresh if viewing the same plate
        self.build_grid()
        
        # Save masks to CSV after copying
        self.save_masks_to_csv()
        self.save_neg_ctrl_masks_to_csv()
        
        # Show confirmation
        self.result_box.delete('1.0', ctk.END)
        self.result_box.insert(ctk.END, f"Selection copied to all time points of plate {plate}_{assay}\n")

    def on_start(self):
        # Compute and display section means for current plate-assay
        plate, assay = self.selected_key.split("_")
        
        # Check if percentage mode is enabled
        use_percentage = self.percent_var.get()
        subtract_neg_ctrl = self.subtract_neg_ctrl_var.get()
        
        # If in advanced mode and an individual plate is selected
        if self.advanced_mode and hasattr(self, 'current_individual_plate'):
            # Analyze just this individual plate
            data = self.current_individual_plate['data'].copy()
            hours = self.current_individual_plate['hours']
            mask = self.mask_map[self.selected_key]
            neg_ctrl_mask = self.neg_ctrl_mask_map[self.selected_key]
            
            # Subtract negative controls if enabled
            if subtract_neg_ctrl:
                # Calculate average and std of negative controls
                neg_ctrl_data = data * neg_ctrl_mask
                valid_neg_ctrls = neg_ctrl_data[neg_ctrl_data != 0]
                if len(valid_neg_ctrls) > 0:
                    neg_ctrl_avg = np.nanmean(valid_neg_ctrls)
                    neg_ctrl_std = np.nanstd(valid_neg_ctrls)
                    # Subtract from all wells
                    data = data - neg_ctrl_avg
                    # Set negative values to 0
                    data[data < 0] = 0
                    
                    # Store the negative control std for error propagation
                    neg_ctrl_info = {'hours': hours, 'neg_ctrl_avg': neg_ctrl_avg, 'neg_ctrl_std': neg_ctrl_std}
                else:
                    neg_ctrl_info = {'hours': hours, 'neg_ctrl_avg': np.nan, 'neg_ctrl_std': np.nan}
            
            # Apply mask
            masked_data = data * mask
            
            # Calculate section means and standard deviations
            sec_means = {}
            sec_stds = {}
            
            # For each section, calculate mean and std with error propagation
            for i, (r1, c1, r2, c2) in enumerate(self.sections):
                section_data = masked_data[r1:r2+1, c1:c2+1]
                # Filter out masked values (zeros)
                valid_data = section_data[section_data != 0]
                if len(valid_data) > 0:
                    sec_means[f"S{i+1}"] = np.nanmean(valid_data)
                    # Propagate error if negative controls were subtracted
                    if subtract_neg_ctrl and not np.isnan(neg_ctrl_std):
                        # Error propagation formula for subtraction: sqrt(std1^2 + std2^2)
                        section_std = np.nanstd(valid_data)
                        propagated_std = np.sqrt(section_std**2 + neg_ctrl_std**2)
                        sec_stds[f"S{i+1}_std"] = propagated_std
                    else:
                        sec_stds[f"S{i+1}_std"] = np.nanstd(valid_data)
                else:
                    sec_means[f"S{i+1}"] = np.nan
                    sec_stds[f"S{i+1}_std"] = np.nan
            
            # Display results
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, f"Analysis for individual plate: {plate}_{assay} at {hours} hours\n\n")
            
            # Show negative control info if used
            if subtract_neg_ctrl:
                neg_ctrl_count = np.sum(neg_ctrl_mask)
                if neg_ctrl_count > 0:
                    self.result_box.insert(ctk.END, f"Negative controls: {neg_ctrl_count} wells, avg value: {neg_ctrl_avg:.4f}, std: {neg_ctrl_std:.4f}\n\n")
                else:
                    self.result_box.insert(ctk.END, "No negative controls selected\n\n")
            
            for sec in sec_means.keys():
                self.result_box.insert(ctk.END, f"{sec}: {sec_means[sec]:.4f} ± {sec_stds[sec]:.4f}\n")
            
            return
        
        # Regular mode - analyze all time points for the selected plate-assay
        sub = self.df[(self.df['plate_no']==plate) & (self.df['assay']==assay)].sort_values('hours')
        mask = self.mask_map[self.selected_key]
        neg_ctrl_mask = self.neg_ctrl_mask_map[self.selected_key]
        results = []
        
        # Process each time point
        for _, row in sub.iterrows():
            data = row['data'].copy()  # Make a copy to avoid modifying original
            
            # Subtract negative controls if enabled
            neg_ctrl_avg = np.nan
            neg_ctrl_std = np.nan
            if subtract_neg_ctrl:
                # Calculate average and std of negative controls for this time point
                neg_ctrl_data = data * neg_ctrl_mask
                valid_neg_ctrls = neg_ctrl_data[neg_ctrl_data != 0]
                if len(valid_neg_ctrls) > 0:
                    neg_ctrl_avg = np.nanmean(valid_neg_ctrls)
                    neg_ctrl_std = np.nanstd(valid_neg_ctrls)
                    # Subtract from all wells
                    data = data - neg_ctrl_avg
                    # Set negative values to 0
                    data[data < 0] = 0
                    
                    # Store the negative control std for error propagation
                    neg_ctrl_info = {'hours': row['hours'], 'neg_ctrl_avg': neg_ctrl_avg, 'neg_ctrl_std': neg_ctrl_std}
                else:
                    neg_ctrl_info = {'hours': row['hours'], 'neg_ctrl_avg': np.nan, 'neg_ctrl_std': np.nan}
            
            # Apply mask
            masked_data = data * mask
            
            sec_means = {}
            sec_stds = {}
            neg_ctrl_info = {'hours': row['hours'], 'neg_ctrl_avg': neg_ctrl_avg, 'neg_ctrl_std': neg_ctrl_std}
            
            # For each section, calculate mean and std with error propagation
            for i, (r1, c1, r2, c2) in enumerate(self.sections):
                section_data = masked_data[r1:r2+1, c1:c2+1]
                # Filter out masked values (zeros)
                valid_data = section_data[section_data != 0]
                if len(valid_data) > 0:
                    sec_means[f"S{i+1}"] = np.nanmean(valid_data)
                    # Propagate error if negative controls were subtracted
                    if subtract_neg_ctrl and not np.isnan(neg_ctrl_std):
                        # Error propagation formula for subtraction: sqrt(std1^2 + std2^2)
                        section_std = np.nanstd(valid_data)
                        propagated_std = np.sqrt(section_std**2 + neg_ctrl_std**2)
                        sec_stds[f"S{i+1}_std"] = propagated_std
                    else:
                        sec_stds[f"S{i+1}_std"] = np.nanstd(valid_data)
                else:
                    sec_means[f"S{i+1}"] = np.nan
                    sec_stds[f"S{i+1}_std"] = np.nan
            
            # Combine means and stds
            combined_results = {**sec_means, **sec_stds, **neg_ctrl_info}
            results.append(combined_results)
        
        # Convert to DataFrame
        res_df = pd.DataFrame(results)
        
        # Apply percentage calculation if enabled
        if use_percentage and len(res_df) > 0:
            # Get the first row values for each section
            first_values = res_df.iloc[0].copy()
            
            # Calculate percentage change for each section mean
            for col in [c for c in res_df.columns if c.startswith('S') and not c.endswith('_std')]:
                base_value = first_values[col]
                if base_value != 0:  # Avoid division by zero
                    # Also adjust the std to be relative to the mean
                    std_col = f"{col}_std"
                    res_df[std_col] = (res_df[std_col] / base_value) * 100
                    res_df[col] = (res_df[col] / base_value - 1) * 100
                else:
                    # If base value is zero, set all values to NaN
                    std_col = f"{col}_std"
                    res_df[col] = np.nan
                    res_df[std_col] = np.nan
            
            # Add % symbol to column names
            display_cols = {}
            for col in res_df.columns:
                if col.startswith('S') and not col.endswith('_std'):
                    display_cols[col] = f"{col} (%)"
                elif col.endswith('_std'):
                    display_cols[col] = f"{col[:-4]} Std (%)"
                elif col == 'neg_ctrl_avg':
                    display_cols[col] = "Neg Ctrl Avg"
                elif col == 'neg_ctrl_std':
                    display_cols[col] = "Neg Ctrl Std"
                else:
                    display_cols[col] = col
            
            display_df = res_df.rename(columns=display_cols)
        else:
            # Just rename std columns for display
            display_cols = {}
            for col in res_df.columns:
                if col.endswith('_std'):
                    display_cols[col] = f"{col[:-4]} Std"
                elif col == 'neg_ctrl_avg':
                    display_cols[col] = "Neg Ctrl Avg"
                elif col == 'neg_ctrl_std':
                    display_cols[col] = "Neg Ctrl Std"
                else:
                    display_cols[col] = col
            
            display_df = res_df.rename(columns=display_cols)
        
        # Display results
        self.result_box.delete('1.0', ctk.END)
        
        # Show negative control info
        if subtract_neg_ctrl:
            neg_ctrl_count = np.sum(neg_ctrl_mask)
            if neg_ctrl_count > 0:
                self.result_box.insert(ctk.END, f"Negative controls: {neg_ctrl_count} wells\n\n")
            else:
                self.result_box.insert(ctk.END, "No negative controls selected\n\n")
        
        self.result_box.insert(ctk.END, display_df.to_string(index=False))

    def analyze_all(self):
        # Compute all results, save to Excel and generate interactive Plotly plots in a single HTML file
        out_dir = "analysis_output"
        os.makedirs(out_dir, exist_ok=True)
        
        # Check options
        use_percentage = self.percent_var.get()
        show_error_bars = self.error_bars_var.get()
        use_bar_chart = self.bar_chart_var.get()
        subtract_neg_ctrl = self.subtract_neg_ctrl_var.get()
        
        try:
            writer = pd.ExcelWriter(os.path.join(out_dir, "all_results.xlsx"), engine='xlsxwriter')
        except ImportError:
            writer = pd.ExcelWriter(os.path.join(out_dir, "all_results.xlsx"), engine='openpyxl')

        # Create a single figure with dropdown menu for all plots
        figures = {}
        
        for key in self.keys:
            plate, assay = key.split("_")
            sub = self.df[(self.df['plate_no']==plate) & (self.df['assay']==assay)].sort_values('hours')
            mask = self.mask_map[key]
            neg_ctrl_mask = self.neg_ctrl_mask_map[key]
            results = []
            
            for _, row in sub.iterrows():
                data = row['data'].copy()
                
                # Subtract negative controls if enabled
                neg_ctrl_avg = np.nan
                neg_ctrl_std = np.nan
                if subtract_neg_ctrl:
                    # Calculate average and std of negative controls for this time point
                    neg_ctrl_data = data * neg_ctrl_mask
                    valid_neg_ctrls = neg_ctrl_data[neg_ctrl_data != 0]
                    if len(valid_neg_ctrls) > 0:
                        neg_ctrl_avg = np.nanmean(valid_neg_ctrls)
                        neg_ctrl_std = np.nanstd(valid_neg_ctrls)
                        # Subtract from all wells
                        data = data - neg_ctrl_avg
                        # Set negative values to 0
                        data[data < 0] = 0
                        
                        # Store the negative control std for error propagation
                        neg_ctrl_info = {'hours': row['hours'], 'neg_ctrl_avg': neg_ctrl_avg, 'neg_ctrl_std': neg_ctrl_std}
                    else:
                        neg_ctrl_info = {'hours': row['hours'], 'neg_ctrl_avg': np.nan, 'neg_ctrl_std': np.nan}
                
                # Apply mask
                masked_data = data * mask
                sec_means = {}
                sec_stds = {}
                neg_ctrl_info = {'hours': row['hours'], 'neg_ctrl_avg': neg_ctrl_avg, 'neg_ctrl_std': neg_ctrl_std}
                
                # For each section, calculate mean and std with error propagation
                for i, (r1, c1, r2, c2) in enumerate(self.sections):
                    section_data = masked_data[r1:r2+1, c1:c2+1]
                    # Filter out masked values (zeros)
                    valid_data = section_data[section_data != 0]
                    if len(valid_data) > 0:
                        sec_means[f"S{i+1}"] = np.nanmean(valid_data)
                        # Propagate error if negative controls were subtracted
                        if subtract_neg_ctrl and not np.isnan(neg_ctrl_std):
                            # Error propagation formula for subtraction: sqrt(std1^2 + std2^2)
                            section_std = np.nanstd(valid_data)
                            propagated_std = np.sqrt(section_std**2 + neg_ctrl_std**2)
                            sec_stds[f"S{i+1}_std"] = propagated_std
                        else:
                            sec_stds[f"S{i+1}_std"] = np.nanstd(valid_data)
                    else:
                        sec_means[f"S{i+1}"] = np.nan
                        sec_stds[f"S{i+1}_std"] = np.nan
                
                # Combine means and stds
                combined_results = {**sec_means, **sec_stds, **neg_ctrl_info}
                results.append(combined_results)
            
            # Convert to DataFrame
            res_df = pd.DataFrame(results)
            
            # Store original values for plotting
            orig_df = res_df.copy()
            
            # Apply percentage calculation if enabled
            if use_percentage and len(res_df) > 0:
                # Get the first row values for each section
                first_values = res_df.iloc[0].copy()
                
                # Calculate percentage change for each section mean
                for col in [c for c in res_df.columns if c.startswith('S') and not c.endswith('_std')]:
                    base_value = first_values[col]
                    if base_value != 0:  # Avoid division by zero
                        # Also adjust the std to be relative to the mean
                        std_col = f"{col}_std"
                        res_df[std_col] = (res_df[std_col] / base_value) * 100
                        res_df[col] = (res_df[col] / base_value - 1) * 100
                    else:
                        # If base value is zero, set all values to NaN
                        std_col = f"{col}_std"
                        res_df[col] = np.nan
                        res_df[std_col] = np.nan
                
                # Add % symbol to column names for display
                display_cols = {}
                for col in res_df.columns:
                    if col.startswith('S') and not col.endswith('_std'):
                        display_cols[col] = f"{col} (%)"
                    elif col.endswith('_std'):
                        display_cols[col] = f"{col[:-4]} Std (%)"
                    elif col == 'neg_ctrl_avg':
                        display_cols[col] = "Neg Ctrl Avg"
                    elif col == 'neg_ctrl_std':
                        display_cols[col] = "Neg Ctrl Std"
                    else:
                        display_cols[col] = col
                
                display_df = res_df.rename(columns=display_cols)
                
                # Save to Excel with percentage column names
                sheet_name = key
                display_df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                # Just rename std columns for display
                display_cols = {}
                for col in res_df.columns:
                    if col.endswith('_std'):
                        display_cols[col] = f"{col[:-4]} Std"
                    elif col == 'neg_ctrl_avg':
                        display_cols[col] = "Neg Ctrl Avg"
                    elif col == 'neg_ctrl_std':
                        display_cols[col] = "Neg Ctrl Std"
                    else:
                        display_cols[col] = col
                
                display_df = res_df.rename(columns=display_cols)
                
                # Save original values to Excel
                sheet_name = key
                display_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Create figure for this plate-assay
            fig = go.Figure()
            
            # Use either percentage or original values based on checkbox
            plot_df = res_df if use_percentage else orig_df
            
            # Determine chart type based on checkbox
            if use_bar_chart:
                # Bar chart mode
                # For bar charts, we need to organize data differently
                # Each section will be a group, and each time point will be a bar within that group
                
                # Get unique time points
                time_points = plot_df['hours'].unique()
                
                # For each section, create a bar trace
                for col in [c for c in plot_df.columns if c.startswith('S') and not c.endswith('_std')]:
                    # Determine y-axis label based on percentage mode
                    y_label = f"{col} (%)" if use_percentage else col
                    
                    # Get corresponding std column
                    std_col = f"{col}_std"
                    
                    # Create error bars if enabled
                    error_y = dict(
                        type='data',
                        array=plot_df[std_col] if show_error_bars else None,
                        visible=show_error_bars
                    )
                    
                    # Add bar trace
                    fig.add_trace(go.Bar(
                        x=plot_df['hours'],
                        y=plot_df[col],
                        name=y_label,
                        error_y=error_y
                    ))
                
                # Update layout for bar chart
                fig.update_layout(
                    barmode='group',  # Group bars by time point
                    bargap=0.15,      # Gap between bars
                    bargroupgap=0.1   # Gap between bar groups
                )
            else:
                # Line chart mode (default)
                for col in [c for c in plot_df.columns if c.startswith('S') and not c.endswith('_std')]:
                    # Get corresponding std column
                    std_col = f"{col}_std"
                    
                    # Determine y-axis label based on percentage mode
                    y_label = f"{col} (%)" if use_percentage else col
                    
                    # Add trace with error bars if enabled
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
            
            # Set appropriate title and axis labels
            title_suffix = " (% change from initial value)" if use_percentage else ""
            chart_type = "Bar Chart" if use_bar_chart else "Line Chart"
            y_axis_label = "% Change" if use_percentage else "Mean value"
            neg_ctrl_text = " (Neg Ctrl Subtracted)" if subtract_neg_ctrl else ""
            
            fig.update_layout(
                title=f"Evolution {key}{title_suffix}{neg_ctrl_text} - {chart_type}", 
                xaxis_title='Hours', 
                yaxis_title=y_axis_label,
                height=600,
                width=900
            )
            
            figures[key] = fig

        writer.close()
        
        # Create a single HTML file with dropdown for all figures and tabs for 2D/3D views
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
        .plot-container { width: 100%; height: 80vh; }
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
        }
        .tabcontent.active {
            display: block;
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

        # Add options for each figure
        for i, key in enumerate(figures.keys()):
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
            <div id="plot-container-2d" class="plot-container"></div>
        </div>
        
        <div id="3D" class="tabcontent">
            <div id="plot-container-3d" class="plot-container"></div>
        </div>
    </div>
    
    <script>
        // Store all the figures
        const figures2D = {};
        const figures3D = {};
        
        // Track log scale state
        let useLogScale = false;
        
        // Function to handle window resize
        function handleResize() {
            const currentKey = document.getElementById('plot-selector').value;
            const activeTab = document.querySelector('.tablinks.active');
            const tabName = activeTab.textContent.trim();
            
            // Redraw the current plot to fit the new window size
            showPlot(currentKey);
        }
        
        // Add resize event listener
        window.addEventListener('resize', handleResize);
"""

        # Add each 2D figure as JSON
        for key, fig in figures.items():
            fig_json = fig.to_json()
            html_content += f'figures2D["{key}"] = {fig_json};\n'

        # Create and add 3D figures
        figures3D = {}
        for key in self.keys:
            plate, assay = key.split("_")
            sub = self.df[(self.df['plate_no']==plate) & (self.df['assay']==assay)].sort_values('hours')
            
            # Skip if no data
            if sub.empty:
                continue
            
            # Get gray values for this plate-assay
            gray_values = self.section_grays[key]
            
            # Create 3D figure
            fig3d = go.Figure()
            
            # Collect all data points for a unified surface
            all_hours = []
            all_grays = []
            all_values = []
            all_stds = []  # Para barras de error
            all_sections = []  # Para identificar la sección
            
            # Get data for each section and time point
            section_data = {}  # Almacenar datos por sección para calcular porcentajes
            
            # First pass: collect all raw data
            for i in range(6):
                section_data[i] = []
                # Get section boundaries
                r1, c1, r2, c2 = self.sections[i]
                
                # Get gray value for this section
                gray = gray_values[i]
                
                # Process each time point
                for _, row in sub.iterrows():
                    data = row['data'].copy()
                    hours = row['hours']
                    
                    # Apply mask and get section data
                    mask = self.mask_map[key]
                    neg_ctrl_mask = self.neg_ctrl_mask_map[key]
                    
                    # Subtract negative controls if enabled
                    neg_ctrl_avg = np.nan
                    neg_ctrl_std = np.nan
                    if subtract_neg_ctrl:
                        neg_ctrl_data = data * neg_ctrl_mask
                        valid_neg_ctrls = neg_ctrl_data[neg_ctrl_data != 0]
                        if len(valid_neg_ctrls) > 0:
                            neg_ctrl_avg = np.nanmean(valid_neg_ctrls)
                            neg_ctrl_std = np.nanstd(valid_neg_ctrls)
                            # Subtract from all wells
                            data = data - neg_ctrl_avg
                            # Set negative values to 0
                            data[data < 0] = 0
                    
                    # Apply mask
                    masked_data = data * mask
                    
                    # Get section data
                    section_data_array = masked_data[r1:r2+1, c1:c2+1]
                    valid_data = section_data_array[section_data_array != 0]
                    
                    if len(valid_data) > 0:
                        mean_value = np.nanmean(valid_data)
                        std_value = np.nanstd(valid_data)
                        
                        # Propagate error if negative controls were subtracted
                        if subtract_neg_ctrl and not np.isnan(neg_ctrl_std):
                            std_value = np.sqrt(std_value**2 + neg_ctrl_std**2)
                        
                        # Store data for this section and time point
                        section_data[i].append({
                            'hours': hours,
                            'gray': gray,
                            'value': mean_value,
                            'std': std_value,
                            'section': i+1
                        })
            
            # Second pass: apply percentage calculation if needed
            if use_percentage:
                for i in range(6):
                    if not section_data[i]:
                        continue
                    
                    # Sort by hours to ensure first time point is used as baseline
                    section_data[i].sort(key=lambda x: x['hours'])
                    
                    # Get baseline value (first time point)
                    baseline = section_data[i][0]['value']
                    
                    if baseline != 0:  # Avoid division by zero
                        for data_point in section_data[i]:
                            # Convert to percentage change
                            data_point['std'] = (data_point['std'] / baseline) * 100
                            data_point['value'] = ((data_point['value'] / baseline) - 1) * 100
            
            # Third pass: collect all processed data for plotting
            for i in range(6):
                for data_point in section_data[i]:
                    all_hours.append(data_point['hours'])
                    all_grays.append(data_point['gray'])
                    all_values.append(data_point['value'])
                    all_stds.append(data_point['std'])
                    all_sections.append(data_point['section'])
            
            # Skip if no valid data
            if not all_hours:
                continue
            
            # Determine if we should use bar chart or surface
            if use_bar_chart:
                # En la función `analyze_all()`, reemplaza el bloque de código que usa `go.Bar3d` (alrededor de la línea 1326) con el siguiente código:
                # Create a 3D bar chart using Scatter3d with markers
                for i in range(6):
                    # Filter data for this section
                    section_hours = [h for h, s in zip(all_hours, all_sections) if s == i+1]
                    section_grays = [g for g, s in zip(all_grays, all_sections) if s == i+1]
                    section_values = [v for v, s in zip(all_values, all_sections) if s == i+1]
                    section_stds = [s for s, sec in zip(all_stds, all_sections) if sec == i+1]
                    
                    if not section_hours:
                        continue
                    
                    # Add a 3D scatter trace with large markers to simulate bars
                    fig3d.add_trace(go.Scatter3d(
                        x=section_hours,
                        y=section_grays,
                        z=section_values,
                        mode='markers',
                        name=f'S{i+1}',
                        marker=dict(
                            size=10,
                            color=self.section_colors[i],
                            opacity=0.8,
                            symbol='square',
                            line=dict(color='black', width=1)
                        )
                    ))
                    
                    # Add error bars if enabled
                    if show_error_bars:
                        for h, g, v, s in zip(section_hours, section_grays, section_values, section_stds):
                            fig3d.add_trace(go.Scatter3d(
                                x=[h, h],
                                y=[g, g],
                                z=[v-s, v+s],
                                mode='lines',
                                line=dict(color='red', width=2),
                                showlegend=False
                            ))
            else:
                # Add scatter3d trace for all points (to keep the individual points visible)
                for i in range(6):
                    # Filter data for this section
                    section_hours = [h for h, s in zip(all_hours, all_sections) if s == i+1]
                    section_grays = [g for g, s in zip(all_grays, all_sections) if s == i+1]
                    section_values = [v for v, s in zip(all_values, all_sections) if s == i+1]
                    section_stds = [s for s, sec in zip(all_stds, all_sections) if sec == i+1]
                    
                    if not section_hours:
                        continue
                    
                    # Add scatter3d trace for this section
                    fig3d.add_trace(go.Scatter3d(
                        x=section_hours,
                        y=section_grays,
                        z=section_values,
                        mode='markers',
                        name=f'S{i+1}',
                        marker=dict(
                            size=5,
                            color=self.section_colors[i],
                            opacity=0.8
                        )
                    ))
                    
                    # Add error bars if enabled
                    if show_error_bars:
                        for h, g, v, s in zip(section_hours, section_grays, section_values, section_stds):
                            fig3d.add_trace(go.Scatter3d(
                                x=[h, h],
                                y=[g, g],
                                z=[v-s, v+s],
                                mode='lines',
                                line=dict(color='red', width=2),
                                showlegend=False
                            ))
                    
                    # Create a surface for this section if we have enough points
                    if len(section_hours) > 3:
                        # Create a grid of x and y values
                        unique_hours = sorted(list(set(section_hours)))
                        unique_grays = sorted(list(set(section_grays)))
                        
                        if len(unique_hours) > 1 and len(unique_grays) > 1:
                            # Create empty grid for z values
                            z_grid = np.zeros((len(unique_grays), len(unique_hours)))
                            z_grid[:] = np.nan  # Fill with NaN initially
                            
                            # Fill the grid with values
                            for h, g, v in zip(section_hours, section_grays, section_values):
                                h_idx = unique_hours.index(h)
                                g_idx = unique_grays.index(g)
                                z_grid[g_idx, h_idx] = v
                            
                            # Interpolate missing values (if any)
                            # Simple linear interpolation along rows and columns
                            for i_row in range(z_grid.shape[0]):
                                row = z_grid[i_row, :]
                                mask = ~np.isnan(row)
                                if np.any(mask) and not np.all(mask):  # If row has some values but not all
                                    indices = np.arange(len(row))
                                    valid_indices = indices[mask]
                                    valid_values = row[mask]
                                    # Interpolate missing values
                                    z_grid[i_row, :] = np.interp(indices, valid_indices, valid_values)
                            
                            for j_col in range(z_grid.shape[1]):
                                col = z_grid[:, j_col]
                                mask = ~np.isnan(col)
                                if np.any(mask) and not np.all(mask):  # If column has some values but not all
                                    indices = np.arange(len(col))
                                    valid_indices = indices[mask]
                                    valid_values = col[mask]
                                    # Interpolate missing values
                                    z_grid[:, j_col] = np.interp(indices, valid_indices, valid_values)
                            
                            # Add surface
                            fig3d.add_trace(go.Surface(
                                z=z_grid,
                                x=unique_hours,
                                y=unique_grays,
                                colorscale=[[0, self.section_colors[i]], [1, self.section_colors[i]]],
                                opacity=0.7,
                                name=f'S{i+1} Surface',
                                showscale=False
                            ))
            
            # Update layout
            title_suffix = " (% change from initial value)" if use_percentage else ""
            neg_ctrl_text = " (with Neg Ctrl Subtracted)" if subtract_neg_ctrl else ""
            chart_type = "3D Bar Chart" if use_bar_chart else "3D Surface"
            error_text = " with Error Bars" if show_error_bars else ""
            
            fig3d.update_layout(
                title=f"3D View: {key}{title_suffix}{neg_ctrl_text} - {chart_type}{error_text}",
                scene=dict(
                    xaxis_title='Hours',
                    yaxis_title='Grays',
                    zaxis_title='Value' + (" (%)" if use_percentage else "")
                ),
                height=600,
                width=900,
                autosize=True
            )
            
            # Add to figures3D
            figures3D[key] = fig3d

        # Add each 3D figure as JSON
        for key, fig3d in figures3D.items():
            fig3d_json = fig3d.to_json()
            html_content += f'figures3D["{key}"] = {fig3d_json};\n'

        html_content += """
        // Function to show the selected plot
        function showPlot(key) {
            // Get active tab
            const activeTab = document.querySelector('.tablinks.active');
            const tabName = activeTab.textContent.trim();
            
            if (tabName === '2D View') {
                // Show 2D plot
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
                
                Plotly.react('plot-container-2d', currentFigure.data, currentFigure.layout);
            } else {
                // Show 3D plot
                const currentFigure = JSON.parse(JSON.stringify(figures3D[key]));
                
                // Make sure the layout is responsive
                currentFigure.layout.autosize = true;
                
                Plotly.react('plot-container-3d', currentFigure.data, currentFigure.layout);
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
            
            if (tabName === '2D View') {
                Plotly.downloadImage('plot-container-2d', {
                    format: 'png',
                    filename: currentKey + '_2D',
                    width: 1200,
                    height: 800
                });
            } else {
                Plotly.downloadImage('plot-container-3d', {
                    format: 'png',
                    filename: currentKey + '_3D',
                    width: 1200,
                    height: 800
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
        
        // Show the first plot by default
        showPlot(document.getElementById('plot-selector').value);
    </script>
</body>
</html>
"""

        # Save the HTML file
        html_path = os.path.join(out_dir, "all_plots.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Open the HTML file in the default browser
        webbrowser.open('file://' + os.path.abspath(html_path))

        # Notify user (in textbox)
        self.result_box.delete('1.0', ctk.END)
        mode_text = "percentage change" if use_percentage else "absolute values"
        chart_type = "bar charts" if use_bar_chart else "line charts"
        error_bars = "with error bars" if show_error_bars else "without error bars"
        neg_ctrl_text = "with negative controls subtracted" if subtract_neg_ctrl else "without negative control subtraction"

        self.result_box.insert(ctk.END, f"Results saved to {out_dir}/all_results.xlsx (showing {mode_text})\n")
        self.result_box.insert(ctk.END, f"Plots saved to {html_path} and opened in browser ({chart_type} {error_bars}, {neg_ctrl_text})\n")
        self.result_box.insert(ctk.END, f"3D plots added with Gray values as the third dimension\n")
        self.result_box.insert(ctk.END, f"Log scale option added to the plot interface\n")
        self.result_box.insert(ctk.END, f"Plots are responsive and will adjust to window size\n")

    def copy_to_assay(self, target_assay):
        # Copy current mask to all plates with the same assay
        current_mask = self.mask_map[self.selected_key].copy()
        current_neg_ctrl_mask = self.neg_ctrl_mask_map[self.selected_key].copy()
        
        for key in self.keys:
            _, assay = key.split("_")
            if assay == target_assay:
                self.mask_map[key] = current_mask.copy()
                self.neg_ctrl_mask_map[key] = current_neg_ctrl_mask.copy()
        
        # Refresh if viewing same assay
        if self.selected_key.split("_")[1] == target_assay:
            self.build_grid()
        
        # Save masks to CSV after copying
        self.save_masks_to_csv()
        self.save_neg_ctrl_masks_to_csv()

    def save_masks_to_csv(self):
        """Save all masks to a CSV file"""
        try:
            with open(self.mask_file, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(['plate_assay', 'row', 'col', 'value'])
                
                # Write each mask
                for key, mask in self.mask_map.items():
                    for i in range(8):
                        for j in range(12):
                            writer.writerow([key, i, j, mask[i, j]])
            
            print(f"Masks saved to {self.mask_file}")
        except Exception as e:
            print(f"Error saving masks: {e}")

    def save_neg_ctrl_masks_to_csv(self):
        """Save all negative control masks to a CSV file"""
        try:
            with open(self.neg_ctrl_mask_file, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(['plate_assay', 'row', 'col', 'value'])
                
                # Write each mask
                for key, mask in self.neg_ctrl_mask_map.items():
                    for i in range(8):
                        for j in range(12):
                            writer.writerow([key, i, j, mask[i, j]])
            
            print(f"Negative control masks saved to {self.neg_ctrl_mask_file}")
        except Exception as e:
            print(f"Error saving negative control masks: {e}")

    def load_masks_from_csv(self):
        """Load masks from CSV if the file exists"""
        if not os.path.exists(self.mask_file):
            print(f"Mask file {self.mask_file} not found. Using default masks.")
            return
            
        try:
            # Read the CSV file
            df = pd.read_csv(self.mask_file)
            
            # Group by plate_assay
            for key, group in df.groupby('plate_assay'):
                # Skip if key is not in our current keys
                if key not in self.mask_map:
                    continue
                    
                # Initialize a new mask
                mask = np.ones((8, 12), dtype=float)
                
                # Fill in the mask values
                for _, row in group.iterrows():
                    i, j = int(row['row']), int(row['col'])
                    mask[i, j] = row['value']
                
                # Update the mask map
                self.mask_map[key] = mask
                
            print(f"Masks loaded from {self.mask_file}")
        except Exception as e:
            print(f"Error loading masks: {e}")

    def load_neg_ctrl_masks_from_csv(self):
        """Load negative control masks from CSV if the file exists"""
        if not os.path.exists(self.neg_ctrl_mask_file):
            print(f"Negative control mask file {self.neg_ctrl_mask_file} not found. Using default masks.")
            return
            
        try:
            # Read the CSV file
            df = pd.read_csv(self.neg_ctrl_mask_file)
            
            # Group by plate_assay
            for key, group in df.groupby('plate_assay'):
                # Skip if key is not in our current keys
                if key not in self.neg_ctrl_mask_map:
                    continue
                    
                # Initialize a new mask
                mask = np.zeros((8, 12), dtype=float)
                
                # Fill in the mask values
                for _, row in group.iterrows():
                    i, j = int(row['row']), int(row['col'])
                    mask[i, j] = row['value']
                
                # Update the mask map
                self.neg_ctrl_mask_map[key] = mask
                
            print(f"Negative control masks loaded from {self.neg_ctrl_mask_file}")
        except Exception as e:
            print(f"Error loading negative control masks: {e}")

    def save_section_grays(self):
        """Save the current gray values for the selected plate-assay"""
        try:
            # Get values from entries
            gray_values = []
            for entry in self.gray_entries:
                try:
                    value = float(entry.get())
                except ValueError:
                    value = 0
                gray_values.append(value)
            
            # Update the gray values for the current plate-assay
            self.section_grays[self.selected_key] = gray_values
            
            # Save to CSV
            self.save_grays_to_csv()
            
            # Show confirmation
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, f"Gray values saved for {self.selected_key}\n")
            for i, value in enumerate(gray_values):
                self.result_box.insert(ctk.END, f"Section {i+1}: {value} Grays\n")
        except Exception as e:
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, f"Error saving gray values: {e}\n")

    def copy_grays_to_all_plates(self):
        """Copy the current gray values to all plates"""
        try:
            # Get values from entries
            gray_values = []
            for entry in self.gray_entries:
                try:
                    value = float(entry.get())
                except ValueError:
                    value = 0
                gray_values.append(value)
            
            # Update all plates with these values
            for key in self.keys:
                self.section_grays[key] = gray_values.copy()
            
            # Save to CSV
            self.save_grays_to_csv()
            
            # Show confirmation
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, "Gray values copied to all plates\n")
            for i, value in enumerate(gray_values):
                self.result_box.insert(ctk.END, f"Section {i+1}: {value} Grays\n")
        except Exception as e:
            self.result_box.delete('1.0', ctk.END)
            self.result_box.insert(ctk.END, f"Error copying gray values: {e}\n")

    def save_grays_to_csv(self):
        """Save all gray values to a CSV file"""
        try:
            with open(self.gray_file, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(['plate_assay', 'section', 'gray_value'])
            
                # Write each gray value
                for key, values in self.section_grays.items():
                    for i, value in enumerate(values):
                        writer.writerow([key, i+1, value])
        
            print(f"Gray values saved to {self.gray_file}")
        except Exception as e:
            print(f"Error saving gray values: {e}")

    def load_grays_from_csv(self):
        """Load gray values from CSV if the file exists"""
        if not os.path.exists(self.gray_file):
            print(f"Gray file {self.gray_file} not found. Using default values.")
            return
        
        try:
            # Read the CSV file
            df = pd.read_csv(self.gray_file)
        
            # Group by plate_assay
            for key, group in df.groupby('plate_assay'):
                # Skip if key is not in our current keys
                if key not in self.section_grays:
                    continue
                
                # Initialize a new array for gray values
                gray_values = [0, 0, 0, 0, 0, 0]
            
                # Fill in the gray values
                for _, row in group.iterrows():
                    section = int(row['section'])
                    if 1 <= section <= 6:
                        gray_values[section-1] = float(row['gray_value'])
            
                # Update the gray values
                self.section_grays[key] = gray_values
            
            print(f"Gray values loaded from {self.gray_file}")
        except Exception as e:
            print(f"Error loading gray values: {e}")

    def on_closing(self):
        """Handle window closing event"""
        # Save masks to CSV
        self.save_masks_to_csv()
        self.save_neg_ctrl_masks_to_csv()
        # Save gray values to CSV
        self.save_grays_to_csv()
        # Destroy the window
        self.destroy()
