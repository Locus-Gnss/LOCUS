"""
tests/test_soc_agents.py - Unit & Integration Tests for LOCUS Phase 6 3-Agent Security SOC.

Validates:
1. Agent 1: GNSS Integrity Agent (Newtonian invariants, geometry dilation, health scoring).
2. Agent 2: Temporal Threat Correlation Agent (persistence streaks, multi-detector convergence, feature attribution).
3. Agent 3: Master SOC Orchestrator (consensus resolution, DEFCON rating, mitigation directives).
4. SOC Pipeline: End-to-end multi-agent execution, incident logging, and stream processing.
"""

import os
import json
import shutil
import tempfile
import unittest
import numpy as np

from src.soc.models import (
    DefconLevel,
    IntegrityStatus,
    ThreatClassification,
    MitigationAction,
    Agent1Assessment,
    Agent2Assessment,
    SOCIncidentReport,
)
from src.soc.integrity_agent import GNSSIntegrityAgent
from src.soc.temporal_threat_agent import TemporalThreatAgent
from src.soc.master_soc_orchestrator import MasterSOCOrchestrator
from src.soc.soc_pipeline import SOCPipeline


class TestGNSSIntegrityAgent(unittest.TestCase):
    def setUp(self):
        self.agent = GNSSIntegrityAgent()

    def test_benign_stationary_epoch(self):
        bundle = {
            "event_id": "evt_test_benign",
            "session_id": 1,
            "epoch_id": 10,
            "security_features": {
                "disp_haversine": 0.05,
                "vel_kinematic": 0.05,
                "acc_kinematic": 0.01,
                "jerk_kinematic": 0.005,
                "bearing_rate": 0.0,
                "HDOP": 0.9,
                "VDOP": 1.2,
                "fix_integrity": 0.95,
                "sat_count_tot": 16.0,
            },
            "physical_rules": {
                "is_anomalous": False,
                "triggered_count": 0,
                "max_severity": "INFO",
                "triggered_rules": [],
            },
            "data_quality": {
                "fix_quality": 1,
                "satellites_used": 16,
            }
        }
        res = self.agent.assess(bundle)
        self.assertEqual(res.integrity_status, IntegrityStatus.NOMINAL)
        self.assertFalse(res.discard_recommended)
        self.assertAlmostEqual(res.kinematic_health, 1.0)
        self.assertAlmostEqual(res.geometry_health, 1.0)
        self.assertGreater(res.confidence_score, 0.9)

    def test_critical_coordinate_jump(self):
        bundle = {
            "event_id": "evt_test_jump",
            "session_id": 1,
            "epoch_id": 11,
            "security_features": {
                "disp_haversine": 120.0,     # > 100m critical
                "vel_kinematic": 120.0,      # > 85 m/s critical
                "acc_kinematic": 115.0,      # > 10 m/s² critical
                "jerk_kinematic": 75.0,      # > 25 m/s³ critical
                "bearing_rate": 180.0,
                "HDOP": 1.1,
                "VDOP": 1.5,
                "fix_integrity": 0.85,
                "sat_count_tot": 14.0,
            },
            "physical_rules": {
                "is_anomalous": True,
                "triggered_count": 4,
                "max_severity": "CRITICAL",
                "triggered_rules": [{"rule_id": "PR_ACC_001"}, {"rule_id": "PR_JERK_001"}],
            }
        }
        res = self.agent.assess(bundle)
        self.assertEqual(res.integrity_status, IntegrityStatus.CRITICAL_INVARIANT_BREACH)
        self.assertTrue(res.discard_recommended)
        self.assertLess(res.kinematic_health, 0.3)
        self.assertIn("CRITICAL", res.verdict_summary)

    def test_geometry_degradation(self):
        bundle = {
            "event_id": "evt_test_geom",
            "session_id": 1,
            "epoch_id": 12,
            "security_features": {
                "disp_haversine": 0.02,
                "vel_kinematic": 0.02,
                "acc_kinematic": 0.0,
                "jerk_kinematic": 0.0,
                "bearing_rate": 0.0,
                "HDOP": 9.2,                 # > 8.0 critical
                "VDOP": 11.5,
                "fix_integrity": 0.18,
                "sat_count_tot": 3.0,        # < 4 critical
            },
            "physical_rules": {
                "is_anomalous": True,
                "triggered_count": 2,
                "max_severity": "LOW",
                "triggered_rules": [{"rule_id": "PR_HDOP_001"}],
            }
        }
        res = self.agent.assess(bundle)
        self.assertEqual(res.integrity_status, IntegrityStatus.GEOMETRY_DEGRADED)
        self.assertLess(res.geometry_health, 0.5)


