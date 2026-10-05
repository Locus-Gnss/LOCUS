import time
import subprocess
import sys
import urllib.request
import json

print("=== MEASURING BASELINE BEFORE OPTIMIZATION ===", flush=True)

# 1. Startup time of uvicorn src.api.app:app
t0 = time.perf_counter()
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "src.api.app:app", "--host", "127.0.0.1", "--port", "8008"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

startup_time = None
# Wait until server responds on port 8008
for _ in range(50):
    time.sleep(0.1)
    try:
        with urllib.request.urlopen("http://127.0.0.1:8008/api/health", timeout=1) as resp:
            if resp.status == 200:
                startup_time = time.perf_counter() - t0
                break
    except Exception:
        pass

print(f"FastAPI startup time: {startup_time:.4f}s" if startup_time else "FastAPI failed to start within timeout", flush=True)

# 2. Measure first request latency for endpoints
def measure_ep(name, path):
    t_start = time.perf_counter()
    with urllib.request.urlopen(f"http://127.0.0.1:8008{path}", timeout=5) as resp:
        _ = resp.read()
        lat = time.perf_counter() - t_start
    print(f"Latency {name:<25}: {lat:.4f}s", flush=True)
    return lat

measure_ep("GET /", "/")
measure_ep("GET /api/health", "/api/health")
measure_ep("GET /api/telemetry/latest", "/api/telemetry/latest")
measure_ep("GET /api/features/latest", "/api/features/latest")

proc.terminate()
proc.wait()
print("=== BASELINE MEASUREMENT COMPLETE ===", flush=True)
