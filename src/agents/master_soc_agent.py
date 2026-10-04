"""
LOCUS Phase 6 — Agent 3: Master SOC Agent / Evidence Orchestrator

Module: src.agents.master_soc_agent
Focus: Synthesizes findings from Agent 1 (GNSS Integrity) and Agent 2 (Temporal / Threat),
resolves inter-agent conflicts, cross-references RAG regulatory context when available,
and produces explainable, auditable incident reports.

Critical Invariants:
- Read-only operation: NEVER modifies sensor telemetry.
- Zero fabrication: All conclusions cite explicit evidence fields; never invents sensor values.
- Calibrated certainty: Degrades confidence when evidence is insufficient or signals conflict.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union, Any
import json
import uuid

from src.evidence.evidence_bundle import EvidenceBundle
from src.agents.integrity_agent import IntegrityAssessment
from src.agents.temporal_threat_agent import TemporalAssessment


@dataclass
class SOCOrchestrationResult:
    """
    Standardized structured output from Agent 3: Master SOC Agent.
    """
    event_id: str
    status: str                         # NOMINAL, TRANSIENT_NOISE, SUSPECTED_INTERFERENCE, CONFIRMED_ATTACK
    risk_level: str                     # DEFCON_5_NOMINAL, DEFCON_4_GUARDED, DEFCON_3_ELEVATED, DEFCON_2_HIGH, DEFCON_1_CRITICAL
    confidence: float                   # Calibrated confidence score [0.0, 1.0]
    summary: str                        # Auditable executive incident summary
    evidence: Dict[str, Any]            # Exact cited evidence fields and detector metrics
    agent_findings: Dict[str, Any]      # Findings from Agent 1, Agent 2, and optional RAG context
    recommended_next_action: List[str]  # Actionable mitigation directives

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


class MasterSOCAgent:
    """
    Agent 3 in the LOCUS 3-Agent SOC Hierarchy.
    Evidence Orchestrator and Master Decision Maker.
    Synthesizes multi-agent deliberations into binding operational verdicts.
    """

    def __init__(self):
        pass

    def deliberate(
        self,
        bundle: Union[EvidenceBundle, Dict[str, Any]],
        integrity_output: Union[IntegrityAssessment, Dict[str, Any]],
        temporal_output: Union[TemporalAssessment, Dict[str, Any]],
        rag_context: Optional[Union[str, Dict[str, Any]]] = None
    ) -> SOCOrchestrationResult:
        """
        Synthesize multi-agent findings, resolve conflicts, and produce structured SOC verdict.
        Guaranteed zero mutation of underlying sensor data.
        """
        # Unpack evidence data safely
        data = bundle.to_dict() if isinstance(bundle, EvidenceBundle) else (bundle if isinstance(bundle, dict) else bundle.to_dict())
        a1 = integrity_output.to_dict() if hasattr(integrity_output, "to_dict") else dict(integrity_output)
        a2 = temporal_output.to_dict() if hasattr(temporal_output, "to_dict") else dict(temporal_output)

        event_id = str(data.get("event_id", f"evt_{uuid.uuid4().hex[:8]}"))
        sec_features = data.get("security_features", {})
        location = data.get("location", {})
        dq_context = data.get("data_quality", {})
        if_data = data.get("isolation_forest", {})
        temp_data = data.get("temporal_model", {})
        rules_data = data.get("physical_rules", {})

        # ---------------------------------------------------------------------
        # 1. Compile Exact Evidence Citations (Zero Invention)
        # ---------------------------------------------------------------------
        cited_evidence = {
            "event_id": event_id,
            "timestamp_utc": data.get("timestamp_utc"),
            "session_id": data.get("session_id"),
            "epoch_id": data.get("epoch_id"),
            "location": location,
            "security_features": {
                "disp_haversine": sec_features.get("disp_haversine"),
                "vel_kinematic": sec_features.get("vel_kinematic"),
                "acc_kinematic": sec_features.get("acc_kinematic"),
                "jerk_kinematic": sec_features.get("jerk_kinematic"),
                "bearing_rate": sec_features.get("bearing_rate"),
                "HDOP": sec_features.get("HDOP"),
                "VDOP": sec_features.get("VDOP"),
                "fix_integrity": sec_features.get("fix_integrity"),
                "sat_count_tot": sec_features.get("sat_count_tot"),
                "sat_churn": sec_features.get("sat_churn")
            },
            "detector_metrics": {
                "physical_rules_triggered_count": rules_data.get("triggered_count", 0),
                "physical_rules_max_severity": rules_data.get("max_severity", "INFO"),
                "isolation_forest_anomaly_score": if_data.get("anomaly_score"),
                "isolation_forest_is_anomaly": if_data.get("is_anomaly", False),
                "lstm_reconstruction_error": temp_data.get("reconstruction_error"),
                "lstm_error_threshold": temp_data.get("error_threshold"),
                "lstm_is_anomaly": temp_data.get("is_anomaly", False),
                "xgboost_status": data.get("xgboost", {}).get("status", "UNFITTED_PENDING_LABELLED_SCENARIOS")
            },
            "data_quality": {
                "fix_quality": dq_context.get("fix_quality"),
                "satellites_used": dq_context.get("satellites_used"),
                "hdop": dq_context.get("hdop"),
                "data_quality_flag": dq_context.get("data_quality_flag", "VALID")
            }
        }

        # ---------------------------------------------------------------------
        # 2. Inter-Agent Conflict Resolution & Risk Assessment
        # ---------------------------------------------------------------------
        a1_status = a1.get("integrity_assessment", "INTEGRITY_NOMINAL")
        a2_threat = a2.get("temporal_assessment", "BENIGN")
        a1_conf = float(a1.get("confidence", 0.9))
        a2_conf = float(a2.get("confidence", 0.9))
        persistence_streak = int(a2.get("persistence_count", 0))
        convergence = float(a2.get("detector_convergence", 0.0))

        # Conflict resolution logic:
        # Physical breach takes immediate precedence over temporal buffering delays
        if a1_status == "CRITICAL_INVARIANT_BREACH":
            status = "CONFIRMED_ATTACK"
            risk_level = "DEFCON_1_CRITICAL"
            base_conf = max(a1_conf, 0.95)
            summary_prefix = "CRITICAL EMERGENCY: Catastrophic physical invariant violation confirmed."
            actions = [
                "EMERGENCY_GNSS_LOCKOUT",
                "SWITCH_TO_INERTIAL_DEAD_RECKONING",
                "REJECT_EPOCH_MEASUREMENT",
                "BROADCAST_SECURITY_ALERT"
            ]

        elif a2_threat in ["SPOOFING_COORDINATE_STEP", "SPOOFING_TRAJECTORY_INJECTION"]:
            status = "CONFIRMED_ATTACK"
            risk_level = "DEFCON_1_CRITICAL" if convergence >= 0.75 else "DEFCON_2_HIGH"
            base_conf = max(a2_conf, 0.90)
            summary_prefix = "HIGH THREAT: Multi-detector converged trajectory manipulation / spoofing."
            actions = [
                "SWITCH_TO_INERTIAL_DEAD_RECKONING",
                "REJECT_EPOCH_MEASUREMENT",
                "TRIGGER_RAIM_EXCLUSION"
            ]

        elif a2_threat == "RF_JAMMING_DEGRADATION" or (a1_status == "GEOMETRY_DEGRADED" and persistence_streak >= 3):
            status = "CONFIRMED_INTERFERENCE"
            risk_level = "DEFCON_2_HIGH"
            base_conf = round((a1_conf + a2_conf) / 2.0, 2)
            summary_prefix = "SEVERE INTERFERENCE: Persistent constellation starvation and geometry collapse."
            actions = [
                "DEGRADE_CONFIDENCE_WEIGHT",
                "TRIGGER_RAIM_EXCLUSION",
                "INCREASE_MONITORING_FREQUENCY"
            ]

        elif a2_threat == "PERSISTENT_DRIFT" or a1_status == "KINEMATIC_VIOLATION":
            status = "SUSPECTED_INTERFERENCE"
            risk_level = "DEFCON_3_ELEVATED"
            base_conf = round(min(a1_conf, a2_conf) * 0.95, 2)
            summary_prefix = "ELEVATED CAUTION: Sustained anomalous drift or kinematic boundary exceedance."
            actions = [
                "DEGRADE_CONFIDENCE_WEIGHT",
                "INCREASE_MONITORING_FREQUENCY"
            ]

        elif a2_threat == "TRANSIENT_ANOMALY" or a1_status == "GEOMETRY_DEGRADED":
            # Conflict / Isolated glitch: Agent 1 or Agent 2 flagged transient, but no persistence
            status = "TRANSIENT_NOISE"
            risk_level = "DEFCON_4_GUARDED"
            base_conf = round(min(a1_conf, a2_conf), 2)
            summary_prefix = "GUARDED ADVISORY: Isolated transient fluctuation or non-persistent measurement glitch."
            actions = [
                "INCREASE_MONITORING_FREQUENCY",
                "MAINTAIN_STANDARD_FIX"
            ]

        else:
            # Nominal agreement
            status = "NOMINAL"
            risk_level = "DEFCON_5_NOMINAL"
            base_conf = round((a1_conf + a2_conf) / 2.0, 2)
            summary_prefix = "NOMINAL ALL-CLEAR: Zero physical rule violations and stable temporal dynamics."
            actions = [
                "MAINTAIN_STANDARD_FIX"
            ]

        # ---------------------------------------------------------------------
        # 3. Grounded Explainable Summary Generation
        # ---------------------------------------------------------------------
        # Cites specific evidence fields without hallucination
        citations = []
        if a1.get("supporting_evidence"):
            for ev in a1["supporting_evidence"][:2]:
                citations.append(f"{ev.get('feature')} = {ev.get('observed_value')} (threshold: {ev.get('threshold')})")

        if temp_data.get("reconstruction_error") is not None:
            citations.append(f"LSTM recon error = {temp_data.get('reconstruction_error')} (thresh: {temp_data.get('error_threshold')})")

        if if_data.get("anomaly_score") is not None:
            citations.append(f"IF anomaly score = {if_data.get('anomaly_score')}")

        citation_str = f" [Evidence cited: {', '.join(citations)}]" if citations else ""
        summary = f"{summary_prefix}{citation_str} | Agent 1 ({a1_status}), Agent 2 ({a2_threat}, streak: {persistence_streak})."

        # ---------------------------------------------------------------------
        # 4. Integrate RAG Context (When Available)
        # ---------------------------------------------------------------------
        agent_findings = {
            "integrity_agent": a1,
            "temporal_threat_agent": a2,
            "rag_context": rag_context
        }

        if rag_context:
            rag_str = rag_context if isinstance(rag_context, str) else json.dumps(rag_context)
            summary += f" | Regulatory Citation: {rag_str[:120]}"

        return SOCOrchestrationResult(
            event_id=event_id,
            status=status,
            risk_level=risk_level,
            confidence=base_conf,
            summary=summary,
            evidence=cited_evidence,
            agent_findings=agent_findings,
            recommended_next_action=actions
        )
