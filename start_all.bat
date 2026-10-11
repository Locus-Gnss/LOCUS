@echo off
REM ========================================================
REM LOCUS Unified Master Launcher (Windows Batch)
REM Starts FastAPI REST Backend (:8000) & React Frontend (:5173)
REM ========================================================

echo ==========================================================
echo   LOCUS CYBER-PHYSICAL GNSS SECURITY OPERATIONS CENTER
echo ==========================================================
echo.

echo [1/2] Starting FastAPI REST Backend on http://127.0.0.1:8000 ...
start "LOCUS REST API Backend (:8000)" cmd /k "python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting React Cyber SOC Frontend on http://localhost:5173 ...
start "LOCUS React Cyber SOC Frontend (:5173)" cmd /k "cd frontend && npm run dev -- --host 127.0.0.1 --port 5173"

timeout /t 2 /nobreak >nul
start http://localhost:5173

echo.
echo ==========================================================
echo   BOTH SERVICES LAUNCHED CONCURRENTLY!
echo   - Web Dashboard:     http://localhost:5173 (Opened in browser)
echo   - REST Backend:      http://127.0.0.1:8000
echo   - API Documentation: http://127.0.0.1:8000/docs
echo ==========================================================
echo.
