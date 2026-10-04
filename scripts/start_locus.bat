@echo off
REM ===================================================
REM LOCUS Master Launch Script (Windows)
REM Starts FastAPI backend on :8000 and Streamlit GUI on :8501
REM ===================================================

echo ========================================================
echo   LOCUS GNSS Security Operations Center (SOC) Launcher
echo ========================================================
echo.

echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "LOCUS REST API Backend" cmd /k "python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching Streamlit SOC Dashboard on http://localhost:8501 ...
start "LOCUS SOC Dashboard" cmd /k "python -m streamlit run dashboard.py --server.port 8501"

echo.
echo Both services launched!
echo - Dashboard: http://localhost:8501
echo - Backend:   http://127.0.0.1:8000
echo - API Docs:  http://127.0.0.1:8000/docs
echo.
