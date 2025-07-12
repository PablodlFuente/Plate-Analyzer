import customtkinter as ctk
import pandas as pd

class ConflictDialog(ctk.CTkToplevel):
    """Dialog to display conflicting records: DB vs Incoming."""

    def __init__(self, parent, db_conflicts_df, incoming_conflicts_df):
        super().__init__(parent)
        self.title("Database Conflicts Detected")
        self.geometry("1000x650")
        self.transient(parent)
        self.grab_set()

        self.result = None  # 'ignore' or 'replace'
        self.db_conflicts_df = db_conflicts_df.reset_index(drop=True)
        self.incoming_conflicts_df = incoming_conflicts_df.reset_index(drop=True)

        self._setup_widgets()
        self.wait_window()

    def _setup_widgets(self):
        """Create and arrange widgets showing both DB and incoming records."""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        label = ctk.CTkLabel(main_frame, text="Duplicate primary keys detected.", font=ctk.CTkFont(weight="bold"))
        label.pack(pady=(0, 10))

        lists_frame = ctk.CTkFrame(main_frame)
        lists_frame.pack(fill="both", expand=True)

        # Existing records textbox
        left_frame = ctk.CTkFrame(lists_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        left_label = ctk.CTkLabel(left_frame, text="Existing record(s) in DB")
        left_label.pack()
        db_text = ctk.CTkTextbox(left_frame, width=450, height=450)
        db_text.pack(fill="both", expand=True)
        db_text.insert("1.0", self.db_conflicts_df.to_string(index=False))
        db_text.configure(state="disabled")

        # Incoming records textbox
        right_frame = ctk.CTkFrame(lists_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)
        right_label = ctk.CTkLabel(right_frame, text="Incoming record(s) from file")
        right_label.pack()
        inc_text = ctk.CTkTextbox(right_frame, width=450, height=450)
        inc_text.pack(fill="both", expand=True)
        inc_text.insert("1.0", self.incoming_conflicts_df.to_string(index=False))
        inc_text.configure(state="disabled")

        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=(10, 0), fill="x")

        info_label = ctk.CTkLabel(button_frame, text="Replace existing records with incoming ones?")
        info_label.pack(side="left", padx=10)

        ignore_button = ctk.CTkButton(button_frame, text="Ignore", command=self._on_ignore)
        ignore_button.pack(side="right", padx=5)

        replace_button = ctk.CTkButton(button_frame, text="Replace", command=self._on_replace)
        replace_button.pack(side="right", padx=5)

    def _on_ignore(self):
        """Set result to 'ignore' and close the dialog."""
        self.result = 'ignore'
        self.destroy()

    def _on_replace(self):
        """Set result to 'replace' and close the dialog."""
        self.result = 'replace'
        self.destroy()
