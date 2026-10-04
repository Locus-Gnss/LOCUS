#!/usr/bin/env bash
# LOCUS Master Launcher (Bash)
echo "========================================================"
echo "  LOCUS GNSS Security Operations Center (SOC) Launcher  "
echo "========================================================"
echo ""

echo "[1/2] Starting FastAPI Backend in background..."
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "[2/2] Starting Streamlit SOC Dashboard..."
python -m streamlit run dashboard.py --server.port 8501

kill $BACKEND_PID
