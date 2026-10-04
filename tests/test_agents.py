"""
Tests for LOCUS Phase 6 — Agentic Security SOC Layer.

Validates:
1. Agent 1: GNSSIntegrityAgent (physical plausibility, fix integrity, navigation quality, satellite behaviour)
2. Agent 2: TemporalThreatAgent (persistent anomalies, temporal patterns, LSTM/XGBoost correlations)
3. Agent 3: MasterSOCAgent (evidence synthesis, conflict resolution, DEFCON risk assessment, grounded citations)
4. Anti-Mutation Invariant: Sensor data and Evidence Bundles are never modified by any agent.
5. Anti-Fabrication Invariant: All cited evidence fields strictly map to verified inputs without hallucination.
"""

import copy
import pytest
from src.evidence.evidence_bundle import EvidenceBundle
from src.agents.integrity_agent import GNSSIntegrityAgent, IntegrityAssessment
from src.agents.temporal_threat_agent import TemporalThreatAgent, TemporalAssessment
from src.agents.master_soc_agent import MasterSOCAgent, SOCOrchestrationResult


def make_sample_bundle(
    disp_haversine=1.2,
    vel_kinematic=12.5,
    acc_kinematic=0.8,
    jerk_kinematic=0.2,
    bearing_rate=1.5,
    hdop=1.2,
    vdop=1.8,
    fix_integrity=0.95,
    sat_count_tot=10,
    sat_churn=0.05,
    rules_anom=False,
    rules_severity="INFO",
    if_score=-0.1,
    if_anom=False,
    lstm_error=0.02,
    lstm_thresh=0.08,
    lstm_anom=False,
    xgb_status="UNFITTED_PENDING_LABELLED_SCENARIOS",
    session_id=1,
    epoch_id=10
) -> EvidenceBundle:
    """Helper to construct a realistic Evidence Bundle for multi-agent evaluation."""
    sec_features = {
        "disp_haversine": disp_haversine,
        "vel_kinematic": vel_kinematic,
        "acc_kinematic": acc_kinematic,
        "jerk_kinematic": jerk_kinematic,
        "bearing_rate": bearing_rate,
        "HDOP": hdop,
        "VDOP": vdop,
        "fix_integrity": fix_integrity,
        "sat_count_tot": sat_count_tot,
        "sat_churn": sat_churn,
    }
    location = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "altitude_m": 15.0,
    }
    dq = {
        "fix_quality": 1,
        "satellites_used": sat_count_tot,
        "hdop": hdop,
        "data_quality_flag": "VALID",
    }
    bundle = EvidenceBundle(
        event_id=f"evt_sess_{session_id}_ep_{epoch_id}",
        timestamp_utc="2026-03-30T12:00:00Z",
        timestamp_pc="2026-03-30T12:00:00.050Z",
        session_id=session_id,
        epoch_id=epoch_id,
        location=location,
        security_features=sec_features,
        physical_rules={
            "triggered_rules": ["ACCELERATION_LIMIT"] if rules_anom else [],
            "is_anomalous": rules_anom,
            "max_severity": rules_severity,
            "triggered_count": 1 if rules_anom else 0,
            "rule_details": []
        },
        isolation_forest={
            "anomaly_score": if_score,
            "is_anomaly": if_anom,
            "status": "INFERRED"
        },
        xgboost={
            "status": xgb_status,
            "available": False
        },
        temporal_model={
            "reconstruction_error": lstm_error,
            "error_threshold": lstm_thresh,
            "is_anomaly": lstm_anom,
            "status": "INFERRED"
        },
        data_quality=dq,
        model_versions={
            "isolation_forest": "v5.5-tuned",
            "temporal_model": "v5.5-lstm-tuned"
        }
    )
    return bundle


# =============================================================================
# AGENT 1: GNSS INTEGRITY AGENT TESTS
# =============================================================================

def test_integrity_agent_nominal():
    """Agent 1 evaluates nominal GNSS features as INTEGRITY_NOMINAL."""
    agent = GNSSIntegrityAgent()
    bundle = make_sample_bundle()

    assessment = agent.assess(bundle)

    assert isinstance(assessment, IntegrityAssessment)
    assert assessment.integrity_assessment == "INTEGRITY_NOMINAL"
    assert assessment.confidence >= 0.90
    assert assessment.kinematic_health == 1.0
    assert assessment.geometry_health == 1.0
    assert assessment.physical_violation_count == 0
    assert not assessment.discard_recommended


def test_integrity_agent_physical_teleportation_breach():
    """Agent 1 detects impossible coordinate displacement as CRITICAL_INVARIANT_BREACH."""
    agent = GNSSIntegrityAgent()
    bundle = make_sample_bundle(disp_haversine=150.0)  # Teleportation > 100m

    assessment = agent.assess(bundle)

    assert assessment.integrity_assessment == "CRITICAL_INVARIANT_BREACH"
    assert assessment.discard_recommended is True
    assert assessment.physical_violation_count >= 1
    assert "disp_haversine" in assessment.feature_level_anomalies
    assert assessment.feature_level_anomalies["disp_haversine"]["observed_value"] == 150.0
    assert "teleportation" in assessment.explanation.lower()


