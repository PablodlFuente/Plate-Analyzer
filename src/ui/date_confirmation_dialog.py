import os
import re
import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox

class DateConfirmationDialog(ctk.CTkToplevel):
    def __init__(self, master, file_paths):
        super().__init__(master)
        self.title("Confirm Dates for Files")
        self.geometry("700x500")
        self.grab_set() # Make dialog modal

        self.file_paths = file_paths
        self.confirmed_dates = {}
        self.entries = []

        self._create_widgets()

    def _create_widgets(self):
        # Frame for file list and entries
        scroll_frame = ctk.CTkScrollableFrame(self, width=650, height=350)
        scroll_frame.pack(pady=10)

        row_num = 0
        for f_path in self.file_paths:
            file_name = os.path.basename(f_path)
            detected_date = self._extract_date_from_filename(file_name)

            ctk.CTkLabel(scroll_frame, text=file_name, wraplength=300).grid(row=row_num, column=0, padx=5, pady=2, sticky="w")
            
            date_entry = ctk.CTkEntry(scroll_frame, width=150)
            date_entry.grid(row=row_num, column=1, padx=5, pady=2, sticky="ew")
            date_entry.insert(0, detected_date if detected_date else "YYYYMMDD")
            self.entries.append((f_path, date_entry))
            
            row_num += 1

        # OK/Cancel buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=10)

        self.ok_button = ctk.CTkButton(button_frame, text="OK", command=self._on_ok)
        self.ok_button.pack(side="left", padx=10)
        self.ok_button.configure(state="disabled") # Initially disabled

        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self._on_cancel)
        cancel_button.pack(side="left", padx=10)

        # Bind validation to entry changes
        for _, entry in self.entries:
            entry.bind("<KeyRelease>", self._validate_entries)
        self._validate_entries() # Initial validation

    def _extract_date_from_filename(self, filename):
        match = re.search(r'(\d{8})[^.]*\.xlsx$', filename)
        if match:
            date_str = match.group(1)
            try:
                datetime.strptime(date_str, '%Y%m%d')
                return date_str
            except ValueError:
                pass
        return ""

    def _validate_entries(self, event=None):
        all_valid = True
        for f_path, entry in self.entries:
            date_str = entry.get()
            try:
                datetime.strptime(date_str, '%Y%m%d')
                entry.configure(border_color="#90EE90") # Light green for valid
            except ValueError:
                all_valid = False
                entry.configure(border_color="#FF6347") # Tomato for invalid
        
        if all_valid:
            self.ok_button.configure(state="normal")
        else:
            self.ok_button.configure(state="disabled")

    def _on_ok(self):
        self.confirmed_dates = {f_path: entry.get() for f_path, entry in self.entries}
        self.destroy()

    def _on_cancel(self):
        self.confirmed_dates = {}
        self.destroy()

    def get_confirmed_dates(self):
        return self.confirmed_dates
