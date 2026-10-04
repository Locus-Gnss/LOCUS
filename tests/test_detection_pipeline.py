"""
LOCUS Phase 5.5 — End-to-End Pipeline & Scenario Verification Tests

Module: tests/test_detection_pipeline.py
Validates the end-to-end integration:
structured dataset -> 10-D features -> physical rules -> Isolation Forest -> XGBoost -> LSTM -> Evidence Bundle.

Tests the mandatory 8 scenarios:
1. Normal GNSS observation
2. Missing-data case (graceful imputation)
3. Invalid-data case (robust error handling)
4. Large timestamp gap (temporal buffer reset)
5. Sudden kinematic change [SYNTHETIC/CONTROLLED]
6. Navigation-quality degradation [SYNTHETIC/CONTROLLED]
7. Satellite behaviour change [SYNTHETIC/CONTROLLED]
8. Temporal anomaly sequence [SYNTHETIC/CONTROLLED]
"""

import os
import json
import unittest
import numpy as np
import pandas as pd

from src.detection.physical_rules import PhysicalRulesEngine, PhysicalRulesConfig
from src.detection.isolation_forest import IsolationForestDetector, OFFICIAL_SECURITY_FEATURES
from src.detection.xgboost_detector import XGBoostDetector
from src.detection.temporal_model import TemporalDetector
from src.evidence.evidence_bundle import EvidenceBundle, EvidenceFusionEngine


