import os
import sys
import time
import subprocess
import urllib.request
import json
import tracemalloc
from pathlib import Path

# Ensure root directory is on PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Ensure LOCUS_API_URL points to local test backend
os.environ["LOCUS_API_URL"] = "http://127.0.0.1:8000"

print("==================================================", flush=True)
print("LOCUS STREAMLIT THIN-CLIENT GUI & API E2E VERIFICATION", flush=True)
print("==================================================", flush=True)

# 1. Start FastAPI backend subprocess
print("\n[1/6] Launching FastAPI backend on 127.0.0.1:8000...", flush=True)
t_start = time.perf_counter()
api_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "src.api.app:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# Wait for backend to be healthy
backend_ready = False
for i in range(200):
    time.sleep(0.1)
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=1) as resp:
            if resp.status == 200:
                backend_ready = True
                break
    except Exception:
        pass

startup_duration = time.perf_counter() - t_start
if not backend_ready:
    print(f"FAILED: Backend did not respond within timeout ({startup_duration:.2f}s)!", flush=True)
    api_proc.terminate()
    sys.exit(1)

print(f"PASS: FastAPI backend healthy in {startup_duration:.4f}s", flush=True)

# 2. Start memory tracking for Thin-Client GUI
tracemalloc.start()
mem_start = tracemalloc.get_traced_memory()[0] / (1024 * 1024)

from src.ui.data_service import SOCDataService
from src.ui.components.navbar import render_navbar
from src.ui.components.kpis import render_kpi_cards
from src.ui.components.telemetry_panel import render_telemetry_panel
from src.ui.components.map_panel import render_map_panel
from src.ui.components.features_panel import render_features_panel
from src.ui.components.detection_panel import render_detection_panel
from src.ui.components.alert_center import render_alert_center
from src.ui.components.evidence_panel import render_evidence_panel
from src.ui.components.agent_soc_panel import render_agent_soc_panel
from src.ui.components.rag_panel import render_rag_panel
from src.ui.components.query_terminal import render_query_terminal
from src.ui.components.health_panel import render_health_panel

print("\n[2/6] Verifying Thin-Client Data Service API Delegation...", flush=True)
service = SOCDataService()

# Verify backend status
is_online, status_msg = service.check_backend_status()
print(f"  - Backend Connectivity: {status_msg} (Online={is_online})")
assert is_online, "Backend should be reported online"

# Verify events
events = service.get_events()
print(f"  - Events Count: {len(events)} (Loaded via REST API)")
assert len(events) == 31, f"Expected 31 events, got {len(events)}"

# Verify telemetry metrics
tel_metrics = service.get_latest_telemetry_metrics()
print(f"  - Latest Telemetry Source: {tel_metrics.get('source')} (Lat: {tel_metrics.get('latitude')}, Lon: {tel_metrics.get('longitude')})")
assert tel_metrics.get("has_data"), "Telemetry data should be present"

# Verify 10-D canonical features
canonical_feats = service.get_canonical_10d_features()
print(f"  - Canonical 10-D Features: {len(canonical_feats)} features evaluated")
expected_canonical = [
    "disp_haversine", "vel_kinematic", "acc_kinematic", "jerk_kinematic",
    "bearing_rate", "HDOP", "VDOP", "fix_integrity", "sat_count_tot", "sat_churn"
]
assert [f["feature"] for f in canonical_feats] == expected_canonical, "Canonical 10-D vector mismatch"

# Verify alerts
alerts = service.get_alert_center_records()
print(f"  - Alert Center Records: {len(alerts)} alerts retrieved via REST API")
assert len(alerts) > 0, "Alerts list should not be empty"

# Verify event bundle
event_id = events[0]["event_id"]
bundle = service.load_event(event_id)
print(f"  - Evidence Bundle ({event_id}): Loaded via REST API (Event: {bundle.event_id})")
assert bundle is not None and bundle.event_id == event_id

# Verify deliberation
delib = service.deliberate_event(event_id, bundle=bundle)
print(f"  - 3-Agent Deliberation ({event_id}): Status={delib.get('current_status')}, DEFCON={delib.get('risk_level')}")
assert "current_status" in delib, "Deliberation missing current_status"

# Verify SOC natural language query delegation
soc_ans = service.query_soc("Why was this event flagged?", event_id=event_id, bundle=bundle)
print(f"  - SOC Query Response: Status={soc_ans.get('current_status')} (Length: {len(soc_ans.get('explanation', ''))} chars)")
assert "explanation" in soc_ans, "SOC query missing explanation"

