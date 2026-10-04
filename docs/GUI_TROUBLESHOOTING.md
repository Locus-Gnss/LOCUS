# LOCUS SOC GUI & Backend Troubleshooting Guide

This guide provides diagnostics and remediation steps for common operational issues encountered while running the LOCUS Security Operations Center GUI and REST backend.

---

## 1. Port Conflicts

### Issue: Port 8000 or 8501 is already in use
```
ERROR: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): only one usage of each socket address is normally permitted
```
### Remediation:
Find and terminate the process occupying the port:

#### On Windows (PowerShell):
```powershell
# Identify process using port 8000 or 8501
netstat -ano | findstr :8000
netstat -ano | findstr :8501

# Terminate process by PID (replace <PID> with number from last column)
taskkill /F /PID <PID>
```

#### On Linux / macOS:
```bash
lsof -i :8000
kill -9 <PID>
```

Alternatively, launch on custom ports:
```bash
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8080
python -m streamlit run dashboard.py --server.port 8502
```

---

## 2. Backend Offline / Fallback Mode

### Indicator in GUI:
The top navigation bar displays:
`Backend: ● FALLBACK` instead of `Backend: ● REST API`.

### Cause:
The Streamlit dashboard started before the FastAPI backend was launched, or FastAPI encountered a startup error.

### Remediation:
1. Start the backend in a separate terminal:
   ```bash
   python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
   ```
2. Verify the backend health endpoint:
   Open [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) in a browser. It should return `{"status": "HEALTHY"}`.
3. Refresh the Streamlit dashboard (`F5` or `R`). The indicator will change to `Backend: ● REST API`.

*Note: The GUI is designed with high resilience and gracefully operates in Local Fallback mode using direct Python modules if the REST server is intentionally stopped.*

---

## 3. Serial / GNSS Hardware Disconnection

### Indicator in GUI:
`Mode: ● REPLAY` • `1. GNSS Status: CONNECTED (HISTORICAL REPLAY)`.

### Explanation:
The system automatically scans all available USB/UART serial ports (`pyserial`). If no active GNSS receiver is sending valid NMEA sentences on the serial bus, LOCUS enters **Historical / Replay Mode** to ensure safe demonstration without fabricating live signals.

### To Enable Live Hardware:
1. Connect the 7Semi L89HA receiver to a USB port.
2. Confirm device driver appears in Windows Device Manager under **Ports (COM & LPT)** (e.g. `COM3` or `COM5`).
3. Set baud rate to `115200` in `configs/` or `.env`.
4. Run `locus_collector.py` or restart the dashboard.

---

## 4. Map Display Issues

### Issue: Geospatial Map View displays blank or grey tiles
### Cause:
OpenStreetMap tiles require an outbound internet connection to download map imagery.

### Remediation:
- If working offline, the map trace points will still plot against coordinate grids, and antenna coordinates remain visible in the executive summary card.
- If behind a corporate proxy, configure standard HTTP/HTTPS proxy environment variables:
  ```powershell
  $env:HTTP_PROXY="http://proxy:port"
  $env:HTTPS_PROXY="http://proxy:port"
  ```

---

## 5. Streamlit Cache Clearing

### Issue: Old telemetry or stale state vector persists in the dashboard
### Remediation:
1. Click the hamburger menu (`⋮`) in the top-right corner of the Streamlit dashboard.
2. Select **Clear cache** and refresh.
3. Alternatively, restart the dashboard process.

---

## 6. Testing Verification

To confirm all components, detector quad, multi-agent hierarchy, and API client interfaces are functioning properly:
```bash
python -m pytest tests/ -v
```
Expected output: **98 passed, 0 failures**.
