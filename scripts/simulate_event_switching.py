"""
Simulate exact Streamlit user clicks and event switching
"""

import sys
import os
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
os.environ["LOCUS_API_URL"] = "http://127.0.0.1:8000"

dashboard_path = str(ROOT_DIR / "dashboard.py")

print("Initializing AppTest...")
at = AppTest.from_file(dashboard_path, default_timeout=20)
at.run(timeout=20)
print("Initial run finished. Exceptions:", len(at.exception))
for ex in at.exception:
    print("  Ex:", ex.value)

print("\nStep 2: Navigate to Threat & Deliberation Hub...")
nav = [r for r in at.sidebar.radio if r.key == "main_soc_navigation"][0]
nav.set_value("2. Threat & Deliberation Hub (Events, Evidence, Agents & RAG)")
at.run(timeout=20)
print("Nav to Threat & Deliberation Hub finished. Exceptions:", len(at.exception))
for ex in at.exception:
    print("  Ex:", ex.value)

print("\nStep 3: Check selectboxes on Threat & Deliberation Hub...")
print("Main selectbox keys:", [s.key for s in at.selectbox])
print("Sidebar selectbox keys:", [s.key for s in at.sidebar.selectbox])

# Change event on Threat Events page
if any(s.key == "ev_deep_select" for s in at.selectbox):
    print("Step 4: Changing event in ev_deep_select to evt_4_221...")
    sb = [s for s in at.selectbox if s.key == "ev_deep_select"][0]
    sb.set_value("evt_4_221")
    at.run(timeout=20)
    print("After changing event to evt_4_221. Exceptions:", len(at.exception))
    for ex in at.exception:
        print("  Ex:", ex.value)
    print("Current selected_event_id in session_state:", at.session_state["selected_event_id"])
    print("Sidebar selectbox value:", [s.value for s in at.sidebar.selectbox if s.key == "global_event_selector"])
    print("Threat events selectbox value:", [s.value for s in at.selectbox if s.key == "ev_deep_select"])

# Step 5: Check Evidence Bundle synchronization
print("\nStep 5: Verify Evidence Bundle synchronization...")
print("Current selected_event_id in session_state:", at.session_state["selected_event_id"])
print("Evidence selectbox value:", [s.value for s in at.selectbox if s.key == "ev_bundle_selector"])

# Step 6: Check SOC Deliberation synchronization
print("\nStep 6: Verify SOC Deliberation synchronization...")
print("Current selected_event_id in session_state:", at.session_state["selected_event_id"])
print("Delib selectbox value:", [s.value for s in at.selectbox if s.key == "delib_event_select"])

# Step 7: Click Run SOC Deliberation button
print("\nStep 7: Click Run SOC Deliberation button...")
btn = [b for b in at.button if b.key == "btn_run_delib"]
if btn:
    btn[0].click()
    at.run(timeout=25)
    print("After clicking Run SOC Deliberation. Exceptions:", len(at.exception))
    for ex in at.exception:
        print("  Ex:", ex.value)

# Step 8: Return to Command Center and back
print("\nStep 8: Navigate to Command Center and return...")
nav = [r for r in at.sidebar.radio if r.key == "main_soc_navigation"][0]
nav.set_value("1. Command Center (Overview & Telemetry)")
at.run(timeout=20)
nav = [r for r in at.sidebar.radio if r.key == "main_soc_navigation"][0]
nav.set_value("2. Threat & Deliberation Hub (Events, Evidence, Agents & RAG)")
at.run(timeout=20)
print("Return to Threat & Deliberation Hub finished. Exceptions:", len(at.exception))
for ex in at.exception:
    print("  Ex:", ex.value)

# Step 9: Change event again in Threat Events to evt_4_222
print("\nStep 9: Change event to evt_4_222 in Threat Events...")
sb = [s for s in at.selectbox if s.key == "ev_deep_select"][0]
sb.set_value("evt_4_222")
at.run(timeout=20)
print("After changing event to evt_4_222. Exceptions:", len(at.exception))
for ex in at.exception:
    print("  Ex:", ex.value)
print("Final selected_event_id in session_state:", at.session_state["selected_event_id"])
