"""
tests/test_detection.py - Unit & Integration Tests for LOCUS Phase 5 Detection & Evidence Fusion.

Validates:
1. Physical Plausibility Rules (kinematic thresholds, navigation quality, severity levels).
2. Isolation Forest Detector (loading, inference, score normalization, imputation).
3. XGBoost Classifier Infrastructure (provenance safeguards, prediction API).
4. LSTM Temporal Detector (session-aware windowing, reconstruction error, tensor shapes).
5. Evidence Fusion Engine (bundle schema, serialization, multi-detector aggregation).
"""

import os
import json
import unittest
import numpy as np
import pandas as pd
import torch

from src.detection.physical_rules import (
    PhysicalRulesEngine,
    PhysicalRulesConfig,
    RuleResult,
)
from src.detection.isolation_forest import (
    IsolationForestDetector,
    OFFICIAL_SECURITY_FEATURES,
)
from src.detection.xgboost_detector import XGBoostDetector
from src.detection.temporal_model import (
    TemporalDetector,
    LSTMAutoencoder,
)
from src.evidence.evidence_bundle import (
    EvidenceBundle,
    EvidenceFusionEngine,
    LocationData,
)


class TestPhysicalRulesEngine(unittest.TestCase):
    def setUp(self):
        self.cfg = PhysicalRulesConfig()
        self.engine = PhysicalRulesEngine(config=self.cfg)

    def test_benign_stationary_epoch(self):
        benign_epoch = {
            "disp_haversine": 0.08,
            "vel_kinematic": 0.08,
            "acc_kinematic": 0.02,
            "jerk_kinematic": 0.01,
            "bearing_rate": 0.0,
            "HDOP": 0.85,
            "VDOP": 1.20,
            "fix_integrity": 0.95,
            "sat_count_tot": 18,
            "sat_churn": np.nan,
        }
        evals = self.engine.evaluate_epoch(benign_epoch)
        summary = self.engine.get_summary(evals)

        self.assertFalse(summary["is_anomalous"])
        self.assertEqual(summary["triggered_count"], 0)
        self.assertEqual(summary["max_severity"], "INFO")

    def test_teleportation_and_acceleration_violations(self):
        spoofed_epoch = {
            "disp_haversine": 150.0,      # > 100m critical
            "vel_kinematic": 150.0,       # > 85m/s critical
            "acc_kinematic": 140.0,       # > 10m/s² critical
            "jerk_kinematic": 80.0,       # > 25m/s³ critical
            "bearing_rate": 180.0,
            "HDOP": 1.1,
            "VDOP": 1.5,
            "fix_integrity": 0.8,
            "sat_count_tot": 16,
            "sat_churn": np.nan,
        }
        evals = self.engine.evaluate_epoch(spoofed_epoch)
        summary = self.engine.get_summary(evals)

        self.assertTrue(summary["is_anomalous"])
        self.assertEqual(summary["max_severity"], "CRITICAL")
        self.assertGreater(summary["triggered_count"], 0)

    def test_degraded_geometry_and_starvation(self):
        degraded_epoch = {
            "disp_haversine": 0.0,
            "vel_kinematic": 0.0,
            "acc_kinematic": 0.0,
            "jerk_kinematic": 0.0,
            "bearing_rate": 0.0,
            "HDOP": 9.5,                 # > 8.0 critical
            "VDOP": 12.0,                # > 10.0 critical
            "fix_integrity": 0.12,       # < 0.20 critical
            "sat_count_tot": 3,          # < 4 critical
            "sat_churn": np.nan,
        }
        evals = self.engine.evaluate_epoch(degraded_epoch)
        summary = self.engine.get_summary(evals)

        self.assertTrue(summary["is_anomalous"])
        self.assertEqual(summary["max_severity"], "CRITICAL")
        self.assertGreater(summary["triggered_count"], 0)


class TestIsolationForestDetector(unittest.TestCase):
    def setUp(self):
        self.model_path = os.path.join("models", "isolation_forest.joblib")
        if os.path.exists(self.model_path):
            self.detector = IsolationForestDetector.load(self.model_path)
        else:
            self.detector = IsolationForestDetector()

    def test_loaded_model_inference(self):
        if not os.path.exists(self.model_path):
            self.skipTest("models/isolation_forest.joblib not present")

        self.assertTrue(self.detector.is_fitted)

        # Benign epoch
        benign_epoch = {
            "disp_haversine": 0.05,
            "vel_kinematic": 0.05,
            "acc_kinematic": 0.01,
            "jerk_kinematic": 0.005,
            "bearing_rate": 0.0,
            "HDOP": 0.8,
            "VDOP": 1.1,
            "fix_integrity": 0.95,
            "sat_count_tot": 18,
            "sat_churn": np.nan,
        }
        out = self.detector.predict_epoch(benign_epoch)
        self.assertIn("anomaly_score", out)
        self.assertIn("is_anomaly", out)
        self.assertGreaterEqual(out["anomaly_score"], 0.0)
        self.assertLessEqual(out["anomaly_score"], 1.0)

        # Extreme outlier
        extreme_epoch = {
            "disp_haversine": 250.0,
            "vel_kinematic": 250.0,
            "acc_kinematic": 150.0,
            "jerk_kinematic": 120.0,
            "bearing_rate": 180.0,
            "HDOP": 15.0,
            "VDOP": 20.0,
            "fix_integrity": 0.05,
            "sat_count_tot": 2,
            "sat_churn": 10.0,
        }
        out_ext = self.detector.predict_epoch(extreme_epoch)
        self.assertTrue(out_ext["is_anomaly"])
        self.assertGreater(out_ext["anomaly_score"], 0.6)


