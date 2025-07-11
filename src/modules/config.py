"""
Configuration module for the Plates Analyzer application.
Handles loading and saving of all application settings.
"""
import os
import json
import numpy as np
from platformdirs import user_config_dir

class Config:
    """Class to manage application configuration."""
    
    def __init__(self):
        """Initialize configuration with default values."""
        config_dir = user_config_dir("PlateAnalyzer", "CMAM") 
        os.makedirs(config_dir, exist_ok=True)
        self.config_file = os.path.join(config_dir, "plates_analyzer_config.json")
        self.masks = {}
        self.neg_ctrl_masks = {}
        self.section_grays = {}
        self.recent_files = []
        self.max_recent_files = 5
        self.default_directory = ""
        self.section_units = "grays"  # Default section units
        self.auto_exclude_orphaned = True  # Auto-exclude wells not in any section
        self.sections = []  # Store the most recently used sections
        self.log_level = "INFO"  # Default log level
        self._dirty = False # Flag to indicate if configuration needs saving
        
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
            "sections": self.sections,  # Save sections to config
            "log_level": self.log_level
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except IOError as e:
            import logging
            logging.getLogger('plate_analyzer').error(f"Error saving configuration to {self.config_file}: {e}")
    
    def load(self):
        """Load configuration from file."""
        if not os.path.exists(self.config_file):
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            recent_files = config_data.get("recent_files", [])
            if isinstance(recent_files, list):
                self.recent_files = recent_files
            else:
                self.recent_files = []

            default_directory = config_data.get("default_directory", "")
            if isinstance(default_directory, str):
                self.default_directory = default_directory
            else:
                self.default_directory = ""

            masks = config_data.get("masks", {})
            if isinstance(masks, dict):
                self.masks = self._convert_dict_to_masks(masks)
            else:
                self.masks = {}

            neg_ctrl_masks = config_data.get("neg_ctrl_masks", {})
            if isinstance(neg_ctrl_masks, dict):
                self.neg_ctrl_masks = self._convert_dict_to_masks(neg_ctrl_masks)
            else:
                self.neg_ctrl_masks = {}

            section_grays = config_data.get("section_grays", {})
            if isinstance(section_grays, dict):
                self.section_grays = section_grays
            else:
                self.section_grays = {}

            section_units = config_data.get("section_units", "grays")
            if isinstance(section_units, str):
                self.section_units = section_units
            else:
                self.section_units = "grays"

            auto_exclude_orphaned = config_data.get("auto_exclude_orphaned", True)
            if isinstance(auto_exclude_orphaned, bool):
                self.auto_exclude_orphaned = auto_exclude_orphaned
            else:
                self.auto_exclude_orphaned = True

            sections = config_data.get("sections", [])
            if isinstance(sections, list):
                self.sections = sections
            else:
                self.sections = []

            log_level = config_data.get("log_level", "INFO")
            if isinstance(log_level, str):
                self.log_level = log_level
            else:
                self.log_level = "INFO"
            
            return True
        except Exception as e:
            import logging
            logging.getLogger('plate_analyzer').error(f"Error loading configuration: {e}")
            return False
    
    def add_recent_file(self, file_path):
        """Add a file to recent files list."""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        self.recent_files.insert(0, file_path)
        
        # Keep only the most recent files
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
        
        self._dirty = True
    
    def update_masks(self, key, mask):
        """Update mask for a specific key."""
        self.masks[key] = mask.copy()
        self._dirty = True
    
    def update_neg_ctrl_masks(self, key, mask):
        """Update negative control mask for a specific key."""
        self.neg_ctrl_masks[key] = mask.copy()
        self._dirty = True
    
    def update_section_grays(self, key, grays):
        """Update section grays for a specific key."""
        self.section_grays[key] = grays.copy()
        self._dirty = True
    
    def update_sections(self, sections):
        """Update the sections configuration."""
        self.sections = sections
        self._dirty = True
    
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

    def save_if_dirty(self):
        """Save configuration if there are pending changes."""
        if self._dirty:
            self.save()
            self._dirty = False
