@echo off
REM Parallel runner for CareerMind AI backend and frontend
REM This batch file starts both services in separate windows

echo.
echo ============================================================
echo 🎯 CareerMind AI - Parallel Runner
echo ============================================================
echo.
echo 📋 Services to start:
echo    • Backend (FastAPI): http://localhost:8000
echo    • Frontend (Static): http://localhost:3000
echo.
echo 💡 Access the application at: http://localhost:3000
echo.
echo ⚠️  Close any window to stop that service
echo ============================================================
echo.

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Start backend in a new window
start "CareerMind Backend" cmd /k "cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to start
timeout /t 2 /nobreak

REM Start frontend in a new window
start "CareerMind Frontend" cmd /k "cd frontend && python -m http.server 3000"

echo.
echo ✅ Both services are running!
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo.
pause
