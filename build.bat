@echo off
setlocal enabledelayedexpansion

:: ═══════════════════════════════════════════════════════════════════
::  Klipwerk — Windows Build Script
::  Produces:
::    1. Portable Executable: Klipwerk-Portable-x64.exe (and Klipwerk.exe)
::    2. Setup Installer:     Klipwerk-Setup-x64.exe
:: ═══════════════════════════════════════════════════════════════════

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║         Klipwerk v1.0.0 — Build System                ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.

:: ── 1. Check Python ────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found on PATH.
    echo  Please install Python 3.11+ from https://python.org
    pause & exit /b 1
)
for /f "tokens=*" %%V in ('python --version') do echo  Python: %%V
echo.

:: ── 2. Install / upgrade PyInstaller ───────────────────────────────
echo  [1/5] Checking PyInstaller...
python -m pip install pyinstaller --quiet --upgrade
if errorlevel 1 (
    echo  [ERROR] Could not install PyInstaller.
    pause & exit /b 1
)

:: ── 3. Install runtime dependencies ────────────────────────────────
echo  [2/5] Checking runtime dependencies...
python -m pip install -r requirements.txt --quiet

:: ── 4. Clean previous build artifacts ──────────────────────────────
echo  [3/5] Cleaning previous builds...
if exist build   rmdir /s /q build
if exist dist    rmdir /s /q dist

:: ── 5. Run PyInstaller ─────────────────────────────────────────────
echo  [4/5] Compiling Klipwerk.exe with PyInstaller...
echo        (this takes 1-2 minutes)...
echo.

python -m PyInstaller Klipwerk.spec --noconfirm

if not exist dist\Klipwerk.exe (
    echo.
    echo  [ERROR] Build failed — dist\Klipwerk.exe was not produced.
    echo  Check the output above for details.
    pause & exit /b 1
)

:: Copy EXE to root as standardized release portable name
copy /y dist\Klipwerk.exe .\Klipwerk-Portable-x64.exe >nul

:: ── 6. Build Windows Setup Installer with Inno Setup ───────────────
echo  [5/5] Building Windows Setup Installer (Klipwerk-Setup-x64.exe)...
set "ISCC_PATH="
if exist "C:\Program Files\Inno Setup 7\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 7\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

if not "!ISCC_PATH!"=="" (
    if not exist installer mkdir installer
    "!ISCC_PATH!" /Q installer.iss
    if exist installer\Klipwerk-Setup-x64.exe (
        copy /y installer\Klipwerk-Setup-x64.exe .\Klipwerk-Setup-x64.exe >nul
        echo        [OK] Setup installer created successfully!
    ) else (
        echo        [WARN] Inno Setup finished but installer\Klipwerk-Setup-x64.exe not found.
    )
) else (
    echo        [INFO] Inno Setup compiler not found in standard paths. Skipping installer step.
)

:: Clean intermediate build directories so only final binaries remain
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist installer rmdir /s /q installer

:: ── 7. Summary ─────────────────────────────────────────────────────
echo.
echo  ╔═══════════════════════════════════════════════════════════════╗
echo  ║  ✓ ALL BUILDS COMPLETED SUCCESSFULLY!                         ║
echo  ╚═══════════════════════════════════════════════════════════════╝
echo.
if exist .\Klipwerk-Portable-x64.exe (
    for %%F in (.\Klipwerk-Portable-x64.exe) do (
        set /a SIZE_MB=%%~zF / 1048576
        echo   ▶ Portable EXE:    .\Klipwerk-Portable-x64.exe   (!SIZE_MB! MB^)
    )
)
if exist .\Klipwerk-Setup-x64.exe (
    for %%F in (.\Klipwerk-Setup-x64.exe) do (
        set /a SIZE_MB=%%~zF / 1048576
        echo   ▶ Setup Installer: .\Klipwerk-Setup-x64.exe      (!SIZE_MB! MB^)
    )
)
echo.
echo   Release files are ready in the root folder!
echo.
