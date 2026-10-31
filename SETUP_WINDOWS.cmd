@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3.11 -m venv .venv
  if errorlevel 1 python -m venv .venv
)
if not exist .venv\Scripts\python.exe (
  echo Python environment creation failed. Install Python 3.11 and retry.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo Installation failed. Review the error above.
  pause
  exit /b 1
)
if not exist .env copy .env.example .env >nul
.venv\Scripts\python.exe setup_demo.py
pause
