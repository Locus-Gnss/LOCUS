"""
Verification test for all 11 LOCUS SOC Dashboard Pages
"""

import os
import sys
from pathlib import Path
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

os.environ["LOCUS_API_URL"] = "http://127.0.0.1:8000"

from src.ui.data_service import SOCDataService
from src.ui.pages.p01_command_center import render_command_center
from src.ui.pages.p02_telemetry import render_telemetry_page
from src.ui.pages.p03_gnss_features import render_gnss_features_page
from src.ui.pages.p04_threat_events import render_threat_events_page
from src.ui.pages.p05_evidence import render_evidence_page
from src.ui.pages.p06_alerts import render_alerts_page
from src.ui.pages.p07_multi_agent import render_multi_agent_page
from src.ui.pages.p08_rag_intelligence import render_rag_intelligence_page
from src.ui.pages.p09_soc_deliberation import render_soc_deliberation_page
from src.ui.pages.p10_data_pipeline import render_data_pipeline_page
from src.ui.pages.p11_system_health import render_system_health_page


class TestAll11Pages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = SOCDataService()

    def test_p01_command_center(self):
        print("Testing P01: Command Center data contract...")
        is_online, b_str = self.service.check_backend_status()
        self.assertIsInstance(is_online, bool)
        self.assertIsInstance(b_str, str)
        events = self.service.get_events()
        self.assertTrue(len(events) > 0)
        alerts = self.service.get_alert_center_records()
        self.assertTrue(len(alerts) > 0)

    def test_p02_telemetry(self):
        print("Testing P02: Telemetry data contract...")
        latest = self.service.get_latest_telemetry_metrics()
        self.assertTrue(latest.get("has_data"))
        df = self.service.load_telemetry_dataset()
        self.assertFalse(df.empty)
        for col in ["latitude", "longitude", "speed_kmh", "satellites_used", "hdop", "vdop"]:
            self.assertIn(col, df.columns)

    def test_p03_gnss_features(self):
        print("Testing P03: GNSS Features canonical 10-D contract...")
        feats = self.service.get_canonical_10d_features()
        self.assertEqual(len(feats), 10)
        feat_keys = [f["feature"] for f in feats]
        canonical = [
            "disp_haversine", "vel_kinematic", "acc_kinematic", "jerk_kinematic",
            "bearing_rate", "HDOP", "VDOP", "fix_integrity", "sat_count_tot", "sat_churn"
        ]
        self.assertEqual(feat_keys, canonical)

    def test_p04_threat_events(self):
        print("Testing P04: Threat Events contract...")
        events = self.service.get_events()
        self.assertGreater(len(events), 0)
        sample = self.service.load_event(events[0]["event_id"])
        self.assertIsNotNone(sample)

    def test_p05_evidence(self):
        print("Testing P05: Evidence bundles contract...")
        b = self.service.load_event("evt_4_220")
        self.assertIsNotNone(b)
        self.assertEqual(b.event_id, "evt_4_220")
        self.assertIsNotNone(b.physical_rules)
        self.assertIsNotNone(b.isolation_forest)
        self.assertIsNotNone(b.xgboost)
        self.assertIsNotNone(b.temporal_model)

    def test_p06_alerts(self):
        print("Testing P06: Alerts stream contract...")
        alerts = self.service.get_alert_center_records()
        self.assertGreater(len(alerts), 0)
        self.assertIn("severity", alerts[0])
        self.assertIn("event_id", alerts[0])

    def test_p07_multi_agent(self):
        print("Testing P07: Multi-Agent Analysis contract...")
        ok, res, err = self.service.api_client.get_agents_status()
        if ok:
            self.assertIn("agents", res)
            self.assertIn("agent_1_integrity", res["agents"])
            self.assertIn("agent_2_temporal_threat", res["agents"])
            self.assertIn("agent_3_master_soc", res["agents"])
        else:
            self.assertIsInstance(err, str)

    def test_p08_rag_intelligence(self):
        print("Testing P08: RAG Intelligence contract...")
        res = self.service.query_rag("What are the RTCA DO-229E limits on HDOP?", top_k=2)
        self.assertIn("citations", res)

    def test_p09_soc_deliberation(self):
        print("Testing P09: SOC Deliberation contract...")
        delib = self.service.deliberate_event("evt_4_220")
        self.assertIsNotNone(delib)
        self.assertIn("current_status", delib)
        self.assertIn("risk_level", delib)

    def test_p10_data_pipeline(self):
        print("Testing P10: Data Pipeline & Data Quality contract...")
        dq = self.service.compute_data_quality_metrics()
        self.assertTrue(dq.get("has_data"))
        self.assertGreater(dq.get("total_records", 0), 0)
        self.assertIn("valid_records", dq)
        self.assertIn("missing_values", dq)
        self.assertIn("hdop_stats", dq)

    def test_p11_system_health(self):
        print("Testing P11: System Health contract...")
        matrix = self.service.get_system_health_matrix()
        self.assertGreater(len(matrix), 5)


if __name__ == "__main__":
    unittest.main()
