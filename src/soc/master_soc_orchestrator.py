"""
LOCUS Phase 6 — Agent 3: Master SOC Orchestrator

Module: src.soc.master_soc_orchestrator
Focus: Multi-agent consensus resolution, DEFCON threat rating, root-cause
attack vector attribution, and actionable mitigation directives.
"""

import uuid
from typing import Dict, List, Optional, Union, Any, Tuple

from src.evidence.evidence_bundle import EvidenceBundle
from src.soc.models import (
    Agent1Assessment,
    Agent2Assessment,
    SOCIncidentReport,
    DefconLevel,
    IntegrityStatus,
    ThreatClassification,
    MitigationAction,
)


class MasterSOCOrchestrator:
    """
    Agent 3 in the LOCUS 3-Agent SOC Hierarchy.
    Synthesizes the physical insights of Agent 1 and the temporal dynamics
    of Agent 2 into a binding operational verdict.
    """

    def __init__(self):
        pass

    def correlate_and_resolve(
        self,
        bundle: Union[EvidenceBundle, Dict[str, Any]],
        a1: Agent1Assessment,
        a2: Agent2Assessment,
        incident_id: Optional[str] = None
    ) -> SOCIncidentReport:
        """
        Synthesize Agent 1 and Agent 2 assessments with raw evidence to produce
        the final SOC Incident Report.
        """
        data = bundle.to_dict() if isinstance(bundle, EvidenceBundle) else bundle

        event_id = data.get("event_id", "")
        ts_utc = data.get("timestamp_utc")
        session_id = int(data.get("session_id", 0))
        epoch_id = data.get("epoch_id")
        loc = data.get("location", {})
        sec_features = data.get("security_features", {})

        inc_id = incident_id or f"inc_{uuid.uuid4().hex[:12]}"

        # 1. Consensus Resolution
        consensus_status, defcon, attack_vector, confidence = self._resolve_consensus(a1, a2)

        # 2. Derive Prioritized Mitigation Directives
        mitigation_actions = self._derive_mitigations(defcon, attack_vector, a1, a2)

        # 3. Formulate Auditable Orchestrator Rationale
        rationale = self._formulate_rationale(
            defcon=defcon,
            consensus_status=consensus_status,
            attack_vector=attack_vector,
            a1=a1,
            a2=a2,
            confidence=confidence
        )

        # Extract primary key features for quick SOC triage
        key_features = {
            "disp_haversine": sec_features.get("disp_haversine"),
            "vel_kinematic": sec_features.get("vel_kinematic"),
            "acc_kinematic": sec_features.get("acc_kinematic"),
            "jerk_kinematic": sec_features.get("jerk_kinematic"),
            "HDOP": sec_features.get("HDOP"),
            "fix_integrity": sec_features.get("fix_integrity"),
            "sat_count_tot": sec_features.get("sat_count_tot"),
        }

        return SOCIncidentReport(
            incident_id=inc_id,
            event_id=event_id,
            timestamp_utc=ts_utc,
            session_id=session_id,
            epoch_id=epoch_id,
            defcon_level=defcon,
            attack_vector=attack_vector,
            consensus_status=consensus_status,
            overall_confidence=confidence,
            mitigation_actions=[m.value for m in mitigation_actions],
            agent_1_assessment=a1.to_dict(),
            agent_2_assessment=a2.to_dict(),
            orchestrator_rationale=rationale,
            location=loc,
            key_features=key_features
        )

    def _resolve_consensus(
        self,
        a1: Agent1Assessment,
        a2: Agent2Assessment
    ) -> Tuple[str, DefconLevel, str, float]:
        """
        Evaluate consensus between Agent 1 and Agent 2 and assign DEFCON level.
        """
        # Case 1: Both nominal -> DEFCON 5
        if (a1.integrity_status == IntegrityStatus.NOMINAL and
                a2.threat_classification == ThreatClassification.BENIGN):
            return "NOMINAL", DefconLevel.DEFCON_5, "BENIGN_NOMINAL", 0.98

        # Case 2: Critical Physical Invariant Breach
        if a1.integrity_status == IntegrityStatus.CRITICAL_INVARIANT_BREACH:
            if a2.threat_classification == ThreatClassification.SPOOFING_COORDINATE_STEP:
                return "UNANIMOUS", DefconLevel.DEFCON_1, "SPOOFING_COORDINATE_STEP", 0.96
            # Even if Agent 2 saw transient, a critical physical breach (e.g. >10 m/s² accel) is high/critical
            if a2.persistence_count > 1 or a2.detector_convergence > 0.4:
                return "MAJORITY", DefconLevel.DEFCON_1, "SPOOFING_COORDINATE_STEP", 0.94
            return "DISCREPANCY_FLAGGED", DefconLevel.DEFCON_2, "UNCONFIRMED_KINEMATIC_SPIKE", 0.88

        # Case 3: Confirmed Persistent Attack (Drift / Trajectory Injection / Jamming)
        if a2.threat_classification in [
            ThreatClassification.SPOOFING_TRAJECTORY_INJECTION,
            ThreatClassification.PERSISTENT_DRIFT,
            ThreatClassification.RF_JAMMING_DEGRADATION
        ]:
            if a1.integrity_status in [IntegrityStatus.KINEMATIC_VIOLATION, IntegrityStatus.GEOMETRY_DEGRADED]:
                vector = "RF_JAMMING_STARVATION" if a2.threat_classification == ThreatClassification.RF_JAMMING_DEGRADATION else "SPOOFING_TRAJECTORY_INJECTION"
                return "UNANIMOUS", DefconLevel.DEFCON_2, vector, 0.92

            # Discrepancy: Agent 2 flags persistent drift (subtle slow walk-off spoofing), but Agent 1 kinematics stay within nominal limits
            vector = "SUBTLE_SPOOFING_WALKOFF" if a2.threat_classification == ThreatClassification.SPOOFING_TRAJECTORY_INJECTION else "PERSISTENT_TEMPORAL_DRIFT"
            return "DISCREPANCY_FLAGGED", DefconLevel.DEFCON_2, vector, 0.86

        # Case 4: Kinematic Violation with Moderate Persistence
        if a1.integrity_status == IntegrityStatus.KINEMATIC_VIOLATION:
            if a2.threat_classification == ThreatClassification.TRANSIENT_ANOMALY:
                return "DISCREPANCY_FLAGGED", DefconLevel.DEFCON_3, "TRANSIENT_KINEMATIC_GLITCH", 0.82
            if a2.detector_convergence >= 0.5:
                return "UNANIMOUS", DefconLevel.DEFCON_2, "SPOOFING_MANEUVER_INJECTION", 0.89
            return "MAJORITY", DefconLevel.DEFCON_3, "KINEMATIC_ANOMALY", 0.85

        # Case 5: Geometry Degradation / Satellite Starvation
        if a1.integrity_status == IntegrityStatus.GEOMETRY_DEGRADED:
            if a2.threat_classification == ThreatClassification.RF_JAMMING_DEGRADATION:
                return "UNANIMOUS", DefconLevel.DEFCON_2, "RF_JAMMING_STARVATION", 0.91
            if a2.threat_classification == ThreatClassification.MULTIPATH_INTERFERENCE:
                return "UNANIMOUS", DefconLevel.DEFCON_4, "MULTIPATH_INTERFERENCE", 0.88
            return "MAJORITY", DefconLevel.DEFCON_4, "GEOMETRIC_STARVATION", 0.85

        # Case 6: Transient Anomaly / Multipath
        if a2.threat_classification in [ThreatClassification.TRANSIENT_ANOMALY, ThreatClassification.MULTIPATH_INTERFERENCE]:
            return "MAJORITY", DefconLevel.DEFCON_4, "MULTIPATH_INTERFERENCE", 0.82

        # Case 7: Uncategorized Anomaly
        return "MAJORITY", DefconLevel.DEFCON_3, "UNCONFIRMED_ANOMALY", 0.75

    def _derive_mitigations(
        self,
        defcon: DefconLevel,
        attack_vector: str,
        a1: Agent1Assessment,
        a2: Agent2Assessment
    ) -> List[MitigationAction]:
        """Formulate prioritized defensive recommendations."""
        if defcon == DefconLevel.DEFCON_5:
            return [MitigationAction.MAINTAIN_STANDARD_FIX]

        if defcon == DefconLevel.DEFCON_4:
            return [
                MitigationAction.INCREASE_MONITORING_FREQUENCY,
                MitigationAction.DEGRADE_CONFIDENCE_WEIGHT
            ]

        if defcon == DefconLevel.DEFCON_3:
            return [
                MitigationAction.DEGRADE_CONFIDENCE_WEIGHT,
                MitigationAction.TRIGGER_RAIM_EXCLUSION,
                MitigationAction.INCREASE_MONITORING_FREQUENCY
            ]

        if defcon == DefconLevel.DEFCON_2:
            return [
                MitigationAction.REJECT_EPOCH_MEASUREMENT,
                MitigationAction.SWITCH_TO_INERTIAL_DEAD_RECKONING,
                MitigationAction.TRIGGER_RAIM_EXCLUSION
            ]

        # DEFCON_1
        return [
            MitigationAction.EMERGENCY_GNSS_LOCKOUT,
            MitigationAction.REJECT_EPOCH_MEASUREMENT,
            MitigationAction.SWITCH_TO_INERTIAL_DEAD_RECKONING
        ]

    def _formulate_rationale(
        self,
        defcon: DefconLevel,
        consensus_status: str,
        attack_vector: str,
        a1: Agent1Assessment,
        a2: Agent2Assessment,
        confidence: float
    ) -> str:
        """Construct clear, auditable operational rationale for human analysts."""
        lines = [
            f"Master SOC assigned threat level {defcon.value} ({attack_vector}) with confidence {confidence * 100:.1f}%.",
            f"Consensus Status: {consensus_status}.",
            f"Agent 1 (Integrity): Status={a1.integrity_status.value}, KinematicHealth={a1.kinematic_health:.2f}, GeometryHealth={a1.geometry_health:.2f}. {a1.verdict_summary}",
            f"Agent 2 (Temporal): Classification={a2.threat_classification.value}, PersistenceStreak={a2.persistence_count}, WindowRatio={a2.persistence_ratio:.2f}, Convergence={a2.detector_convergence:.2f}. {a2.threat_summary}"
        ]
        if a2.primary_feature_contributors:
            lines.append(f"Primary error drivers: {', '.join(a2.primary_feature_contributors)}.")
        return " | ".join(lines)
