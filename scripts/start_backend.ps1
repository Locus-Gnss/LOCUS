# LOCUS REST Backend Launcher (PowerShell)
Write-Host "[LOCUS] Starting FastAPI REST API Backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
