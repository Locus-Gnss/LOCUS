"""
LOCUS Master Container Orchestration Runner
Module: scripts.run_container

Launches and monitors both the FastAPI REST backend and Streamlit SOC Dashboard
inside a single Docker container or local deployment.
"""

import os
import sys
import time
import signal
import subprocess

def run():
    port = int(os.getenv("PORT", "8501"))
    api_port = int(os.getenv("LOCUS_API_PORT", "8000"))
    
    print("=" * 60)
    print("  LOCUS — Cyber-Physical GNSS Security Operations Center")
    print(f"  Starting FastAPI Backend on port {api_port} ...")
    print(f"  Starting Streamlit Dashboard on port {port} ...")
    print("=" * 60)

    # 1. Start FastAPI backend
    api_env = os.environ.copy()
    api_cmd = [
        sys.executable, "-m", "uvicorn",
        "src.api.app:app",
        "--host", "0.0.0.0",
        "--port", str(api_port)
    ]
    api_proc = subprocess.Popen(api_cmd, env=api_env)
    print(f"[LOCUS] Backend process spawned (PID: {api_proc.pid})")

    # Give backend a short moment to initialize
    time.sleep(2)

    # 2. Start Streamlit GUI
    gui_env = os.environ.copy()
    gui_env["LOCUS_API_URL"] = f"http://127.0.0.1:{api_port}"
    gui_cmd = [
        sys.executable, "-m", "streamlit", "run",
        "dashboard.py",
        "--server.address", "0.0.0.0",
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    gui_proc = subprocess.Popen(gui_cmd, env=gui_env)
    print(f"[LOCUS] GUI process spawned (PID: {gui_proc.pid})")

    def shutdown(signum, frame):
        print("\n[LOCUS] Shutdown signal received. Terminating services...")
        gui_proc.terminate()
        api_proc.terminate()
        try:
            gui_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            gui_proc.kill()
        try:
            api_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_proc.kill()
        print("[LOCUS] All services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Monitor processes
    while True:
        api_code = api_proc.poll()
        if api_code is not None:
            print(f"[LOCUS ERROR] FastAPI backend exited unexpectedly with code {api_code}")
            gui_proc.terminate()
            sys.exit(api_code)

        gui_code = gui_proc.poll()
        if gui_code is not None:
            print(f"[LOCUS ERROR] Streamlit GUI exited unexpectedly with code {gui_code}")
            api_proc.terminate()
            sys.exit(gui_code)

        time.sleep(1)

if __name__ == "__main__":
    run()
