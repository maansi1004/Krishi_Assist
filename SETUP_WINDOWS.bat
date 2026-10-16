@echo off
setlocal
cd /d %~dp0

echo ========================================
echo KrishiAssist - Windows Setup
echo ========================================

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11+ and try again.
  pause
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo Node.js/npm was not found. Install Node.js 18+ and try again.
  pause
  exit /b 1
)

if not exist backend\.venv\Scripts\python.exe (
  echo Creating backend virtual environment...
  python -m venv backend\.venv
  if errorlevel 1 exit /b 1
)

echo Installing backend dependencies...
backend\.venv\Scripts\python.exe -m pip install --upgrade pip
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if errorlevel 1 exit /b 1

echo Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 exit /b 1
cd ..

echo.
echo Setup complete.
echo Run START_BACKEND.bat and START_FRONTEND.bat in separate windows.
pause
