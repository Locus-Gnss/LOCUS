"""
LOCUS Detection & Machine Learning Quad Panel
Module: src.ui.components.detection_panel
"""

import streamlit as st


def render_detection_panel(bundle_dict: dict, final_verdict: dict = None):
    """
    Render outputs of the 4-detector quad:
    1. RULE: Physical Rules Engine
    2. UNSUPERVISED ML: Isolation Forest
    3. SUPERVISED ML: XGBoost Classifier
    4. TEMPORAL MODEL: LSTM Sequence Autoencoder
    5. FINAL DECISION: Master SOC Deliberation
    """
    st.subheader("🛡️ Multi-Detector Quad & Machine Learning Anomaly Detection")
    st.caption("Decoupled Inference Architecture • Invariant Physics + Spatial + Supervised + Sequence Models")

    pr = bundle_dict.get("physical_rules", {})
    ifo = bundle_dict.get("isolation_forest", {})
    xgb = bundle_dict.get("xgboost", {})
    temp = bundle_dict.get("temporal_model", {})

    # Top row: 4 Detectors
    c1, c2 = st.columns(2)

    with c1:
        # 1. RULE ENGINE
        st.markdown(
            """
            <div class='agent-container' style='border-left: 4px solid #10b981;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-weight: 700; font-size: 15px;'>PATH 1: PHYSICAL RULES ENGINE</span>
                    <span class='provenance-tag'>RULE-BASED</span>
                </div>
                <div style='color: #94a3b8; font-size: 12px; margin-top: 4px;'>
                    Zero-shot Newtonian Kinematic Invariants & Geometry Degradation Rules
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        pr_status = pr.get("status", "NOMINAL")
        pr_trig = pr.get("triggered_count", 0)
        badge = "badge-normal" if pr_status == "NOMINAL" else "badge-critical"
        st.markdown(f"**Engine Status**: <span class='{badge}'>{pr_status}</span> ({pr_trig} violations)", unsafe_allow_html=True)
        st.write(f"**Max Rule Severity**: `{pr.get('max_severity', 'INFO')}`")
        if pr.get("triggered_rules"):
            st.json(pr["triggered_rules"])
        else:
            st.success("✅ Zero physical kinematic invariants violated (Mach 1, 4g acceleration, jump bounds nominal).")

        # 3. SUPERVISED ML (XGBoost)
        st.markdown(
            """
            <div class='agent-container' style='border-left: 4px solid #f59e0b; margin-top: 20px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-weight: 700; font-size: 15px;'>PATH 3: SUPERVISED XGBOOST CLASSIFIER</span>
                    <span class='provenance-tag'>SUPERVISED ML</span>
                </div>
                <div style='color: #94a3b8; font-size: 12px; margin-top: 4px;'>
                    Gradient-Boosted Decision Trees trained on Spoofing, Jamming, and Multipath Profiles
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write(f"**Infrastructure Status**: `{xgb.get('status', 'AUDITED_v1.1')}`")
        st.write(f"**Attack Classification**: `{xgb.get('predicted_label', 'UNFITTED_BASELINE')}`")
        st.write(f"**Confidence**: `{xgb.get('confidence', 1.0)*100:.1f}%`")
        if xgb.get("class_probabilities"):
            st.write("**Attack Probabilities:**", xgb["class_probabilities"])

    with c2:
        # 2. UNSUPERVISED ML (Isolation Forest)
        st.markdown(
            """
            <div class='agent-container' style='border-left: 4px solid #38bdf8;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-weight: 700; font-size: 15px;'>PATH 2: ISOLATION FOREST</span>
                    <span class='provenance-tag'>UNSUPERVISED ML</span>
                </div>
                <div style='color: #94a3b8; font-size: 12px; margin-top: 4px;'>
                    10-D Spatial Out-of-Distribution Detector (Calibrated Contamination=0.01)
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        ifo_anom = ifo.get("is_anomaly", False)
        score = ifo.get("anomaly_score", 0.0)
        ifo_badge = "badge-critical" if ifo_anom else "badge-normal"
        st.markdown(f"**Spatial Classification**: <span class='{ifo_badge}'>{'ANOMALY' if ifo_anom else 'NOMINAL'}</span>", unsafe_allow_html=True)
        st.write(f"**Anomaly Score**: `{score:.4f}` (Decision boundary: 0.5000)")
        st.progress(min(max(float(score), 0.0), 1.0))

        # 4. TEMPORAL MODEL (LSTM Autoencoder)
        st.markdown(
            """
            <div class='agent-container' style='border-left: 4px solid #a855f7; margin-top: 20px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-weight: 700; font-size: 15px;'>PATH 4: TEMPORAL LSTM AUTOENCODER</span>
                    <span class='provenance-tag'>TEMPORAL MODEL</span>
                </div>
                <div style='color: #94a3b8; font-size: 12px; margin-top: 4px;'>
                    Sliding Sequence Window (W=10 epochs) Reconstruction Error Engine
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        temp_anom = temp.get("is_anomaly", False)
        recon_err = temp.get("reconstruction_error", 0.0)
        thresh = temp.get("error_threshold")
        temp_badge = "badge-critical" if temp_anom else "badge-normal"
        st.markdown(f"**Temporal Status**: <span class='{temp_badge}'>{'ANOMALY' if temp_anom else 'NOMINAL'}</span>", unsafe_allow_html=True)
        st.write(f"**Reconstruction Error**: `{recon_err:.4f}`")
        if thresh:
            st.write(f"**Baseline Limit**: `{thresh:.4f}`")
        if temp.get("feature_attribution"):
            st.write("**Top Drift Contributors:**", temp.get("feature_attribution"))

    # Bottom Banner: 5. FINAL DECISION
    st.markdown("---")
    st.markdown("##### 5. FINAL DECISION — AGENTIC CONSENSUS SYNTHESIS")
    if final_verdict:
        v_status = final_verdict.get("status", "NOMINAL")
        v_risk = final_verdict.get("risk_level", "DEFCON_5")
        v_conf = final_verdict.get("confidence", 1.0)
        v_badge = "badge-critical" if "CRITICAL" in v_status or "1" in v_risk else ("badge-warning" if "WARNING" in v_status or "3" in v_risk else "badge-normal")
        st.markdown(
            f"""
            <div style='background: #1e293b; border: 1px solid #475569; border-radius: 8px; padding: 14px; display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <span style='font-size: 18px; font-weight: 800; color: #ffffff;'>Consensus Status: </span>
                    <span class='{v_badge}' style='font-size: 16px;'>{v_status} ({v_risk})</span>
                </div>
                <div style='font-family: monospace; font-size: 15px; color: #38bdf8;'>
                    Confidence: {v_conf*100:.1f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write(f"**Forensic Consensus Summary**: {final_verdict.get('summary', 'No summary.')}")
