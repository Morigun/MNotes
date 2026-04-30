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
if errorlevel 1 (
    echo Failed to install deps
    pause
    exit /b 1
)

python main.py
