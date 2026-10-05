import os
import sys
import unittest
from pathlib import Path

# Ensure root directory is on PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Set test environment
os.environ["LOCUS_API_URL"] = "http://127.0.0.1:8000"

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

class TestStreamlitViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = SOCDataService()
        cls.conn_info = cls.service.check_gnss_connection()
        cls.df_telemetry = cls.service.load_telemetry_dataset()
        cls.df_features = cls.service.load_features_dataset()
        cls.alerts_list = cls.service.get_alert_center_records()
        cls.health_matrix = cls.service.get_system_health_matrix()
        cls.events = cls.service.get_events()
        cls.active_bundle = cls.service.load_event(cls.events[0]["event_id"]) if cls.events else None
        cls.delib = cls.service.deliberate_event(cls.events[0]["event_id"], bundle=cls.active_bundle) if cls.events else {}

    def test_view_1_overview_components(self):
        print("Testing View 1: Main SOC Overview components...")
        self.assertIsNotNone(self.conn_info)
        self.assertIsNotNone(self.delib)
        tel_metrics = self.service.get_latest_telemetry_metrics()
        self.assertIn("has_data", tel_metrics)

    def test_view_2_live_gnss_monitoring(self):
        print("Testing View 2: Live GNSS Monitoring...")
        self.assertFalse(self.df_telemetry.empty)
        self.assertIn("latitude", self.df_telemetry.columns)
        self.assertIn("longitude", self.df_telemetry.columns)

    def test_view_3_geospatial_map(self):
        print("Testing View 3: Geospatial Map View...")
        self.assertTrue(len(self.df_telemetry) > 0)
        self.assertTrue(len(self.alerts_list) > 0)

    def test_view_4_10d_security_features(self):
        print("Testing View 4: 10-D Security Features...")
        canonical = self.service.get_canonical_10d_features(bundle=self.active_bundle)
        self.assertEqual(len(canonical), 10)
        expected_keys = [
            "disp_haversine", "vel_kinematic", "acc_kinematic", "jerk_kinematic",
            "bearing_rate", "HDOP", "VDOP", "fix_integrity", "sat_count_tot", "sat_churn"
        ]
        feature_names = [f["feature"] for f in canonical]
        self.assertEqual(feature_names, expected_keys)

    def test_view_5_detection_ml_quad(self):
        print("Testing View 5: Detection & ML Quad...")
        b_dict = self.active_bundle.to_dict()
        self.assertIn("physical_rules", b_dict)
        self.assertIn("isolation_forest", b_dict)
        self.assertIn("xgboost", b_dict)
        self.assertIn("temporal_model", b_dict)

    def test_view_6_alert_center(self):
        print("Testing View 6: Alert Center...")
        self.assertTrue(len(self.alerts_list) > 0)
        self.assertIn("alert_id", self.alerts_list[0])
        self.assertIn("severity", self.alerts_list[0])

    def test_view_7_evidence_bundle(self):
        print("Testing View 7: Evidence Bundle...")
        self.assertIsNotNone(self.active_bundle)
        self.assertIsNotNone(self.active_bundle.event_id)

    def test_view_8_3agent_soc(self):
        print("Testing View 8: 3-Agent Security SOC...")
        agent_findings = self.delib.get("agent_findings", {})
        self.assertIn("agent_1_integrity", agent_findings)
        self.assertIn("agent_2_temporal_threat", agent_findings)
        self.assertIn("agent_3_master_soc", agent_findings)

    def test_view_9_regulatory_rag(self):
        print("Testing View 9: Regulatory RAG...")
        self.assertIsNotNone(self.service.processor.rag_engine)
        count = self.service.processor.rag_engine.vector_store.count()
        self.assertEqual(count, 50)

    def test_view_10_soc_query_assistant(self):
        print("Testing View 10: SOC Query Assistant...")
        res = self.service.processor.process_query("What is this event?", bundle=self.active_bundle)
        self.assertIn("explanation", res)

    def test_view_11_system_health(self):
        print("Testing View 11: System Health...")
        self.assertTrue(len(self.health_matrix) >= 12)
        components = [item["component"] for item in self.health_matrix]
        self.assertIn("FastAPI SOC REST Backend", components)

if __name__ == "__main__":
    unittest.main()