def test_integrity_agent_extreme_acceleration():
    """Agent 1 flags extreme acceleration jump (> 10 m/s²) as CRITICAL_INVARIANT_BREACH."""
    agent = GNSSIntegrityAgent()
    bundle = make_sample_bundle(acc_kinematic=14.5)

    assessment = agent.assess(bundle)

    assert assessment.integrity_assessment == "CRITICAL_INVARIANT_BREACH"
    assert assessment.discard_recommended is True
    assert "acc_kinematic" in assessment.feature_level_anomalies
    assert assessment.feature_level_anomalies["acc_kinematic"]["severity"] == "CRITICAL"


def test_integrity_agent_geometry_degradation():
    """Agent 1 detects severe constellation dilution and churn as GEOMETRY_DEGRADED."""
    agent = GNSSIntegrityAgent()
    bundle = make_sample_bundle(
        hdop=9.5,            # Critical HDOP > 8.0
        vdop=12.0,           # Critical VDOP > 10.0
        sat_count_tot=3,     # Satellite starvation < 4
        sat_churn=0.75       # Extreme churn > 0.60
    )

    assessment = agent.assess(bundle)

    assert assessment.integrity_assessment == "GEOMETRY_DEGRADED"
    assert assessment.geometry_health < 0.50
    assert "HDOP" in assessment.feature_level_anomalies
    assert "sat_count_tot" in assessment.feature_level_anomalies


# =============================================================================
# AGENT 2: TEMPORAL / THREAT AGENT TESTS
# =============================================================================

def test_temporal_threat_agent_benign():
    """Agent 2 evaluates single benign epoch as BENIGN with zero streak."""
    agent = TemporalThreatAgent()
    bundle = make_sample_bundle()

    assessment = agent.assess(bundle)

    assert isinstance(assessment, TemporalAssessment)
    assert assessment.temporal_assessment == "BENIGN"
    assert assessment.persistence_count == 0
    assert assessment.detector_convergence == 0.0


def test_temporal_threat_agent_transient_noise():
    """Agent 2 flags single isolated anomaly as TRANSIENT_ANOMALY when not persistent."""
    agent = TemporalThreatAgent()
    bundle = make_sample_bundle(
        if_anom=True,
        if_score=0.45,
        lstm_anom=False
    )

    assessment = agent.assess(bundle)

    assert assessment.temporal_assessment == "TRANSIENT_ANOMALY"
    assert assessment.persistence_count == 1
    assert "transient" in assessment.pattern_description.lower()


def test_temporal_threat_agent_persistent_drift():
    """Agent 2 tracks persistent streak across consecutive epochs to flag PERSISTENT_DRIFT."""
    agent = TemporalThreatAgent(persistent_streak_thresh=3)

    # Feed 4 consecutive anomalous epochs
    for ep in range(1, 5):
        bundle = make_sample_bundle(
            epoch_id=ep,
            if_anom=True,
            if_score=0.55,
            lstm_anom=True,
            lstm_error=0.15
        )
        assessment = agent.assess(bundle)

    assert assessment.temporal_assessment in ["PERSISTENT_DRIFT", "SPOOFING_TRAJECTORY_INJECTION"]
    assert assessment.persistence_count >= 3
    assert assessment.detector_convergence >= 0.50


def test_temporal_threat_agent_spoofing_step_convergence():
    """Agent 2 identifies SPOOFING_COORDINATE_STEP when multiple detectors converge on sudden displacement."""
    agent = TemporalThreatAgent()
    bundle = make_sample_bundle(
        disp_haversine=120.0,
        rules_anom=True,
        rules_severity="CRITICAL",
        if_anom=True,
        if_score=0.72,
        lstm_anom=True,
        lstm_error=0.25
    )

    assessment = agent.assess(bundle)

    assert assessment.temporal_assessment == "SPOOFING_COORDINATE_STEP"
    assert assessment.detector_convergence >= 0.66
    assert len(assessment.supporting_evidence) >= 2


# =============================================================================
# AGENT 3: MASTER SOC / EVIDENCE ORCHESTRATOR TESTS
# =============================================================================

def test_master_soc_agent_nominal():
    """Master SOC Agent produces DEFCON 5 NOMINAL when all agents agree nominal."""
    soc = MasterSOCAgent()
    a1_agent = GNSSIntegrityAgent()
    a2_agent = TemporalThreatAgent()

    bundle = make_sample_bundle()
    a1_out = a1_agent.assess(bundle)
    a2_out = a2_agent.assess(bundle)

    result = soc.deliberate(bundle, a1_out, a2_out)

    assert isinstance(result, SOCOrchestrationResult)
    assert result.status == "NOMINAL"
    assert result.risk_level == "DEFCON_5_NOMINAL"
    assert result.confidence >= 0.90
    assert "NOMINAL" in result.summary
    assert "MAINTAIN_STANDARD_FIX" in result.recommended_next_action
    assert "disp_haversine" in result.evidence["security_features"]