class TestXGBoostDetectorInfrastructure(unittest.TestCase):
    def setUp(self):
        self.detector = XGBoostDetector()

    def test_unfitted_inference_returns_honest_status(self):
        epoch = {feat: 1.0 for feat in OFFICIAL_SECURITY_FEATURES}
        out = self.detector.predict_epoch(epoch)
        self.assertIn("status", out)
        self.assertEqual(out["status"], "UNFITTED_PENDING_LABELLED_SCENARIOS")
        self.assertFalse(out["available"])


class TestTemporalDetector(unittest.TestCase):
    def setUp(self):
        self.weights_path = os.path.join("models", "temporal_model.pt")
        self.meta_path = os.path.join("models", "temporal_metadata.joblib")
        if os.path.exists(self.weights_path) and os.path.exists(self.meta_path):
            self.detector = TemporalDetector.load(self.weights_path, self.meta_path)
        else:
            self.detector = TemporalDetector(window_size=10)

    def test_session_aware_window_isolation(self):
        # Synthesize 2 sessions
        df_dummy = pd.DataFrame({
            "session_id": [1] * 15 + [2] * 8,
            "epoch_id": list(range(1, 16)) + list(range(1, 9)),
            "timestamp_utc": [f"2026-09-28T10:00:{i:02d}.000Z" for i in range(23)],
        })
        for feat in OFFICIAL_SECURITY_FEATURES:
            df_dummy[feat] = np.random.uniform(0.1, 1.0, size=23)

        windows, metadata = self.detector.generate_sequences(
            df_dummy,
            fit_preprocessor=True
        )
        # Session 1 has length 15 -> 15 - 10 + 1 = 6 windows
        # Session 2 has length 8 (< 10) -> 0 windows
        self.assertEqual(len(windows), 6)
        self.assertEqual(windows.shape, (6, 10, 10))

    def test_temporal_stream_inference(self):
        if not os.path.exists(self.weights_path):
            self.skipTest("models/temporal_model.pt not present")

        self.assertTrue(self.detector.is_fitted)
        self.detector.reset_buffer()

        # Push 9 epochs -> buffer filling, not yet ready
        for ep in range(1, 10):
            row = {feat: 0.1 for feat in OFFICIAL_SECURITY_FEATURES}
            row["session_id"] = 1
            row["epoch_id"] = ep
            res = self.detector.process_epoch_stream(row)
            self.assertEqual(res["status"], "BUFFERING")

        # 10th epoch completes the window -> inference occurs
        row10 = {feat: 0.1 for feat in OFFICIAL_SECURITY_FEATURES}
        row10["session_id"] = 1
        row10["epoch_id"] = 10
        res10 = self.detector.process_epoch_stream(row10)
        self.assertEqual(res10["status"], "INFERRED")
        self.assertIn("temporal_anomaly_score", res10)
        self.assertIn("reconstruction_error", res10)
        self.assertIn("feature_errors", res10)


class TestEvidenceFusionEngine(unittest.TestCase):
    def setUp(self):
        self.fusion = EvidenceFusionEngine(
            rules_engine=PhysicalRulesEngine(),
            iforest_detector=IsolationForestDetector(),
            xgb_detector=XGBoostDetector(),
            temporal_detector=TemporalDetector()
        )
        if os.path.exists(os.path.join("models", "isolation_forest.joblib")):
            self.fusion.iforest_detector.load(os.path.join("models", "isolation_forest.joblib"))

    def test_bundle_creation_and_serialization(self):
        epoch_data = {
            "session_id": 4,
            "epoch_id": 220,
            "timestamp_utc": "2026-09-28T07:15:30.000Z",
            "timestamp_pc": "2026-09-28T12:45:30.123+05:30",
            "latitude": 23.10432,
            "longitude": 72.59254,
            "altitude_m": 58.4,
            "disp_haversine": 0.07,
            "vel_kinematic": 0.07,
            "acc_kinematic": 0.01,
            "jerk_kinematic": 0.005,
            "bearing_rate": 0.0,
            "HDOP": 0.82,
            "VDOP": 1.15,
            "fix_integrity": 0.94,
            "sat_count_tot": 19,
            "sat_churn": np.nan,
            "fix_quality": 1,
            "satellites_used": 19,
            "satellites_in_view": 23,
            "avg_cno": 37.5,
            "data_quality_flag": "VALID",
        }

        bundle = self.fusion.build_bundle(epoch_data, event_id="evt_test_001")
        self.assertIsInstance(bundle, EvidenceBundle)
        self.assertEqual(bundle.event_id, "evt_test_001")
        self.assertEqual(bundle.session_id, 4)
        self.assertEqual(bundle.epoch_id, 220)

        # Validate JSON serialization
        json_str = bundle.to_json()
        data = json.loads(json_str)
        self.assertEqual(data["event_id"], "evt_test_001")
        self.assertIn("location", data)
        self.assertIn("security_features", data)
        self.assertIn("physical_rules", data)
        self.assertIn("isolation_forest", data)
        self.assertIn("xgboost", data)
        self.assertIn("temporal_model", data)
        self.assertIn("data_quality", data)
        self.assertIn("model_versions", data)

        # Check location
        self.assertAlmostEqual(data["location"]["latitude"], 23.10432)
        self.assertAlmostEqual(data["location"]["longitude"], 72.59254)

        # Check security features preserved
        self.assertEqual(len(data["security_features"]), 10)
        self.assertIsNone(data["security_features"]["sat_churn"])  # NaN serializes to None


if __name__ == "__main__":
    unittest.main()
