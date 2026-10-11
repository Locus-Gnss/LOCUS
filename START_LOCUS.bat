@echo off
setlocal
REM =========================================================================
REM  LOCUS — One-Click Localhost Launcher for Windows
REM  Starts FastAPI Backend (:8000) and React Vite Frontend (:5173)
REM =========================================================================

cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\localhost_engine.ps1" -Action start

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Launcher encountered an issue. See logs\launcher.log for details.
    echo Press any key to close this window...
    pause >nul
) else (
    timeout /t 5 >nul
)
