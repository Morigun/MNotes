@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   MNotes MSI Installer Builder
echo ========================================
echo.

taskkill /IM MNotes.exe /F >nul 2>&1

echo [1/3] Building MNotes.exe ...
cd /d "%~dp0client\desktop"

if not exist ".venv\Scripts\activate.bat" (
    echo Creating venv...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create venv
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

pip install -r requirements.txt -q
pip install pyinstaller -q
if errorlevel 1 (
    echo Failed to install deps
    pause
    exit /b 1
)

pyinstaller --noconfirm --onefile --windowed ^
    --name "MNotes" ^
    --icon="app.ico" ^
    --add-data "resources;resources" ^
    --add-data "app.ico;." ^
    --hidden-import=plugins.plugin_base ^
    --exclude-module torch ^
    --exclude-module transformers ^
    --exclude-module vosk ^
    main.py

if errorlevel 1 (
    echo Build failed
    pause
    exit /b 1
)

if not exist "dist\MNotes.exe" (
    echo ERROR: MNotes.exe not found after build
    pause
    exit /b 1
)

echo.
echo [2/3] Cleaning old installer ...
cd /d "%~dp0"
if exist "installer_output" rmdir /s /q installer_output
mkdir installer_output

echo.
echo [3/3] Building MSI with WiX v4 ...

where wix >nul 2>&1
if errorlevel 1 (
    echo ERROR: WiX v4 not found in PATH.
    echo Install: dotnet tool install --global wix
    echo Then run: wix extension add WixToolset.UI.wixext
    pause
    exit /b 1
)

echo Running: wix build installer.wxs -ext WixToolset.UI.wixext
wix build "%~dp0installer.wxs" -ext WixToolset.UI.wixext -o "%~dp0installer_output\MNotes_1.1.1.msi"

if errorlevel 1 (
    echo MSI build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Done: installer_output\MNotes_1.1.1.msi
echo ========================================
pause
