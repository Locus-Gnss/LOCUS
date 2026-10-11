@echo off
setlocal
REM =========================================================================
REM  LOCUS — System Diagnostics and Health Verification Tool
REM =========================================================================

cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\localhost_engine.ps1" -Action check

echo.
echo Press any key to close this diagnostic report...
pause >nul
