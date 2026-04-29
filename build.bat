@echo off

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

echo Building MNotes.exe ...
pyinstaller --noconfirm --onefile --windowed ^
    --name "MNotes" ^
    --icon="app.ico" ^
    --add-data "resources;resources" ^
    --add-data "app.ico;." ^
    main.py

if errorlevel 1 (
    echo Build failed
    pause
    exit /b 1
)

echo.
echo Build complete: dist\MNotes.exe
pause
