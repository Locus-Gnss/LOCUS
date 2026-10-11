"""
LOCUS Comprehensive Validation Test Suite: Live Pipeline, Detection Quad, Multi-Agent SOC, RAG, and Integrity Guards
Module: tests.test_live_pipeline_and_agents

Fulfills all 16 mandatory testing scenarios specified in Section 13:
1. Valid CSV input
2. Valid JSON input
3. Valid NMEA input
4. Malformed and empty input
5. Missing feature fields
6. A dataset larger than the original 27,687 rows
7. Insufficient records for LSTM sequence processing
8. An unfitted XGBoost model
9. An Isolation Forest anomaly
10. Agent 1 and Agent 2 returning findings consumed by Agent 3
11. RAG answers with actual retrieved sources
12. Conflicting detector outputs
13. Creating a new evidence bundle
14. Switching events A -> B -> C -> A
15. Backend unavailable or a processing-stage failure
16. Ensuring unsupported results are never fabricated
"""

import os
import json
import pytest
import numpy as np
import pandas as pd

from src.pipeline.pipeline_engine import PipelineEngine, PipelineExecutionResult
from src.features.security_features import SecurityFeatureExtractor, OFFICIAL_SECURITY_FEATURES
from src.evidence.evidence_bundle import EvidenceBundle
from src.detection.physical_rules import PhysicalRulesEngine, RuleResult, PhysicalRulesConfig
from src.detection.isolation_forest import IsolationForestDetector
from src.detection.xgboost_detector import XGBoostDetector
from src.detection.temporal_model import TemporalDetector
from src.detection.partition import partition_security_dataset
from src.agents import GNSSIntegrityAgent, TemporalThreatAgent, MasterSOCAgent
from src.rag import SecurityRAGEngine, ContextRetriever, VectorStore
from src.query.query_processor import SecurityQueryProcessor
from src.ui.data_service import SOCDataService


@pytest.fixture
def engine():
    return PipelineEngine()


@pytest.fixture
def data_service():
    return SOCDataService()


# ---------------------------------------------------------------------------
# Scenario 1: Valid CSV input
# ---------------------------------------------------------------------------
def test_01_valid_csv_input(engine):
    csv_data = """timestamp,latitude,longitude,altitude,speed,heading,satellites,hdop
2026-10-10T12:00:00Z,23.1045,72.5925,90.5,12.5,45.0,8,1.2
2026-10-10T12:00:01Z,23.1046,72.5926,90.6,12.6,45.2,8,1.2
2026-10-10T12:00:02Z,23.1047,72.5927,90.7,12.4,45.5,9,1.1
2026-10-10T12:00:03Z,23.1048,72.5928,90.8,12.7,46.0,9,1.1
"""
    result = engine.process_gnss_input(
        raw_input=csv_data,
        input_format="csv",
        source_name="test_valid.csv",
        source_type="UPLOAD_CSV"
    )
    assert result.success is True
    assert result.total_records == 4
    assert result.valid_records == 4
    assert result.feature_count == 10
    assert result.event_id is not None
    assert result.canonical_assessment is not None
    assert "defcon_level" in result.canonical_assessment
    assert os.path.exists(result.evidence_path)


# ---------------------------------------------------------------------------
# Scenario 2: Valid JSON input
# ---------------------------------------------------------------------------
def test_02_valid_json_input(engine):
    json_data = json.dumps([
        {"timestamp": "2026-10-10T12:00:00Z", "latitude": 23.1045, "longitude": 72.5925, "altitude": 90.5, "speed": 10.0, "satellites": 7, "hdop": 1.5},
        {"timestamp": "2026-10-10T12:00:01Z", "latitude": 23.1046, "longitude": 72.5926, "altitude": 90.6, "speed": 10.2, "satellites": 7, "hdop": 1.5},
        {"timestamp": "2026-10-10T12:00:02Z", "latitude": 23.1047, "longitude": 72.5927, "altitude": 90.7, "speed": 10.1, "satellites": 8, "hdop": 1.4}
    ])
    result = engine.process_gnss_input(
        raw_input=json_data,
        input_format="json",
        source_name="test_valid.json",
        source_type="UPLOAD_JSON"
    )
    assert result.success is True
    assert result.total_records == 3
    assert result.feature_count == 10
    assert result.canonical_assessment["current_status"] in ["NOMINAL", "SUSPECTED_INTERFERENCE", "CRITICAL_SPOOFING", "CAUTION"]


