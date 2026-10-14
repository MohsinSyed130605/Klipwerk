@echo off
cd /d "%~dp0"

:: Launch without console if pythonw exists, otherwise python
where pythonw >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" pythonw main.py %*
) else (
    python main.py %*
)
