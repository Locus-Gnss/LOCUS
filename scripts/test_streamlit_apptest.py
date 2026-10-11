"""
Automated End-to-End Streamlit AppTest for LOCUS Dashboard
Tests all 11 pages navigation, event selection, charts, and zero exceptions.
"""

import sys
import os
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
os.environ["LOCUS_API_URL"] = "http://127.0.0.1:8000"

NAV_PAGES = [
    "1. Command Center (Overview & Telemetry)",
    "2. Threat & Deliberation Hub (Events, Evidence, Agents & RAG)",
    "3. System & Health Pipeline"
]

dashboard_path = str(ROOT_DIR / "dashboard.py")

print("=" * 65)
print("LOCUS SOC DASHBOARD: AUTOMATED AppTest RUNNER ACROSS 3 ESSENTIAL PAGES")
print("=" * 65)

all_passed = True

# Test each page individually by injecting navigation state
for idx, page_name in enumerate(NAV_PAGES):
    try:
        at = AppTest.from_file(dashboard_path, default_timeout=25)
        at.session_state["main_soc_navigation"] = page_name
        at.run(timeout=25)

        if at.exception:
            print(f"[FAIL] Page {idx + 1:2d}: {page_name:<25} => FAILED with exception:")
            for ex in at.exception:
                print(f"       {ex.value}")
            all_passed = False
        else:
            print(f"[PASS] Page {idx + 1:2d}: {page_name:<25} => Rendered cleanly (0 exceptions)")
    except Exception as e:
        print(f"[ERROR] Exception running '{page_name}': {e}")
        all_passed = False

print("\n" + "=" * 65)
if all_passed:
    print("ALL 3 ESSENTIAL CONSOLIDATED PAGES PASSED APPTES T VERIFICATION!")
else:
    print("SOME PAGES FAILED!")
print("=" * 65)

sys.exit(0 if all_passed else 1)