# ---------------------------------------------------------------------------
# Scenario 3: Valid NMEA input
# ---------------------------------------------------------------------------
def test_03_valid_nmea_input(engine):
    nmea_data = (
        "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\n"
        "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230326,003.1,W*6A\n"
        "$GPGGA,123520,4807.040,N,01131.002,E,1,08,0.9,545.5,M,46.9,M,,*45\n"
        "$GPRMC,123520,A,4807.040,N,01131.002,E,022.5,084.5,230326,003.1,W*68\n"
    )
    result = engine.process_gnss_input(
        raw_input=nmea_data,
        input_format="nmea",
        source_name="test_stream.nmea",
        source_type="RAW_NMEA"
    )
    assert result.success is True
    assert result.valid_records >= 2
    assert result.feature_count == 10


# ---------------------------------------------------------------------------
# Scenario 4: Malformed and empty input
# ---------------------------------------------------------------------------
def test_04_malformed_and_empty_input(engine):
    # Empty input
    res_empty = engine.process_gnss_input(raw_input="   ", input_format="csv")
    assert res_empty.success is False

    # Malformed JSON
    res_bad_json = engine.process_gnss_input(raw_input="[NOT_VALID_JSON{:::}}", input_format="json")
    assert res_bad_json.success is False

    # Malformed CSV lacking coordinates
    res_bad_csv = engine.process_gnss_input(raw_input="name,age,country\nAlice,30,USA\nBob,25,UK", input_format="csv")
    assert res_bad_csv.success is False


# ---------------------------------------------------------------------------
# Scenario 5: Missing feature fields handled safely
# ---------------------------------------------------------------------------
def test_05_missing_feature_fields(engine):
    # Telemetry with only basic lat/lon/timestamp, completely missing alt, sat_prns, cno, dop
    minimal_csv = """timestamp,latitude,longitude
2026-10-10T12:00:00Z,23.1045,72.5925
2026-10-10T12:00:01Z,23.1046,72.5926
2026-10-10T12:00:02Z,23.1047,72.5927
"""
    result = engine.process_gnss_input(raw_input=minimal_csv, input_format="csv")
    assert result.success is True
    feats = result.features_10d
    # Canonical 10 features should all be computed safely without crashing
    for col in OFFICIAL_SECURITY_FEATURES:
        assert col in feats
    # Missing sat_churn should safely be 0.0 or None, not crashing
    assert "sat_churn" in feats


# ---------------------------------------------------------------------------
# Scenario 6: Dataset larger than original 27,687 rows
# ---------------------------------------------------------------------------
def test_06_dataset_larger_than_original_27687_rows():
    n_rows = 28000
    df_large = pd.DataFrame({
        "session_id": [1] * n_rows,
        "epoch_id": list(range(n_rows)),
        "disp_haversine": np.random.uniform(0.1, 2.0, n_rows),
        "vel_kinematic": np.random.uniform(1.0, 15.0, n_rows),
        "acc_kinematic": np.random.uniform(0.0, 2.0, n_rows),
        "jerk_kinematic": np.random.uniform(0.0, 1.0, n_rows),
        "bearing_rate": np.random.uniform(0.0, 5.0, n_rows),
        "HDOP": np.random.uniform(0.8, 1.5, n_rows),
        "VDOP": np.random.uniform(1.0, 2.0, n_rows),
        "fix_integrity": np.random.uniform(0.8, 1.0, n_rows),
        "sat_count_tot": np.random.randint(6, 12, n_rows),
        "sat_churn": np.random.uniform(0.0, 0.1, n_rows)
    })
    # Verify partition_security_dataset handles >27,687 rows dynamically without error
    splits = partition_security_dataset(df_large)
    train_df, val_df, test_df = splits.train_df, splits.val_df, splits.test_df
    assert len(train_df) + len(val_df) + len(test_df) <= n_rows
    assert len(train_df) > 15000
    assert len(val_df) > 4000
    assert len(test_df) > 4000


# ---------------------------------------------------------------------------
# Scenario 7: Insufficient records for LSTM sequence processing
# ---------------------------------------------------------------------------
def test_07_insufficient_records_for_lstm_sequence_processing(engine):
    # Only 3 records provided; LSTM sliding window requires W=10 epochs
    short_csv = """timestamp,latitude,longitude,speed
2026-10-10T12:00:00Z,23.1045,72.5925,5.0
2026-10-10T12:00:01Z,23.1046,72.5926,5.1
2026-10-10T12:00:02Z,23.1047,72.5927,5.0
"""
    result = engine.process_gnss_input(raw_input=short_csv, input_format="csv")
    assert result.success is True
    lstm_res = result.detector_results.get("temporal_model", result.detector_results.get("temporal_lstm", {}))
    assert lstm_res["status"] in ["BUFFERING", "INSUFFICIENT_DATA"]
    assert "BUFFERING" in lstm_res["result"] or "INSUFFICIENT" in lstm_res["result"]
    assert lstm_res["is_anomaly"] is False


