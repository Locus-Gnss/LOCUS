"""
Module 6: Alert Center
Module: src.ui.pages.p06_alerts
Real-time security incident monitoring, threat severity classification, and incident triage.
"""

from typing import Dict, Any, List
import pandas as pd
import streamlit as st

from src.ui.utils.state import set_selected_event
from src.ui.utils.formatting import safe_float, safe_int, safe_str


def render_alerts_page(data_service, selected_event_id: str):
    """
    Render Alert Center module matching Screenshot 6 specification.
    """
    st.markdown("<div class='section-header'>ACTIVE SECURITY INCIDENTS &amp; ALERT CENTER</div>", unsafe_allow_html=True)
    st.markdown(
        """
    <div class="soc-callout">
        <strong>INCIDENT STREAM:</strong> Prioritized alert queue triaged by the Phase 5 Evidence Fusion Engine.
        Severity assigned by highest detector confidence (Critical &gt; High &gt; Warning &gt; Info).
    </div>
    """,
        unsafe_allow_html=True,
    )

    alerts = data_service.get_alert_center_records()
    if not alerts:
        st.info("NO ACTIVE SECURITY ALERTS RECORDED")
        return

    # Metrics summary
    total_alerts = len(alerts)
    crit_count = len([a for a in alerts if a.get("severity") == "CRITICAL"])
    warn_count = len([a for a in alerts if a.get("severity") in ["HIGH", "WARNING"]])
    info_count = total_alerts - crit_count - warn_count

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("TOTAL INCIDENTS", str(total_alerts))
    with c2:
        st.markdown(
            f"""
        <div class="kpi-card" style="padding: 10px;">
            <div class="kpi-label">CRITICAL BREACHES</div>
            <div class="kpi-val" style="color: #ef4444;">{crit_count}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
        <div class="kpi-card" style="padding: 10px;">
            <div class="kpi-label">WARNINGS / ELEVATED</div>
            <div class="kpi-val" style="color: #fbbf24;">{warn_count}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
        <div class="kpi-card" style="padding: 10px;">
            <div class="kpi-label">MONITORED / INFO</div>
            <div class="kpi-val" style="color: #38bdf8;">{info_count}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='border-color: #1e293b; margin: 14px 0;'>", unsafe_allow_html=True)

    # Filter selector
    f_col1, f_col2 = st.columns([2, 4])
    with f_col1:
        sev_filter = st.selectbox("Filter by Severity:", options=["ALL", "CRITICAL", "HIGH", "WARNING", "INFO"], key="alert_sev_filter")

    filtered_alerts = alerts
    if sev_filter != "ALL":
        filtered_alerts = [a for a in alerts if a.get("severity") == sev_filter]

    # Render Table & Interactive Focus Selector
    st.markdown("<div class='soc-panel-title'>TRIAGED ALERT LOGS</div>", unsafe_allow_html=True)

    table_rows = []
    for a in filtered_alerts:
        eid = a.get("event_id", "")
        sev = a.get("severity", "INFO")
        score = safe_float(a.get("anomaly_score", 0.0))
        conf = 0.95 if sev in ["CRITICAL", "HIGH"] else (0.85 if sev == "WARNING" else 0.70)
        affected = ", ".join(a.get("affected_features", [])) or "nominal"

        table_rows.append({
            "Alert ID": a.get("alert_id", "ALT"),
            "Event ID": eid,
            "Severity": sev,
            "Threat Type": a.get("event_type", "INCIDENT"),
            "Timestamp": safe_str(a.get("timestamp", "N/A")),
            "Status": safe_str(a.get("status", "UNRESOLVED")),
            "Confidence": f"{conf*100:.1f}%",
            "Reason": affected
        })

    df_alerts = pd.DataFrame(table_rows)
    st.dataframe(df_alerts, use_container_width=True, hide_index=True)

    # Focus selection
    st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
    sel_eid = st.selectbox(
        "Select Incident to Focus Active SOC Investigation:",
        options=[a["event_id"] for a in filtered_alerts[:30]],
        index=0 if filtered_alerts else 0,
        key="alert_focus_selector"
    )
    if st.button("SET AS ACTIVE FORENSIC TARGET", key="btn_alert_set_focus"):
        set_selected_event(sel_eid)
        st.success(f"Forensic target set to {sel_eid}. All SOC modules updated.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
