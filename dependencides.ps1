<#
.SYNOPSIS
Installs dependencies for the JSON job viewer application.
#>

# Check Python installation
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found. Install Python from https://www.python.org/ first."
    exit 1
}

# Install required packages
pip install PyQt6          # GUI framework
pip install pandas         # JSON/data handling

Write-Output "Dependencies installed successfully."