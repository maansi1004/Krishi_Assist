@echo off
cd /d %~dp0
if not exist backend\.venv\Scripts\python.exe (
  echo Backend environment not found. Run SETUP_WINDOWS.bat first.
  pause
  exit /b 1
)
cd backend
call .venv\Scripts\activate.bat
set PYTHONPATH=.
echo Starting KrishiAssist API on http://127.0.0.1:8000
echo Keep this window open while using the frontend.
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
