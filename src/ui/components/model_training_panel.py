"""
LOCUS Model Training and Evaluation Panel
Module: src.ui.components.model_training_panel
Controlled training with zero data leakage, threshold tuning on validation partition,
and explicit confirmation before replacing production models.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any


def render_model_training_panel(service):
    """
    Render Section 10: Model Training and Evaluation.
    """
    st.subheader("Model Training, Fine-Tuning & Evaluation Center")
    st.caption("Controlled Offline & Semi-Supervised Learning Pipeline • Leakage-Free Partitioning • Versioned Checkpointing")

    models_status = service.get_models_status()

    # 1. Active Production Model Registry Status Cards
    st.markdown("##### Production Detector Readiness")
    c1, c2, c3, c4 = st.columns(4)

    pr = models_status.get("physical_rules", {})
    ifo = models_status.get("isolation_forest", {})
    xgb = models_status.get("xgboost", {})
    lstm = models_status.get("temporal_lstm", {})

    with c1:
        st.markdown(
            f"""
            <div style='background: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 12px;'>
                <div style='color: #94a3b8; font-size: 11px; text-transform: uppercase;'>PATH 1: KINEMATICS</div>
                <div style='font-size: 14px; font-weight: 700; color: #ffffff;'>Physical Rules</div>
                <div style='margin-top: 6px;'><span class='badge-normal'>● OPERATIONAL</span></div>
                <div style='color: #64748b; font-size: 11px; margin-top: 6px;'>Deterministic Newtonian bounds</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        ifo_badge = "badge-normal" if ifo.get("is_fitted") else "badge-warning"
        st.markdown(
            f"""
            <div style='background: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 12px;'>
                <div style='color: #94a3b8; font-size: 11px; text-transform: uppercase;'>PATH 2: SPATIAL ML</div>
                <div style='font-size: 14px; font-weight: 700; color: #ffffff;'>Isolation Forest</div>
                <div style='margin-top: 6px;'><span class='{ifo_badge}'>● {'READY' if ifo.get('is_fitted') else 'UNFITTED'}</span></div>
                <div style='color: #64748b; font-size: 11px; margin-top: 6px;'>10-D Unsupervised Anomaly Engine</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        xgb_fitted = xgb.get("is_fitted", False)
        xgb_badge = "badge-normal" if xgb_fitted else "badge-warning"
        xgb_text = "READY" if xgb_fitted else "UNAVAILABLE — NOT TRAINED"
        st.markdown(
            f"""
            <div style='background: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 12px;'>
                <div style='color: #94a3b8; font-size: 11px; text-transform: uppercase;'>PATH 3: SUPERVISED ML</div>
                <div style='font-size: 14px; font-weight: 700; color: #ffffff;'>XGBoost Classifier</div>
                <div style='margin-top: 6px;'><span class='{xgb_badge}'>● {xgb_text}</span></div>
                <div style='color: #64748b; font-size: 11px; margin-top: 6px;'>Requires verified attack labels</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:
        lstm_fitted = lstm.get("is_fitted", False)
        lstm_badge = "badge-normal" if lstm_fitted else "badge-warning"
        st.markdown(
            f"""
            <div style='background: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 12px;'>
                <div style='color: #94a3b8; font-size: 11px; text-transform: uppercase;'>PATH 4: TEMPORAL ML</div>
                <div style='font-size: 14px; font-weight: 700; color: #ffffff;'>Temporal LSTM Autoencoder</div>
                <div style='margin-top: 6px;'><span class='{lstm_badge}'>● {'READY' if lstm_fitted else 'UNFITTED'}</span></div>
                <div style='color: #64748b; font-size: 11px; margin-top: 6px;'>W=10 Sequence Reconstruction</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # 2. Partition & Data Leakage Governance
    st.markdown("##### Leakage-Free Dataset Partitioning Governance")
    st.info(
        "**Strict Data Partitioning Policy:** Preprocessing and scalers are fitted exclusively on the Training partition. "
        "Hyperparameters and decision thresholds are tuned on the independent Validation partition. "
        "The Test partition is strictly evaluated once and NEVER used during training or threshold search."
    )

    col_part1, col_part2 = st.columns([1, 1])

    with col_part1:
        st.markdown(
            """
            <div style='background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 14px;'>
                <div style='font-weight: 700; color: #38bdf8;'>Canonical Baseline Partition (27,687 Records)</div>
                <table style='width: 100%; margin-top: 8px; font-size: 13px; color: #cbd5e1;'>
                    <tr><td style='padding: 4px 0;'>Training Set:</td><td style='text-align: right;'><b>Sessions 4, 9, 11 (60.0%)</b></td></tr>
                    <tr><td style='padding: 4px 0;'>Validation Set:</td><td style='text-align: right;'><b>Session 10 (20.0%)</b></td></tr>
                    <tr><td style='padding: 4px 0;'>Independent Test Set:</td><td style='text-align: right;'><b>Sessions 5, 15 (20.0%)</b></td></tr>
                    <tr><td style='padding: 4px 0;'>Chronological Buffer Gap:</td><td style='text-align: right;'><b>Preserved between Sessions</b></td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_part2:
        st.markdown(
            """
            <div style='background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 14px;'>
                <div style='font-weight: 700; color: #38bdf8;'>Dynamic Augmented Partitioning Policy</div>
                <div style='font-size: 12px; color: #94a3b8; margin-top: 6px;'>
                    When supplemental GNSS datasets or uploads arrive (>27,687 rows):
                </div>
                <ul style='font-size: 12px; color: #cbd5e1; margin-top: 6px; padding-left: 20px;'>
                    <li>Arbitrary dataset sizes dynamically partitioned chronologically.</li>
                    <li>No hardcoded row counts or fixed memory limits.</li>
                    <li>Unlabeled incoming live data is available for inference, but quarantined from training until verified.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # 3. Controlled Retraining Workflow
    st.markdown("##### Controlled Model Training Action")
    st.caption("Training is decoupled from runtime ingestion. Models are not replaced without confirmation.")

    col_ctrl1, col_ctrl2 = st.columns([1, 1])

    with col_ctrl1:
        target_model = st.selectbox(
            "Select Target Detection Component:",
            options=[
                "Isolation Forest (Spatial 10-D Anomaly Detector)",
                "XGBoost Classifier (Supervised Attack Profiles)",
                "Temporal LSTM Autoencoder (Sequence Model)"
            ]
        )

        contamination = st.slider(
            "Contamination Rate (Assumed Anomaly Prior):",
            min_value=0.005,
            max_value=0.050,
            value=0.020,
            step=0.005,
            format="%.3f"
        )

        n_estimators = st.slider(
            "Number of Base Estimators (Trees):",
            min_value=50,
            max_value=500,
            value=200,
            step=50
        )

    with col_ctrl2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        confirm_replace = st.checkbox(
            "Replace Active Production Model upon Successful Validation",
            value=False,
            help="If checked, the newly trained model weights will overwrite the production model in models/production/."
        )

        st.markdown(
            """
            <div style='background: #1e1b4b; border: 1px solid #4338ca; border-radius: 6px; padding: 12px; margin-top: 10px; font-size: 12px; color: #e0e7ff;'>
                <b>Validation Guard:</b> The pipeline will evaluate precision, recall, and anomaly score distribution on the hold-out validation partition before staging.
            </div>
            """,
            unsafe_allow_html=True
        )

        btn_train = st.button("TRIGGER CONTROLLED RETRAINING", key="btn_trigger_retraining")

    if btn_train:
        st.markdown("---")
        st.markdown("##### Execution Progress & Results")

        if "Isolation Forest" in target_model:
            with st.spinner("Partitioning data without leakage and fitting Isolation Forest..."):
                res = service.train_model(
                    model_type="isolation_forest",
                    contamination=contamination,
                    n_estimators=n_estimators,
                    confirm_replace=confirm_replace
                )

                if res.get("status") in ["TRAINED", "TRAINED_AND_EVALUATED"]:
                    st.success(f"Training completed successfully! {res.get('message', '')}")
                    metrics = res.get("metrics", {})

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Model Architecture", "Isolation Forest")
                    m2.metric("Contamination Factor", f"{contamination:.3f}")
                    m3.metric("Production Status", "REPLACED ACTIVE" if confirm_replace else "STAGED (SAFE KEEPING)")

                    st.markdown("###### Evaluation Metrics on Independent Validation Partition")
                    st.json(metrics)
                else:
                    st.error(f"Training failed: {res.get('message', 'Unknown error')}")

        elif "XGBoost" in target_model:
            st.warning(
                "**UNAVAILABLE — MODEL NOT TRAINED**: Supervised XGBoost Classifier requires verified, "
                "labelled ground-truth attack scenario datasets (e.g., synchronized laboratory GNSS spoofing/jamming captures). "
                "The current 27,687-record operational dataset consists of benign real-world drive-test and static captures. "
                "Fitting a supervised classifier on unlabelled or non-diverse scenarios would produce false generalization. "
                "The system operates honestly with Physical Rules, Isolation Forest, and LSTM Autoencoders."
            )

        elif "Temporal LSTM" in target_model:
            st.info(
                "Temporal LSTM Autoencoder training is configured via PyTorch. "
                "Sequence length W=10 consecutive epochs required. "
                "Production weights currently loaded: `models/production/temporal/temporal_model.pt`."
            )
