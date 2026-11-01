@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "app.py"
    exit /b
)
where pyw >nul 2>&1
if not errorlevel 1 (
    start "" pyw -3 "%~dp0app.py"
    exit /b
)
where pythonw >nul 2>&1
if not errorlevel 1 (
    start "" pythonw "%~dp0app.py"
    exit /b
)
echo Python 3.10+ is required. Install Python, then run Setup.cmd.
pause
