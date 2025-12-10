# Installation Guide

Complete installation instructions for No-Driver GPM Package.

## System Requirements

### Operating System
- **Windows 10/11** (Required)
- Linux/macOS not supported (due to win32 dependencies)

### Python
- **Python 3.8+** (Required)
- Python 3.10+ recommended

### External Requirements
- **GPM (Gologin Profile Manager)** running locally
- Default URL: `http://127.0.0.1:12003`

## Installation Methods

### Method 1: Development Installation (Recommended for Local Use)

Install in editable mode for development:

```bash
# Navigate to package directory
cd nodrive_gpm_package

# Install in editable mode
pip install -e .
```

This allows you to modify the source code and see changes immediately.

### Method 2: Standard Installation

Install as a regular package:

```bash
cd nodrive_gpm_package
pip install .
```

### Method 3: From PyPI (When Published)

```bash
pip install nodrive-gpm-package
```

### Method 4: With Development Dependencies

For contributors:

```bash
pip install -e ".[dev]"
```

This installs additional tools:
- pytest (testing)
- black (code formatting)
- mypy (type checking)
- ruff (linting)

## Verify Installation

### Check Package Installation

```python
python -c "import nodrive_gpm_package; print(nodrive_gpm_package.__version__)"
```

Expected output: `1.0.0`

### Check Dependencies

```python
python -c "import nodriver, requests, psutil, pydantic; print('All dependencies OK')"
```

### Run Test Script

Create `test_install.py`:

```python
from nodrive_gpm_package import GPMClient, GPMConfig

print("✅ Import successful!")
print(f"Default API URL: {GPMConfig().gpm_api_base_url}")
```

Run it:

```bash
python test_install.py
```

## Dependencies

### Core Dependencies (Installed Automatically)

```
nodriver>=0.28          # Browser automation
requests>=2.31.0        # HTTP client
psutil>=5.9.0          # Process management
pywin32>=306           # Windows API
pydantic>=2.0.0        # Data validation
pydantic-settings>=2.0.0  # Config management
python-dotenv>=1.0.0   # Environment variables
```

### Optional Dependencies

```
PySocks>=1.7.1         # SOCKS proxy support
```

Install optional dependencies:

```bash
pip install PySocks
```

## Configuration Setup

### Step 1: Create .env File

Copy the example:

```bash
# On Windows
copy env.example .env

# On Unix-like systems
cp env.example .env
```

### Step 2: Edit Configuration

Open `.env` and customize:

```env
# Required: GPM API URL
GPM_API_BASE_URL=http://127.0.0.1:12003/api/v3

# Optional: Custom profiles directory
GPM_PROFILES_DIR=C:/Users/YourName/profiles

# Optional: Browser settings
BROWSER_WIDTH=1920
BROWSER_HEIGHT=1080
BROWSER_SCALE=0.8

# Optional: Debug mode
DEBUG=true
```

### Step 3: Test Configuration

```python
from nodrive_gpm_package import get_config

config = get_config()
print(f"API URL: {config.gpm_api_base_url}")
print(f"Profiles Dir: {config.profiles_directory}")
```

## Virtual Environment Setup (Recommended)

### Using venv

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Unix-like)
source venv/bin/activate

# Install package
cd nodrive_gpm_package
pip install -e .
```

### Using conda

```bash
# Create environment
conda create -n gpm python=3.10

# Activate
conda activate gpm

# Install package
cd nodrive_gpm_package
pip install -e .
```

## Troubleshooting Installation

### Issue 1: pip not found

**Solution:**
```bash
python -m pip install --upgrade pip
```

### Issue 2: Permission denied

**Solution (Windows):**
Run Command Prompt as Administrator

**Solution (Unix-like):**
```bash
pip install --user -e .
```

### Issue 3: pywin32 installation fails

**Solution:**
```bash
# Install pywin32 separately
pip install pywin32

# Then install package
pip install -e .
```

### Issue 4: Can't find package after install

**Solution:**
```bash
# Check if package is installed
pip list | grep nodrive-gpm

# If not found, reinstall
pip install -e . --force-reinstall
```

### Issue 5: Import errors

**Error:**
```
ModuleNotFoundError: No module named 'nodrive_gpm_package'
```

**Solution:**
```bash
# Verify you're in the right directory
cd nodrive_gpm_package

# Check current directory
pwd  # or dir on Windows

# Should see: setup.py, pyproject.toml, etc.

# Reinstall
pip install -e .
```

## Updating the Package

### Update from source

```bash
cd nodrive_gpm_package
git pull  # If using git
pip install -e . --upgrade
```

### Update from PyPI (when published)

```bash
pip install --upgrade nodrive-gpm-package
```

## Uninstallation

```bash
pip uninstall nodrive-gpm-package
```

## Post-Installation

### 1. Verify GPM is Running

Open browser: `http://127.0.0.1:12003`

Should see GPM API interface.

### 2. Run Examples

```bash
cd nodrive_gpm_package
python examples/basic_usage.py
```

### 3. Read Documentation

- [README.md](../README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [examples/](examples/) - Code examples

## For Developers

### Clone and Install

```bash
# Clone repository
git clone https://github.com/Nam-BackEnd-Bn/nodrive-gpm-package.git
cd nodrive-gpm-package

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Type check
mypy nodrive_gpm_package
```

### Development Workflow

1. Make changes to source code
2. Changes are immediately available (editable install)
3. Run examples to test
4. Format with black
5. Check types with mypy
6. Run tests with pytest

## Platform-Specific Notes

### Windows

- Requires Windows 10/11
- pywin32 is required (installed automatically)
- GPM must be running on Windows

### Linux/macOS

Currently not supported due to:
- win32gui dependency
- Windows-specific process management
- GPM is Windows-only

## Support

### Documentation
- [README.md](../README.md)
- [QUICKSTART.md](QUICKSTART.md)
- [MIGRATION.md](MIGRATION.md)

### Issues
- GitHub Issues: Report bugs or request features

### Community
- GitHub Discussions: Ask questions

---

**Installation complete? Start with [QUICKSTART.md](QUICKSTART.md)!** 🚀