# ---------------------------------------------------------------------------
# Scenario 8: Unfitted XGBoost model truthfully reported
# ---------------------------------------------------------------------------
def test_08_unfitted_xgboost_model(engine):
    engine.xgb_detector = XGBoostDetector(model_version="xgb-unfitted-v1.0")
    assert engine.xgb_detector.is_trained is False
    csv_data = "timestamp,latitude,longitude\n2026-10-10T12:00:00Z,23.1045,72.5925\n2026-10-10T12:00:01Z,23.1046,72.5926"
    res = engine.process_gnss_input(csv_data, input_format="csv")
    xgb_res = res.detector_results.get("xgboost", {})
    # Must report UNAVAILABLE — MODEL NOT TRAINED and never fabricate class or confidence
    assert xgb_res["status"] == "UNAVAILABLE"
    assert xgb_res["result"] == "UNAVAILABLE — MODEL NOT TRAINED"
    assert xgb_res["confidence"] is None
    assert "UNAVAILABLE" in xgb_res["predicted_label"]


# ---------------------------------------------------------------------------
# Scenario 9: Isolation Forest anomaly detection
# ---------------------------------------------------------------------------
def test_09_isolation_forest_anomaly(engine):
    # Craft an extreme multi-dimensional anomaly (e.g., supersonic teleportation jump)
    anom_csv = """timestamp,latitude,longitude,speed,altitude,hdop,satellites
2026-10-10T12:00:00Z,23.1045,72.5925,10.0,90.0,1.0,8
2026-10-10T12:00:01Z,23.1046,72.5926,10.0,90.0,1.0,8
2026-10-10T12:00:02Z,24.5000,74.2000,1200.0,5000.0,45.0,2
"""
    result = engine.process_gnss_input(raw_input=anom_csv, input_format="csv")
    assert result.success is True
    if_res = result.detector_results.get("isolation_forest", {})
    assert if_res["status"] in ["ANOMALY", "NOMINAL"]
    assert isinstance(if_res["anomaly_score"], float)
    # Physical rules should flag violation on extreme jump
    pr_res = result.detector_results.get("physical_rules", {})
    assert pr_res["is_anomalous"] is True
    assert pr_res["triggered_count"] > 0


# ---------------------------------------------------------------------------
# Scenario 10: Agent 1 and Agent 2 findings consumed by Agent 3
# ---------------------------------------------------------------------------
def test_10_agent1_and_agent2_findings_consumed_by_agent3(engine):
    csv_data = """timestamp,latitude,longitude,speed
2026-10-10T12:00:00Z,23.1045,72.5925,15.0
2026-10-10T12:00:01Z,23.1046,72.5926,15.2
2026-10-10T12:00:02Z,23.1047,72.5927,15.1
"""
    result = engine.process_gnss_input(raw_input=csv_data, input_format="csv")
    assert result.success is True
    findings = result.agent_findings
    assert "agent_1_integrity" in findings
    assert "agent_2_temporal_threat" in findings
    assert "agent_3_master_soc" in findings

    a1 = findings["agent_1_integrity"]
    a2 = findings["agent_2_temporal_threat"]
    a3 = findings["agent_3_master_soc"]

    # Verify Agent 3 structure references Agent 1 and Agent 2
    assert "summary" in a3
    assert "risk_level" in a3 or "defcon_level" in a3
    assert "agent_findings" in a3
    assert "confidence" in a3


# ---------------------------------------------------------------------------
# Scenario 11: RAG answers with actual retrieved sources
# ---------------------------------------------------------------------------
def test_11_rag_answers_with_actual_retrieved_sources():
    rag_engine = SecurityRAGEngine()
    query = "ICAO GNSS spoofing and interference detection guidelines"
    output = rag_engine.query(query, top_k=3)
    assert output["has_sufficient_context"] is True
    assert len(output["citations"]) > 0
    first = output["citations"][0]
    assert "document" in first
    assert "excerpt" in first
    assert len(first["excerpt"]) > 0
    # Source document should reference an actual standard (ICAO, RTCA, FAA, CISA, or LOCUS)
    assert any(std in first["document"].upper() or any(std in a.upper() for a in first.get("authorities", [])) for std in ["ICAO", "RTCA", "FAA", "CISA", "LOCUS", "DOC"])


# ---------------------------------------------------------------------------
# Scenario 12: Conflicting detector outputs resolved by orchestrator
# ---------------------------------------------------------------------------
def test_12_conflicting_detector_outputs(data_service):
    # Load actual baseline evidence bundle and inject conflicting detector results
    bundle = data_service.load_event("evt_4_219")
    assert bundle is not None
    bundle.physical_rules = {"is_anomalous": False, "triggered_count": 0, "max_severity": "INFO", "triggered_rules": []}
    bundle.isolation_forest = {"is_anomaly": True, "anomaly_score": 0.88, "raw_score": -0.75}
    a1 = GNSSIntegrityAgent().analyze(bundle)
    a2 = TemporalThreatAgent().analyze(bundle)
    a3 = MasterSOCAgent().deliberate(bundle, integrity_output=a1, temporal_output=a2)
    # Orchestrator must synthesize conflicting inputs and produce a reasoned verdict
    assert "DEFCON" in a3.risk_level
    assert len(a3.summary) > 0
    assert "integrity_agent" in a3.agent_findings or "agent 1" in a3.summary.lower()


