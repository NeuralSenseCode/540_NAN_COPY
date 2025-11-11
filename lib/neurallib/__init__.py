"""
NeuralLib - A custom library for neural and behavioral data analysis.

This package provides tools for processing and analyzing data from:
- iMotions sensor data
- Tobii eye tracking
- GSR (Galvanic Skin Response)
- ET (Eye Tracking)
- IAT (Implicit Association Test)
- FAM (Familiarity) measures

Modules:
- clean: Data cleaning and preprocessing utilities
- extract: Data extraction functions
- plot: Visualization and plotting functions
- stats: Statistical analysis tools
- imotionstools: iMotions-specific utilities
- tobiitools: Tobii eye tracker utilities
- batch: Batch processing functions
- signal_processing: Signal processing utilities
- project_management: Project organization tools
"""

__version__ = "0.1.0"

# Import main modules for easy access
from . import clean
from . import extract
from . import plot
from . import stats
from . import imotionstools
from . import tobiitools
from . import batch
from . import signal_processing
from . import project_management

__all__ = [
    'clean',
    'extract',
    'plot',
    'stats',
    'imotionstools',
    'tobiitools',
    'batch',
    'signal_processing',
    'project_management',
]
