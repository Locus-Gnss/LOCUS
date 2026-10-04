"""
LOCUS Phase 5 — Physical Plausibility Rule Engine

Module: src.detection.physical_rules
Implements transparent, configurable physical plausibility detection rules
based on kinematic constraints and GNSS receiver physics.

Output structure per rule:
- rule_id: Unique identifier for the rule
- feature: Evaluated feature name from official 10-D vector
- observed_value: Value observed in current epoch
- threshold: Threshold configured for rule triggering
- triggered: Boolean indicator whether rule triggered
- severity: INFO | WARNING | HIGH | CRITICAL
- explanation: Physically motivated explanation of violation
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union, Any
import numpy as np
import pandas as pd


@dataclass
class RuleResult:
    """Standardized output of a physical plausibility rule evaluation."""
    rule_id: str
    feature: str
    observed_value: Optional[float]
    threshold: Any
    triggered: bool
    severity: str  # INFO, WARNING, HIGH, CRITICAL
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PhysicalRulesConfig:
    """Configurable physical thresholds with explicit scientific rationale."""

    # 1. KINEMATIC & PHYSICAL LIMITS
    # Acceleration thresholds (m/s²)
    # Rationale: Standard road vehicles rarely exceed 4 m/s² (0.4g) under normal conditions.
    # Emergency braking caps at ~8 m/s² (0.8g). > 10 m/s² indicates non-physical coordinate jump.
    acc_warning_mps2: float = 4.0
    acc_critical_mps2: float = 10.0

    # Jerk thresholds (m/s³)
    # Rationale: Passenger comfort limit is ~2 m/s³. Vehicle mechanical suspension and engine
    # limits cap jerk below 10-15 m/s³. Higher values indicate discontinuous spoofing takeovers.
    jerk_warning_mps3: float = 15.0
    jerk_critical_mps3: float = 25.0

    # Kinematic Velocity limits (m/s)
    # Rationale: 50 m/s = 180 km/h (terrestrial speed limit). 85 m/s = 306 km/h.
    # Instantaneous kinematic velocity exceeding terrestrial limits indicates coordinate teleportation.
    vel_warning_mps: float = 50.0
    vel_critical_mps: float = 85.0

    # Stationary receiver drift velocity (m/s)
    # Rationale: For stationary receivers, apparent kinematic velocity > 3 m/s indicates spoofed movement.
    stationary_drift_mps: float = 3.0
    stationary_mode: bool = False

    # Haversine Single-Epoch Displacement (meters)
    # Rationale: In a 1-second interval, displacement > 50m equates to > 180 km/h. > 100m equates to 360 km/h.
    disp_warning_m: float = 50.0
    disp_critical_m: float = 100.0

    # Bearing Rate limits (deg/s)
    # Rationale: Vehicles turning > 90 deg/s at significant speed (> 2.0 m/s) violate steering geometry.
    # At zero/low speed, bearing is noisy and heading swings are non-physical artifacts.
    bearing_rate_max_deg_s: float = 90.0
    bearing_rate_min_speed_mps: float = 2.0

    # 2. NAVIGATION QUALITY & DILUTION OF PRECISION
    # HDOP (Horizontal Dilution of Precision)
    # Rationale: Ideal < 1.0; Excellent 1-2; Good 2-4; Degraded > 4; Poor/Severely degraded > 8.
    hdop_warning: float = 4.0
    hdop_critical: float = 8.0

    # VDOP (Vertical Dilution of Precision)
    # Rationale: Typical GNSS geometry has higher vertical dilution than horizontal.
    vdop_warning: float = 5.0
    vdop_critical: float = 10.0

    # Fix Integrity Score [0.0 - 1.0]
    # Rationale: Combined health score incorporating fix quality, sat count, and DOP.
    # Below 0.45 indicates degraded fix; below 0.2 indicates loss of valid navigation.
    fix_integrity_min_warning: float = 0.45
    fix_integrity_min_critical: float = 0.20

    # 3. SATELLITE BEHAVIOR & CONSTELLATION HEALTH
    # Minimum Satellites in Fix / Tracked
    # Rationale: Minimum 4 satellites strictly required for mathematical 3D pseudorange resolution.
    # < 6 indicates vulnerability to spoofing and poor constellation geometry.
    sat_count_min_warning: int = 6
    sat_count_min_critical: int = 4

    # Satellite Churn Rate [0.0 - 1.0]
    # Rationale: Satellites orbit with ~12h periods; PRN set changes slowly (<10% per minute).
    # Churn > 35% in 1 second indicates abrupt constellation spoofing takeover or receiver lock loss.
    sat_churn_warning: float = 0.35
    sat_churn_critical: float = 0.60


class PhysicalRulesEngine:
    """Rule engine evaluating the official 10-D security feature vector against physical constraints."""

    def __init__(self, config: Optional[PhysicalRulesConfig] = None):
        self.config = config or PhysicalRulesConfig()

    def evaluate_epoch(self, epoch: Union[Dict[str, Any], pd.Series]) -> List[RuleResult]:
        """
        Evaluate a single GNSS epoch against all physical rules.
        
        Args:
            epoch: Dictionary or Series containing 10-D security features:
                   disp_haversine, vel_kinematic, acc_kinematic, jerk_kinematic,
                   bearing_rate, HDOP, VDOP, fix_integrity, sat_count_tot, sat_churn.
        
        Returns:
            List of RuleResult objects for every checked rule.
        """
        results: List[RuleResult] = []

        # Helper to safely extract float values
        def get_val(key: str) -> Optional[float]:
            val = epoch.get(key) if isinstance(epoch, dict) else epoch.get(key, None)
            if val is None or pd.isna(val):
                return None
            try:
                fval = float(val)
                return fval if np.isfinite(fval) else None
            except (ValueError, TypeError):
                return None

        disp = get_val("disp_haversine")
        vel = get_val("vel_kinematic")
        acc = get_val("acc_kinematic")
        jerk = get_val("jerk_kinematic")
        brate = get_val("bearing_rate")
        hdop = get_val("HDOP")
        vdop = get_val("VDOP")
        fix_int = get_val("fix_integrity")
        sat_cnt = get_val("sat_count_tot")
        sat_churn = get_val("sat_churn")

        # -------------------------------------------------------------------------
        # Rule 1: Kinematic Acceleration Limit (PR_ACC_001 / PR_ACC_002)
        # -------------------------------------------------------------------------
        if acc is not None:
            acc_mag = abs(acc)
            if acc_mag > self.config.acc_critical_mps2:
                results.append(RuleResult(
                    rule_id="PR_ACC_002",
                    feature="acc_kinematic",
                    observed_value=acc,
                    threshold=self.config.acc_critical_mps2,
                    triggered=True,
                    severity="CRITICAL",
                    explanation=f"Observed acceleration magnitude ({acc_mag:.2f} m/s²) exceeds critical vehicle dynamics threshold ({self.config.acc_critical_mps2} m/s²), indicating non-physical coordinate jump."
                ))
            elif acc_mag > self.config.acc_warning_mps2:
                results.append(RuleResult(
                    rule_id="PR_ACC_001",
                    feature="acc_kinematic",
                    observed_value=acc,
                    threshold=self.config.acc_warning_mps2,
                    triggered=True,
                    severity="WARNING",
                    explanation=f"Observed acceleration magnitude ({acc_mag:.2f} m/s²) exceeds normal driving envelope ({self.config.acc_warning_mps2} m/s²)."
                ))
            else:
                results.append(RuleResult(
                    rule_id="PR_ACC_001",
                    feature="acc_kinematic",
                    observed_value=acc,
                    threshold=self.config.acc_warning_mps2,
                    triggered=False,
                    severity="INFO",
                    explanation=f"Acceleration ({acc:.2f} m/s²) is within plausible physical limits."
                ))

        # -------------------------------------------------------------------------
        # Rule 2: Kinematic Jerk Limit (PR_JERK_001 / PR_JERK_002)
        # -------------------------------------------------------------------------
        if jerk is not None:
            jerk_mag = abs(jerk)
            if jerk_mag > self.config.jerk_critical_mps3:
                results.append(RuleResult(
                    rule_id="PR_JERK_002",
                    feature="jerk_kinematic",
                    observed_value=jerk,
                    threshold=self.config.jerk_critical_mps3,
                    triggered=True,
                    severity="CRITICAL",
                    explanation=f"Observed jerk magnitude ({jerk_mag:.2f} m/s³) exceeds mechanical actuator limits ({self.config.jerk_critical_mps3} m/s³), indicating trajectory discontinuity or spoofing step."
                ))
            elif jerk_mag > self.config.jerk_warning_mps3:
                results.append(RuleResult(
                    rule_id="PR_JERK_001",
                    feature="jerk_kinematic",
                    observed_value=jerk,
                    threshold=self.config.jerk_warning_mps3,
                    triggered=True,
                    severity="WARNING",
                    explanation=f"Observed jerk magnitude ({jerk_mag:.2f} m/s³) exceeds normal threshold ({self.config.jerk_warning_mps3} m/s³)."
                ))
            else:
                results.append(RuleResult(
                    rule_id="PR_JERK_001",
                    feature="jerk_kinematic",
                    observed_value=jerk,
                    threshold=self.config.jerk_warning_mps3,
                    triggered=False,
                    severity="INFO",
                    explanation=f"Jerk ({jerk:.2f} m/s³) is within plausible physical limits."
                ))

        # -------------------------------------------------------------------------
        # Rule 3: Velocity Bound (PR_VEL_001 / PR_VEL_002 / PR_VEL_STAT)
        # -------------------------------------------------------------------------
        if vel is not None:
            if self.config.stationary_mode and vel > self.config.stationary_drift_mps:
                results.append(RuleResult(
                    rule_id="PR_VEL_STAT",
                    feature="vel_kinematic",
                    observed_value=vel,
                    threshold=self.config.stationary_drift_mps,
                    triggered=True,
                    severity="HIGH",
                    explanation=f"Velocity ({vel:.2f} m/s) observed in stationary receiver mode exceeds drift limit ({self.config.stationary_drift_mps} m/s)."
                ))
            elif vel > self.config.vel_critical_mps:
                results.append(RuleResult(
                    rule_id="PR_VEL_002",
                    feature="vel_kinematic",
                    observed_value=vel,
                    threshold=self.config.vel_critical_mps,
                    triggered=True,
                    severity="CRITICAL",
                    explanation=f"Kinematic velocity ({vel:.2f} m/s) exceeds maximum plausible terrestrial speed ({self.config.vel_critical_mps} m/s)."
                ))
            elif vel > self.config.vel_warning_mps:
                results.append(RuleResult(
                    rule_id="PR_VEL_001",
                    feature="vel_kinematic",
                    observed_value=vel,
                    threshold=self.config.vel_warning_mps,
                    triggered=True,
                    severity="WARNING",
                    explanation=f"Kinematic velocity ({vel:.2f} m/s) exceeds standard speed boundary ({self.config.vel_warning_mps} m/s)."
                ))
            else:
                results.append(RuleResult(
                    rule_id="PR_VEL_001",
                    feature="vel_kinematic",
                    observed_value=vel,
                    threshold=self.config.vel_warning_mps,
                    triggered=False,
                    severity="INFO",
                    explanation=f"Kinematic velocity ({vel:.2f} m/s) is within plausible bounds."
                ))

        # -------------------------------------------------------------------------
        # Rule 4: Haversine Displacement Step (PR_DISP_001 / PR_DISP_002)
        # -------------------------------------------------------------------------
        if disp is not None:
            if disp > self.config.disp_critical_m:
                results.append(RuleResult(
                    rule_id="PR_DISP_002",
                    feature="disp_haversine",
                    observed_value=disp,
                    threshold=self.config.disp_critical_m,
                    triggered=True,
                    severity="CRITICAL",
                    explanation=f"Single-epoch displacement ({disp:.2f} m) exceeds critical threshold ({self.config.disp_critical_m} m), indicating instantaneous teleportation."
                ))
            elif disp > self.config.disp_warning_m:
                results.append(RuleResult(
                    rule_id="PR_DISP_001",
                    feature="disp_haversine",
                    observed_value=disp,
                    threshold=self.config.disp_warning_m,
                    triggered=True,
                    severity="WARNING",
                    explanation=f"Single-epoch displacement ({disp:.2f} m) exceeds warning threshold ({self.config.disp_warning_m} m)."
                ))
            else:
                results.append(RuleResult(
                    rule_id="PR_DISP_001",
                    feature="disp_haversine",
                    observed_value=disp,
                    threshold=self.config.disp_warning_m,
                    triggered=False,
                    severity="INFO",
                    explanation=f"Haversine displacement ({disp:.2f} m) is plausible."
                ))

        # -------------------------------------------------------------------------
        # Rule 5: Angular Bearing Rate (PR_BEAR_001)
        # -------------------------------------------------------------------------
        if brate is not None:
            # Check bearing rate only when moving faster than min speed to filter stationary noise
            if vel is not None and vel >= self.config.bearing_rate_min_speed_mps:
                if brate > self.config.bearing_rate_max_deg_s:
                    results.append(RuleResult(
                        rule_id="PR_BEAR_001",
                        feature="bearing_rate",
                        observed_value=brate,
                        threshold=self.config.bearing_rate_max_deg_s,
                        triggered=True,
                        severity="HIGH",
                        explanation=f"Bearing turn rate ({brate:.1f}°/s at {vel:.1f} m/s) exceeds vehicle turning limits ({self.config.bearing_rate_max_deg_s}°/s)."
                    ))
                else:
                    results.append(RuleResult(
                        rule_id="PR_BEAR_001",
                        feature="bearing_rate",
                        observed_value=brate,
                        threshold=self.config.bearing_rate_max_deg_s,
                        triggered=False,
                        severity="INFO",
                        explanation=f"Bearing rate ({brate:.1f}°/s) is within vehicle maneuver envelope."
                    ))
            else:
                results.append(RuleResult(
                    rule_id="PR_BEAR_001",
                    feature="bearing_rate",
                    observed_value=brate,
                    threshold=self.config.bearing_rate_max_deg_s,
                    triggered=False,
                    severity="INFO",
                    explanation="Receiver velocity below bearing evaluation threshold; bearing rate fluctuation is benign stationary noise."
                ))

        # -------------------------------------------------------------------------
        # Rule 6: HDOP Quality (PR_HDOP_001 / PR_HDOP_002)
        # -------------------------------------------------------------------------
        if hdop is not None:
            if hdop > self.config.hdop_critical:
                results.append(RuleResult(
                    rule_id="PR_HDOP_002",
                    feature="HDOP",
                    observed_value=hdop,
                    threshold=self.config.hdop_critical,
                    triggered=True,
                    severity="CRITICAL",
                    explanation=f"HDOP ({hdop:.2f}) indicates severe horizontal geometric dilution of precision / satellite masking."
                ))
            elif hdop > self.config.hdop_warning:
                results.append(RuleResult(
                    rule_id="PR_HDOP_001",
                    feature="HDOP",
                    observed_value=hdop,
                    threshold=self.config.hdop_warning,
                    triggered=True,
                    severity="WARNING",
                    explanation=f"HDOP ({hdop:.2f}) indicates degraded horizontal satellite geometry."
                ))
            else:
                results.append(RuleResult(
                    rule_id="PR_HDOP_001",
                    feature="HDOP",
                    observed_value=hdop,
                    threshold=self.config.hdop_warning,
                    triggered=False,
                    severity="INFO",
                    explanation=f"HDOP ({hdop:.2f}) is within nominal bounds."
                ))

        # -------------------------------------------------------------------------
        # Rule 7: VDOP Quality (PR_VDOP_001 / PR_VDOP_002)
        # -------------------------------------------------------------------------
        if vdop is not None:
            if vdop > self.config.vdop_critical:
                results.append(RuleResult(
                    rule_id="PR_VDOP_002",
                    feature="VDOP",
                    observed_value=vdop,
                    threshold=self.config.vdop_critical,
                    triggered=True,
                    severity="CRITICAL",
                    explanation=f"VDOP ({vdop:.2f}) indicates severe vertical geometric dilution of precision."
                ))
            elif vdop > self.config.vdop_warning:
                results.append(RuleResult(
                    rule_id="PR_VDOP_001",
                    feature="VDOP",
                    observed_value=vdop,
                    threshold=self.config.vdop_warning,
                    triggered=True,
                    severity="WARNING",
                    explanation=f"VDOP ({vdop:.2f}) indicates degraded vertical satellite geometry."
                ))
            else:
                results.append(RuleResult(
                    rule_id="PR_VDOP_001",
                    feature="VDOP",
                    observed_value=vdop,
                    threshold=self.config.vdop_warning,
                    triggered=False,
                    severity="INFO",
                    explanation=f"VDOP ({vdop:.2f}) is within nominal bounds."
                ))

        # -------------------------------------------------------------------------
        # Rule 8: Fix Integrity Score (PR_INT_001 / PR_INT_002)
        # -------------------------------------------------------------------------
        if fix_int is not None:
            if fix_int < self.config.fix_integrity_min_critical:
                results.append(RuleResult(
                    rule_id="PR_INT_002",
                    feature="fix_integrity",
                    observed_value=fix_int,
                    threshold=self.config.fix_integrity_min_critical,
                    triggered=True,
                    severity="CRITICAL",
                    explanation=f"Fix integrity score ({fix_int:.2f}) is critically compromised (< {self.config.fix_integrity_min_critical})."
                ))
            elif fix_int < self.config.fix_integrity_min_warning:
                results.append(RuleResult(
                    rule_id="PR_INT_001",
                    feature="fix_integrity",
                    observed_value=fix_int,
                    threshold=self.config.fix_integrity_min_warning,
                    triggered=True,
                    severity="WARNING",
                    explanation=f"Fix integrity score ({fix_int:.2f}) is degraded (< {self.config.fix_integrity_min_warning})."
                ))
            else:
                results.append(RuleResult(
                    rule_id="PR_INT_001",
                    feature="fix_integrity",
                    observed_value=fix_int,
                    threshold=self.config.fix_integrity_min_warning,
                    triggered=False,
                    severity="INFO",
                    explanation=f"Fix integrity ({fix_int:.2f}) is healthy."
                ))

        # -------------------------------------------------------------------------
        # Rule 9: Satellite Constellation Count (PR_SAT_001 / PR_SAT_002)
        # -------------------------------------------------------------------------
        if sat_cnt is not None:
            if sat_cnt < self.config.sat_count_min_critical:
                results.append(RuleResult(
                    rule_id="PR_SAT_002",
                    feature="sat_count_tot",
                    observed_value=sat_cnt,
                    threshold=self.config.sat_count_min_critical,
                    triggered=True,
                    severity="CRITICAL",
                    explanation=f"Tracked satellite count ({int(sat_cnt)}) is below minimum required for 3D trilateration (< {self.config.sat_count_min_critical})."
                ))
            elif sat_cnt < self.config.sat_count_min_warning:
                results.append(RuleResult(
                    rule_id="PR_SAT_001",
                    feature="sat_count_tot",
                    observed_value=sat_cnt,
                    threshold=self.config.sat_count_min_warning,
                    triggered=True,
                    severity="WARNING",
                    explanation=f"Satellite count ({int(sat_cnt)}) is degraded (< {self.config.sat_count_min_warning}), increasing vulnerability."
                ))
            else:
                results.append(RuleResult(
                    rule_id="PR_SAT_001",
                    feature="sat_count_tot",
                    observed_value=sat_cnt,
                    threshold=self.config.sat_count_min_warning,
                    triggered=False,
                    severity="INFO",
                    explanation=f"Tracked satellite count ({int(sat_cnt)}) is robust."
                ))

        # -------------------------------------------------------------------------
        # Rule 10: Satellite Churn Rate (PR_CHURN_001 / PR_CHURN_002)
        # -------------------------------------------------------------------------
        if sat_churn is not None:
            if sat_churn > self.config.sat_churn_critical:
                results.append(RuleResult(
                    rule_id="PR_CHURN_002",
                    feature="sat_churn",
                    observed_value=sat_churn,
                    threshold=self.config.sat_churn_critical,
                    triggered=True,
                    severity="CRITICAL",
                    explanation=f"Abrupt satellite constellation turnover ({sat_churn * 100:.1f}%) exceeds critical threshold ({self.config.sat_churn_critical * 100:.1f}%), indicating spoofer lock-on or receiver reset."
                ))
            elif sat_churn > self.config.sat_churn_warning:
                results.append(RuleResult(
                    rule_id="PR_CHURN_001",
                    feature="sat_churn",
                    observed_value=sat_churn,
                    threshold=self.config.sat_churn_warning,
                    triggered=True,
                    severity="WARNING",
                    explanation=f"Elevated satellite turnover ({sat_churn * 100:.1f}%) indicates constellation instability."
                ))
            else:
                results.append(RuleResult(
                    rule_id="PR_CHURN_001",
                    feature="sat_churn",
                    observed_value=sat_churn,
                    threshold=self.config.sat_churn_warning,
                    triggered=False,
                    severity="INFO",
                    explanation=f"Satellite churn ({sat_churn * 100:.1f}%) is within expected orbital drift."
                ))

        return results

    def get_summary(self, results: List[RuleResult]) -> Dict[str, Any]:
        """
        Aggregate evaluated rule results into a compact summary for evidence bundling.
        """
        severity_rank = {"INFO": 0, "WARNING": 1, "HIGH": 2, "CRITICAL": 3}
        triggered = [r for r in results if r.triggered]
        
        max_sev = "INFO"
        if triggered:
            max_sev = max((r.severity for r in triggered), key=lambda s: severity_rank.get(s, 0))

        return {
            "is_anomalous": len(triggered) > 0,
            "triggered_count": len(triggered),
            "total_rules_evaluated": len(results),
            "max_severity": max_sev,
            "triggered_rules": [r.to_dict() for r in triggered],
            "all_rules": [r.to_dict() for r in results]
        }

    def evaluate_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Evaluate an entire DataFrame of 10-D feature vectors.
        Returns a list of summary dicts, one per row.
        """
        summaries = []
        for _, row in df.iterrows():
            res = self.evaluate_epoch(row)
            summaries.append(self.get_summary(res))
        return summaries
