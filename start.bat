@echo off
title Exault Server
cd /d "%~dp0"

echo Starting Exault Server...

set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
set "RUN_SCRIPT=%~dp0run.py"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Virtual environment not found at: "%PYTHON_EXE%"
    echo Please run: python -m venv venv
    pause
    exit /b
)

"%PYTHON_EXE%" "%RUN_SCRIPT%"
pause
