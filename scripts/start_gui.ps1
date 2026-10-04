# LOCUS SOC Dashboard Launcher (PowerShell)
Write-Host "[LOCUS] Starting Streamlit SOC Dashboard on http://localhost:8501 ..." -ForegroundColor Green
python -m streamlit run dashboard.py --server.port 8501
