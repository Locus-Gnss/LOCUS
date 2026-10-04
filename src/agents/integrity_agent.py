"""
LOCUS Phase 6 — Agent 1: GNSS Integrity Agent

Module: src.agents.integrity_agent
Focus: Evaluates physical plausibility, fix integrity, navigation quality,
satellite behaviour, and feature-level anomalies from the 10-D Security Vector
and Evidence Bundle.

Critical Invariants:
- Read-only operation: NEVER modifies sensor telemetry.
- Zero fabrication: All evaluations strictly reference verified evidence.
- Transparent explainability: Cites exact feature values and violated thresholds.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union, Any
import numpy as np

from src.evidence.evidence_bundle import EvidenceBundle
from src.detection.isolation_forest import OFFICIAL_SECURITY_FEATURES


@dataclass
class IntegrityAssessment:
    """
    Structured output from Agent 1 (GNSS Integrity Agent).
    """
    agent_id: str = "agent_1_integrity"
    event_id: str = ""
    timestamp_utc: Optional[str] = None
    session_id: int = 0
    epoch_id: Optional[int] = None
    integrity_assessment: str = "INTEGRITY_NOMINAL"  # NOMINAL, GEOMETRY_DEGRADED, KINEMATIC_VIOLATION, CRITICAL_INVARIANT_BREACH
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0
    explanation: str = ""
    kinematic_health: float = 1.0   # [0.0 = severe violation, 1.0 = flawless]
    geometry_health: float = 1.0    # [0.0 = acute dilution/starvation, 1.0 = robust geometry]
    feature_level_anomalies: Dict[str, Any] = field(default_factory=dict)
    physical_violation_count: int = 0
    discard_recommended: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GNSSIntegrityAgent:
    """
    Agent 1 in the LOCUS 3-Agent SOC Hierarchy.
    Specialized in physical plausibility, fix integrity, navigation geometry,
    constellation behaviour, and 10-D feature-level anomaly analysis.
    """

    def __init__(
        self,
        critical_accel_thresh: float = 10.0,    # m/s² (~1.0g)
        warning_accel_thresh: float = 4.0,       # m/s²
        critical_jerk_thresh: float = 25.0,     # m/s³
        warning_jerk_thresh: float = 15.0,      # m/s³
        critical_vel_thresh: float = 85.0,      # m/s (~306 km/h)
        warning_vel_thresh: float = 50.0,       # m/s (~180 km/h)
        critical_disp_thresh: float = 100.0,    # m
        warning_disp_thresh: float = 50.0,      # m
        critical_hdop_thresh: float = 8.0,
        warning_hdop_thresh: float = 4.0,
        critical_vdop_thresh: float = 10.0,
        warning_vdop_thresh: float = 5.0,
        critical_integrity_thresh: float = 0.20,
        warning_integrity_thresh: float = 0.45,
        min_critical_sats: int = 4,
        min_warning_sats: int = 6,
        critical_churn_thresh: float = 0.60,
        warning_churn_thresh: float = 0.35,
        max_bearing_rate_deg_s: float = 90.0,
        bearing_speed_floor_mps: float = 2.0
    ):
        self.critical_accel_thresh = critical_accel_thresh
        self.warning_accel_thresh = warning_accel_thresh
        self.critical_jerk_thresh = critical_jerk_thresh
        self.warning_jerk_thresh = warning_jerk_thresh
        self.critical_vel_thresh = critical_vel_thresh
        self.warning_vel_thresh = warning_vel_thresh
        self.critical_disp_thresh = critical_disp_thresh
        self.warning_disp_thresh = warning_disp_thresh
        self.critical_hdop_thresh = critical_hdop_thresh
        self.warning_hdop_thresh = warning_hdop_thresh
        self.critical_vdop_thresh = critical_vdop_thresh
        self.warning_vdop_thresh = warning_vdop_thresh
        self.critical_integrity_thresh = critical_integrity_thresh
        self.warning_integrity_thresh = warning_integrity_thresh
        self.min_critical_sats = min_critical_sats
        self.min_warning_sats = min_warning_sats
        self.critical_churn_thresh = critical_churn_thresh
        self.warning_churn_thresh = warning_churn_thresh
        self.max_bearing_rate_deg_s = max_bearing_rate_deg_s
        self.bearing_speed_floor_mps = bearing_speed_floor_mps

    @staticmethod
    def _safe_float(val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            f = float(val)
            return f if np.isfinite(f) else None
        except (ValueError, TypeError):
            return None

    def assess(
        self,
        bundle_or_features: Union[EvidenceBundle, Dict[str, Any]],
        physical_rules_override: Optional[Dict[str, Any]] = None
    ) -> IntegrityAssessment:
        """
        Evaluate Evidence Bundle or raw 10-D features and produce Agent 1's integrity assessment.
        Read-only: Sensor data is never modified.
        """
        # Unpack evidence container
        if isinstance(bundle_or_features, EvidenceBundle):
            data = bundle_or_features.to_dict()
        elif hasattr(bundle_or_features, "to_dict"):
            data = bundle_or_features.to_dict()
        else:
            data = dict(bundle_or_features)

        event_id = data.get("event_id", "")
        ts_utc = data.get("timestamp_utc")
        session_id = int(data.get("session_id", 0))
        epoch_id = data.get("epoch_id")

        # 10-D features may be directly in top-level or under "security_features"
        sec_features = data.get("security_features", {}) if "security_features" in data else data
        rules_data = physical_rules_override or data.get("physical_rules", {})
        dq_context = data.get("data_quality", {})

        # Extract verified 10-D metrics
        disp = self._safe_float(sec_features.get("disp_haversine"))
        vel = self._safe_float(sec_features.get("vel_kinematic"))
        acc = self._safe_float(sec_features.get("acc_kinematic"))
        jerk = self._safe_float(sec_features.get("jerk_kinematic"))
        bearing_rate = self._safe_float(sec_features.get("bearing_rate"))
        hdop = self._safe_float(sec_features.get("HDOP")) or self._safe_float(dq_context.get("hdop"))
        vdop = self._safe_float(sec_features.get("VDOP"))
        fix_int = self._safe_float(sec_features.get("fix_integrity"))
        sats = self._safe_float(sec_features.get("sat_count_tot")) or self._safe_float(dq_context.get("satellites_used"))
        churn = self._safe_float(sec_features.get("sat_churn"))

        supporting_evidence: List[Dict[str, Any]] = []
        feature_anomalies: Dict[str, Any] = {}
        explanations: List[str] = []

        # ---------------------------------------------------------------------
        # 1. Physical Plausibility & Kinematic Invariants
        # ---------------------------------------------------------------------
        kinematic_health = 1.0
        has_critical_kinematic = False
        has_warning_kinematic = False

        # Acceleration
        if acc is not None:
            acc_mag = abs(acc)
            if acc_mag > self.critical_accel_thresh:
                has_critical_kinematic = True
                kinematic_health -= 0.6
                evidence_item = {
                    "feature": "acc_kinematic",
                    "observed_value": acc,
                    "threshold": self.critical_accel_thresh,
                    "severity": "CRITICAL",
                    "rationale": f"Acceleration magnitude ({acc_mag:.2f} m/s²) exceeds physical limits (> {self.critical_accel_thresh} m/s²)"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["acc_kinematic"] = evidence_item
                explanations.append(f"Non-physical acceleration jump ({acc_mag:.2f} m/s² > {self.critical_accel_thresh} m/s²)")
            elif acc_mag > self.warning_accel_thresh:
                has_warning_kinematic = True
                kinematic_health -= 0.25
                evidence_item = {
                    "feature": "acc_kinematic",
                    "observed_value": acc,
                    "threshold": self.warning_accel_thresh,
                    "severity": "WARNING",
                    "rationale": f"Elevated acceleration ({acc_mag:.2f} m/s² > {self.warning_accel_thresh} m/s²)"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["acc_kinematic"] = evidence_item
                explanations.append(f"High acceleration ({acc_mag:.2f} m/s²)")

        # Jerk
        if jerk is not None:
            jerk_mag = abs(jerk)
            if jerk_mag > self.critical_jerk_thresh:
                has_critical_kinematic = True
                kinematic_health -= 0.5
                evidence_item = {
                    "feature": "jerk_kinematic",
                    "observed_value": jerk,
                    "threshold": self.critical_jerk_thresh,
                    "severity": "CRITICAL",
                    "rationale": f"Actuator/drivetrain jerk exceedance ({jerk_mag:.2f} m/s³ > {self.critical_jerk_thresh} m/s³)"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["jerk_kinematic"] = evidence_item
                explanations.append(f"Critical jerk spike ({jerk_mag:.2f} m/s³ > {self.critical_jerk_thresh} m/s³)")
            elif jerk_mag > self.warning_jerk_thresh:
                has_warning_kinematic = True
                kinematic_health -= 0.20
                evidence_item = {
                    "feature": "jerk_kinematic",
                    "observed_value": jerk,
                    "threshold": self.warning_jerk_thresh,
                    "severity": "WARNING",
                    "rationale": f"Elevated jerk ({jerk_mag:.2f} m/s³ > {self.warning_jerk_thresh} m/s³)"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["jerk_kinematic"] = evidence_item

        # Ground Speed (Kinematic Velocity)
        if vel is not None:
            if vel > self.critical_vel_thresh:
                has_critical_kinematic = True
                kinematic_health -= 0.7
                evidence_item = {
                    "feature": "vel_kinematic",
                    "observed_value": vel,
                    "threshold": self.critical_vel_thresh,
                    "severity": "CRITICAL",
                    "rationale": f"Terrestrial speed bound exceeded ({vel:.2f} m/s > {self.critical_vel_thresh} m/s)"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["vel_kinematic"] = evidence_item
                explanations.append(f"Impossible terrestrial velocity ({vel:.2f} m/s > {self.critical_vel_thresh} m/s)")
            elif vel > self.warning_vel_thresh:
                has_warning_kinematic = True
                kinematic_health -= 0.3
                evidence_item = {
                    "feature": "vel_kinematic",
                    "observed_value": vel,
                    "threshold": self.warning_vel_thresh,
                    "severity": "WARNING",
                    "rationale": f"Velocity exceeds normal highway bound ({vel:.2f} m/s > {self.warning_vel_thresh} m/s)"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["vel_kinematic"] = evidence_item

        # Single-Epoch Haversine Displacement
        if disp is not None:
            if disp > self.critical_disp_thresh:
                has_critical_kinematic = True
                kinematic_health -= 0.8
                evidence_item = {
                    "feature": "disp_haversine",
                    "observed_value": disp,
                    "threshold": self.critical_disp_thresh,
                    "severity": "CRITICAL",
                    "rationale": f"Single-epoch coordinate teleportation ({disp:.2f} m > {self.critical_disp_thresh} m)"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["disp_haversine"] = evidence_item
                explanations.append(f"Instantaneous position teleportation ({disp:.2f} m > {self.critical_disp_thresh} m)")
            elif disp > self.warning_disp_thresh:
                has_warning_kinematic = True
                kinematic_health -= 0.3
                evidence_item = {
                    "feature": "disp_haversine",
                    "observed_value": disp,
                    "threshold": self.warning_disp_thresh,
                    "severity": "WARNING",
                    "rationale": f"Single-epoch displacement exceeds threshold ({disp:.2f} m > {self.warning_disp_thresh} m)"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["disp_haversine"] = evidence_item

        # Bearing Rate (filtered against stationary jitter)
        if bearing_rate is not None and vel is not None and vel >= self.bearing_speed_floor_mps:
            if bearing_rate > self.max_bearing_rate_deg_s:
                has_warning_kinematic = True
                kinematic_health -= 0.3
                evidence_item = {
                    "feature": "bearing_rate",
                    "observed_value": bearing_rate,
                    "threshold": self.max_bearing_rate_deg_s,
                    "severity": "HIGH",
                    "rationale": f"Angular turn rate ({bearing_rate:.1f}°/s at {vel:.1f} m/s) violates steering envelope (> {self.max_bearing_rate_deg_s}°/s)"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["bearing_rate"] = evidence_item
                explanations.append(f"Steering turn rate breach ({bearing_rate:.1f}°/s at {vel:.1f} m/s)")

        kinematic_health = max(0.0, min(1.0, round(kinematic_health, 4)))

        # ---------------------------------------------------------------------
        # 2. Navigation Quality & Dilution of Precision
        # ---------------------------------------------------------------------
        geometry_health = 1.0
        has_critical_geometry = False
        has_warning_geometry = False

        if hdop is not None:
            if hdop > self.critical_hdop_thresh:
                has_critical_geometry = True
                geometry_health -= 0.6
                evidence_item = {
                    "feature": "HDOP",
                    "observed_value": hdop,
                    "threshold": self.critical_hdop_thresh,
                    "severity": "CRITICAL",
                    "rationale": f"Severe horizontal dilution of precision ({hdop:.2f} > {self.critical_hdop_thresh})"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["HDOP"] = evidence_item
                explanations.append(f"Severe HDOP masking ({hdop:.2f} > {self.critical_hdop_thresh})")
            elif hdop > self.warning_hdop_thresh:
                has_warning_geometry = True
                geometry_health -= 0.25
                evidence_item = {
                    "feature": "HDOP",
                    "observed_value": hdop,
                    "threshold": self.warning_hdop_thresh,
                    "severity": "WARNING",
                    "rationale": f"Degraded horizontal geometry ({hdop:.2f} > {self.warning_hdop_thresh})"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["HDOP"] = evidence_item

        if vdop is not None:
            if vdop > self.critical_vdop_thresh:
                has_critical_geometry = True
                geometry_health -= 0.4
                evidence_item = {
                    "feature": "VDOP",
                    "observed_value": vdop,
                    "threshold": self.critical_vdop_thresh,
                    "severity": "CRITICAL",
                    "rationale": f"Severe vertical dilution of precision ({vdop:.2f} > {self.critical_vdop_thresh})"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["VDOP"] = evidence_item
            elif vdop > self.warning_vdop_thresh:
                has_warning_geometry = True
                geometry_health -= 0.15
                evidence_item = {
                    "feature": "VDOP",
                    "observed_value": vdop,
                    "threshold": self.warning_vdop_thresh,
                    "severity": "WARNING",
                    "rationale": f"Degraded vertical geometry ({vdop:.2f} > {self.warning_vdop_thresh})"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["VDOP"] = evidence_item

        # ---------------------------------------------------------------------
        # 3. Fix Integrity & Satellite Behaviour
        # ---------------------------------------------------------------------
        if fix_int is not None:
            if fix_int < self.critical_integrity_thresh:
                has_critical_geometry = True
                geometry_health -= 0.5
                evidence_item = {
                    "feature": "fix_integrity",
                    "observed_value": fix_int,
                    "threshold": self.critical_integrity_thresh,
                    "severity": "CRITICAL",
                    "rationale": f"Fix integrity critically compromised ({fix_int:.2f} < {self.critical_integrity_thresh})"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["fix_integrity"] = evidence_item
                explanations.append(f"Critical fix integrity collapse ({fix_int:.2f} < {self.critical_integrity_thresh})")
            elif fix_int < self.warning_integrity_thresh:
                has_warning_geometry = True
                geometry_health -= 0.20
                evidence_item = {
                    "feature": "fix_integrity",
                    "observed_value": fix_int,
                    "threshold": self.warning_integrity_thresh,
                    "severity": "WARNING",
                    "rationale": f"Fix integrity degraded ({fix_int:.2f} < {self.warning_integrity_thresh})"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["fix_integrity"] = evidence_item

        # Satellite Count (trilateration limit)
        if sats is not None:
            if sats < self.min_critical_sats:
                has_critical_geometry = True
                geometry_health -= 0.7
                evidence_item = {
                    "feature": "sat_count_tot",
                    "observed_value": int(sats),
                    "threshold": self.min_critical_sats,
                    "severity": "CRITICAL",
                    "rationale": f"Satellite count ({int(sats)}) below mathematical 3D trilateration limit (< {self.min_critical_sats})"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["sat_count_tot"] = evidence_item
                explanations.append(f"Mathematical trilateration loss ({int(sats)} sats < {self.min_critical_sats})")
            elif sats < self.min_warning_sats:
                has_warning_geometry = True
                geometry_health -= 0.25
                evidence_item = {
                    "feature": "sat_count_tot",
                    "observed_value": int(sats),
                    "threshold": self.min_warning_sats,
                    "severity": "WARNING",
                    "rationale": f"Low satellite count ({int(sats)} < {self.min_warning_sats}) increasing vulnerability"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["sat_count_tot"] = evidence_item

        # Satellite Churn
        if churn is not None:
            if churn > self.critical_churn_thresh:
                has_critical_geometry = True
                geometry_health -= 0.5
                evidence_item = {
                    "feature": "sat_churn",
                    "observed_value": round(churn, 4),
                    "threshold": self.critical_churn_thresh,
                    "severity": "CRITICAL",
                    "rationale": f"Abrupt satellite constellation turnover ({churn * 100:.1f}% > {self.critical_churn_thresh * 100:.1f}%)"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["sat_churn"] = evidence_item
                explanations.append(f"Abrupt constellation turnover ({churn * 100:.1f}%)")
            elif churn > self.warning_churn_thresh:
                has_warning_geometry = True
                geometry_health -= 0.20
                evidence_item = {
                    "feature": "sat_churn",
                    "observed_value": round(churn, 4),
                    "threshold": self.warning_churn_thresh,
                    "severity": "WARNING",
                    "rationale": f"Elevated satellite turnover ({churn * 100:.1f}% > {self.warning_churn_thresh * 100:.1f}%)"
                }
                supporting_evidence.append(evidence_item)
                feature_anomalies["sat_churn"] = evidence_item

        geometry_health = max(0.0, min(1.0, round(geometry_health, 4)))

        # Also incorporate any physical rule findings from the Evidence Bundle
        rule_violations = rules_data.get("triggered_rules", [])
        rules_max_sev = rules_data.get("max_severity", "INFO")
        if rules_max_sev == "CRITICAL":
            has_critical_kinematic = True
            kinematic_health = min(kinematic_health, 0.3)
        elif rules_max_sev == "WARNING":
            has_warning_kinematic = True
            kinematic_health = min(kinematic_health, 0.7)

        for r in rule_violations:
            if isinstance(r, dict):
                feat_name = r.get("feature", "unknown")
                rule_item = {
                    "feature": feat_name,
                    "observed_value": r.get("observed_value"),
                    "threshold": r.get("threshold"),
                    "severity": r.get("severity", rules_max_sev),
                    "rationale": r.get("explanation", f"Rule {r.get('rule_id', feat_name)} triggered")
                }
            else:
                feat_name = str(r)
                rule_item = {
                    "feature": feat_name,
                    "observed_value": None,
                    "threshold": None,
                    "severity": rules_max_sev if rules_max_sev != "INFO" else "WARNING",
                    "rationale": f"Physical rule {r} triggered"
                }
            if feat_name not in feature_anomalies:
                supporting_evidence.append(rule_item)
                feature_anomalies[feat_name] = rule_item

        # ---------------------------------------------------------------------
        # 4. Synthesize Assessment Status & Operational Verdict
        # ---------------------------------------------------------------------
        if has_critical_kinematic:
            status = "CRITICAL_INVARIANT_BREACH"
            discard_rec = True
        elif has_critical_geometry:
            status = "GEOMETRY_DEGRADED"
            discard_rec = True
        elif has_warning_kinematic:
            status = "KINEMATIC_VIOLATION"
            discard_rec = False
        elif has_warning_geometry:
            status = "GEOMETRY_DEGRADED"
            discard_rec = False
        else:
            status = "INTEGRITY_NOMINAL"
            discard_rec = False

        # ---------------------------------------------------------------------
        # 5. Rigorous Confidence Calculation
        # ---------------------------------------------------------------------
        # Confidence must reflect observational certainty.
        # Degraded when satellites are missing or DOP is noisy.
        conf = 0.98
        if sats is None or sats < 4:
            conf -= 0.35  # High uncertainty when trilateration is mathematically impaired
        elif sats < 6:
            conf -= 0.15
        if hdop is not None and hdop > 4.0:
            conf -= min(0.30, (hdop - 4.0) * 0.05)
        if len(supporting_evidence) > 0 and status == "CRITICAL_INVARIANT_BREACH":
            conf = 0.99  # Absolute physical contradiction yields near-certain rejection
        conf = max(0.10, min(0.99, round(conf, 2)))

        # Explainable summary
        if status == "INTEGRITY_NOMINAL":
            explanation = "NOMINAL: Kinematic invariants, receiver geometry, and satellite counts strictly conform to Newtonian physics and healthy navigation tolerances."
        else:
            reason_str = " | ".join(explanations) if explanations else "Anomalous rule triggers detected in evidence."
            explanation = f"INTEGRITY ALERT [{status}]: {reason_str}"

        return IntegrityAssessment(
            agent_id="agent_1_integrity",
            event_id=str(event_id),
            timestamp_utc=ts_utc,
            session_id=session_id,
            epoch_id=epoch_id,
            integrity_assessment=status,
            supporting_evidence=supporting_evidence,
            confidence=conf,
            explanation=explanation,
            kinematic_health=kinematic_health,
            geometry_health=geometry_health,
            feature_level_anomalies=feature_anomalies,
            physical_violation_count=len(supporting_evidence),
            discard_recommended=discard_rec
        )


def pd_is_nan(val: Any) -> bool:
    """Helper to detect NaN without requiring pandas import inside inner loops."""
    if val is None:
        return True
    try:
        return bool(np.isnan(val))
    except (TypeError, ValueError):
        return False
