# LOCUS SOC Dashboard & REST API — Complete Setup Guide

## 1. System Requirements & Prerequisites
- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), or macOS
- **Python**: 3.10, 3.11, or 3.12
- **Hardware (Optional)**: 7Semi L89HA Multi-GNSS module connected via USB/UART for Live Mode. (System automatically enters Replay Mode if hardware is not present).

---

## 2. Installation & Environment Configuration

### Step 1: Clone the Repository
```bash
git clone https://github.com/mahakagrawal7/LOCUS.git
cd LOCUS
```

### Step 2: Create and Activate Virtual Environment
```bash
# Windows (cmd / PowerShell)
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

---

## 3. Quickstart: Launching LOCUS

### Option A: One-Click Master Launchers (Recommended)

#### On Windows:
Double-click `scripts\start_locus.bat` or run in PowerShell:
```powershell
.\scripts\start_locus.ps1
```

#### On Linux / macOS:
```bash
chmod +x scripts/*.sh
./scripts/start_locus.sh
```

---

### Option B: Separate Terminal Launchers

#### Terminal 1 — Start FastAPI REST Backend (Port 8000)
```bash
# Windows
scripts\start_backend.bat

# Or direct command:
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Redoc Spec: `http://127.0.0.1:8000/redoc`

#### Terminal 2 — Start Streamlit SOC Dashboard (Port 8501)
```bash
# Windows
scripts\start_gui.bat

# Or direct command:
python -m streamlit run dashboard.py --server.port 8501
```
- Web Dashboard: `http://localhost:8501`

---

## 4. Operation Modes

### Mode 1: Historical / Replay Mode (Default)
When no physical GNSS receiver is detected on serial ports:
- The GUI badges provenance as `REAL GNSS TELEMETRY (HISTORICAL RECORDING)`.
- Replays valid fixes from `data/processed/locus_telemetry_clean.csv` (10,938 epochs, 9,382 valid fixes).
- All 10-D features, detector evaluations, evidence bundles, and multi-agent findings are fully interactive.

### Mode 2: Live Sensor Stream Mode
When a 7Semi L89HA receiver is plugged into a USB port:
- The dashboard automatically detects the serial connection.
- Provenance updates to `REAL GNSS TELEMETRY (LIVE HARDWARE)`.
- Telemetry cards and charts display real-time incoming PVT fixes.

---

## 5. REST API Endpoints Specification

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | System health matrix, model states, active RAG chunks |
| `/api/events` | `GET` | Lists all indexed forensic events from `data/evidence/` |
| `/api/events/{id}` | `GET` | Detailed telemetry, 10-D features, and detector outputs |
| `/api/evidence/{id}` | `GET` | Full immutable Evidence Bundle representation |
| `/api/telemetry/latest` | `GET` | Most recent valid GNSS navigation fix |
| `/api/telemetry/history` | `GET` | Recent trajectory sequence with coordinates and DOP |
| `/api/features/latest` | `GET` | Canonical 10-D security vector with calibrated threshold limits |
| `/api/alerts` | `GET` | Filtered security incident queue with severity ratings |
| `/api/alerts/{id}` | `GET` | Single alert forensic detail |
| `/api/agents/status` | `GET` | Operational status of Agent 1, Agent 2, and Agent 3 |
| `/api/query` | `POST` | Natural-language query execution through 3-Agent SOC & RAG |
| `/api/rag/query` | `POST` | Direct regulatory knowledge base search |
| `/api/soc/deliberate` | `POST` | Multi-agent SOC deliberation on custom evidence bundles |

---

## 6. Running Tests & Automated Verification
```bash
# Run full repository test suite (98 tests passing)
python -m pytest tests/ -v

# Run GUI & API integration tests specifically
python -m pytest tests/test_gui_integration.py -v
```
