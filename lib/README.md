# Neurallib - Neural Data Analysis Library

A custom Python library for processing and analyzing multi-modal neural and behavioral data, specifically designed for consumer neuroscience research.

## Overview

Neurallib is a vendorized package providing specialized tools for:
- iMotions sensor data processing
- Tobii eye tracking analysis
- Statistical testing and effect size calculations
- Publication-ready visualizations
- Signal processing and feature extraction
- Batch processing workflows

## Modules

### clean.py
**Data Cleaning and Preprocessing**

Core utilities for data manipulation and cleaning:

**Key Functions:**
- `read_imotions(path, metadata=None)` - Parse iMotions CSV files with metadata extraction
- `get_files(path, tags=[])` - Get file lists with filtering
- `drop_duplicates(lst)` - Remove duplicate entries from lists
- `flatten_list(nested_list)` - Flatten nested list structures
- `print_status(status, message)` - Formatted status messages
- `header(message)` - Print formatted section headers

**Data Operations:**
- Missing data handling
- Timestamp normalization
- Column renaming and standardization
- Data type conversions
- Filtering and masking

### extract.py
**Feature Extraction**

Extracts meaningful features from raw sensor data:

**Capabilities:**
- Time-domain features (mean, std, peaks)
- Frequency-domain features (FFT, power spectral density)
- Event detection (fixations, blinks, button presses)
- AOI (Area of Interest) metrics
- Response time calculations

### plot.py
**Visualization Tools**

Creates publication-quality visualizations:

**Plot Types:**
- Time series plots with multiple signals
- Bar charts with significance markers
- Heatmaps and correlation matrices
- Fixation plots overlaid on stimuli
- Word clouds for text data
- Box plots and violin plots

**Features:**
- Custom color schemes
- Automatic significance annotations
- LaTeX-style formatting
- Export to PNG/PDF with high DPI
- Consistent styling across plots

**Key Functions:**
- `time_proportions(input_folder, results_folder, tags)` - Plot time-based proportions
- `bar(out_path, data, ...)` - Create bar charts with error bars
- `get_significance_footnote(significance_df)` - Generate significance annotations

### stats.py
**Statistical Analysis**

Comprehensive statistical testing tools:

**Tests Supported:**
- Independent t-tests
- Paired t-tests
- One-way ANOVA
- Repeated measures ANOVA
- Mixed-effects models
- Post-hoc comparisons (Tukey, Bonferroni)
- Non-parametric tests (Mann-Whitney, Wilcoxon)

**Effect Sizes:**
- Cohen's d
- Hedges' g
- Eta-squared (η²)
- Partial eta-squared

**Key Functions:**
- `get_significance(stats_data, groups, label)` - Perform significance testing
- `get_significance_footnote(significance_df)` - Format results for plots
- `bootstrap_test(pre, post, n_bootstrap)` - Bootstrap resampling test

### imotionstools.py
**iMotions Specific Utilities**

Specialized tools for iMotions data:

**Features:**
- Metadata extraction from headers
- Stimulus-level data segmentation
- Event marker parsing
- GSR signal processing
- Heart rate variability analysis
- Response synchronization

**Classes:**
- `ImotionsProcessor` - Main processing class for sensor data
  - `load_data()` - Load and parse iMotions files
  - `extract_events()` - Extract event markers
  - `segment_by_stimulus()` - Split data by stimuli

**Functions:**
- `combine_key_file(df, key_path, on)` - Merge with key/lookup files
- `process_gsr(df, sampling_rate)` - GSR signal cleaning
- `extract_ecg_features(df)` - ECG feature extraction

### tobiitools.py
**Tobii Eye Tracking Tools**

Specialized for Tobii eye tracker data:

**Metrics:**
- Fixation duration and count
- Saccade velocity and amplitude
- AOI dwell time
- First fixation duration (FFD)
- Time to first fixation (TTFF)
- Total fixation duration (TFD)
- Gaze path analysis

**Functions:**
- `extract_tobii_data(path, task)` - Load and parse Tobii exports
- `calculate_aoi_metrics(df, aoi_definitions)` - Compute AOI metrics
- `fixation_heatmap(df, image_path)` - Generate fixation heatmaps

### batch.py
**Batch Processing**

Utilities for processing multiple files:

**Features:**
- Parallel processing support
- Progress tracking
- Error handling and logging
- Resume capability for interrupted jobs
- Batch statistics aggregation

**Functions:**
- `process_directory(input_path, output_path, processor_func)` - Process all files
- `parallel_process(files, func, n_workers)` - Multi-threaded processing

### signal_processing.py
**Signal Processing**

Signal analysis and filtering:

**Operations:**
- Butterworth filtering (lowpass, highpass, bandpass)
- Gaussian smoothing
- Artifact removal
- Downsampling and resampling
- Power spectral density analysis
- KNN imputation for missing values

