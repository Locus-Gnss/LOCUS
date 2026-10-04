@echo off
REM ===================================================
REM LOCUS Security Operations Center — Start GUI Dashboard
REM Port: 8501
REM ===================================================

echo [LOCUS] Starting Streamlit SOC Dashboard on http://localhost:8501 ...
python -m streamlit run dashboard.py --server.port 8501
pause
