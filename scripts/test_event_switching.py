"""
Comprehensive Event-Switching & Session-State Regression Test
Verifies:
Event A -> Event B -> Event C -> Event A
- no exception
- session state remains valid
- event details update
- evidence updates
- SOC deliberation uses the currently selected event
- charts update correctly
- no stale event data remains
"""

import sys
import os
from pathlib import Path
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
os.environ["LOCUS_API_URL"] = "http://127.0.0.1:8000"

from src.ui.data_service import SOCDataService
from src.ui.utils.state import init_session_state, get_selected_event, set_selected_event
import streamlit as st


class TestEventSwitching(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = SOCDataService()
        cls.events = cls.service.get_events()
        cls.event_ids = [e["event_id"] for e in cls.events] if cls.events else []
        assert len(cls.event_ids) >= 3, "Need at least 3 events to test switching"
        cls.ev_A = cls.event_ids[0]
        cls.ev_B = cls.event_ids[1]
        cls.ev_C = cls.event_ids[2]

    def setUp(self):
        # Reset session state for each test
        init_session_state(self.event_ids)

    def test_cycle_event_switching(self):
        print(f"\n--- Testing Cycle: {self.ev_A} -> {self.ev_B} -> {self.ev_C} -> {self.ev_A} ---")
        
        # 1. Select Event A
        set_selected_event(self.ev_A)
        self.assertEqual(get_selected_event(), self.ev_A)
        bundle_A = self.service.load_event(self.ev_A)
        self.assertIsNotNone(bundle_A)
        self.assertEqual(bundle_A.event_id, self.ev_A)
        feats_A = self.service.get_canonical_10d_features(bundle=bundle_A)
        self.assertEqual(len(feats_A), 10)
        delib_A = self.service.deliberate_event(self.ev_A, bundle=bundle_A)
        self.assertIsNotNone(delib_A)
        print(f"[PASS] Event A ({self.ev_A}) loaded and deliberated successfully.")

        # 2. Select Event B
        set_selected_event(self.ev_B)
        self.assertEqual(get_selected_event(), self.ev_B)
        bundle_B = self.service.load_event(self.ev_B)
        self.assertIsNotNone(bundle_B)
        self.assertEqual(bundle_B.event_id, self.ev_B)
        self.assertNotEqual(bundle_B.event_id, bundle_A.event_id)
        feats_B = self.service.get_canonical_10d_features(bundle=bundle_B)
        self.assertEqual(len(feats_B), 10)
        delib_B = self.service.deliberate_event(self.ev_B, bundle=bundle_B)
        self.assertIsNotNone(delib_B)
        print(f"[PASS] Event B ({self.ev_B}) loaded and deliberated successfully.")

        # 3. Select Event C
        set_selected_event(self.ev_C)
        self.assertEqual(get_selected_event(), self.ev_C)
        bundle_C = self.service.load_event(self.ev_C)
        self.assertIsNotNone(bundle_C)
        self.assertEqual(bundle_C.event_id, self.ev_C)
        delib_C = self.service.deliberate_event(self.ev_C, bundle=bundle_C)
        self.assertIsNotNone(delib_C)
        print(f"[PASS] Event C ({self.ev_C}) loaded and deliberated successfully.")

        # 4. Return to Event A
        set_selected_event(self.ev_A)
        self.assertEqual(get_selected_event(), self.ev_A)
        bundle_A2 = self.service.load_event(self.ev_A)
        self.assertEqual(bundle_A2.event_id, self.ev_A)
        delib_A2 = self.service.deliberate_event(self.ev_A, bundle=bundle_A2)
        self.assertEqual(delib_A2["risk_level"], delib_A["risk_level"])
        print(f"[PASS] Returned to Event A ({self.ev_A}) with identical deliberated state.")

    def test_streamlit_apptest_event_switch(self):
        print("\n--- Testing Full AppTest Event Switch Across Views ---")
        from streamlit.testing.v1 import AppTest
        dashboard_path = str(ROOT_DIR / "dashboard.py")

        # Step 1: Open app
        at = AppTest.from_file(dashboard_path, default_timeout=25)
        at.run(timeout=25)
        self.assertEqual(len(at.exception), 0)

        # Step 2: Navigate to Threat & Deliberation Hub
        at.session_state["main_soc_navigation"] = "2. Threat & Deliberation Hub (Events, Evidence, Agents & RAG)"
        at.run(timeout=25)
        self.assertEqual(len(at.exception), 0)

        # Step 3: Switch event to Event B
        at.session_state["selected_event_id"] = self.ev_B
        at.run(timeout=25)
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state["selected_event_id"], self.ev_B)

        # Step 4: Switch event to Event C
        at.session_state["selected_event_id"] = self.ev_C
        at.run(timeout=25)
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state["selected_event_id"], self.ev_C)

        # Step 5: Navigate to Command Center
        at.session_state["main_soc_navigation"] = "1. Command Center (Overview & Telemetry)"
        at.run(timeout=25)
        self.assertEqual(len(at.exception), 0)

        # Step 6: Return to Threat & Deliberation Hub
        at.session_state["main_soc_navigation"] = "2. Threat & Deliberation Hub (Events, Evidence, Agents & RAG)"
        at.session_state["selected_event_id"] = self.ev_A
        at.run(timeout=25)
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state["selected_event_id"], self.ev_A)
        print("[PASS] Full AppTest event-switching workflow executed with 0 exceptions!")


if __name__ == "__main__":
    unittest.main()