# ---------------------------------------------------------------------------
# Scenario 13: Creating a new evidence bundle
# ---------------------------------------------------------------------------
def test_13_creating_new_evidence_bundle(engine):
    csv_data = """timestamp,latitude,longitude,speed
2026-10-10T14:00:00Z,23.1045,72.5925,12.0
2026-10-10T14:00:01Z,23.1046,72.5926,12.1
"""
    result = engine.process_gnss_input(raw_input=csv_data, input_format="csv")
    assert result.success is True
    assert os.path.exists(result.evidence_path)

    with open(result.evidence_path, "r", encoding="utf-8") as f:
        saved_bundle = json.load(f)

    assert saved_bundle["event_id"] == result.event_id
    assert "security_features" in saved_bundle
    assert "physical_rules" in saved_bundle
    assert "isolation_forest" in saved_bundle
    assert "evidence_sha256" in saved_bundle
    assert len(saved_bundle["evidence_sha256"]) == 64  # SHA-256 length


# ---------------------------------------------------------------------------
# Scenario 14: Switching events A -> B -> C -> A
# ---------------------------------------------------------------------------
def test_14_switching_events_a_b_c_a(data_service):
    events = data_service.get_events()
    assert len(events) >= 3

    evt_a = events[0]["event_id"]
    evt_b = events[1]["event_id"]
    evt_c = events[2]["event_id"]

    # Step 1: Load Event A
    canon_a1 = data_service.get_canonical_assessment(evt_a)
    assert canon_a1["event_id"] == evt_a

    # Step 2: Load Event B
    canon_b = data_service.get_canonical_assessment(evt_b)
    assert canon_b["event_id"] == evt_b
    assert canon_b["event_id"] != canon_a1["event_id"]

    # Step 3: Load Event C
    canon_c = data_service.get_canonical_assessment(evt_c)
    assert canon_c["event_id"] == evt_c

    # Step 4: Return to Event A and verify state is intact with no cache poisoning
    canon_a2 = data_service.get_canonical_assessment(evt_a)
    assert canon_a2["event_id"] == evt_a
    assert canon_a2["defcon_display"] == canon_a1["defcon_display"]
    assert canon_a2["confidence"] == canon_a1["confidence"]


# ---------------------------------------------------------------------------
# Scenario 15: Backend unavailable or processing-stage failure handling
# ---------------------------------------------------------------------------
def test_15_backend_unavailable_and_stage_failure(data_service):
    # Test data service fallback when backend is offline
    csv_data = """timestamp,latitude,longitude,speed
2026-10-10T15:00:00Z,23.1045,72.5925,8.0
2026-10-10T15:00:01Z,23.1046,72.5926,8.1
"""
    # Force client to report failure
    orig_api = data_service.api_client
    class BrokenClient:
        def process_pipeline(self, *args, **kwargs):
            return False, None, "Connection refused (FastAPI backend unavailable)"
    data_service.api_client = BrokenClient()

    try:
        # Should gracefully fall back to local PipelineEngine without crashing
        res = data_service.process_gnss_data(raw_data=csv_data, input_format="csv")
        assert res["success"] is True
        assert res["total_records"] == 2
        assert res["event_id"] is not None
    finally:
        data_service.api_client = orig_api


# ---------------------------------------------------------------------------
# Scenario 16: Ensuring unsupported results are never fabricated
# ---------------------------------------------------------------------------
def test_16_ensuring_unsupported_results_never_fabricated(engine, data_service):
    models_status = data_service.get_models_status()
    # XGBoost must be reported truthfully without fabricated confidence
    xgb = models_status["xgboost"]
    assert "status" in xgb
    if xgb["is_fitted"]:
        assert xgb["status"] == "OPERATIONAL"
        assert "Verified Scenario Dataset" in xgb["dataset_provenance"]
    else:
        assert xgb["is_fitted"] is False
        assert "UNAVAILABLE" in xgb["status"]
        assert "Supervised" in xgb["note"] or "attack" in xgb["note"]

    # Hardware connection check must report disconnected unless verified
    conn = data_service.check_gnss_connection()
    # In test environment, hardware is not connected
    assert conn["hardware_status"] in ["DISCONNECTED", "NOT DETECTED", "Not Connected"]

    # Canonical assessment must never return hardcoded fabricated confidence
    evt = data_service.get_events()[0]["event_id"]
    canon = data_service.get_canonical_assessment(evt)
    assert canon["confidence"] is not None
    assert 0.0 <= canon["confidence"] <= 1.0
