"""
Page 4: Threat Events
Module: src.ui.pages.p04_threat_events
Forensic event investigation interface. Enumerates actual events from the backend/evidence repository.
Permits selecting active forensic event and synchronizes state across Evidence and SOC Deliberation.
Strictly no emojis.
"""

from typing import Dict, Any, List
import pandas as pd
import streamlit as st

from src.ui.utils.state import get_selected_event, set_selected_event
from src.ui.utils.formatting import safe_float, safe_int, safe_str


def render_threat_events_page(data_service):
    """
    Render Threat Events Investigation Page.
    """
    st.markdown("<div class='section-header'>THREAT EVENT FORENSIC INVESTIGATION</div>", unsafe_allow_html=True)

    # 1. Retrieve Events from Backend
    events = data_service.get_events()
    if not events:
        st.info("NO DATA AVAILABLE FOR THREAT EVENTS")
        return

    # 2. Enrich Events List with Alert Metadata (Fast bulk lookup without 31 HTTP calls)
    alerts = data_service.get_alert_center_records()
    alert_map = {a.get("event_id"): a for a in alerts if isinstance(a, dict)}

    event_rows = []
    for ev in events:
        eid = ev.get("event_id", "unknown")
        alt = alert_map.get(eid)
        if alt:
            sev = alt.get("severity", "INFO")
            classification = alt.get("event_type", "NOMINAL_FLIGHT")
            confidence = 0.95 if sev in ["CRITICAL", "HIGH"] else (0.85 if sev == "WARNING" else 0.70)
            status = alt.get("status", "MONITORED")
            ts = alt.get("timestamp") or ev.get("timestamp_utc") or "N/A"
        else:
            sev = "INFO"
            classification = "NOMINAL_FLIGHT"
            confidence = 0.50
            status = "MONITORED"
            ts = ev.get("timestamp_utc") or "N/A"

        event_rows.append({
            "event_id": eid,
            "timestamp": safe_str(ts),
            "classification": safe_str(classification),
            "severity": safe_str(sev),
            "confidence": f"{confidence * 100:.1f}%",
            "status": safe_str(status)
        })

    df_events = pd.DataFrame(event_rows)

    # Filter controls
    col_f1, col_f2 = st.columns([2, 2])
    with col_f1:
        sev_filter = st.multiselect(
            "Filter by Severity:",
            options=["CRITICAL", "HIGH", "WARNING", "INFO"],
            default=["CRITICAL", "HIGH", "WARNING", "INFO"],
            key="ev_sev_filter"
        )
    with col_f2:
        search_query = st.text_input("Search Event ID or Classification:", "", key="ev_search_input")

    filtered_df = df_events[df_events["severity"].isin(sev_filter)]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["event_id"].str.contains(search_query, case=False, na=False) |
            filtered_df["classification"].str.contains(search_query, case=False, na=False)
        ]

    st.markdown("<div class='soc-panel-title'>AVAILABLE FORENSIC EVENTS</div>", unsafe_allow_html=True)
    st.dataframe(filtered_df, width="stretch", hide_index=True)

    # 3. Active Event Selection with Safe Synchronized State
    current_selected = get_selected_event()
    available_ids = filtered_df["event_id"].tolist() if not filtered_df.empty else df_events["event_id"].tolist()

    if "ev_deep_select" not in st.session_state:
        st.session_state["ev_deep_select"] = current_selected if current_selected in available_ids else (available_ids[0] if available_ids else "")
    elif st.session_state["ev_deep_select"] not in available_ids and available_ids:
        st.session_state["ev_deep_select"] = available_ids[0]

    st.markdown("<hr style='border-color: #1e293b; margin: 16px 0;'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>EVENT FORENSIC DETAILS</div>", unsafe_allow_html=True)

    def on_threat_event_pick():
        picked = st.session_state.get("ev_deep_select")
        if picked:
            set_selected_event(picked)

    sel_col1, sel_col2 = st.columns([3, 1])
    with sel_col1:
        chosen_event = st.selectbox(
            "Select Event for Deep Inspection:",
            options=available_ids,
            key="ev_deep_select",
            on_change=on_threat_event_pick
        )
    with sel_col2:
        if st.button("Set as Active SOC Target", key="btn_set_active_event"):
            set_selected_event(chosen_event)
            st.success(f"Active event updated to {chosen_event}")

    # Display Detailed Event Info
    bundle = data_service.load_event(chosen_event)
    if not bundle:
        st.warning(f"Forensic bundle for event '{chosen_event}' not found.")
        return

    det_c1, det_c2, det_c3, det_c4 = st.columns(4)
    with det_c1:
        st.metric("EVENT ID", safe_str(bundle.event_id))
    with det_c2:
        st.metric("TIMESTAMP UTC", safe_str(bundle.timestamp_utc))
    with det_c3:
        st.metric("SESSION / EPOCH", f"SES-{safe_int(bundle.session_id)} / EP-{safe_int(bundle.epoch_id)}")
    with det_c4:
        sha = safe_str(getattr(bundle, "evidence_sha256", "UNHASHED"), default="UNHASHED")
        st.metric("EVIDENCE HASH", f"{sha[:10]}..." if len(sha) > 10 else sha)

    # Multi-Detector Quad Findings Breakdown
    st.markdown("<div class='soc-panel-title'>MULTI-DETECTOR QUAD EVIDENCE SUMMARY</div>", unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)

    pr = bundle.physical_rules if isinstance(bundle.physical_rules, dict) else {}
    ifo = bundle.isolation_forest if isinstance(bundle.isolation_forest, dict) else {}
    xgb = bundle.xgboost if isinstance(bundle.xgboost, dict) else {}
    temp = bundle.temporal_model if isinstance(bundle.temporal_model, dict) else {}

    with q1:
        st.markdown(
            f"""
        <div class="soc-panel">
            <div style="font-weight: 700; color: #38bdf8; font-size: 11px; margin-bottom: 6px;">PHYSICAL RULES</div>
            <div>Status: <span class="badge {'badge-critical' if pr.get('status') == 'VIOLATED' else 'badge-normal'}">{safe_str(pr.get('status'), 'NORMAL')}</span></div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">Violations: {safe_int(pr.get('triggered_count'))} rules</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Max Sev: {safe_str(pr.get('max_severity'), 'NONE')}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with q2:
        st.markdown(
            f"""
        <div class="soc-panel">
            <div style="font-weight: 700; color: #38bdf8; font-size: 11px; margin-bottom: 6px;">ISOLATION FOREST</div>
            <div>Anomaly: <span class="badge {'badge-warning' if ifo.get('is_anomaly') else 'badge-normal'}">{'ANOMALY' if ifo.get('is_anomaly') else 'NOMINAL'}</span></div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">Score: {safe_float(ifo.get('anomaly_score')):.4f}</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Model: {safe_str(ifo.get('model_version'), 'Tuned v1.1')}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with q3:
        st.markdown(
            f"""
        <div class="soc-panel">
            <div style="font-weight: 700; color: #38bdf8; font-size: 11px; margin-bottom: 6px;">XGBOOST CLASSIFIER</div>
            <div>Class: <span class="badge badge-info">{safe_str(xgb.get('predicted_label'), 'UNASSIGNED')}</span></div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">Confidence: {safe_float(xgb.get('confidence')) * 100:.1f}%</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Status: {safe_str(xgb.get('status'), 'AUDITED')}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with q4:
        st.markdown(
            f"""
        <div class="soc-panel">
            <div style="font-weight: 700; color: #38bdf8; font-size: 11px; margin-bottom: 6px;">TEMPORAL LSTM</div>
            <div>Anomaly: <span class="badge {'badge-warning' if temp.get('is_anomaly') else 'badge-normal'}">{'ANOMALY' if temp.get('is_anomaly') else 'NOMINAL'}</span></div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">Recon Error: {safe_float(temp.get('reconstruction_error')):.4f}</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Window: W=10 epochs</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
