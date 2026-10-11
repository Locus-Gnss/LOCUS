@echo off
setlocal
REM =========================================================================
REM  LOCUS — Safe Process Stop Script
REM =========================================================================

cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\localhost_engine.ps1" -Action stop

timeout /t 5 >nul
