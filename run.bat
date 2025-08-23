@echo off
setlocal

rem Ensure we run from the repo root (folder of this script)
cd /d "%~dp0"

rem Pick Python inside the local venv if present; otherwise create the venv
if exist ".venv\Scripts\python.exe" (
    set "PYEXE=.venv\Scripts\python.exe"
) else (
    echo Creating virtual environment...
    rem Prefer the Windows Python launcher if available
    where py >nul 2>nul
    if %ERRORLEVEL%==0 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )

    if not exist ".venv\Scripts\python.exe" (
        echo Failed to create virtual environment. Ensure Python 3 is installed and on PATH.
        exit /b 1
    )

    set "PYEXE=.venv\Scripts\python.exe"
)

"%PYEXE%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

"%PYEXE%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

"%PYEXE%" archive_builder.py
endlocal