class TestTemporalThreatAgent(unittest.TestCase):
    def setUp(self):
        self.agent = TemporalThreatAgent(
            history_window_size=10,
            persistence_streak_threshold=3
        )

    def test_benign_stream(self):
        bundle = {
            "event_id": "evt_t_01",
            "session_id": 1,
            "epoch_id": 1,
            "isolation_forest": {"is_anomaly": False, "anomaly_score": 0.12},
            "temporal_model": {"status": "INFERRED", "is_anomaly": False, "temporal_anomaly_score": 0.08},
            "physical_rules": {"is_anomalous": False},
            "security_features": {"disp_haversine": 0.05, "acc_kinematic": 0.02, "sat_count_tot": 15.0}
        }
        res = self.agent.assess(bundle)
        self.assertEqual(res.threat_classification, ThreatClassification.BENIGN)
        self.assertEqual(res.persistence_count, 0)
        self.assertAlmostEqual(res.persistence_ratio, 0.0)

    def test_transient_anomaly_vs_sustained_drift(self):
        # Epoch 1: single anomaly -> transient
        b_anom = {
            "event_id": "evt_t_02",
            "session_id": 1,
            "epoch_id": 2,
            "isolation_forest": {"is_anomaly": True, "anomaly_score": 0.75},
            "temporal_model": {"status": "INFERRED", "is_anomaly": False, "temporal_anomaly_score": 0.3},
            "physical_rules": {"is_anomalous": False},
            "security_features": {"disp_haversine": 1.2, "acc_kinematic": 0.5, "HDOP": 2.5, "sat_count_tot": 12.0}
        }
        res1 = self.agent.assess(b_anom)
        self.assertIn(res1.threat_classification, [ThreatClassification.TRANSIENT_ANOMALY, ThreatClassification.MULTIPATH_INTERFERENCE])
        self.assertEqual(res1.persistence_count, 1)

        # Epochs 2, 3, 4: sustained anomalies -> persistent drift
        for ep in range(3, 6):
            b_drift = {
                "event_id": f"evt_t_0{ep}",
                "session_id": 1,
                "epoch_id": ep,
                "isolation_forest": {"is_anomaly": True, "anomaly_score": 0.82},
                "temporal_model": {
                    "status": "INFERRED",
                    "is_anomaly": True,
                    "temporal_anomaly_score": 0.78,
                    "reconstruction_error": 0.045,
                    "feature_errors": {"vel_kinematic": 0.12, "disp_haversine": 0.09, "acc_kinematic": 0.07}
                },
                "physical_rules": {"is_anomalous": False},
                "security_features": {"disp_haversine": 8.5, "vel_kinematic": 8.5, "acc_kinematic": 1.2, "sat_count_tot": 12.0}
            }
            res_drift = self.agent.assess(b_drift)

        # By epoch 4 in streak (streak >= 3), classification should be persistent drift / trajectory injection
        self.assertGreaterEqual(res_drift.persistence_count, 3)
        self.assertIn(
            res_drift.threat_classification,
            [ThreatClassification.SPOOFING_TRAJECTORY_INJECTION, ThreatClassification.PERSISTENT_DRIFT]
        )
        self.assertIn("vel_kinematic", res_drift.primary_feature_contributors)

    def test_rf_jamming_starvation(self):
        bundle = {
            "event_id": "evt_t_jam",
            "session_id": 1,
            "epoch_id": 7,
            "isolation_forest": {"is_anomaly": True, "anomaly_score": 0.90},
            "temporal_model": {"status": "INFERRED", "is_anomaly": True, "temporal_anomaly_score": 0.85},
            "physical_rules": {"is_anomalous": True},
            "security_features": {"disp_haversine": 0.0, "acc_kinematic": 0.0, "HDOP": 8.5, "sat_count_tot": 2.0}
        }
        res = self.agent.assess(bundle)
        self.assertEqual(res.threat_classification, ThreatClassification.RF_JAMMING_DEGRADATION)


class TestMasterSOCOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = MasterSOCOrchestrator()

    def test_defcon_5_nominal_resolution(self):
        a1 = Agent1Assessment(
            integrity_status=IntegrityStatus.NOMINAL,
            confidence_score=0.98,
            kinematic_health=1.0,
            geometry_health=1.0
        )
        a2 = Agent2Assessment(
            threat_classification=ThreatClassification.BENIGN,
            confidence_score=0.98,
            persistence_count=0
        )
        bundle = {"event_id": "evt_def5", "session_id": 1, "epoch_id": 1, "security_features": {}}
        report = self.orchestrator.correlate_and_resolve(bundle, a1, a2)

        self.assertEqual(report.defcon_level, DefconLevel.DEFCON_5)
        self.assertEqual(report.attack_vector, "BENIGN_NOMINAL")
        self.assertIn(MitigationAction.MAINTAIN_STANDARD_FIX.value, report.mitigation_actions)

    def test_defcon_1_critical_spoofing_resolution(self):
        a1 = Agent1Assessment(
            integrity_status=IntegrityStatus.CRITICAL_INVARIANT_BREACH,
            confidence_score=0.95,
            kinematic_health=0.1,
            geometry_health=0.9,
            discard_recommended=True,
            violated_rules=["PR_ACC_001", "PR_JERK_001"]
        )
        a2 = Agent2Assessment(
            threat_classification=ThreatClassification.SPOOFING_COORDINATE_STEP,
            confidence_score=0.95,
            persistence_count=1,
            detector_convergence=0.75,
            primary_feature_contributors=["disp_haversine", "acc_kinematic"]
        )
        bundle = {
            "event_id": "evt_def1",
            "session_id": 2,
            "epoch_id": 45,
            "security_features": {"disp_haversine": 150.0, "acc_kinematic": 140.0}
        }
        report = self.orchestrator.correlate_and_resolve(bundle, a1, a2)

        self.assertEqual(report.defcon_level, DefconLevel.DEFCON_1)
        self.assertEqual(report.attack_vector, "SPOOFING_COORDINATE_STEP")
        self.assertIn(MitigationAction.EMERGENCY_GNSS_LOCKOUT.value, report.mitigation_actions)
        self.assertIn(MitigationAction.REJECT_EPOCH_MEASUREMENT.value, report.mitigation_actions)
        self.assertEqual(report.consensus_status, "UNANIMOUS")

    def test_defcon_2_persistent_drift_resolution(self):
        a1 = Agent1Assessment(
            integrity_status=IntegrityStatus.KINEMATIC_VIOLATION,
            confidence_score=0.85,
            kinematic_health=0.6,
            geometry_health=0.9
        )
        a2 = Agent2Assessment(
            threat_classification=ThreatClassification.SPOOFING_TRAJECTORY_INJECTION,
            confidence_score=0.90,
            persistence_count=5,
            persistence_ratio=0.5,
            detector_convergence=0.66
        )
        bundle = {"event_id": "evt_def2", "session_id": 3, "epoch_id": 80, "security_features": {}}
        report = self.orchestrator.correlate_and_resolve(bundle, a1, a2)

        self.assertEqual(report.defcon_level, DefconLevel.DEFCON_2)
        self.assertEqual(report.attack_vector, "SPOOFING_TRAJECTORY_INJECTION")
        self.assertIn(MitigationAction.SWITCH_TO_INERTIAL_DEAD_RECKONING.value, report.mitigation_actions)


class TestSOCPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.pipeline = SOCPipeline(incidents_dir=self.temp_dir)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_end_to_end_stream_execution(self):
        synthetic_stream = [
            # Epoch 1: Benign
            {
                "event_id": "evt_stream_01",
                "session_id": 1,
                "epoch_id": 1,
                "security_features": {"disp_haversine": 0.05, "acc_kinematic": 0.01, "HDOP": 0.8, "sat_count_tot": 16.0},
                "physical_rules": {"is_anomalous": False, "max_severity": "INFO", "triggered_rules": []},
                "isolation_forest": {"is_anomaly": False, "anomaly_score": 0.15},
                "temporal_model": {"status": "INFERRED", "is_anomaly": False, "temporal_anomaly_score": 0.1}
            },
            # Epoch 2: Degraded geometry
            {
                "event_id": "evt_stream_02",
                "session_id": 1,
                "epoch_id": 2,
                "security_features": {"disp_haversine": 0.1, "acc_kinematic": 0.05, "HDOP": 5.5, "sat_count_tot": 5.0},
                "physical_rules": {"is_anomalous": False, "max_severity": "LOW", "triggered_rules": []},
                "isolation_forest": {"is_anomaly": False, "anomaly_score": 0.3},
                "temporal_model": {"status": "INFERRED", "is_anomaly": False, "temporal_anomaly_score": 0.2}
            },
            # Epoch 3: Hostile spoofer jump
            {
                "event_id": "evt_stream_03",
                "session_id": 1,
                "epoch_id": 3,
                "security_features": {"disp_haversine": 110.0, "acc_kinematic": 105.0, "HDOP": 1.2, "sat_count_tot": 14.0},
                "physical_rules": {"is_anomalous": True, "max_severity": "CRITICAL", "triggered_rules": [{"rule_id": "PR_ACC_001"}]},
                "isolation_forest": {"is_anomaly": True, "anomaly_score": 0.92},
                "temporal_model": {"status": "INFERRED", "is_anomaly": True, "temporal_anomaly_score": 0.88}
            }
        ]

        incidents, summary = self.pipeline.process_bundle_stream(synthetic_stream, save_incidents=True)

        self.assertEqual(len(incidents), 3)
        self.assertEqual(incidents[0].defcon_level, DefconLevel.DEFCON_5)
        self.assertEqual(incidents[1].defcon_level, DefconLevel.DEFCON_4)
        self.assertEqual(incidents[2].defcon_level, DefconLevel.DEFCON_1)

        # Check summary metrics
        self.assertEqual(summary["total_epochs_processed"], 3)
        self.assertEqual(summary["defcon_distribution"]["DEFCON_1"], 1)
        self.assertEqual(summary["defcon_distribution"]["DEFCON_4"], 1)
        self.assertEqual(summary["defcon_distribution"]["DEFCON_5"], 1)

        # Verify files were created
        files = os.listdir(self.temp_dir)
        self.assertTrue(any(f.endswith(".jsonl") for f in files))
        self.assertTrue(any("defcon_1" in f for f in files))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "soc_run_summary.json")))


if __name__ == "__main__":
    unittest.main()
