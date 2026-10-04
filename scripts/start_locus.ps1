# LOCUS Master Launcher (PowerShell)
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  LOCUS GNSS Security Operations Center (SOC) Launcher  " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

Write-Host "`n[1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload"

Write-Host "[2/2] Launching Streamlit SOC Dashboard on http://localhost:8501 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m streamlit run dashboard.py --server.port 8501"

Write-Host "`nBoth services launched in separate windows!" -ForegroundColor Green
Write-Host "- Dashboard: http://localhost:8501"
Write-Host "- Backend:   http://127.0.0.1:8000"
Write-Host "- API Docs:  http://127.0.0.1:8000/docs"
