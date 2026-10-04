#!/usr/bin/env bash
# LOCUS REST Backend Launcher (Bash)
echo "[LOCUS] Starting FastAPI REST API Backend on http://127.0.0.1:8000 ..."
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
