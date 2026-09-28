"""
LOCUS Phase 6 — Agent 2: Temporal Threat Correlation Agent

Module: src.soc.temporal_threat_agent
Focus: Multi-epoch temporal dynamics, statistical anomaly correlation across
Isolation Forest and LSTM Autoencoder, anomaly persistence tracking,
and per-feature error attribution.
"""

from collections import deque
from typing import Dict, List, Optional, Union, Any, Tuple
import numpy as np

from src.evidence.evidence_bundle import EvidenceBundle
from src.soc.models import Agent2Assessment, ThreatClassification


class TemporalThreatAgent:
    """
    Agent 2 in the LOCUS 3-Agent SOC Hierarchy.
    Maintains session-level sliding window history to assess persistence,
    multi-detector convergence, and feature-level root causes.
    """

    def __init__(
        self,
        history_window_size: int = 15,
        persistence_streak_threshold: int = 3,
        persistence_ratio_threshold: float = 0.35,
        iforest_anomaly_threshold: float = 0.60,
        lstm_anomaly_threshold: float = 0.50
    ):
        self.history_window_size = history_window_size
        self.persistence_streak_threshold = persistence_streak_threshold
        self.persistence_ratio_threshold = persistence_ratio_threshold
        self.iforest_anomaly_threshold = iforest_anomaly_threshold
        self.lstm_anomaly_threshold = lstm_anomaly_threshold

        # Session-aware rolling buffers: session_id -> deque of recent epoch records
        self._session_histories: Dict[int, deque] = {}
        # Consecutive anomaly streaks per session: session_id -> int
        self._consecutive_streaks: Dict[int, int] = {}

    def reset(self, session_id: Optional[int] = None) -> None:
        """Reset internal history for a specific session or all sessions."""
        if session_id is not None:
            self._session_histories.pop(session_id, None)
            self._consecutive_streaks.pop(session_id, None)
        else:
            self._session_histories.clear()
            self._consecutive_streaks.clear()

    def assess(self, bundle: Union[EvidenceBundle, Dict[str, Any]]) -> Agent2Assessment:
        """
        Evaluate an Evidence Bundle against rolling temporal history and cross-detector synergy.
        """
        data = bundle.to_dict() if isinstance(bundle, EvidenceBundle) else bundle

        event_id = data.get("event_id", "")
        ts_utc = data.get("timestamp_utc")
        session_id = int(data.get("session_id", 0))
        epoch_id = data.get("epoch_id")

        if_data = data.get("isolation_forest", {})
        lstm_data = data.get("temporal_model", {})
        xgb_data = data.get("xgboost", {})
        rules_data = data.get("physical_rules", {})
        sec_features = data.get("security_features", {})

        # 1. Parse individual detector outputs
        if_is_anom = bool(if_data.get("is_anomaly", False))
        if_score = self._to_float(if_data.get("anomaly_score"))

        lstm_status = lstm_data.get("status", "UNAVAILABLE")
        lstm_is_anom = bool(lstm_data.get("is_anomaly", False))
        lstm_score = self._to_float(lstm_data.get("temporal_anomaly_score"))
        lstm_recon_err = self._to_float(lstm_data.get("reconstruction_error"))
        feat_errors = lstm_data.get("feature_errors", {})

        rules_is_anom = bool(rules_data.get("is_anomalous", False))
        xgb_avail = bool(xgb_data.get("available", False))

        # Determine if this epoch is flagged as anomalous by any detector
        active_detectors = 0
        anomalous_detectors = 0

        # Physical Rules detector
        active_detectors += 1
        if rules_is_anom:
            anomalous_detectors += 1

        # Isolation Forest detector
        if if_data.get("status") != "UNAVAILABLE" and if_score is not None:
            active_detectors += 1
            if if_is_anom or if_score >= self.iforest_anomaly_threshold:
                anomalous_detectors += 1

        # Temporal LSTM detector
        if lstm_status == "INFERRED" and lstm_score is not None:
            active_detectors += 1
            if lstm_is_anom or lstm_score >= self.lstm_anomaly_threshold:
                anomalous_detectors += 1

        # XGBoost detector
        if xgb_avail:
            active_detectors += 1
            if xgb_data.get("attack_probability", 0.0) and xgb_data.get("attack_probability", 0.0) > 0.5:
                anomalous_detectors += 1

        epoch_has_anomaly = anomalous_detectors > 0
        convergence = round(anomalous_detectors / max(active_detectors, 1), 4)

        # 2. Update session sliding history
        if session_id not in self._session_histories:
            self._session_histories[session_id] = deque(maxlen=self.history_window_size)
            self._consecutive_streaks[session_id] = 0

        history = self._session_histories[session_id]

        if epoch_has_anomaly:
            self._consecutive_streaks[session_id] += 1
        else:
            self._consecutive_streaks[session_id] = 0

        current_streak = self._consecutive_streaks[session_id]

        # Record this epoch in history
        history.append({
            "epoch_id": epoch_id,
            "has_anomaly": epoch_has_anomaly,
            "anomalous_detectors": anomalous_detectors,
            "convergence": convergence,
            "if_score": if_score,
            "lstm_score": lstm_score,
        })

        # Calculate persistence ratio in window
        window_anoms = sum(1 for h in history if h["has_anomaly"])
        window_len = len(history)
        persistence_ratio = round(window_anoms / max(window_len, 1), 4)

        # 3. Feature Attribution: identify which physical dimensions drive the error
        top_contributors = self._extract_top_contributors(feat_errors, sec_features)

        # 4. Threat Pattern Classification
        classification, confidence, rationale = self._classify_threat(
            epoch_has_anomaly=epoch_has_anomaly,
            current_streak=current_streak,
            persistence_ratio=persistence_ratio,
            convergence=convergence,
            anomalous_detectors=anomalous_detectors,
            rules_is_anom=rules_is_anom,
            if_is_anom=if_is_anom,
            if_score=if_score,
            lstm_is_anom=lstm_is_anom,
            top_contributors=top_contributors,
            sec_features=sec_features
        )

        return Agent2Assessment(
            agent_id="agent_2_temporal_threat",
            event_id=event_id,
            timestamp_utc=ts_utc,
            session_id=session_id,
            epoch_id=epoch_id,
            threat_classification=classification,
            confidence_score=confidence,
            persistence_count=current_streak,
            persistence_ratio=persistence_ratio,
            detector_convergence=convergence,
            active_detectors_count=active_detectors,
            anomalous_detectors_count=anomalous_detectors,
            primary_feature_contributors=top_contributors,
            lstm_reconstruction_error=lstm_recon_err,
            iforest_anomaly_score=if_score,
            xgboost_prediction=xgb_data if xgb_avail else None,
            threat_summary=rationale
        )

    def _extract_top_contributors(
        self,
        feat_errors: Dict[str, Any],
        sec_features: Dict[str, Any]
    ) -> List[str]:
        """Rank features by contribution to anomalous behavior."""
        if feat_errors and isinstance(feat_errors, dict):
            # Sort features by highest reconstruction MSE
            valid_errs = {
                k: float(v) for k, v in feat_errors.items()
                if v is not None and np.isfinite(float(v))
            }
            if valid_errs:
                sorted_feats = sorted(valid_errs.items(), key=lambda x: x[1], reverse=True)
                return [f[0] for f in sorted_feats[:3]]

        # Fallback: identify features that exceed heuristic nominal standard ranges
        heuristic_culprits = []
        acc = self._to_float(sec_features.get("acc_kinematic"))
        if acc is not None and abs(acc) > 4.0:
            heuristic_culprits.append("acc_kinematic")

        disp = self._to_float(sec_features.get("disp_haversine"))
        if disp is not None and disp > 10.0:
            heuristic_culprits.append("disp_haversine")

        jerk = self._to_float(sec_features.get("jerk_kinematic"))
        if jerk is not None and abs(jerk) > 12.0:
            heuristic_culprits.append("jerk_kinematic")

        hdop = self._to_float(sec_features.get("HDOP"))
        if hdop is not None and hdop > 3.0:
            heuristic_culprits.append("HDOP")

        sats = self._to_float(sec_features.get("sat_count_tot"))
        if sats is not None and sats < 5:
            heuristic_culprits.append("sat_count_tot")

        return heuristic_culprits[:3]

    def _classify_threat(
        self,
        epoch_has_anomaly: bool,
        current_streak: int,
        persistence_ratio: float,
        convergence: float,
        anomalous_detectors: int,
        rules_is_anom: bool,
        if_is_anom: bool,
        if_score: Optional[float],
        lstm_is_anom: bool,
        top_contributors: List[str],
        sec_features: Dict[str, Any]
    ) -> Tuple[ThreatClassification, float, str]:
        """Classify temporal threat pattern based on multi-detector and persistence evidence."""
        if not epoch_has_anomaly and persistence_ratio == 0.0:
            return (
                ThreatClassification.BENIGN,
                0.98,
                "Temporal sequence is nominal with no multi-detector anomalies or persistence."
            )

        # High convergence attack patterns
        disp = self._to_float(sec_features.get("disp_haversine")) or 0.0
        acc = abs(self._to_float(sec_features.get("acc_kinematic")) or 0.0)
        sats = self._to_float(sec_features.get("sat_count_tot")) or 12.0
        hdop = self._to_float(sec_features.get("HDOP")) or 1.0

        # 1. Coordinate step injection / Teleportation
        if disp > 50.0 or acc > 10.0:
            return (
                ThreatClassification.SPOOFING_COORDINATE_STEP,
                0.95,
                f"Abrupt spatial coordinate injection detected (disp: {disp:.1f}m, acc: {acc:.1f}m/s²). Multi-detector convergence: {convergence:.2f}."
            )

        # 2. RF Jamming / Satellite Starvation
        if sats < 4 or (hdop > 7.0 and sats < 6):
            return (
                ThreatClassification.RF_JAMMING_DEGRADATION,
                0.90,
                f"Severe satellite starvation/loss (sats: {int(sats)}, HDOP: {hdop:.1f}) indicative of intentional RF jamming or dense obscuration."
            )

        # 3. Persistent Trajectory Drift / Slow Walk-off Spoofing
        # A single epoch (streak == 1) cannot be a sustained drift.
        is_persistent = (
            current_streak >= self.persistence_streak_threshold or
            (current_streak >= 2 and persistence_ratio >= self.persistence_ratio_threshold)
        )

        if is_persistent:
            if "vel_kinematic" in top_contributors or "disp_haversine" in top_contributors or "acc_kinematic" in top_contributors:
                return (
                    ThreatClassification.SPOOFING_TRAJECTORY_INJECTION,
                    0.88,
                    f"Sustained temporal drift detected across {current_streak} consecutive epochs (persistence ratio: {persistence_ratio:.2f}). Kinematic trajectory manipulation suspected."
                )
            return (
                ThreatClassification.PERSISTENT_DRIFT,
                0.85,
                f"Persistent anomalous dynamics over {current_streak} consecutive epochs (ratio: {persistence_ratio:.2f}). Multi-detector convergence: {convergence:.2f}."
            )

        # 4. Isolated / Transient Glitch (Multipath or temporary cycle slip)
        if not is_persistent:
            if "HDOP" in top_contributors or "bearing_rate" in top_contributors:
                return (
                    ThreatClassification.MULTIPATH_INTERFERENCE,
                    0.80,
                    f"Transient geometric fluctuation detected (streak: {current_streak}, persistence ratio: {persistence_ratio:.2f}). Consistent with localized multipath."
                )
            return (
                ThreatClassification.TRANSIENT_ANOMALY,
                0.82,
                f"Isolated transient anomaly (streak: {current_streak}). Non-persistent detector trigger; probable receiver jitter or brief measurement artifact."
            )

        return (
            ThreatClassification.UNKNOWN_ANOMALY,
            0.70,
            f"Anomalous behavior detected with uncharacterized signature (detectors: {anomalous_detectors}, convergence: {convergence:.2f})."
        )

    @staticmethod
    def _to_float(val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            f = float(val)
            return round(f, 4) if np.isfinite(f) else None
        except (ValueError, TypeError):
            return None
