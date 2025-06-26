"""
Configuration module for the Plates Analyzer application.
Handles loading and saving of all application settings.
"""
import os
import json
import numpy as np
import pandas as pd

class Config:
    """Class to manage application configuration."""
    
    def __init__(self):
        """Initialize configuration with default values."""
        self.config_file = "plates_analyzer_config.json"
        self.masks = {}
        self.neg_ctrl_masks = {}
        self.section_grays = {}
        self.recent_files = []
        self.max_recent_files = 5
        self.default_directory = ""
        self.section_units = "grays"  # Default section units
        self.auto_exclude_orphaned = True  # Auto-exclude wells not in any section
        self.sections = []  # Store the most recently used sections
        
    def save(self):
        """Save configuration to file."""
        config_data = {
            "recent_files": self.recent_files,
            "default_directory": self.default_directory,
            "masks": self._convert_masks_to_dict(self.masks),
            "neg_ctrl_masks": self._convert_masks_to_dict(self.neg_ctrl_masks),
            "section_grays": self.section_grays,
            "section_units": self.section_units,
            "auto_exclude_orphaned": self.auto_exclude_orphaned,
            "sections": self.sections  # Save sections to config
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load(self):
        """Load configuration from file."""
        if not os.path.exists(self.config_file):
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            self.recent_files = config_data.get("recent_files", [])
            self.default_directory = config_data.get("default_directory", "")
            self.masks = self._convert_dict_to_masks(config_data.get("masks", {}))
            self.neg_ctrl_masks = self._convert_dict_to_masks(config_data.get("neg_ctrl_masks", {}))
            self.section_grays = config_data.get("section_grays", {})
            self.section_units = config_data.get("section_units", "grays")
            self.auto_exclude_orphaned = config_data.get("auto_exclude_orphaned", True)
            self.sections = config_data.get("sections", [])  # Load sections from config
            
            return True
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def add_recent_file(self, file_path):
        """Add a file to recent files list."""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        self.recent_files.insert(0, file_path)
        
        # Keep only the most recent files
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
        
        self.save()
    
    def update_masks(self, key, mask):
        """Update mask for a specific key."""
        self.masks[key] = mask.copy()
        self.save()
    
    def update_neg_ctrl_masks(self, key, mask):
        """Update negative control mask for a specific key."""
        self.neg_ctrl_masks[key] = mask.copy()
        self.save()
    
    def update_section_grays(self, key, grays):
        """Update section grays for a specific key."""
        self.section_grays[key] = grays.copy()
        self.save()
    
    def update_sections(self, sections):
        """Update the sections configuration."""
        self.sections = sections
        self.save()
    
    def _convert_masks_to_dict(self, masks_dict):
        """Convert numpy arrays to lists for JSON serialization."""
        result = {}
        for key, mask in masks_dict.items():
            result[key] = mask.tolist()
        return result
    
    def _convert_dict_to_masks(self, dict_data):
        """Convert lists back to numpy arrays."""
        result = {}
        for key, data in dict_data.items():
            result[key] = np.array(data)
        return result
