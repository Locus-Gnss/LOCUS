"""
LOCUS Phase 6 — Agent 1: GNSS Integrity Agent

Module: src.soc.integrity_agent
Focus: Low-level physical plausibility, kinematic invariants, receiver geometry,
and observation health evaluation. Operates on individual epoch Evidence Bundles.
"""

from typing import Dict, List, Optional, Union, Any
import numpy as np

from src.evidence.evidence_bundle import EvidenceBundle
from src.soc.models import Agent1Assessment, IntegrityStatus


class GNSSIntegrityAgent:
    """
    Agent 1 in the LOCUS 3-Agent SOC Hierarchy.
    Specialized in Newtonian kinematics, geometric dilution of precision (DOP),
    and raw observation sanity.
    """

    def __init__(
        self,
        critical_accel_thresh: float = 10.0,   # m/s²
        critical_jerk_thresh: float = 25.0,    # m/s³
        critical_vel_thresh: float = 85.0,     # m/s (~306 km/h)
        critical_disp_thresh: float = 100.0,   # m (instantaneous teleportation)
        critical_hdop_thresh: float = 8.0,
        min_healthy_sats: int = 4
    ):
        self.critical_accel_thresh = critical_accel_thresh
        self.critical_jerk_thresh = critical_jerk_thresh
        self.critical_vel_thresh = critical_vel_thresh
        self.critical_disp_thresh = critical_disp_thresh
        self.critical_hdop_thresh = critical_hdop_thresh
        self.min_healthy_sats = min_healthy_sats

    def assess(self, bundle: Union[EvidenceBundle, Dict[str, Any]]) -> Agent1Assessment:
        """
        Evaluate an Evidence Bundle and produce Agent 1's integrity assessment.
        """
        data = bundle.to_dict() if isinstance(bundle, EvidenceBundle) else bundle

        event_id = data.get("event_id", "")
        ts_utc = data.get("timestamp_utc")
        session_id = data.get("session_id", 0)
        epoch_id = data.get("epoch_id")

        rules_summary = data.get("physical_rules", {})
        sec_features = data.get("security_features", {})
        dq_context = data.get("data_quality", {})

        # Extract features safely
        acc = self._get_float(sec_features.get("acc_kinematic"))
        jerk = self._get_float(sec_features.get("jerk_kinematic"))
        vel = self._get_float(sec_features.get("vel_kinematic"))
        disp = self._get_float(sec_features.get("disp_haversine"))
        hdop = self._get_float(sec_features.get("HDOP")) or self._get_float(dq_context.get("hdop"))
        vdop = self._get_float(sec_features.get("VDOP"))
        fix_int = self._get_float(sec_features.get("fix_integrity"))
        sats = self._get_float(sec_features.get("sat_count_tot")) or self._get_float(dq_context.get("satellites_used"))
        bearing_rate = self._get_float(sec_features.get("bearing_rate"))

        # Triggered physical rules
        is_anom_rules = rules_summary.get("is_anomalous", False)
        max_severity = rules_summary.get("max_severity", "INFO")
        triggered_rules = rules_summary.get("triggered_rules", [])
        violated_rule_ids = [r.get("rule_id", "UNKNOWN") for r in triggered_rules]

        # 1. Compute Kinematic Health [0.0, 1.0]
        kinematic_health = 1.0
        kinematic_penalties = []

        if acc is not None:
            if abs(acc) > self.critical_accel_thresh:
                kinematic_health -= 0.6
                kinematic_penalties.append(f"Critical acceleration ({acc:.2f} m/s² > {self.critical_accel_thresh})")
            elif abs(acc) > 4.0:
                kinematic_health -= 0.25
                kinematic_penalties.append(f"High acceleration ({acc:.2f} m/s²)")

        if jerk is not None:
            if abs(jerk) > self.critical_jerk_thresh:
                kinematic_health -= 0.5
                kinematic_penalties.append(f"Critical jerk spike ({jerk:.2f} m/s³ > {self.critical_jerk_thresh})")
            elif abs(jerk) > 12.0:
                kinematic_health -= 0.2
                kinematic_penalties.append(f"Moderate jerk ({jerk:.2f} m/s³)")

        if vel is not None and vel > self.critical_vel_thresh:
            kinematic_health -= 0.7
            kinematic_penalties.append(f"Speed exceedance ({vel:.2f} m/s > {self.critical_vel_thresh})")

        if disp is not None and disp > self.critical_disp_thresh:
            kinematic_health -= 0.8
            kinematic_penalties.append(f"Coordinate jump ({disp:.2f} m > {self.critical_disp_thresh})")

        kinematic_health = max(0.0, min(1.0, round(kinematic_health, 4)))

        # 2. Compute Geometry Health [0.0, 1.0]
        geometry_health = 1.0
        geometry_penalties = []

        if hdop is not None:
            if hdop > self.critical_hdop_thresh:
                geometry_health -= 0.5
                geometry_penalties.append(f"Severe HDOP dilation ({hdop:.2f} > {self.critical_hdop_thresh})")
            elif hdop > 3.0:
                geometry_health -= 0.2
                geometry_penalties.append(f"Elevated HDOP ({hdop:.2f})")

        if vdop is not None and vdop > 8.0:
            geometry_health -= 0.2
            geometry_penalties.append(f"Elevated VDOP ({vdop:.2f})")

        if sats is not None:
            if sats < self.min_healthy_sats:
                geometry_health -= 0.6
                geometry_penalties.append(f"Satellite starvation ({int(sats)} < {self.min_healthy_sats})")
            elif sats < 6:
                geometry_health -= 0.25
                geometry_penalties.append(f"Low satellite count ({int(sats)})")

        if fix_int is not None and fix_int < 0.3:
            geometry_health -= 0.25
            geometry_penalties.append(f"Degraded fix integrity index ({fix_int:.2f})")

        geometry_health = max(0.0, min(1.0, round(geometry_health, 4)))

        # 3. Classify Integrity Status
        discard_rec = False
        if max_severity == "CRITICAL" or kinematic_health < 0.3:
            status = IntegrityStatus.CRITICAL_INVARIANT_BREACH
            discard_rec = True
            confidence = 0.95
            summary_parts = ["CRITICAL PHYSICAL INVARIANT BREACH: Impossible kinematic motion detected."]
            if kinematic_penalties:
                summary_parts.append("; ".join(kinematic_penalties))
        elif max_severity in ["HIGH", "MEDIUM"] or kinematic_health < 0.7:
            status = IntegrityStatus.KINEMATIC_VIOLATION
            discard_rec = True
            confidence = 0.85
            summary_parts = ["KINEMATIC VIOLATION: Kinematic limits exceeded."]
            if kinematic_penalties:
                summary_parts.append("; ".join(kinematic_penalties))
        elif geometry_health < 0.6 or max_severity == "LOW":
            status = IntegrityStatus.GEOMETRY_DEGRADED
            discard_rec = False
            confidence = 0.80
            summary_parts = ["GEOMETRY DEGRADED: Navigational dilution / satellite visibility impaired."]
            if geometry_penalties:
                summary_parts.append("; ".join(geometry_penalties))
        else:
            status = IntegrityStatus.NOMINAL
            discard_rec = False
            confidence = 0.98
            summary_parts = ["NOMINAL: Kinematics and constellation geometry strictly conform to physical laws."]

        verdict_text = " ".join(summary_parts)

        return Agent1Assessment(
            agent_id="agent_1_integrity",
            event_id=event_id,
            timestamp_utc=ts_utc,
            session_id=session_id,
            epoch_id=epoch_id,
            integrity_status=status,
            confidence_score=confidence,
            kinematic_health=kinematic_health,
            geometry_health=geometry_health,
            physical_violation_count=len(triggered_rules),
            violated_rules=violated_rule_ids,
            max_rule_severity=max_severity,
            discard_recommended=discard_rec,
            verdict_summary=verdict_text
        )

    @staticmethod
    def _get_float(val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            f = float(val)
            return f if np.isfinite(f) else None
        except (ValueError, TypeError):
            return None