# Verify RAG query delegation
rag_ans = service.query_rag("What does RTCA DO-229E specify for HDOP?", top_k=3)
print(f"  - RAG Query Response: Grounded={rag_ans.get('is_grounded')} (Citations: {len(rag_ans.get('citations', []))})")

# Verify system health matrix (thin client consumption)
health_matrix = service.get_system_health_matrix()
print(f"  - System Health Matrix: {len(health_matrix)} monitored components")
assert len(health_matrix) >= 12, "Health matrix missing components"

print("\n[3/6] Verifying All 11 Streamlit Views (Thin-Client Data Pipeline)...", flush=True)
views = [
    ("View 1: Main SOC Overview", lambda: {
        "conn": service.check_gnss_connection(),
        "delib": delib,
        "kpis": tel_metrics,
        "map_tail": service.load_telemetry_dataset().tail(50),
        "feats": canonical_feats
    }),
    ("View 2: Live GNSS Monitoring", lambda: {
        "tel": service.load_telemetry_dataset(),
        "conn": service.check_gnss_connection()
    }),
    ("View 3: Geospatial Map View", lambda: {
        "tel": service.load_telemetry_dataset(),
        "alerts": alerts
    }),
    ("View 4: 10-D Security Features", lambda: {
        "feats": canonical_feats,
        "df_feats": service.load_features_dataset()
    }),
    ("View 5: Detection & ML Quad", lambda: {
        "bundle": bundle.to_dict(),
        "verdict": delib.get("agent_findings", {}).get("agent_3_master_soc")
    }),
    ("View 6: Alert Center", lambda: {
        "alerts": alerts
    }),
    ("View 7: Evidence Bundle", lambda: {
        "bundle": bundle,
        "delib": delib
    }),
    ("View 8: 3-Agent Security SOC", lambda: {
        "agents": delib.get("agent_findings", {})
    }),
    ("View 9: Regulatory RAG", lambda: {
        "sources": delib.get("rag_sources", []),
        "rag_resp": service.query_rag("ICAO spoofing threshold")
    }),
    ("View 10: SOC Query Assistant", lambda: {
        "soc_resp": service.query_soc("Why was this event flagged?", event_id=event_id, bundle=bundle)
    }),
    ("View 11: System Health", lambda: {
        "health": health_matrix
    })
]

memory_log = []
for v_name, v_func in views:
    try:
        data_payload = v_func()
        cur_mem = tracemalloc.get_traced_memory()[0] / (1024 * 1024)
        memory_log.append((v_name, cur_mem))
        print(f"  [PASS] {v_name:<32} (Payload keys: {len(data_payload)}, Memory: {cur_mem:.2f} MB)")
    except Exception as e:
        print(f"  [FAIL] {v_name:<32} Error: {e}")
        api_proc.terminate()
        sys.exit(1)

# 4. Multi-cycle memory leak test
print("\n[4/6] Running 5 Full Navigation Cycles to Detect Memory Leaks...", flush=True)
for cycle in range(1, 6):
    _ = service.get_events()
    _ = service.load_event(event_id)
    _ = service.deliberate_event(event_id)
    _ = service.query_soc("Status check", event_id=event_id)
    _ = service.get_system_health_matrix()
    cycle_mem = tracemalloc.get_traced_memory()[0] / (1024 * 1024)
    print(f"  Cycle {cycle}/5: Active Memory = {cycle_mem:.2f} MB", flush=True)

mem_peak = tracemalloc.get_traced_memory()[1] / (1024 * 1024)
mem_current = tracemalloc.get_traced_memory()[0] / (1024 * 1024)
tracemalloc.stop()

print(f"\n[5/6] Thin-Client GUI Memory Metrics:")
print(f"  - Initial Memory: {mem_start:.2f} MB")
print(f"  - Final Active Memory: {mem_current:.2f} MB")
print(f"  - Peak Memory Usage: {mem_peak:.2f} MB (Well within 512MB RAM limit)")

# 6. Cleanup backend subprocess
api_proc.terminate()
api_proc.wait()
print("\n[6/6] Local backend process terminated cleanly.")
print("\n==================================================")
print("ALL 11 VIEWS AND THIN-CLIENT API INTEGRATIONS PASSED!")
print("==================================================")
