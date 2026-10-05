"""
LOCUS Cyber-Physical GNSS Security Operations Center (SOC) — Master Dashboard
Module: src.ui.dashboard
Run: streamlit run dashboard.py
"""

import os
import streamlit as st
import pandas as pd

from src.ui.data_service import SOCDataService
from src.ui.components.theme import inject_custom_css
from src.ui.components.navbar import render_navbar
from src.ui.components.kpis import render_kpi_cards
from src.ui.components.telemetry_panel import render_telemetry_panel
from src.ui.components.map_panel import render_map_panel
from src.ui.components.features_panel import render_features_panel
from src.ui.components.detection_panel import render_detection_panel
from src.ui.components.alert_center import render_alert_center
from src.ui.components.evidence_panel import render_evidence_panel
from src.ui.components.agent_soc_panel import render_agent_soc_panel
from src.ui.components.rag_panel import render_rag_panel
from src.ui.components.query_terminal import render_query_terminal
from src.ui.components.health_panel import render_health_panel


# Set page configuration
st.set_page_config(
    page_title="LOCUS — GNSS Security Operations Center",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject dark cybersecurity stylesheet
inject_custom_css()


@st.cache_resource
def get_soc_data_service():
    return SOCDataService()


service = get_soc_data_service()

# Detect hardware / connection status (Zero fabrication)
conn_info = service.check_gnss_connection()

# Cached dataset loading
@st.cache_data(ttl=60)
def load_cached_datasets():
    df_tel = service.load_telemetry_dataset()
    df_feat = service.load_features_dataset()
    alerts = service.get_alert_center_records()
    health = service.get_system_health_matrix()
    return df_tel, df_feat, alerts, health


@st.cache_data(ttl=60)
def get_cached_events():
    return service.get_events()


@st.cache_data(ttl=60)
def get_cached_deliberation(event_id: str):
    return service.deliberate_event(event_id)


df_telemetry, df_features, alerts_list, health_matrix = load_cached_datasets()

# Sidebar: Navigation & Event Selection
st.sidebar.markdown("### LOCUS SOC Command")
st.sidebar.caption("Autonomous GNSS Threat Detection & Agentic SOC")

events = get_cached_events()
event_ids = [e["event_id"] for e in events] if events else ["No Events"]

selected_event_id = st.sidebar.selectbox(
    "Active Forensic Event:",
    options=event_ids,
    index=1 if len(event_ids) > 1 else 0
)

# Navigation View Selector
nav_section = st.sidebar.radio(
    "Security Console Views:",
    options=[
        "Main SOC Overview",
        "Live GNSS Monitoring",
        "Geospatial Map View",
        "10-D Security Features",
        "Detection & ML Quad",
        "Alert Center",
        "Evidence Bundle",
        "3-Agent Security SOC",
        "Regulatory RAG",
        "SOC Query Assistant",
        "System Health"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("##### Pipeline Architecture")
st.sidebar.markdown("""
- **Sensor**: 7Semi L89HA Multi-GNSS
- **Vector**: 10-D Canonical Features
- **Detectors**: Physical, IF, XGB, LSTM
- **SOC Layer**: 3-Agent Deliberative
- **Knowledge**: RAG (ICAO, RTCA, CISA, MITRE)
""")

# Load active event bundle & deliberation
active_bundle = service.load_event(selected_event_id)
if active_bundle:
    delib = get_cached_deliberation(selected_event_id)
    current_status = delib.get("current_status", "NOMINAL")
    defcon_level = delib.get("risk_level", "DEFCON_5")
    confidence = delib.get("confidence", 1.0)
else:
    delib = {}
    current_status = "NOMINAL"
    defcon_level = "DEFCON_5"
    confidence = 1.0

api_online, api_status_msg = service.check_backend_status()

# 1. Render Top Cybersecurity Navbar
render_navbar(
    conn_info=conn_info,
    system_status="HEALTHY",
    defcon_level=defcon_level,
    api_online=api_online
)

# Waking up / Connectivity status notification (graceful degradation)
if not api_online:
    if "waking up" in api_status_msg.lower():
        st.warning(f"**Backend Notice:** {api_status_msg}")
    else:
        st.info(f"**Standalone Mode Active:** FastAPI backend is currently unavailable ({api_status_msg}). Running in local replay mode with verified dataset.")

# Latest Telemetry Metrics for KPI cards
tel_metrics = service.get_latest_telemetry_metrics()

# 2. Render Main 6 KPI Cards
render_kpi_cards(
    telemetry=tel_metrics,
    security_status=current_status,
    defcon_level=defcon_level,
    active_alerts_count=len(alerts_list),
    is_live=conn_info.get("is_live", False)
)

st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

# 3. View Routing
if nav_section == "Main SOC Overview":
    st.subheader("Executive Security Overview & Operational Directives")
    st.caption(f"Active Incident Event: `{selected_event_id}` • Defcon State: `{defcon_level}` • Consensus Confidence: `{confidence*100:.1f}%`")

    col_sum, col_dir = st.columns([3, 2])
    with col_sum:
        st.markdown("##### Master SOC Executive Summary")
        summary_text = delib.get("agent_findings", {}).get("agent_3_master_soc", {}).get("summary", "Consensus verified nominal across all detectors.")
        st.info(summary_text)

        loc = active_bundle.location if active_bundle else {}
        st.markdown(
            f"""
            <div style='background: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 12px; margin-top: 10px;'>
                <b>Antenna Fix Coordinates:</b> <code>{loc.get('latitude', 'N/A')} °N, {loc.get('longitude', 'N/A')} °E</code> | 
                <b>Altitude MSL:</b> <code>{loc.get('altitude_m', 'N/A')} m</code>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_dir:
        st.markdown("##### Mandated Mitigation Directives")
        actions = delib.get("recommended_next_action", ["MAINTAIN_STANDARD_FIX"])
        for act in actions:
            st.markdown(f"- **`{act}`**")

    st.markdown("---")
    # Quick Trajectory & 10-D Preview
    col_map_preview, col_feat_preview = st.columns([1, 1])
    with col_map_preview:
        render_map_panel(df_telemetry=df_telemetry.tail(100), alerts=alerts_list[:3])
    with col_feat_preview:
        canonical_feats = service.get_canonical_10d_features(bundle=active_bundle)
        render_features_panel(canonical_feats)

elif nav_section == "Live GNSS Monitoring":
    render_telemetry_panel(df_telemetry=df_telemetry, conn_info=conn_info)

elif nav_section == "Geospatial Map View":
    render_map_panel(df_telemetry=df_telemetry, alerts=alerts_list)

elif nav_section == "10-D Security Features":
    canonical_feats = service.get_canonical_10d_features(bundle=active_bundle)
    render_features_panel(features_list=canonical_feats, df_features=df_features)

elif nav_section == "Detection & ML Quad":
    bundle_dict = active_bundle.to_dict() if active_bundle else {}
    render_detection_panel(
        bundle_dict=bundle_dict,
        final_verdict=delib.get("agent_findings", {}).get("agent_3_master_soc")
    )

elif nav_section == "Alert Center":
    clicked_event = render_alert_center(alerts=alerts_list)
    if clicked_event:
        st.info(f"Viewing selected alert: `{clicked_event}`")
        alt_bundle = service.load_event(clicked_event)
        if alt_bundle:
            render_evidence_panel(alt_bundle)

elif nav_section == "Evidence Bundle":
    if active_bundle:
        render_evidence_panel(bundle=active_bundle, deliberation_result=delib)
    else:
        st.warning("No active Evidence Bundle selected.")

elif nav_section == "3-Agent Security SOC":
    agent_findings = delib.get("agent_findings", {})
    render_agent_soc_panel(agent_findings=agent_findings)

elif nav_section == "Regulatory RAG":
    rag_sources = delib.get("rag_sources", [])
    render_rag_panel(rag_sources=rag_sources, service=service)

elif nav_section == "SOC Query Assistant":
    render_query_terminal(
        service=service,
        event_id=selected_event_id,
        bundle=active_bundle
    )

elif nav_section == "System Health":
    render_health_panel(health_matrix=health_matrix)
