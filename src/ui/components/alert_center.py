"""
LOCUS Alert Center & Security Incident Manager
Module: src.ui.components.alert_center
"""

import streamlit as st
import pandas as pd


def render_alert_center(alerts: list, on_select_event=None):
    """
    Render filterable alert center and incident queue.
    """
    st.subheader("🚨 Security Alert Center & Incident Queue")
    st.caption("Central Incident Dispatch • Correlated Multi-Detector Alarms • High-Priority Incident Management")

    if not alerts:
        st.success("✅ Clean security queue: No anomalies or threat incidents flagged.")
        return None

    # Severity filters
    f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
    with f_col1:
        sev_filter = st.multiselect(
            "Filter Severity:",
            options=["CRITICAL", "HIGH", "WARNING", "INFO"],
            default=["CRITICAL", "HIGH", "WARNING"]
        )
    with f_col2:
        search_kw = st.text_input("Filter by Event or Feature:", "")

    filtered = [a for a in alerts if a["severity"] in sev_filter]
    if search_kw:
        kw = search_kw.lower()
        filtered = [
            a for a in filtered
            if kw in a["alert_id"].lower()
            or kw in a["event_type"].lower()
            or any(kw in f.lower() for f in a.get("affected_features", []))
        ]

    st.write(f"Displaying **{len(filtered)}** of **{len(alerts)}** total incidents:")

    # Summary table
    table_data = []
    for a in filtered:
        loc = a.get("location", {})
        coords = f"{loc.get('latitude', 0.0):.4f}, {loc.get('longitude', 0.0):.4f}" if loc.get("latitude") else "N/A"
        table_data.append({
            "Alert ID": a["alert_id"],
            "Severity": a["severity"],
            "Event Type": a["event_type"],
            "Timestamp UTC": a["timestamp"],
            "Score": f"{a['anomaly_score']:.4f}",
            "Affected Features": ", ".join(a.get("affected_features", []))[:30],
            "Location": coords,
            "Status": a["status"]
        })

    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    # Interactive selector for alert details drill-down
    st.markdown("---")
    st.markdown("##### 🔍 Drill-Down into Incident Evidence")
    alert_ids = [a["alert_id"] for a in filtered]
    if alert_ids:
        selected_alert_id = st.selectbox(
            "Select Alert to Inspect Evidence Bundle:",
            options=alert_ids,
            index=0
        )
        selected_event_id = selected_alert_id.replace("ALT-", "")
        return selected_event_id

    return None
