@echo off
cd /d %~dp0
if not exist frontend\node_modules (
  echo Frontend dependencies not found. Run SETUP_WINDOWS.bat first.
  pause
  exit /b 1
)
cd frontend
echo Starting KrishiAssist frontend on http://localhost:5173
call npm run dev -- --host 127.0.0.1
pause