def test_master_soc_agent_conflict_resolution_physical_override():
    """Conflict resolution: Physical breach overrides temporal buffering delay immediately."""
    soc = MasterSOCAgent()
    a1_agent = GNSSIntegrityAgent()
    a2_agent = TemporalThreatAgent()

    # Acute physical breach (teleportation), but Agent 2 has only seen 1 epoch
    bundle = make_sample_bundle(disp_haversine=150.0, rules_anom=True, rules_severity="CRITICAL")
    a1_out = a1_agent.assess(bundle)
    a2_out = a2_agent.assess(bundle)

    # Agent 1 identifies CRITICAL_INVARIANT_BREACH
    assert a1_out.integrity_assessment == "CRITICAL_INVARIANT_BREACH"

    # Master SOC resolves in favor of immediate lockout
    result = soc.deliberate(bundle, a1_out, a2_out)

    assert result.status == "CONFIRMED_ATTACK"
    assert result.risk_level == "DEFCON_1_CRITICAL"
    assert result.confidence >= 0.95
    assert "EMERGENCY_GNSS_LOCKOUT" in result.recommended_next_action
    assert "SWITCH_TO_INERTIAL_DEAD_RECKONING" in result.recommended_next_action


def test_master_soc_agent_transient_noise_resolution():
    """Master SOC resolves isolated non-persistent anomaly as DEFCON 4 GUARDED (TRANSIENT_NOISE)."""
    soc = MasterSOCAgent()
    a1_agent = GNSSIntegrityAgent()
    a2_agent = TemporalThreatAgent()

    # Slight geometry fluctuation
    bundle = make_sample_bundle(hdop=5.5)  # Warning level, not critical
    a1_out = a1_agent.assess(bundle)
    a2_out = a2_agent.assess(bundle)

    result = soc.deliberate(bundle, a1_out, a2_out)

    assert result.status in ["TRANSIENT_NOISE", "NOMINAL"]
    assert result.risk_level in ["DEFCON_4_GUARDED", "DEFCON_5_NOMINAL"]


def test_master_soc_agent_rag_context_integration():
    """Master SOC Agent integrates RAG regulatory context into agent_findings and auditable summary."""
    soc = MasterSOCAgent()
    bundle = make_sample_bundle(disp_haversine=150.0)
    a1_out = GNSSIntegrityAgent().assess(bundle)
    a2_out = TemporalThreatAgent().assess(bundle)

    rag_text = "ICAO Annex 10 SARPs Section 3.7.2.4: Position jump exceeding 100m requires instantaneous RAIM exclusion."
    result = soc.deliberate(bundle, a1_out, a2_out, rag_context=rag_text)

    assert result.agent_findings["rag_context"] == rag_text
    assert "ICAO Annex 10" in result.summary


# =============================================================================
# INVARIANT TESTS: ANTI-MUTATION & ZERO-FABRICATION
# =============================================================================

def test_invariants_sensor_data_immutability():
    """
    CRITICAL CONSTRAINT: Ensure agents never modify sensor data in Evidence Bundle.
    """
    soc = MasterSOCAgent()
    a1 = GNSSIntegrityAgent()
    a2 = TemporalThreatAgent()

    bundle = make_sample_bundle(
        disp_haversine=45.2,
        vel_kinematic=28.1,
        acc_kinematic=3.2,
        hdop=2.1,
        sat_count_tot=8
    )

    # Deepcopy original data for strict equality verification
    original_dict = copy.deepcopy(bundle.to_dict())

    # Run all 3 agents
    a1_out = a1.assess(bundle)
    a2_out = a2.assess(bundle)
    result = soc.deliberate(bundle, a1_out, a2_out)

    # Verify bundle remains 100% identical
    after_dict = bundle.to_dict()
    assert original_dict == after_dict, "Violation: EvidenceBundle sensor data was mutated by agents!"

    # Verify security features match
    for feat, val in original_dict["security_features"].items():
        assert bundle.security_features[feat] == val
        assert result.evidence["security_features"][feat] == val


def test_invariants_zero_fabrication_and_grounded_citations():
    """
    CRITICAL CONSTRAINT: Every conclusion must cite verified evidence fields without hallucination.
    """
    soc = MasterSOCAgent()
    bundle = make_sample_bundle(
        disp_haversine=120.0,
        acc_kinematic=15.0,
        lstm_error=0.18,
        lstm_thresh=0.08
    )

    a1_out = GNSSIntegrityAgent().assess(bundle)
    a2_out = TemporalThreatAgent().assess(bundle)
    result = soc.deliberate(bundle, a1_out, a2_out)

    # Check evidence citations in summary
    assert "120" in result.summary or "15" in result.summary or "0.18" in result.summary
    assert result.evidence["security_features"]["disp_haversine"] == 120.0
    assert result.evidence["security_features"]["acc_kinematic"] == 15.0

    # Ensure required structured keys are present
    out_dict = result.to_dict()
    required_keys = [
        "event_id", "status", "risk_level", "confidence",
        "summary", "evidence", "agent_findings", "recommended_next_action"
    ]
    for key in required_keys:
        assert key in out_dict, f"Missing required output key: {key}"
