# 540_NAN_COPY - Nandos Neural Data Analysis Project

A comprehensive data analysis project for processing and analyzing neural sensor data, eye tracking, and behavioral metrics collected from Nandos consumer research study.

## Project Overview

This project processes multi-modal data including:
- **iMotions sensor data** - Physiological responses (GSR, heart rate)
- **Eye tracking data** (ET) - Gaze patterns and fixations from Tobii devices
- **Implicit Association Tests** (IAT) - Cognitive associations
- **Familiarity measures** (FAM) - Brand and product familiarity ratings
- **Survey data** - Self-reported measures and demographics

The analysis pipeline extracts features, performs statistical analyses, and generates visualizations to understand consumer responses to marketing stimuli.

## Directory Structure

```
540_NAN_COPY/
├── data/                          # Raw and processed data files
│   └── infiles/                   # Input data organized by type
│       ├── ET/                    # Eye tracking data
│       ├── GSR/                   # Galvanic skin response data
│       ├── IAT/                   # Implicit association test data
│       ├── FAM/                   # Familiarity measure data
│       ├── Sensors/               # iMotions sensor data files
│       └── Keys/                  # Lookup tables and ID mappings
├── analysis/                      # Analysis scripts and notebooks
│   ├── assembly.py                # Data assembly and merging pipeline
│   ├── data_preparation.ipynb     # Data cleaning and preparation
│   └── data_analysis.ipynb        # Statistical analysis and visualization
├── results/                       # Generated outputs and reports
│   ├── specific/                  # Task-specific analysis results
│   └── *.csv                      # Merged and processed datasets
├── lib/                           # Vendorized custom libraries
│   └── neurallib/                 # Custom neural data analysis toolkit
│       ├── clean.py               # Data cleaning utilities
│       ├── extract.py             # Feature extraction functions
│       ├── plot.py                # Visualization tools
│       ├── stats.py               # Statistical analysis functions
│       ├── imotionstools.py       # iMotions-specific utilities
│       ├── tobiitools.py          # Tobii eye tracking tools
│       ├── batch.py               # Batch processing utilities
│       ├── signal_processing.py   # Signal processing functions
│       └── project_management.py  # Project organization tools
├── requirements.txt               # Python package dependencies
├── setup.sh                       # Unix/macOS setup script
├── setup.bat                      # Windows setup script
├── test_setup.py                  # Setup validation script
└── validate_deployment.py         # Deployment readiness checker
```

## Quick Start

### Prerequisites
- Python 3.8 or later
- 2GB+ free disk space
- Virtual environment support

### Installation

**Windows:**
```powershell
.\setup.bat
```

**Unix/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Create a virtual environment (`.venv`)
2. Install all required dependencies
3. Run validation tests
4. Report any issues

### Manual Setup
See [SETUP.md](SETUP.md) for detailed manual installation instructions.

## Usage

### Activate Environment

**Windows:**
```powershell
.venv\Scripts\activate
```

**Unix/macOS:**
```bash
source .venv/bin/activate
```

### Run Analysis Pipeline

1. **Data Preparation** - Open and run `analysis/data_preparation.ipynb`
   - Loads raw data files
   - Cleans and normalizes data
   - Merges data sources
   - Outputs prepared datasets to `results/`

2. **Data Assembly** - Run the assembly script:
   ```bash
   python analysis/assembly.py
   ```
   - Processes sensor data
   - Extracts task-specific metrics
   - Aligns timing across data sources
   - Generates merged output files

3. **Statistical Analysis** - Open and run `analysis/data_analysis.ipynb`
   - Performs statistical tests
   - Generates visualizations
   - Produces final reports

## Key Features

### Data Processing
- Multi-modal data integration
- Automated timestamp alignment
- AOI (Area of Interest) analysis
- Fixation and gaze metric extraction
- GSR signal processing

### Statistical Analysis
- Mixed-effects models
- ANOVA and post-hoc tests
- Bootstrap resampling
- Cohen's d effect sizes
- Repeated measures analysis

### Visualization
- Time-series plots
- Heatmaps and fixation plots
- Statistical comparison charts
- Custom styling with brand colors

## Neurallib Package

The `lib/neurallib` package is a vendorized custom library providing specialized tools for neural and behavioral data analysis. It includes:

- **clean.py** - Data cleaning, filtering, and preprocessing
- **extract.py** - Feature extraction from sensor data
- **plot.py** - Publication-ready visualizations
- **stats.py** - Statistical testing and effect size calculations
- **imotionstools.py** - iMotions file parsing and processing
- **tobiitools.py** - Tobii eye tracker data handling

See [lib/README.md](lib/README.md) for detailed package documentation.

## Validation

Run validation checks to ensure project integrity:

```bash
python validate_deployment.py
```

This checks:
- File structure completeness
- Package imports
- Data directory contents
- Script path configurations
- Git repository status

## Troubleshooting

### Import Errors
If you encounter import errors with neurallib:
- Ensure the virtual environment is activated
- Verify the lib/ directory exists
- Check that analysis scripts have the PROJECT_ROOT configuration

### Missing Data Files
- Verify all data files are in `data/infiles/` subdirectories
- Check file naming conventions match expected patterns
- Ensure key mapping files exist in `data/infiles/Keys/`

### Package Installation Issues
- Update pip: `python -m pip install --upgrade pip`
- Install packages individually to identify conflicts
- Check Python version compatibility (requires 3.8+)

For more troubleshooting help, see [SETUP.md](SETUP.md#troubleshooting).

## Project Status

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for:
- Current completion status
- Known issues and limitations
- Planned enhancements
- Version history

## Deployment

For deployment to production environments, see [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Pre-deployment checklist
- Environment configuration
- Security considerations
- Performance optimization

## Contributing

This is a research analysis project. For modifications:
1. Create a new branch for changes
2. Test changes with validation scripts
3. Update documentation as needed
4. Maintain reproducibility of results

## License

Internal research project. Contact project owner for usage permissions.

## Contact

For questions or issues:
- Project: 540_NAN_COPY
- Client: Nandos
- Analysis Framework: NeuralSense

---

**Last Updated:** 2025-01-11
