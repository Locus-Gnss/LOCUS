"""
Module 5: Detection Quad
Module: src.ui.pages.p_detection_quad
Phase 5.5 Multi-Detector Consensus Quad inspecting physical invariants, spatial ML, supervised trees, and deep sequence autoencoders.
"""

from typing import Dict, Any, List
import pandas as pd
import streamlit as st

from src.ui.utils.formatting import safe_float, safe_int, safe_str


def render_detection_quad(data_service, selected_event_id: str):
    """
    Render Detection Quad module matching Screenshot 5 specification.
    """
    st.markdown("<div class='section-header'>PHASE 5.5 MULTI-DETECTOR CONSENSUS QUAD</div>", unsafe_allow_html=True)
    st.markdown(
        """
    <div class="soc-callout">
        <strong>MULTI-DETECTOR ARCHITECTURE:</strong> Quad-layered defense in depth combining deterministic kinematics,
        unsupervised spatial isolation, gradient-boosted decision trees, and temporal sequence autoencoding.
    </div>
    """,
        unsafe_allow_html=True,
    )

    bundle = data_service.load_event(selected_event_id)
    if not bundle:
        st.info("NO DETECTION DATA AVAILABLE FOR ACTIVE EVENT")
        return

    pr = bundle.physical_rules if isinstance(bundle.physical_rules, dict) else {}
    ifo = bundle.isolation_forest if isinstance(bundle.isolation_forest, dict) else {}
    xgb = bundle.xgboost if isinstance(bundle.xgboost, dict) else {}
    temp = bundle.temporal_model if isinstance(bundle.temporal_model, dict) else {}

    pr_viol = pr.get("triggered_count", 0) > 0 or pr.get("status") == "VIOLATED"
    ifo_anom = bool(ifo.get("is_anomaly", False))
    xgb_label = safe_str(xgb.get("predicted_label"), "NOMINAL")
    xgb_anom = xgb_label not in ["NOMINAL", "UNASSIGNED", "NOMINAL_FLIGHT"]
    temp_anom = bool(temp.get("is_anomaly", False))

    d1, d2, d3, d4 = st.columns(4)

    # DETECTOR 1 / DETERMINISTIC: Physical Rules Engine
    with d1:
        st.markdown(
            f"""
        <div class="detector-card" style="border-left: 3px solid {'#f87171' if pr_viol else '#34d399'};">
            <div style="font-size: 8.5px; color: #64748b; font-family: monospace;">DETECTOR 1 / DETERMINISTIC</div>
            <div class="det-title">PHYSICAL RULES ENGINE</div>
            <div style="margin: 6px 0;"><span class="badge {'badge-critical' if pr_viol else 'badge-normal'}">{'VIOLATION' if pr_viol else 'NOMINAL'}</span></div>
            <div class="det-score">VIOLATIONS: {safe_int(pr.get('triggered_count', 0))} / 9</div>
            <div class="det-score">MAX SEVERITY: {safe_str(pr.get('max_severity', 'INFO'))}</div>
            <div class="det-model">MODEL: rules-engine-v2.0</div>
            <div style="font-size: 9px; color: #94a3b8; margin-top: 6px; line-height: 1.3;">
                Evaluates acceleration (&lt;4m/s²), jerk (&lt;12m/s³), speed of sound (&lt;340m/s).
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # DETECTOR 2 / SPATIAL ML: Spatial Isolation Forest
    with d2:
        ifo_score = safe_float(ifo.get("anomaly_score", 0.0))
        ifo_thresh = safe_float(ifo.get("threshold", -0.05))
        st.markdown(
            f"""
        <div class="detector-card" style="border-left: 3px solid {'#f87171' if ifo_anom else '#34d399'};">
            <div style="font-size: 8.5px; color: #64748b; font-family: monospace;">DETECTOR 2 / SPATIAL ML</div>
            <div class="det-title">SPATIAL ISOLATION FOREST</div>
            <div style="margin: 6px 0;"><span class="badge {'badge-critical' if ifo_anom else 'badge-normal'}">{'ANOMALY' if ifo_anom else 'NOMINAL'}</span></div>
            <div class="det-score">SCORE: {ifo_score:.4f}</div>
            <div class="det-score">THRESHOLD: {ifo_thresh:.4f}</div>
            <div class="det-model">MODEL: iforest-v1.0 (100 Trees)</div>
            <div style="font-size: 9px; color: #94a3b8; margin-top: 6px; line-height: 1.3;">
                Unsupervised partitioning isolating outliers in 10-D subspace.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # DETECTOR 3 / SUPERVISED TIER: XGBoost Classifier
    with d3:
        xgb_conf = safe_float(xgb.get("confidence", 0.0))
        st.markdown(
            f"""
        <div class="detector-card" style="border-left: 3px solid {'#f87171' if xgb_anom else '#34d399'};">
            <div style="font-size: 8.5px; color: #64748b; font-family: monospace;">DETECTOR 3 / SUPERVISED TIER</div>
            <div class="det-title">XGBOOST CLASSIFIER</div>
            <div style="margin: 6px 0;"><span class="badge {'badge-critical' if xgb_anom else 'badge-normal'}">{xgb_label}</span></div>
            <div class="det-score">CLASS: {xgb_label}</div>
            <div class="det-score">CONFIDENCE: {xgb_conf*100:.1f}%</div>
            <div class="det-model">MODEL: xgb-classifier-v1.0</div>
            <div style="font-size: 9px; color: #94a3b8; margin-top: 6px; line-height: 1.3;">
                Multi-class gradient boosted trees classifying attack signatures.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # DETECTOR 4 / DEEP LEARNING: LSTM Autoencoder
    with d4:
        recon_err = safe_float(temp.get("reconstruction_error", 0.0))
        temp_thresh = safe_float(temp.get("threshold", 0.045))
        st.markdown(
            f"""
        <div class="detector-card" style="border-left: 3px solid {'#f87171' if temp_anom else '#34d399'};">
            <div style="font-size: 8.5px; color: #64748b; font-family: monospace;">DETECTOR 4 / DEEP LEARNING</div>
            <div class="det-title">LSTM AUTOENCODER</div>
            <div style="margin: 6px 0;"><span class="badge {'badge-critical' if temp_anom else 'badge-normal'}">{'ANOMALY' if temp_anom else 'NOMINAL'}</span></div>
            <div class="det-score">RECON ERROR: {recon_err:.5f}</div>
            <div class="det-score">P99 THRESHOLD: {temp_thresh:.5f}</div>
            <div class="det-model">MODEL: lstm-temporal-v1.0</div>
            <div style="font-size: 9px; color: #94a3b8; margin-top: 6px; line-height: 1.3;">
                Reconstructs kinematic trajectories across W=10 epoch sliding window.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='border-color: #1e293b; margin: 14px 0 10px 0;'>", unsafe_allow_html=True)

    # Detailed Forensic Breakdown Expanders
    trig_rules = pr.get("triggered_rules", [])
    if trig_rules and isinstance(trig_rules, list):
        st.markdown("<div class='soc-panel-title'>TRIGGERED PHYSICAL INVARIANT RULES</div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(trig_rules), use_container_width=True, hide_index=True)
    else:
        st.markdown(
            "<div class='soc-panel' style='font-size: 11px; color: #34d399; font-family: monospace;'>"
            "ALL 9 PHYSICAL INVARIANT RULES SATISFIED — ZERO DETERMINISTIC KINEMATIC BREACHES DETECTED"
            "</div>",
            unsafe_allow_html=True,
        )

    feat_attr = temp.get("feature_attribution")
    if feat_attr and isinstance(feat_attr, dict):
        with st.expander("LSTM Autoencoder — Feature Attribution Sensitivity Matrix", expanded=False):
            attr_df = pd.DataFrame([{"Feature": k, "Attribution Magnitude": v} for k, v in feat_attr.items()])
            st.dataframe(attr_df, use_container_width=True, hide_index=True)
