"""
Script to reproduce the exact user workflow:
1. Open Command Center
2. Open Threat Events
3. Select an event
4. Change the selected event to another event
5. Navigate to Evidence
6. Navigate to SOC Deliberation
7. Return to Threat Events
8. Change the event again
"""

import sys
import os
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
os.environ["LOCUS_API_URL"] = "http://127.0.0.1:8000"

dashboard_path = str(ROOT_DIR / "dashboard.py")

print("=" * 60)
print("REPRODUCING EXACT USER WORKFLOW")
print("=" * 60)

try:
    # 1. Open Command Center
    print("[Step 1] Opening Command Center...")
    at = AppTest.from_file(dashboard_path, default_timeout=30)
    at.run()
    if at.exception:
        print(f"Exception at step 1: {at.exception[0].value}")

    # 2. Open Threat & Deliberation Hub
    print("[Step 2] Navigating to Threat & Deliberation Hub...")
    at.sidebar.radio(key="main_soc_navigation").set_value("2. Threat & Deliberation Hub (Events, Evidence, Agents & RAG)").run()
    if at.exception:
        print(f"Exception at step 2: {at.exception[0].value}")

    # 3. Select an event
    print("[Step 3] Inspecting Threat & Deliberation Hub...")
    print("Sidebar selectboxes:", [(s.key, s.value) for s in at.sidebar.selectbox])
    print("Main selectboxes:", [(s.key, s.value) for s in at.main.selectbox])
    print("Main errors:", [e.value for e in at.main.error])
    print("Main warnings:", [w.value for w in at.main.warning])
    print("Main infos:", [i.value for i in at.main.info])
    if at.exception:
        print(f"Exception at step 3: {at.exception[0].value}")

    # 4. Change selected event to another event (evt_4_221)
    print("[Step 4] Changing event to evt_4_221...")
    if at.selectbox(key="ev_deep_select"):
        at.selectbox(key="ev_deep_select").set_value("evt_4_221").run()
    if at.exception:
        print(f"Exception at step 4: {at.exception[0].value}")

    # 5. Navigate to Command Center
    print("[Step 5] Navigating to Command Center...")
    for r in at.sidebar.radio:
        if r.key == "main_soc_navigation":
            r.set_value("1. Command Center (Overview & Telemetry)")
            break
    at.run()
    if at.exception:
        print(f"Exception at step 5: {at.exception[0].value}")

    # 6. Navigate to System & Health Pipeline
    print("[Step 6] Navigating to System & Health Pipeline...")
    for r in at.sidebar.radio:
        if r.key == "main_soc_navigation":
            r.set_value("3. System & Health Pipeline")
            break
    at.run()
    if at.exception:
        print(f"Exception at step 6: {at.exception[0].value}")

    # 7. Return to Threat & Deliberation Hub
    print("[Step 7] Returning to Threat & Deliberation Hub...")
    for r in at.sidebar.radio:
        if r.key == "main_soc_navigation":
            r.set_value("2. Threat & Deliberation Hub (Events, Evidence, Agents & RAG)")
            break
    at.run()
    if at.exception:
        print(f"Exception at step 7: {at.exception[0].value}")

    # 8. Change event again
    print("[Step 8] Changing event again to evt_4_222...")
    if at.selectbox(key="ev_deep_select"):
        at.selectbox(key="ev_deep_select").set_value("evt_4_222").run()
    if at.exception:
        print(f"Exception at step 8: {at.exception[0].value}")

    print("Workflow completed.")
except Exception as e:
    import traceback
    print(f"CRASH CAUGHT: {e}")
    traceback.print_exc()
