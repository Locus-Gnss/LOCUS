# LOCUS Unified Master Launcher (PowerShell)
# Starts FastAPI REST Backend (Port 8000) & React Cyber SOC Frontend (Port 5173)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  LOCUS CYBER-PHYSICAL GNSS SECURITY OPERATIONS CENTER    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python and Node.js
Write-Host "`n[1/3] Verifying runtime dependencies..." -ForegroundColor Yellow
$py = Get-Command python -ErrorAction SilentlyContinue
$node = Get-Command node -ErrorAction SilentlyContinue

if (-not $py) {
    Write-Host "Error: Python executable not found on PATH!" -ForegroundColor Red
    Exit 1
}
if (-not $node) {
    Write-Host "Error: Node.js executable not found on PATH!" -ForegroundColor Red
    Exit 1
}

Write-Host "  - Python: OK" -ForegroundColor Green
Write-Host "  - Node.js: OK" -ForegroundColor Green

# 2. Launch FastAPI Backend on Port 8000
Write-Host "`n[2/3] Starting FastAPI REST Backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload"

# 3. Launch React + Vite Frontend on Port 5173
Write-Host "[3/3] Starting React Cyber SOC Frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location frontend; npm run dev -- --host 127.0.0.1 --port 5173"

Start-Sleep -Seconds 2
Start-Process "http://localhost:5173"

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  LOCUS SERVICES LAUNCHED CONCURRENTLY!                  " -ForegroundColor Green
Write-Host "  - Web Dashboard:    http://localhost:5173 (Opened)     " -ForegroundColor White
Write-Host "  - REST API:         http://127.0.0.1:8000              " -ForegroundColor White
Write-Host "  - Interactive Docs: http://127.0.0.1:8000/docs         " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
