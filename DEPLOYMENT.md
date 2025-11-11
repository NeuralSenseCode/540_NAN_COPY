# Deployment Readiness - 540_NAN_COPY Project

This document outlines the deployment checklist and requirements for the Nandos neural data analysis project.

## Pre-Deployment Checklist

Run through this checklist before considering the project deployment-ready:

### ✓ Environment Setup
- [ ] Virtual environment created and activated
- [ ] All dependencies installed from requirements.txt
- [ ] Python version 3.8+ verified
- [ ] test_setup.py passes all checks
- [ ] validate_deployment.py passes all checks

### ✓ Project Structure
- [ ] All required directories present (data/, analysis/, results/, lib/)
- [ ] Neurallib package properly vendorized in lib/
- [ ] Analysis scripts have PROJECT_ROOT configuration
- [ ] .gitignore excludes virtual environment and outputs
- [ ] No sensitive data in repository

### ✓ Documentation
- [ ] README.md complete and accurate
- [ ] SETUP.md provides clear installation steps
- [ ] DEPLOYMENT.md (this file) reviewed
- [ ] PROJECT_STATUS.md reflects current state
- [ ] lib/README.md documents neurallib package

### ✓ Code Quality
- [ ] All imports resolve correctly
- [ ] No hard-coded absolute paths
- [ ] Relative paths used for data access
- [ ] Error handling implemented
- [ ] Logging/output messages are clear

### ✓ Data Integrity
- [ ] Raw data files present in data/infiles/
- [ ] Key/lookup files available
- [ ] Data file naming conventions consistent
- [ ] No corrupted or incomplete data files

### ✓ Functionality
- [ ] assembly.py runs without errors
- [ ] data_preparation.ipynb executes successfully
- [ ] data_analysis.ipynb produces expected outputs
- [ ] Results written to results/ directory
- [ ] Visualizations generate correctly

## Validation Commands

Run these commands to validate deployment readiness:

```bash
# Activate environment
source .venv/bin/activate  # Unix/macOS
# OR
.venv\Scripts\activate      # Windows

# Run validation
python validate_deployment.py

# Run setup tests
python test_setup.py

# Test main script
python analysis/assembly.py

# Test notebook execution (optional)
jupyter nbconvert --execute --to notebook \
    --inplace analysis/data_preparation.ipynb
```

## Deployment Scenarios

### Scenario 1: Local Workstation
**Use Case:** Individual analyst working on local machine

**Requirements:**
- Python 3.8+ installed
- 8GB RAM minimum
- 5GB disk space for data + outputs
- Git for version control

**Setup:**
1. Clone repository
2. Run setup script (setup.bat or setup.sh)
3. Verify with validation scripts
4. Begin analysis

**Considerations:**
- Virtual environment isolates dependencies
- Results saved locally
- No network requirements after setup

### Scenario 2: Shared Research Server
**Use Case:** Multiple analysts accessing shared data

**Requirements:**
- Python 3.8+ in shared location
- Shared data directory with read access
- Individual user directories for results
- Network file system

**Setup:**
1. Install Python to /opt/python or equivalent
2. Create shared virtual environment or per-user environments
3. Mount shared data directory (read-only)
4. Configure per-user results directories
5. Set environment variables for paths

**Considerations:**
- Use environment variables for data paths
- Implement file locking for concurrent access
- Version control for analysis code
- Centralized logging

### Scenario 3: Cloud/HPC Environment
**Use Case:** Large-scale processing, parallel execution

**Requirements:**
- Container support (Docker) or module system
- Batch job scheduling
- Distributed file system
- Scalable compute resources

**Setup:**
1. Create Docker container or Singularity image
2. Package dependencies with container
3. Submit jobs via scheduler (SLURM, PBS)
4. Configure distributed data access
5. Aggregate results from parallel jobs

**Considerations:**
- Containerization ensures reproducibility
- Parallel processing for multiple files
- Cloud storage for results (S3, Azure Blob)
- Resource quotas and limits

## Environment Variables

Configure these optional environment variables:

```bash
# Data directory (if not using default data/)
export NEURAL_DATA_DIR=/path/to/shared/data

# Results directory (if not using default results/)
export NEURAL_RESULTS_DIR=/path/to/user/results

# Temp directory for intermediate files
export NEURAL_TEMP_DIR=/tmp/neural_temp

# Python path (if neurallib not in lib/)
export PYTHONPATH=/path/to/custom/lib:$PYTHONPATH

# Number of parallel workers
export NEURAL_N_WORKERS=4

# Logging level (DEBUG, INFO, WARNING, ERROR)
export NEURAL_LOG_LEVEL=INFO
```

### Using Environment Variables in Code

```python
import os

# Get data directory with fallback
data_dir = os.getenv('NEURAL_DATA_DIR', '../data/infiles')

# Get results directory with fallback
results_dir = os.getenv('NEURAL_RESULTS_DIR', '../results')

# Get number of workers
n_workers = int(os.getenv('NEURAL_N_WORKERS', '1'))
```

## Security Considerations

### Data Privacy
- [ ] No personally identifiable information (PII) in code or docs
- [ ] Participant IDs anonymized (resp_id format)
- [ ] Raw data not committed to version control
- [ ] Results reviewed before sharing
- [ ] Access controls on data directories

