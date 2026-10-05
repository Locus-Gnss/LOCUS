"""
LOCUS Canonical 10-D Security Feature Vector Monitor
Module: src.ui.components.features_panel
"""

import streamlit as st
import pandas as pd
import numpy as np


def render_features_panel(features_list: list, df_features: pd.DataFrame = None):
    """
    Render canonical 10-D feature vector with units, calibrated limits, status chips,
    and historical mini-trends.
    """
    st.subheader("Official 10-Dimensional Security Feature Vector")
    st.caption("Standardized Schema: `locus-sec-v2.0-10d` • Physics, Navigation Quality & Satellite Constellation Dynamics")

    # Render Metric Cards in two rows of 5
    row1 = features_list[:5]
    row2 = features_list[5:]

    st.markdown("##### Kinematic & Physical Invariants")
    cols1 = st.columns(5)
    for col, feat in zip(cols1, row1):
        with col:
            status = feat["status"]
            val_str = f"{feat['value']:.3f}" if isinstance(feat['value'], float) else str(feat['value'])
            badge_class = "badge-normal" if status == "NORMAL" else ("badge-warning" if status == "WARNING" else "badge-critical")
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-title'>{feat['feature']}</div>
                <div class='kpi-value'>{val_str} <span style='font-size: 13px; color: #94a3b8;'>{feat['unit']}</span></div>
                <div style='margin-top: 6px;'><span class='{badge_class}'>{status}</span></div>
                <div class='kpi-sub'>Limit: &lt; {feat['warning_limit']} {feat['unit']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("##### Navigation Quality & Constellation State")
    cols2 = st.columns(5)
    for col, feat in zip(cols2, row2):
        with col:
            status = feat["status"]
            val_str = f"{feat['value']:.2f}" if isinstance(feat['value'], float) else str(feat['value'])
            badge_class = "badge-normal" if status == "NORMAL" else ("badge-warning" if status == "WARNING" else "badge-critical")
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-title'>{feat['feature']}</div>
                <div class='kpi-value'>{val_str} <span style='font-size: 13px; color: #94a3b8;'>{feat['unit']}</span></div>
                <div style='margin-top: 6px;'><span class='{badge_class}'>{status}</span></div>
                <div class='kpi-sub'>Warn: {feat['warning_limit']} | Crit: {feat['critical_limit']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Feature Evaluation Matrix (Calibrated against `configs/model_training.yaml`)")

    # Table format
    table_rows = []
    for f in features_list:
        table_rows.append({
            "Feature (Canonical)": f["feature"],
            "Description": f["name"],
            "Observed Value": f"{f['value']:.4f}" if isinstance(f['value'], float) else f["value"],
            "Unit": f["unit"],
            "Warning Bound": f["warning_limit"],
            "Critical Bound": f["critical_limit"],
            "Security Status": f["status"]
        })

    df_table = pd.DataFrame(table_rows)
    st.dataframe(df_table, use_container_width=True, hide_index=True)

    # Historical trends if df_features is available
    if df_features is not None and not df_features.empty:
        with st.expander("View 10-D Feature Historical Sequences"):
            feat_select = st.selectbox(
                "Select Feature for Sequence Inspection:",
                options=[f["feature"] for f in features_list],
                index=0
            )
            if feat_select in df_features.columns:
                st.line_chart(df_features[feat_select].tail(200))
