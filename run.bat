@echo off
echo Starting WiiWare Modder...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
pip show pillow >nul 2>&1
if errorlevel 1 (
    echo Installing required dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Launch the application
echo Launching WiiWare Modder...
python main.py

REM If the application crashes, pause to show error messages
if errorlevel 1 (
    echo.
    echo Application exited with an error. Check the console output above.
    pause
)