### Code Security
- [ ] No passwords or API keys in code
- [ ] No hard-coded credentials
- [ ] Secure file permissions (read/write access controlled)
- [ ] Dependencies from trusted sources only
- [ ] Regular security updates for packages

### Compliance
- [ ] Research ethics approval documented
- [ ] Data usage agreement followed
- [ ] GDPR/privacy regulations complied with (if applicable)
- [ ] Data retention policies followed

## Performance Optimization

### Memory Management
```python
# Read data in chunks for large files
for chunk in pd.read_csv('large_file.csv', chunksize=10000):
    process(chunk)

# Clear memory after processing
import gc
gc.collect()

# Use appropriate dtypes
df = pd.read_csv('file.csv', dtype={
    'id': 'int32',
    'value': 'float32'
})
```

### Computation Optimization
```python
# Vectorize operations instead of loops
df['result'] = df['a'] * df['b']  # Fast
# NOT: df['result'] = df.apply(lambda x: x['a'] * x['b'], axis=1)

# Use query for filtering
df_filtered = df.query('value > 10 & category == "A"')

# Parallel processing
from multiprocessing import Pool
with Pool(4) as pool:
    results = pool.map(process_func, file_list)
```

### I/O Optimization
```python
# Use efficient file formats
df.to_parquet('output.parquet')  # Faster than CSV
df.to_pickle('output.pkl')       # Fastest for Python

# Compress large results
df.to_csv('output.csv.gz', compression='gzip')
```

## Backup and Recovery

### What to Backup
1. **Code:** All Python scripts and notebooks (via Git)
2. **Configuration:** requirements.txt, setup scripts, configs
3. **Raw Data:** Original input files (backup before processing)
4. **Results:** Key outputs and final reports
5. **Documentation:** All markdown files

### What NOT to Backup
- Virtual environment (.venv/)
- Temporary files and caches
- Intermediate processing files
- Log files (unless critical)
- Generated plots (can be regenerated)

### Backup Strategy
```bash
# Create backup archive
tar -czf backup_$(date +%Y%m%d).tar.gz \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='results/tmp' \
    .

# Or use Git
git add -A
git commit -m "Backup: $(date)"
git push origin main
```

## Rollback Procedures

If deployment issues occur:

### Quick Rollback
1. Deactivate environment: `deactivate`
2. Delete virtual environment: `rm -rf .venv`
3. Restore from backup: `tar -xzf backup_YYYYMMDD.tar.gz`
4. Re-run setup: `./setup.sh`

### Code Rollback (Git)
```bash
# View commit history
git log --oneline

# Rollback to specific commit
git checkout <commit-hash>

# Or revert last commit
git revert HEAD
```

## Monitoring and Logging

### Enable Logging in Scripts
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Processing started")
```

### Monitor Resource Usage
```bash
# CPU and memory usage
top -p $(pgrep -f python)

# Or use htop
htop -p $(pgrep -f python)

# Disk usage
du -sh results/
df -h
```

## Troubleshooting Deployment Issues

### Issue: Import Errors After Deployment

**Symptoms:** `ModuleNotFoundError` when running scripts

**Solutions:**
1. Verify virtual environment is activated
2. Check PYTHONPATH includes lib/
3. Reinstall requirements: `pip install -r requirements.txt`
4. Validate: `python test_setup.py`

### Issue: Path Not Found Errors

**Symptoms:** `FileNotFoundError` for data files

**Solutions:**
1. Use relative paths from PROJECT_ROOT
2. Set environment variables for data directories
3. Verify data files copied to deployment location
4. Check file permissions

### Issue: Memory Errors

**Symptoms:** `MemoryError` or system freezes

**Solutions:**
1. Process data in chunks
2. Close unused plots: `plt.close('all')`
3. Optimize data types (use int32 instead of int64)
4. Increase system swap space
5. Use batch processing with smaller datasets

### Issue: Performance Degradation

**Symptoms:** Slow processing, timeouts

**Solutions:**
1. Profile code: `python -m cProfile script.py`
2. Optimize bottlenecks
3. Use parallel processing
4. Cache intermediate results
5. Upgrade hardware resources

## Post-Deployment Verification

After deployment, verify:

```bash
# 1. Environment check
python --version
pip list | grep -E "pandas|numpy|scipy"

# 2. Functionality check
python test_setup.py
python validate_deployment.py

# 3. Sample execution
python analysis/assembly.py

# 4. Check outputs
ls -lh results/
```

Expected output:
- ✓ All validation tests pass
- ✓ Sample script completes successfully
- ✓ Results files created in results/
- ✓ No error messages or warnings

## Deployment Sign-Off

Before considering deployment complete:

**Completed By:** ________________  
**Date:** ________________  
**Environment:** [ ] Local [ ] Server [ ] Cloud  

**Checklist Status:**
- [ ] All validation scripts pass
- [ ] Documentation reviewed and accurate
- [ ] Sample analysis runs successfully
- [ ] Results verified for correctness
- [ ] Backup created
- [ ] Rollback procedure tested
- [ ] Performance acceptable
- [ ] Security review completed

**Notes:**
_____________________________________________
_____________________________________________
_____________________________________________

**Approved By:** ________________  
**Date:** ________________  

---

**Last Updated:** 2025-01-11
