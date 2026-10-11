# LOCUS — Localhost Execution Guide

## Overview

**LOCUS** is a GNSS integrity monitoring and cybersecurity operations center application comprising:
1. **Frontend:** React + Vite (`http://127.0.0.1:5173/`)
2. **Backend:** Python FastAPI REST API (`http://127.0.0.1:8000/`)
3. **Swagger Interactive API Documentation:** (`http://127.0.0.1:8000/docs`)

All services run locally on your Windows machine, bound exclusively to `127.0.0.1` for privacy and stability.

---

## The Three Fixed Localhost URLs

Whenever LOCUS is running, the following URLs are fixed and accessible in your web browser:

| Component | Fixed Local URL | Description |
| :--- | :--- | :--- |
| **Web Dashboard** | [`http://127.0.0.1:5173/`](http://127.0.0.1:5173/) | Cyber SOC Dashboard with map, features, 3-agent deliberation, and RAG |
| **FastAPI Backend** | [`http://127.0.0.1:8000/`](http://127.0.0.1:8000/) | REST API root status and system health |
| **API Documentation** | [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs) | Swagger UI for interactive API route inspection and testing |

> [!NOTE]
> **Understanding Localhost:** `http://127.0.0.1` (localhost) is an internal loopback address on your computer. It is not an external cloud website. Whenever you restart Windows or turn off your computer, the background processes stop. Double-clicking the launcher starts them right back up at the exact same URLs.

---

## 1. How to Start LOCUS (One-Click)

### Option A: From Desktop Shortcut
- Double-click the **LOCUS Launcher** shortcut on your Windows Desktop.

### Option B: From File Explorer
- Double-click `START_LOCUS.bat` in `D:\LOCUS\LOCUS-main` (or `D:\LOCUS\START_LOCUS.bat`).

### What Happens Automatically:
1. Checks that Python, Node.js, and npm are available.
2. Checks that required dependencies exist.
3. Detects if LOCUS is already running to prevent duplicate instances or port collisions.
4. Starts the FastAPI backend in a dedicated console window: `LOCUS_BACKEND_8000`.
5. Starts the Vite frontend in a dedicated console window: `LOCUS_FRONTEND_5173`.
6. Polls both services until `/health` returns `200 HEALTHY` and Vite returns `HTTP 200`.
7. Automatically launches your default web browser to `http://127.0.0.1:5173/`.

---

## 2. How to Stop LOCUS Safely

To safely stop LOCUS without leaving zombie processes or killing unrelated programs:

- **Double-click `STOP_LOCUS.bat`** in `D:\LOCUS\LOCUS-main` (or `D:\LOCUS\STOP_LOCUS.bat`).

This script:
1. Identifies only the processes listening on port 8000 (`python.exe` / `uvicorn`) and port 5173 (`node.exe`).
2. Stops those specific processes and closes their dedicated terminal windows.
3. Verifies that ports 8000 and 5173 are free.
4. Leaves all unrelated Python and Node.js applications completely untouched.

---

## 3. How to Check System Health & Diagnostics

Run **`CHECK_LOCUS.bat`** at any time to inspect the full stack:

- **Python & Node.js environment:** Verifies binary paths and versions.
- **Critical files:** Checks dataset, model, and vector store files.
- **Backend Health:** Tests `http://127.0.0.1:8000/health` (returns event count and vector store chunks).
- **Swagger Docs:** Tests `http://127.0.0.1:8000/docs`.
- **Detection Quad:** Verifies runtime readiness for Physical Rules, Isolation Forest, XGBoost, and Temporal LSTM.
- **Frontend GUI:** Tests `http://127.0.0.1:5173/`.
- **Log generation:** Diagnostic outputs are saved to `logs/health_check.log`.

---

## 4. Troubleshooting & FAQs

### Q1: The browser shows "This site can’t be reached / Connection Refused"
- **Cause:** Services were closed or Windows was restarted.
- **Fix:** Double-click `START_LOCUS.bat`. Wait 5–10 seconds for the green `[OK]` confirmation.

### Q2: `START_LOCUS.bat` reports "Port 8000 occupied by PID [x]"
- **Cause:** A previous instance or another application is using port 8000.
- **Fix:** Double-click `STOP_LOCUS.bat` to clear previous LOCUS instances. If a third-party application is holding the port, inspect the PID reported by the launcher.

### Q3: How do I view backend error logs?
- Look at the open terminal window titled `LOCUS_BACKEND_8000`.
- Or check `logs/launcher.log` and `logs/health_check.log` in the project root.

### Q4: Does LOCUS require an internet connection?
- **No.** The entire 3-Agent SOC pipeline, 10-D feature engineering, Detection Quad, RAG SQLite vector store, and React frontend run 100% offline on your local computer.
