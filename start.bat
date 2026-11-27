@echo off
setlocal
cd /d "%~dp0"

echo === N-dine-lang-translator Setup ^& Launcher ===

where python >nul 2>nul
if errorlevel 1 (
    echo Error: Python is not installed or not on PATH. Install Python 3.8+ from python.org.
    pause
    exit /b 1
)

python bootstrap.py
if errorlevel 1 exit /b 1

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment ^(.venv^)...
    python -m venv .venv
    if errorlevel 1 exit /b 1
)

echo Installing/verifying dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip -q
.venv\Scripts\pip.exe install --prefer-binary -r requirements.txt
if errorlevel 1 exit /b 1

echo.
echo Starting N-dine-lang-translator at http://127.0.0.1:5000 ...
echo ^(First run downloads the ~777 MB AI model automatically. Press Ctrl+C to stop.^)
echo.
.venv\Scripts\python.exe app.py
