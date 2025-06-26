"""
Core functionality package for plate analysis.
"""
from .data import PlateData, parse_spectro_excel
from .analysis import analyze_plate, analyze_all_plates

__all__ = ['PlateData', 'parse_spectro_excel', 'analyze_plate', 'analyze_all_plates']
