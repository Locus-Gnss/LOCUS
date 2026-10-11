"""
Module 4: 10-D Security Vectors
Module: src.ui.pages.p03_gnss_features
Monitors the official 10-D canonical feature vector across kinematic, geometric, and constellation axes.
"""

from typing import Dict, Any, List
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.utils.formatting import safe_float, safe_int, safe_str


def render_gnss_features_page(data_service, selected_event_id: str):
    """
    Render 10-D Security Features module matching Screenshot 4 specification.
    """
    st.markdown("<div class='section-header'>10-DIMENSIONAL CYBERSECURITY FEATURE MONITOR</div>", unsafe_allow_html=True)
    st.markdown(
        """
    <div class="soc-callout">
        <strong>FEATURE VECTOR ARCHITECTURE:</strong> Canonical 10-dimensional space spanning physical invariants,
        satellite constellation geometry, and RF health.
        <strong>NOTE:</strong> <code>sat_churn</code> represents true constellation PRN identity turnover,
        measuring Jaccard set distance of visible Space Vehicle IDs rather than net satellite count difference.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 1. Load active event bundle
    bundle = data_service.load_event(selected_event_id)
    features = data_service.get_canonical_10d_features(bundle=bundle)

    if not features:
        st.info("NO FEATURE DATA AVAILABLE FOR ACTIVE EVENT")
        return

    # Categorization map
    cat_map = {
        "disp_haversine": "KINEMATICS",
        "vel_kinematic": "KINEMATICS",
        "acc_kinematic": "KINEMATICS",
        "jerk_kinematic": "KINEMATICS",
        "bearing_rate": "KINEMATICS",
        "HDOP": "GEOMETRY",
        "VDOP": "GEOMETRY",
        "fix_integrity": "INTEGRITY",
        "sat_count_tot": "CONSTELLATION",
        "sat_churn": "CONSTELLATION"
    }

    desc_map = {
        "disp_haversine": "Great-circle geodesic displacement between consecutive epochs.",
        "vel_kinematic": "Instantaneous velocity derived from differential position over delta-T.",
        "acc_kinematic": "Second kinematic derivative; flags non-physical inertial spikes.",
        "jerk_kinematic": "Rate of acceleration change; sensitive to spoofed step-jumps.",
        "bearing_rate": "Angular velocity of heading changes within vehicle turning envelope.",
        "HDOP": "Horizontal Dilution of Precision; geometric constellation dispersion.",
        "VDOP": "Vertical Dilution of Precision; vertical axis geometry dilution.",
        "fix_integrity": "Weighted composite score evaluating carrier-to-noise ratio and lock.",
        "sat_count_tot": "Total count of tracked space vehicles contributing to navigation solution.",
        "sat_churn": "PRN identity turnover ratio; Jaccard set distance of tracked SV set."
    }

    # Render 10 Cards in 2 rows of 5
    row_1 = features[:5]
    row_2 = features[5:]

    def _render_feature_box(feat):
        status = feat.get("status", "NORMAL")
        key = feat.get("feature", "")
        category = cat_map.get(key, "SECURITY")
        desc = desc_map.get(key, "")
        val = safe_float(feat.get("value", 0.0))
        warn = safe_float(feat.get("warning_limit", 0.0))
        crit = safe_float(feat.get("critical_limit", 1.0))
        unit = feat.get("unit", "")

        color_map = {"CRITICAL": "#f87171", "WARNING": "#fbbf24", "NORMAL": "#34d399"}
        val_color = color_map.get(status, "#34d399")
        badge_cls = {"CRITICAL": "badge-critical", "WARNING": "badge-warning", "NORMAL": "badge-normal"}.get(status, "badge-normal")

        # Threshold progress calculation
        max_bound = max(crit * 1.25, val * 1.1, 1.0)
        pct = min(max(val / max_bound, 0.0), 1.0) * 100

        return f"""
        <div class="feature-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                <span style="font-size: 8.5px; font-weight: 700; color: #64748b; font-family: monospace;">{category}</span>
                <span class="badge {badge_cls}" style="font-size: 8px; padding: 1px 4px;">{status}</span>
            </div>
            <div style="font-size: 11px; font-weight: 700; color: #f8fafc; font-family: monospace;">{key}</div>
            <div style="font-size: 10px; color: #94a3b8; margin-bottom: 6px;">{feat.get('name', '')}</div>
            <div style="font-size: 17px; font-weight: 800; color: {val_color}; font-family: monospace;">
                {val:.4f} <span style="font-size: 10px; color: #64748b;">{unit}</span>
            </div>
            <div style="background: #1e293b; height: 3px; border-radius: 2px; margin: 6px 0;">
                <div style="background: {val_color}; width: {pct:.1f}%; height: 100%; border-radius: 2px;"></div>
            </div>
            <div style="font-size: 8.5px; color: #64748b; font-family: monospace;">
                WARN: {warn} &nbsp;|&nbsp; CRIT: {crit}
            </div>
            <div style="font-size: 9px; color: #475569; margin-top: 5px; line-height: 1.2;">
                {desc}
            </div>
        </div>
        """

    cols_a = st.columns(5)
    for idx, f in enumerate(row_1):
        with cols_a[idx]:
            st.markdown(_render_feature_box(f), unsafe_allow_html=True)

    cols_b = st.columns(5)
    for idx, f in enumerate(row_2):
        with cols_b[idx]:
            st.markdown(_render_feature_box(f), unsafe_allow_html=True)

    st.markdown("<hr style='border-color: #1e293b; margin: 16px 0 10px 0;'>", unsafe_allow_html=True)

    # Feature Magnitude Bar Chart
    st.markdown("<div class='soc-panel-title'>CANONICAL FEATURE VECTOR MAGNITUDE DISTRIBUTION</div>", unsafe_allow_html=True)

    names = [r["feature"] for r in features]
    vals = [r["value"] for r in features]
    statuses = [r["status"] for r in features]
    colors = ["#ef4444" if s == "CRITICAL" else ("#fbbf24" if s == "WARNING" else "#10b981") for s in statuses]

    fig = go.Figure(go.Bar(
        x=names,
        y=vals,
        marker={"color": colors},
        hovertext=[f"{r['name']}: {r['value']:.4f} {r['unit']} [{r['status']}]" for r in features],
        hoverinfo="text"
    ))
    fig.update_layout(
        paper_bgcolor="#090e18",
        plot_bgcolor="#090e18",
        font={"color": "#94a3b8", "family": "'SF Mono', Monaco, monospace"},
        margin={"l": 40, "r": 20, "t": 20, "b": 35},
        xaxis={"gridcolor": "#1e293b", "tickangle": -25},
        yaxis={"gridcolor": "#1e293b"},
        height=260
    )
    st.plotly_chart(fig, use_container_width=True)
