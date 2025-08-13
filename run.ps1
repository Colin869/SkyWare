# WiiWare Modder Launcher Script
# PowerShell version with enhanced error handling

Write-Host "Starting WiiWare Modder..." -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if requirements are installed
Write-Host "Checking dependencies..." -ForegroundColor Cyan
try {
    $pillow = pip show pillow 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing required dependencies..." -ForegroundColor Yellow
        pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
        Write-Host "Dependencies installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Dependencies already installed." -ForegroundColor Green
    }
} catch {
    Write-Host "Error checking dependencies: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Launch the application
Write-Host "Launching WiiWare Modder..." -ForegroundColor Green
try {
    python main.py
} catch {
    Write-Host "Error launching application: $_" -ForegroundColor Red
}

# If the application crashes, pause to show error messages
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Application exited with an error. Check the console output above." -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
