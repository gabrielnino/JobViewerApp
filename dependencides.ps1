<#
.SYNOPSIS
Robust dependency installer for Job Viewer application with enhanced error recovery.

.DESCRIPTION
This improved script:
1. Validates Python installation more thoroughly
2. Implements multi-stage package installation with retries
3. Provides detailed error reporting
4. Includes fallback installation methods
#>

# Configuration
$ErrorActionPreference = "Stop"
$MAX_RETRIES = 2
$PYTHON_MIN_VERSION = [version]"3.8.0"

# Colors for better visibility
$colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
    Progress = "Magenta"
}

function Write-Status {
    param($message, $color = "White")
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] " -NoNewline
    Write-Host $message -ForegroundColor $color
}

function Test-PythonVersion {
    try {
        $python = $null
        $commands = @("python", "python3", "py")

        foreach ($cmd in $commands) {
            if (Get-Command $cmd -ErrorAction SilentlyContinue) {
                $python = (Get-Command $cmd).Source
                break
            }
        }

        if (-not $python) {
            Write-Status "Python not found in PATH" $colors.Error
            return $null
        }

        $versionOutput = & $python --version 2>&1
        $versionString = $versionOutput -replace "[^0-9.]", ""
        $version = [version]$versionString

        if ($version -ge $PYTHON_MIN_VERSION) {
            Write-Status "Found Python $version" $colors.Success
            return $python
        } else {
            Write-Status "Python $version found but requires $PYTHON_MIN_VERSION+" $colors.Error
            return $null
        }
    } catch {
        Write-Status "Python version check failed: $_" $colors.Error
        return $null
    }
}

function Install-Package {
    param($python, $package, $retry = 0)

    try {
        Write-Status "Installing $package (attempt $($retry+1))..." $colors.Progress
        $installArgs = @(
            "-m", "pip", "install",
            "--upgrade",
            "--no-warn-script-location",
            "--disable-pip-version-check",
            $package
        )

        $process = Start-Process -FilePath $python -ArgumentList $installArgs -Wait -NoNewWindow -PassThru

        if ($process.ExitCode -ne 0) {
            throw "Exit code $($process.ExitCode)"
        }

        Write-Status "$package installed successfully" $colors.Success
        return $true
    } catch {
        if ($retry -lt $MAX_RETRIES) {
            Write-Status "Retrying $package..." $colors.Warning
            return Install-Package $python $package ($retry + 1)
        } else {
            Write-Status "Failed to install $package after $($retry+1) attempts" $colors.Error
            Write-Status "Error: $_" $colors.Error
            return $false
        }
    }
}

function Verify-Installation {
    param($python)

    $testScript = @"
import sys
try:
    from PySide6.QtCore import __version__ as qt_version
    print(f"SUCCESS: PySide6 {qt_version} installed")
    sys.exit(0)
except ImportError as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1)
"@

    $testPath = Join-Path $env:TEMP "verify_pyside6.py"
    $testScript | Out-File -FilePath $testPath -Encoding utf8

    try {
        $output = & $python $testPath 2>&1
        $exitCode = $LASTEXITCODE

        if ($exitCode -eq 0) {
            Write-Status $output $colors.Success
            return $true
        } else {
            Write-Status $output $colors.Error

            # Additional diagnostics
            Write-Status "Running diagnostics..." $colors.Warning
            $diagnostics = & $python -m pip show PySide6 2>&1
            Write-Status "Pip package info:`n$diagnostics" $colors.Info

            return $false
        }
    } finally {
        Remove-Item $testPath -Force -ErrorAction SilentlyContinue
    }
}

function Install-Dependencies {
    param($python)

    # Core packages with fallback options
    $packages = @(
        @{ Name = "PySide6"; Package = "PySide6==6.5.2" },
        @{ Name = "orjson"; Package = "orjson==3.9.0" },
        @{ Name = "psutil"; Package = "psutil==5.9.5" }
    )

    $success = $true
    foreach ($pkg in $packages) {
        if (-not (Install-Package $python $pkg.Package)) {
            Write-Status "Critical package $($pkg.Name) failed to install" $colors.Error
            $success = $false
        }
    }

    if (-not $success) {
        Write-Status "Attempting fallback installation..." $colors.Warning
        $fallback = Install-Package $python "PySide6"  # Try without version pin
        if (-not $fallback) {
            throw "Critical dependencies could not be installed"
        }
    }

    # Verify Qt installation
    if (-not (Verify-Installation $python)) {
        throw "PySide6 verification failed after installation"
    }
}

function Set-Optimizations {
    Write-Status "Configuring system optimizations..." $colors.Info

    $envVars = @{
        "QT_ENABLE_HIGHDPI_SCALING" = "1"
        "QT_SCALE_FACTOR_ROUNDING_POLICY" = "PassThrough"
        "QT_QUICK_BACKEND" = "software"
    }

    foreach ($var in $envVars.Keys) {
        [Environment]::SetEnvironmentVariable($var, $envVars[$var], "User")
        Write-Status "Set $var=$($envVars[$var])" $colors.Progress
    }

    Write-Status "Optimizations configured" $colors.Success
}

# Main execution
try {
    Write-Host "`nJob Viewer Dependency Installer (Enhanced)" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow

    # 1. Validate Python
    $python = Test-PythonVersion
    if (-not $python) {
        Write-Status "Please install Python 3.8+ from python.org" $colors.Error
        Write-Status "Ensure 'Add Python to PATH' is checked during installation" $colors.Warning
        exit 1
    }

    # 2. Upgrade pip first
    Write-Status "Upgrading pip..." $colors.Info
    $null = Install-Package $python "pip"

    # 3. Install core packages
    Install-Dependencies $python

    # 4. Apply optimizations
    Set-Optimizations

    Write-Status "`nInstallation completed successfully!" $colors.Success
    Write-Status "You can now run the Job Viewer application." $colors.Success

} catch {
    Write-Status "`nINSTALLATION FAILED: $_" $colors.Error
    Write-Status "Please try these manual steps:" $colors.Warning
    Write-Status "1. Open command prompt as administrator" $colors.Info
    Write-Status "2. Run: $python -m pip install PySide6 --user" $colors.Info
    Write-Status "3. If that fails, try: $python -m pip install PySide6 --user --pre" $colors.Info
    exit 1
}