#!/usr/bin/env bash
# LOCUS SOC Dashboard Launcher (Bash)
echo "[LOCUS] Starting Streamlit SOC Dashboard on http://localhost:8501 ..."
python -m streamlit run dashboard.py --server.port 8501