**Functions:**
- `butter_filter(data, cutoff, fs, order, filter_type)` - Apply Butterworth filter
- `apply_bandpass(data, low, high, fs)` - Bandpass filter
- `psd_welch(signal, fs)` - Power spectral density estimation

### project_management.py
**Project Organization**

Tools for managing analysis projects:

**Features:**
- Project directory creation
- Configuration file handling
- Result archiving
- Metadata tracking
- Reproducibility logging

## Usage Examples

### Basic Data Loading

```python
import os
import sys

# Add library to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lib"))

from neurallib import clean, plot, stats

# Load iMotions data
df, metadata = clean.read_imotions('data/sensor_001.csv', 
                                   metadata=['Respondent Name', 'Study name'])
print(f"Loaded data for: {metadata['Respondent Name']}")
print(f"Shape: {df.shape}")
```

### AOI Analysis

```python
from neurallib import clean

# Load eye tracking data
df, _ = clean.read_imotions('data/et_001.csv')

# Extract AOI metrics
aoi_metrics = df.groupby('AOI').agg({
    'Fixation Index': 'count',
    'Fixation Duration': 'sum',
    'TTFF (AOI)': 'first'
})

print(aoi_metrics)
```

### Statistical Testing

```python
from neurallib import stats
import pandas as pd

# Prepare data
group_a = df[df['Group'] == 'A']['Metric'].values
group_b = df[df['Group'] == 'B']['Metric'].values

# Run t-test
results = stats.get_significance(
    {' A': group_a, 'B': group_b},
    ['A', 'B'],
    'Comparison AB'
)

print(f"p-value: {results['p_value'].values[0]:.4f}")
print(f"Cohen's d: {results['cohens_d'].values[0]:.4f}")
```

### Visualization

```python
from neurallib import plot
import pandas as pd

# Create bar chart with significance
data = pd.DataFrame({
    'Condition': ['A', 'B', 'C'],
    'Mean': [4.5, 5.2, 3.8],
    'SEM': [0.3, 0.4, 0.2]
})

plot.bar(
    'results/plots/',
    data,
    x='Condition',
    y='Mean',
    error='SEM',
    title='Condition Comparison',
    ylabel='Response Time (s)'
)
```

### Batch Processing

```python
from neurallib import batch, clean

def process_file(filepath):
    """Process a single sensor file."""
    df, metadata = clean.read_imotions(filepath)
    # ... processing logic ...
    return results

# Process all files in directory
results = batch.process_directory(
    'data/sensors/',
    'results/',
    process_file
)
```

## Dependencies

Neurallib relies on these packages (automatically installed with project):
- pandas, numpy - Data manipulation
- scipy - Scientific computing
- matplotlib, seaborn, plotly - Visualization
- pingouin, scikit-posthocs - Statistical testing
- PIL - Image processing
- wordcloud, nltk - Text analysis
- scikit-learn - Machine learning utilities

## Module Import Structure

All modules use relative imports internally for portability:

```python
# Inside neurallib modules
from .clean import *  # Import from same package
from . import plot     # Import module from same package
```

This allows the package to work when vendorized in `lib/`.

## Path Configuration

To use neurallib in analysis scripts, add this configuration at the top:

```python
import os
import sys

# Configure path to find vendorized neurallib
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lib"))

# Now you can import
from neurallib.clean import *
```

For Jupyter notebooks, use:

```python
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(
    os.path.abspath(__file__ if '__file__' in dir() else os.getcwd())
))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lib"))

from neurallib import clean, plot, stats
```

## Version

Current version: **0.1.0**

## Development Notes

### Adding New Modules

1. Create module file in `lib/neurallib/`
2. Use relative imports for internal dependencies
3. Add module to `__init__.py` imports
4. Document functions with docstrings
5. Add usage examples to this README

### Coding Standards

- PEP 8 style guide
- Docstrings for all public functions
- Type hints where appropriate
- Comprehensive error handling
- Unit tests for critical functions

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'neurallib'`:

1. Check that `lib/neurallib/` directory exists
2. Verify `__init__.py` is present
3. Ensure path configuration is at top of script
4. Confirm you're using the project's virtual environment

### Circular Import Issues

If modules have circular dependencies:
- Use relative imports (`. import module`)
- Import functions/classes, not entire modules with `*`
- Move shared utilities to `clean.py`

### Performance Issues

For large datasets:
- Use pandas `chunksize` parameter for incremental processing
- Enable low_memory mode: `pd.read_csv(..., low_memory=False)`
- Process files in parallel with `batch.parallel_process()`
- Close figures after saving to free memory: `plt.close()`

## Support

For neurallib-specific issues:
- Check function docstrings: `help(neurallib.clean.read_imotions)`
- Review module source code in `lib/neurallib/`
- Refer to main project documentation

---

**Package:** neurallib  
**Version:** 0.1.0  
**Last Updated:** 2025-01-11