class TestPhase55PipelineIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize the production pipeline engine
        cls.engine = EvidenceFusionEngine(pipeline_tier="PRODUCTION")

    def test_scenario_1_normal_gnss_observation(self):
        """Test Case 1: Nominal GNSS observation."""
        normal_epoch = {
            "session_id": 15,
            "epoch_id": 100,
            "timestamp_utc": "2026-09-27T22:00:00.000Z",
            "timestamp_pc": "2026-09-27T22:00:00.100Z",
            "latitude": 23.1043,
            "longitude": 72.5925,
            "altitude_m": 66.5,
            "disp_haversine": 0.04,
            "vel_kinematic": 0.04,
            "acc_kinematic": 0.01,
            "jerk_kinematic": 0.005,
            "bearing_rate": 0.0,
            "HDOP": 0.85,
            "VDOP": 0.90,
            "fix_integrity": 0.82,
            "sat_count_tot": 22,
            "sat_churn": np.nan,
            "fix_quality": 1,
            "satellites_used": 22,
            "satellites_in_view": 26,
            "hdop": 0.85,
            "avg_cno": 39.5,
            "data_quality_flag": "VALID"
        }
        bundle = self.engine.build_bundle(normal_epoch, event_id="test_normal_001")

        self.assertIsInstance(bundle, EvidenceBundle)
        self.assertEqual(bundle.model_version, "locus-production-v5.5")
        self.assertEqual(bundle.feature_schema_version, "locus-sec-v2.0-10d")
        self.assertEqual(bundle.model_training_date, "2026-10-04")
        self.assertEqual(bundle.model_versions["pipeline_tier"], "PRODUCTION")

        # Physical rules should be nominal
        self.assertFalse(bundle.physical_rules["is_anomalous"])
        self.assertEqual(bundle.physical_rules["max_severity"], "INFO")

        # Isolation Forest should not flag normal observation
        if bundle.isolation_forest.get("is_anomaly") is not None:
            self.assertFalse(bundle.isolation_forest["is_anomaly"])

    def test_scenario_2_missing_data_case(self):
        """Test Case 2: Missing data (NaN values) must be imputed without crashing."""
        missing_epoch = {
            "session_id": 15,
            "epoch_id": 101,
            "timestamp_utc": "2026-09-27T22:00:01.000Z",
            "timestamp_pc": "2026-09-27T22:00:01.100Z",
            "latitude": 23.1043,
            "longitude": 72.5925,
            "altitude_m": np.nan,
            "disp_haversine": 0.05,
            "vel_kinematic": np.nan,  # Missing velocity
            "acc_kinematic": np.nan,
            "jerk_kinematic": np.nan,
            "bearing_rate": 0.0,
            "HDOP": 0.9,
            "VDOP": np.nan,           # Missing VDOP
            "fix_integrity": 0.75,
            "sat_count_tot": 20,
            "sat_churn": np.nan       # Missing churn
        }
        bundle = self.engine.build_bundle(missing_epoch, event_id="test_missing_002")
        self.assertIsInstance(bundle, EvidenceBundle)
        # Check that 10-D vector handled NaNs gracefully
        self.assertIsNone(bundle.security_features["vel_kinematic"])
        self.assertIsNone(bundle.security_features["VDOP"])

    def test_scenario_3_invalid_data_case(self):
        """Test Case 3: Invalid data types (None, non-numeric strings, infinities)."""
        invalid_epoch = {
            "session_id": 15,
            "epoch_id": 102,
            "disp_haversine": "INVALID_STR",
            "vel_kinematic": float("inf"),
            "acc_kinematic": -float("inf"),
            "jerk_kinematic": None,
            "bearing_rate": 0.0,
            "HDOP": "BAD_DOP",
            "VDOP": None,
            "fix_integrity": 0.5,
            "sat_count_tot": 15,
            "sat_churn": None
        }
        bundle = self.engine.build_bundle(invalid_epoch, event_id="test_invalid_003")
        self.assertIsInstance(bundle, EvidenceBundle)
        self.assertIsNone(bundle.security_features["disp_haversine"])
        self.assertIsNone(bundle.security_features["vel_kinematic"])

    def test_scenario_4_large_timestamp_gap(self):
        """Test Case 4: Large timestamp gap between epochs."""
        epoch_1 = {
            "session_id": 15,
            "epoch_id": 200,
            "timestamp_utc": "2026-09-27T22:00:00.000Z",
            "vel_kinematic": 0.05, "acc_kinematic": 0.01, "jerk_kinematic": 0.0,
            "HDOP": 0.8, "VDOP": 0.9, "fix_integrity": 0.85, "sat_count_tot": 20, "sat_churn": 0.0
        }
        epoch_2 = {
            "session_id": 15,
            "epoch_id": 201,
            # 300 second gap
            "timestamp_utc": "2026-09-27T22:05:00.000Z",
            "vel_kinematic": 0.05, "acc_kinematic": 0.01, "jerk_kinematic": 0.0,
            "HDOP": 0.8, "VDOP": 0.9, "fix_integrity": 0.85, "sat_count_tot": 20, "sat_churn": 0.0
        }
        b1 = self.engine.build_bundle(epoch_1, event_id="gap_01")
        b2 = self.engine.build_bundle(epoch_2, event_id="gap_02")
        self.assertIsInstance(b1, EvidenceBundle)
        self.assertIsInstance(b2, EvidenceBundle)

    def test_scenario_5_sudden_kinematic_change(self):
        """Test Case 5 [SYNTHETIC/CONTROLLED]: Sudden coordinate jump / severe kinematic step."""
        kinematic_attack_epoch = {
            "session_id": 999,
            "epoch_id": 500,
            "timestamp_utc": "2026-10-04T12:00:00.000Z",
            "latitude": 23.2000,
            "longitude": 72.7000,
            "altitude_m": 250.0,
            # Kinematic violation: 120m jump in 1s -> 120 m/s, 80 m/s², 50 m/s³
            "disp_haversine": 120.0,
            "vel_kinematic": 120.0,
            "acc_kinematic": 80.0,
            "jerk_kinematic": 50.0,
            "bearing_rate": 120.0,
            "HDOP": 1.2,
            "VDOP": 1.5,
            "fix_integrity": 0.70,
            "sat_count_tot": 18,
            "sat_churn": np.nan,
            "scenario_type": "SYNTHETIC/CONTROLLED"
        }
        bundle = self.engine.build_bundle(kinematic_attack_epoch, event_id="synth_kinematic_005")

        # Physical rules MUST trigger CRITICAL
        self.assertTrue(bundle.physical_rules["is_anomalous"])
        self.assertEqual(bundle.physical_rules["max_severity"], "CRITICAL")
        triggered_ids = [r["rule_id"] for r in bundle.physical_rules["triggered_rules"]]
        self.assertIn("PR_DISP_002", triggered_ids)
        self.assertIn("PR_ACC_002", triggered_ids)
        self.assertIn("PR_JERK_002", triggered_ids)

        # Isolation Forest should report high anomaly score
        if bundle.isolation_forest.get("anomaly_score") is not None:
            self.assertGreater(bundle.isolation_forest["anomaly_score"], 0.50)

    def test_scenario_6_navigation_quality_degradation(self):
        """Test Case 6 [SYNTHETIC/CONTROLLED]: Navigation quality collapse / RF geometry masking."""
        degraded_epoch = {
            "session_id": 999,
            "epoch_id": 600,
            "disp_haversine": 0.05,
            "vel_kinematic": 0.05,
            "acc_kinematic": 0.01,
            "jerk_kinematic": 0.005,
            "bearing_rate": 0.0,
            "HDOP": 9.8,                 # > 8.0 CRITICAL
            "VDOP": 12.5,                # > 10.0 CRITICAL
            "fix_integrity": 0.12,       # < 0.20 CRITICAL
            "sat_count_tot": 12,
            "sat_churn": 0.0,
            "scenario_type": "SYNTHETIC/CONTROLLED"
        }
        bundle = self.engine.build_bundle(degraded_epoch, event_id="synth_degraded_006")

        self.assertTrue(bundle.physical_rules["is_anomalous"])
        self.assertEqual(bundle.physical_rules["max_severity"], "CRITICAL")
        triggered_ids = [r["rule_id"] for r in bundle.physical_rules["triggered_rules"]]
        self.assertIn("PR_HDOP_002", triggered_ids)
        self.assertIn("PR_VDOP_002", triggered_ids)
        self.assertIn("PR_INT_002", triggered_ids)

    def test_scenario_7_satellite_behaviour_change(self):
        """Test Case 7 [SYNTHETIC/CONTROLLED]: Satellite starvation and sudden PRN turnover."""
        sat_attack_epoch = {
            "session_id": 999,
            "epoch_id": 700,
            "disp_haversine": 0.05,
            "vel_kinematic": 0.05,
            "acc_kinematic": 0.01,
            "jerk_kinematic": 0.005,
            "bearing_rate": 0.0,
            "HDOP": 2.5,
            "VDOP": 3.0,
            "fix_integrity": 0.55,
            "sat_count_tot": 3,          # < 4 CRITICAL trilateration failure
            "sat_churn": 0.85,           # > 0.60 CRITICAL constellation turnover
            "scenario_type": "SYNTHETIC/CONTROLLED"
        }
        bundle = self.engine.build_bundle(sat_attack_epoch, event_id="synth_sat_007")

        self.assertTrue(bundle.physical_rules["is_anomalous"])
        self.assertEqual(bundle.physical_rules["max_severity"], "CRITICAL")
        triggered_ids = [r["rule_id"] for r in bundle.physical_rules["triggered_rules"]]
        self.assertIn("PR_SAT_002", triggered_ids)
        self.assertIn("PR_CHURN_002", triggered_ids)

    def test_scenario_8_temporal_anomaly_sequence(self):
        """Test Case 8 [SYNTHETIC/CONTROLLED]: 10-epoch sliding window with creeping velocity drift."""
        if self.engine.temporal_detector is None or not self.engine.temporal_detector.is_fitted:
            self.skipTest("Temporal detector not loaded.")

        self.engine.temporal_detector.reset_buffer()
        session_id = 888

        # Feed 10 synthetic epochs with escalating kinematic drift
        last_result = None
        for step in range(10):
            epoch = {
                "session_id": session_id,
                "epoch_id": 800 + step,
                "disp_haversine": 0.5 * step,
                "vel_kinematic": 1.5 * step,      # Creeping acceleration from 0 to 13.5 m/s
                "acc_kinematic": 1.5,
                "jerk_kinematic": 0.5,
                "bearing_rate": 5.0,
                "HDOP": 1.0,
                "VDOP": 1.2,
                "fix_integrity": 0.80,
                "sat_count_tot": 18,
                "sat_churn": 0.0,
                "scenario_type": "SYNTHETIC/CONTROLLED"
            }
            temp_out = self.engine.temporal_detector.process_epoch_stream(epoch)
            bundle = self.engine.build_bundle(epoch, event_id=f"synth_temp_{step}", precomputed_temp=temp_out)
            last_result = bundle

        # Window size is 10, so step 9 must produce INFERRED status
        self.assertEqual(last_result.temporal_model["status"], "INFERRED")
        self.assertGreater(last_result.temporal_model["reconstruction_error"], 0.0)


if __name__ == "__main__":
    unittest.main()
