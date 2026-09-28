"""
LOCUS Phase 6 — 3-Agent Security SOC Data Models & Contracts

Module: src.soc.models
Defines the typed data contracts, enums, and structured reports exchanged
between Agent 1 (Integrity), Agent 2 (Temporal Threat), and Agent 3 (Master SOC Orchestrator).
"""

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any


class DefconLevel(str, Enum):
    """
    Standardized Defense Readiness Condition (DEFCON) threat levels for GNSS security.
    """
    DEFCON_5 = "DEFCON_5"  # Normal / All Clear: Nominal operation, no threats
    DEFCON_4 = "DEFCON_4"  # Guarded / Advisory: Minor geometry degradation or isolated transient glitch
    DEFCON_3 = "DEFCON_3"  # Elevated / Caution: Moderate anomaly, multiple warnings, caution advised
    DEFCON_2 = "DEFCON_2"  # High / Severe: Multi-detector confirmed threat, probable spoofing or jamming
    DEFCON_1 = "DEFCON_1"  # Critical / Emergency: Active confirmed attack, impossible kinematics or takeover


class IntegrityStatus(str, Enum):
    """
    Agent 1 (GNSS Integrity Agent) status classifications.
    """
    NOMINAL = "INTEGRITY_NOMINAL"
    GEOMETRY_DEGRADED = "GEOMETRY_DEGRADED"
    KINEMATIC_VIOLATION = "KINEMATIC_VIOLATION"
    CRITICAL_INVARIANT_BREACH = "CRITICAL_INVARIANT_BREACH"


class ThreatClassification(str, Enum):
    """
    Agent 2 (Temporal Threat Correlation Agent) threat categorization.
    """
    BENIGN = "BENIGN"
    TRANSIENT_ANOMALY = "TRANSIENT_ANOMALY"
    PERSISTENT_DRIFT = "PERSISTENT_DRIFT"
    SPOOFING_COORDINATE_STEP = "SPOOFING_COORDINATE_STEP"
    SPOOFING_TRAJECTORY_INJECTION = "SPOOFING_TRAJECTORY_INJECTION"
    RF_JAMMING_DEGRADATION = "RF_JAMMING_DEGRADATION"
    MULTIPATH_INTERFERENCE = "MULTIPATH_INTERFERENCE"
    UNKNOWN_ANOMALY = "UNKNOWN_ANOMALY"


class MitigationAction(str, Enum):
    """
    Actionable mitigation directives issued by Agent 3 (Master SOC Orchestrator).
    """
    MAINTAIN_STANDARD_FIX = "MAINTAIN_STANDARD_FIX"
    INCREASE_MONITORING_FREQUENCY = "INCREASE_MONITORING_FREQUENCY"
    DEGRADE_CONFIDENCE_WEIGHT = "DEGRADE_CONFIDENCE_WEIGHT"
    REJECT_EPOCH_MEASUREMENT = "REJECT_EPOCH_MEASUREMENT"
    TRIGGER_RAIM_EXCLUSION = "TRIGGER_RAIM_EXCLUSION"
    SWITCH_TO_INERTIAL_DEAD_RECKONING = "SWITCH_TO_INERTIAL_DEAD_RECKONING"
    EMERGENCY_GNSS_LOCKOUT = "EMERGENCY_GNSS_LOCKOUT"


@dataclass
class Agent1Assessment:
    """
    Assessment payload emitted by Agent 1: GNSS Integrity Agent.
    Evaluates kinematic plausibility, geometric dilution, and observation health.
    """
    agent_id: str = "agent_1_integrity"
    event_id: str = ""
    timestamp_utc: Optional[str] = None
    session_id: int = 0
    epoch_id: Optional[int] = None
    integrity_status: IntegrityStatus = IntegrityStatus.NOMINAL
    confidence_score: float = 1.0
    kinematic_health: float = 1.0  # [0.0 = completely broken, 1.0 = flawless]
    geometry_health: float = 1.0   # [0.0 = acute starvation, 1.0 = robust geometry]
    physical_violation_count: int = 0
    violated_rules: List[str] = field(default_factory=list)
    max_rule_severity: str = "INFO"
    discard_recommended: bool = False
    verdict_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["integrity_status"] = self.integrity_status.value
        return d


@dataclass
class Agent2Assessment:
    """
    Assessment payload emitted by Agent 2: Temporal & Threat Correlation Agent.
    Evaluates temporal sequence persistence, multi-detector convergence, and feature attribution.
    """
    agent_id: str = "agent_2_temporal_threat"
    event_id: str = ""
    timestamp_utc: Optional[str] = None
    session_id: int = 0
    epoch_id: Optional[int] = None
    threat_classification: ThreatClassification = ThreatClassification.BENIGN
    confidence_score: float = 1.0
    persistence_count: int = 0         # Consecutive anomalous epochs in current streak
    persistence_ratio: float = 0.0     # Fraction of anomalous epochs in recent window (e.g. last 10)
    detector_convergence: float = 0.0  # Agreement score [0.0 to 1.0] across active detectors
    active_detectors_count: int = 0
    anomalous_detectors_count: int = 0
    primary_feature_contributors: List[str] = field(default_factory=list)
    lstm_reconstruction_error: Optional[float] = None
    iforest_anomaly_score: Optional[float] = None
    xgboost_prediction: Optional[Dict[str, Any]] = None
    threat_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["threat_classification"] = self.threat_classification.value
        return d


@dataclass
class SOCIncidentReport:
    """
    Comprehensive incident report emitted by Agent 3: Master SOC Orchestrator.
    Synthesizes multi-agent consensus, DEFCON threat rating, root-cause attribution,
    and actionable mitigation directives.
    """
    incident_id: str
    event_id: str
    timestamp_utc: Optional[str]
    session_id: int
    epoch_id: Optional[int]
    defcon_level: DefconLevel
    attack_vector: str
    consensus_status: str  # "UNANIMOUS", "MAJORITY", "DISCREPANCY_FLAGGED", "NOMINAL"
    overall_confidence: float
    mitigation_actions: List[str]
    agent_1_assessment: Dict[str, Any]
    agent_2_assessment: Dict[str, Any]
    orchestrator_rationale: str
    location: Dict[str, Any]
    key_features: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["defcon_level"] = self.defcon_level.value
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)
