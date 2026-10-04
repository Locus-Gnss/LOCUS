"""
LOCUS Phase 6 — Agent 2: Temporal & Threat Correlation Agent

Module: src.agents.temporal_threat_agent
Focus: Evaluates temporal sequence persistence, historical event context,
LSTM reconstruction error spectra, XGBoost supervised status, and multi-detector convergence.

Critical Invariants:
- Read-only operation: NEVER modifies sensor telemetry.
- Zero fabrication: All evaluations strictly reference verified evidence.
- Transparent explainability: Cites exact error values, thresholds, and persistence streaks.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union, Any
import numpy as np

from src.evidence.evidence_bundle import EvidenceBundle


@dataclass
class TemporalAssessment:
    """
    Structured output from Agent 2 (Temporal / Threat Agent).
    """
    agent_id: str = "agent_2_temporal_threat"
    event_id: str = ""
    timestamp_utc: Optional[str] = None
    session_id: int = 0
    epoch_id: Optional[int] = None
    temporal_assessment: str = "BENIGN"  # BENIGN, TRANSIENT_ANOMALY, PERSISTENT_DRIFT, SPOOFING_COORDINATE_STEP, etc.
    pattern_description: str = ""
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0
    persistence_count: int = 0
    persistence_ratio: float = 0.0
    detector_convergence: float = 0.0
    active_detectors_count: int = 0
    anomalous_detectors_count: int = 0
    primary_feature_contributors: List[str] = field(default_factory=list)
    lstm_reconstruction_error: Optional[float] = None
    iforest_anomaly_score: Optional[float] = None
    xgboost_status: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TemporalThreatAgent:
    """
    Agent 2 in the LOCUS 3-Agent SOC Hierarchy.
    Specialized in temporal sequence modeling, rolling window persistence tracking,
    threat pattern classification, and historical context analysis.
    """

    def __init__(
        self,
        persistence_window: int = 10,
        persistent_streak_thresh: int = 3,
        convergence_high_thresh: float = 0.60
    ):
        self.persistence_window = persistence_window
        self.persistent_streak_thresh = persistent_streak_thresh
        self.convergence_high_thresh = convergence_high_thresh

        # Internal state memory for session-aware streaming
        self._history_buffers: Dict[int, List[Dict[str, Any]]] = {}
        self._current_streak: Dict[int, int] = {}

    def reset(self, session_id: Optional[int] = None) -> None:
        """Clear historical buffers."""
        if session_id is not None:
            self._history_buffers.pop(session_id, None)
            self._current_streak.pop(session_id, None)
        else:
            self._history_buffers.clear()
            self._current_streak.clear()

    def assess(
        self,
        bundle: Union[EvidenceBundle, Dict[str, Any]],
        historical_context: Optional[List[Dict[str, Any]]] = None
    ) -> TemporalAssessment:
        """
        Evaluate temporal dynamics of an Evidence Bundle within its session context.
        Read-only: Sensor data is never modified.
        """
        data = bundle.to_dict() if isinstance(bundle, EvidenceBundle) else (bundle if isinstance(bundle, dict) else bundle.to_dict())

        event_id = str(data.get("event_id", ""))
        ts_utc = data.get("timestamp_utc")
        session_id = int(data.get("session_id", 0))
        epoch_id = data.get("epoch_id")

        rules_summary = data.get("physical_rules", {})
        if_summary = data.get("isolation_forest", {})
        temp_summary = data.get("temporal_model", {})
        xgb_summary = data.get("xgboost", {})
        sec_features = data.get("security_features", {})

        # ---------------------------------------------------------------------
        # 1. Detector Signals Extraction
        # ---------------------------------------------------------------------
        # Physical rules signal
        rules_anom = bool(rules_summary.get("is_anomalous", False))
        max_rule_sev = rules_summary.get("max_severity", "INFO")

        # Isolation Forest signal
        if_anom = bool(if_summary.get("is_anomaly", False))
        if_score = if_summary.get("anomaly_score")
        if if_score is not None:
            try:
                if_score = float(if_score)
            except (ValueError, TypeError):
                if_score = None

        # Temporal LSTM signal
        temp_status = temp_summary.get("status", "UNAVAILABLE")
        temp_anom = bool(temp_summary.get("is_anomaly", False))
        lstm_error = temp_summary.get("reconstruction_error")
        error_thresh = temp_summary.get("error_threshold")
        feature_errors = temp_summary.get("feature_errors", {})

        # XGBoost signal
        xgb_avail = bool(xgb_summary.get("available", False))
        xgb_status = xgb_summary.get("status", "UNFITTED_PENDING_LABELLED_SCENARIOS")
        xgb_pred = xgb_summary.get("predicted_label")

        # ---------------------------------------------------------------------
        # 2. Multi-Detector Convergence Calculation
        # ---------------------------------------------------------------------
        active_detectors = 0
        anomalous_detectors = 0

        # Detector 1: Physical Rules
        active_detectors += 1
        if rules_anom:
            anomalous_detectors += 1

        # Detector 2: Isolation Forest
        if if_summary.get("status") != "UNAVAILABLE" and if_score is not None:
            active_detectors += 1
            if if_anom:
                anomalous_detectors += 1

        # Detector 3: Temporal LSTM Autoencoder
        if temp_status == "INFERRED" and lstm_error is not None:
            active_detectors += 1
            if temp_anom:
                anomalous_detectors += 1

        # Detector 4: XGBoost (when operational)
        if xgb_avail:
            active_detectors += 1
            if xgb_pred is not None and xgb_pred > 0:
                anomalous_detectors += 1

        convergence = round(anomalous_detectors / active_detectors, 3) if active_detectors > 0 else 0.0

        # Identify primary feature contributors from LSTM reconstruction errors
        primary_contributors = []
        if feature_errors and isinstance(feature_errors, dict):
            sorted_feats = sorted(feature_errors.items(), key=lambda kv: kv[1] if isinstance(kv[1], (int, float)) else 0.0, reverse=True)
            primary_contributors = [f[0] for f in sorted_feats[:3] if isinstance(f[1], (int, float)) and f[1] > 0.05]

        # ---------------------------------------------------------------------
        # 3. Rolling Window Persistence & Historical Context Tracking
        # ---------------------------------------------------------------------
        # Determine whether current epoch is anomalous
        epoch_is_anomalous = (anomalous_detectors >= 1)

        # Update session buffer
        if historical_context is not None:
            history = list(historical_context)
        else:
            if session_id not in self._history_buffers:
                self._history_buffers[session_id] = []
                self._current_streak[session_id] = 0
            history = self._history_buffers[session_id]

        if epoch_is_anomalous:
            streak = self._current_streak.get(session_id, 0) + 1
        else:
            streak = 0
        self._current_streak[session_id] = streak

        # Record this epoch in history
        history.append({
            "event_id": event_id,
            "epoch_id": epoch_id,
            "is_anomalous": epoch_is_anomalous,
            "anomalous_count": anomalous_detectors,
            "rules_anom": rules_anom,
            "if_anom": if_anom,
            "temp_anom": temp_anom
        })
        if len(history) > self.persistence_window:
            history.pop(0)

        # Calculate persistence metrics
        recent_window = history[-min(len(history), self.persistence_window):]
        anom_in_window = sum(1 for h in recent_window if h["is_anomalous"])
        persistence_ratio = round(anom_in_window / len(recent_window), 3) if len(recent_window) > 0 else 0.0

        # ---------------------------------------------------------------------
        # 4. Temporal Threat Pattern Categorization
        # ---------------------------------------------------------------------
        supporting_evidence: List[Dict[str, Any]] = []

        if lstm_error is not None and error_thresh is not None:
            supporting_evidence.append({
                "detector": "temporal_lstm",
                "reconstruction_error": round(float(lstm_error), 4),
                "error_threshold": round(float(error_thresh), 4),
                "is_anomaly": temp_anom,
                "top_reconstruction_features": primary_contributors
            })

        if if_score is not None:
            supporting_evidence.append({
                "detector": "isolation_forest",
                "anomaly_score": round(float(if_score), 4),
                "is_anomaly": if_anom
            })

        supporting_evidence.append({
            "persistence_streak": streak,
            "persistence_ratio_last_10": persistence_ratio,
            "detector_convergence": convergence,
            "active_detectors": active_detectors,
            "anomalous_detectors": anomalous_detectors
        })

        # Pattern resolution logic
        if anomalous_detectors == 0 and persistence_ratio == 0.0:
            classification = "BENIGN"
            pattern_desc = "Nominal temporal baseline: consecutive epochs exhibit stable reconstruction and zero detector convergence."
            conf = 0.98

        elif max_rule_sev == "CRITICAL" and convergence >= 0.5:
            classification = "SPOOFING_COORDINATE_STEP"
            pattern_desc = (
                f"Instantaneous coordinate step detected: Multiple independent detectors converged (convergence: {convergence*100:.1f}%) "
                f"with critical physical violation. Abrupt kinematic disruption confirmed."
            )
            conf = 0.95

        elif streak >= self.persistent_streak_thresh or (len(recent_window) >= self.persistent_streak_thresh and persistence_ratio >= 0.5):
            # Check if RF jamming / starvation or trajectory injection
            hdop_val = sec_features.get("HDOP")
            sats_val = sec_features.get("sat_count_tot")
            if (hdop_val is not None and hdop_val > 4.0) or (sats_val is not None and sats_val < 6):
                classification = "RF_JAMMING_DEGRADATION"
                pattern_desc = (
                    f"Persistent RF interference / constellation degradation: Sustained anomaly across {streak} consecutive epochs "
                    f"accompanied by degraded satellite geometry (HDOP: {hdop_val}, Satellites: {sats_val})."
                )
                conf = 0.90
            elif temp_anom and primary_contributors:
                classification = "SPOOFING_TRAJECTORY_INJECTION"
                pattern_desc = (
                    f"Persistent trajectory deviation: Sustained multi-epoch drift (streak: {streak}, window ratio: {persistence_ratio:.2f}) "
                    f"with elevated LSTM reconstruction error on features: {', '.join(primary_contributors)}."
                )
                conf = 0.88
            else:
                classification = "PERSISTENT_DRIFT"
                pattern_desc = (
                    f"Sustained anomalous trend across {streak} consecutive epochs (window ratio: {persistence_ratio:.2f}). "
                    f"Exceeds transient noise threshold."
                )
                conf = 0.85

        elif streak <= 2 and convergence < 0.6:
            # Transient / isolated glitch
            classification = "TRANSIENT_ANOMALY"
            pattern_desc = (
                f"Isolated transient anomaly (streak: {streak}, window ratio: {persistence_ratio:.2f}). "
                f"Non-persistent detector trigger; probable receiver jitter or brief measurement artifact."
            )
            conf = 0.80

        else:
            classification = "UNKNOWN_ANOMALY"
            pattern_desc = f"Anomalous temporal behavior observed (streak: {streak}, convergence: {convergence:.2f})."
            conf = 0.70

        return TemporalAssessment(
            agent_id="agent_2_temporal_threat",
            event_id=event_id,
            timestamp_utc=ts_utc,
            session_id=session_id,
            epoch_id=epoch_id,
            temporal_assessment=classification,
            pattern_description=pattern_desc,
            supporting_evidence=supporting_evidence,
            confidence=conf,
            persistence_count=streak,
            persistence_ratio=persistence_ratio,
            detector_convergence=convergence,
            active_detectors_count=active_detectors,
            anomalous_detectors_count=anomalous_detectors,
            primary_feature_contributors=primary_contributors,
            lstm_reconstruction_error=round(float(lstm_error), 4) if lstm_error is not None else None,
            iforest_anomaly_score=round(float(if_score), 4) if if_score is not None else None,
            xgboost_status=xgb_status
        )
