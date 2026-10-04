"""
LOCUS Cyber-Physical GNSS Security Operations Center (SOC) — Streamlit Dashboard

Module: src.ui.dashboard
Run: streamlit run src/ui/dashboard.py
"""

import os
import json
import streamlit as st
import pandas as pd
import numpy as np

from src.query.query_processor import SecurityQueryProcessor


# Set page layout
st.set_page_config(
    page_title="LOCUS — GNSS Security Operations Center",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Cyber-Security CSS Styling
st.markdown("""
<style>
    .main {
        background-color: #0b0f19;
    }
    .metric-card {
        background: linear-gradient(135deg, #131b2e 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .defcon-1 { background-color: #ef4444; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .defcon-2 { background-color: #f97316; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .defcon-3 { background-color: #eab308; color: black; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .defcon-4 { background-color: #3b82f6; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .defcon-5 { background-color: #10b981; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .agent-box {
        border-left: 4px solid #38bdf8;
        background: #0f172a;
        padding: 12px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
    }
    .rag-badge {
        background-color: #6366f1;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_query_processor():
    return SecurityQueryProcessor()


processor = get_query_processor()

# Header
st.title("🛰️ LOCUS — Cyber-Physical GNSS Security Operations Center")
st.caption("Live Observation, Cybersecurity & Unified Security for GNSS | 3-Agent SOC & Regulatory RAG")

# Sidebar
st.sidebar.header("Navigation & Event Feed")
events = processor.list_available_events()

if not events:
    st.error("No evidence events found in data/evidence/. Run detection pipeline first.")
    st.stop()

event_options = [e["event_id"] for e in events]
selected_event_id = st.sidebar.selectbox("Select GNSS Event:", event_options, index=0)

# Sidebar System Health
st.sidebar.markdown("---")
st.sidebar.subheader("System Architecture")
st.sidebar.markdown("""
- **Hardware**: 7Semi L89HA Multi-GNSS
- **Features**: Official 10-D Security Vector
- **Detectors**: Physical, IForest, XGBoost, LSTM
- **SOC Layer**: 3-Agent Hierarchy
- **Knowledge Base**: RAG (ICAO, RTCA, CISA, MITRE)
""")

# Load Selected Event Bundle
bundle = processor.load_event(selected_event_id)
if not bundle:
    st.error(f"Failed to load event: {selected_event_id}")
    st.stop()

# Run Deliberation & Grounding for Event
query_result = processor.process_query(
    query="Initial security status assessment.",
    event_id=selected_event_id,
    bundle=bundle
)

status = query_result["current_status"]
defcon = query_result["risk_level"]
conf = query_result["confidence"]
features = query_result["feature_values"]
outputs = query_result["model_outputs"]
agents = query_result["agent_findings"]
rag_sources = query_result["rag_sources"]

# Top Status Bar
col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
with col1:
    st.markdown(f"**Event ID**: `{bundle.event_id}`")
    st.markdown(f"**UTC Timestamp**: `{bundle.timestamp_utc}`")
with col2:
    st.markdown("**Incident Status**")
    if status == "CONFIRMED_ATTACK":
        st.error(f"🚨 {status}")
    elif status == "SUSPECTED_INTERFERENCE":
        st.warning(f"⚠️ {status}")
    else:
        st.success(f"✅ {status}")
with col3:
    st.markdown("**DEFCON Readiness**")
    defcon_class = "defcon-5"
    if "1" in defcon: defcon_class = "defcon-1"
    elif "2" in defcon: defcon_class = "defcon-2"
    elif "3" in defcon: defcon_class = "defcon-3"
    elif "4" in defcon: defcon_class = "defcon-4"
    st.markdown(f"<span class='{defcon_class}'>{defcon}</span>", unsafe_allow_html=True)
with col4:
    st.markdown(f"**Consensus Confidence**: `{conf * 100:.1f}%`")
    st.progress(float(conf))

st.markdown("---")

# Main Content Tabs
tab_overview, tab_features, tab_detectors, tab_agents, tab_rag, tab_query = st.tabs([
    "📊 Executive Summary",
    "📈 10-D Security Features",
    "🛡️ Detector Quad",
    "🤖 3-Agent Findings",
    "📚 Regulatory RAG",
    "💬 Security Query Terminal"
])

# TAB 1: EXECUTIVE SUMMARY
with tab_overview:
    st.subheader("Master SOC Executive Summary")
    st.info(agents.get("agent_3_master_soc", {}).get("summary", "No summary available."))

    st.subheader("Mandated Mitigation Directives")
    actions = query_result.get("recommended_next_action", [])
    for act in actions:
        st.markdown(f"- **`{act}`**")

    st.subheader("Geospatial & Antenna Position")
    loc = bundle.location
    c_lat, c_lon, c_alt = st.columns(3)
    c_lat.metric("Latitude", f"{loc.get('latitude', 'N/A')} °N")
    c_lon.metric("Longitude", f"{loc.get('longitude', 'N/A')} °E")
    c_alt.metric("Altitude MSL", f"{loc.get('altitude_m', 'N/A')} m")

# TAB 2: 10-D SECURITY FEATURES
with tab_features:
    st.subheader("Official 10-Dimensional Security Feature Vector")
    st.caption("Structured across Physical Kinematics, Navigation Quality, and Satellite Constellation Dynamics.")

    col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
    col_k1.metric("disp_haversine", f"{features.get('disp_haversine', 0.0):.3f} m")
    col_k2.metric("vel_kinematic", f"{features.get('vel_kinematic', 0.0):.3f} m/s")
    col_k3.metric("acc_kinematic", f"{features.get('acc_kinematic', 0.0):.3f} m/s²")
    col_k4.metric("jerk_kinematic", f"{features.get('jerk_kinematic', 0.0):.3f} m/s³")
    col_k5.metric("bearing_rate", f"{features.get('bearing_rate', 0.0):.2f} °/s")

    col_q1, col_q2, col_q3, col_q4, col_q5 = st.columns(5)
    col_q1.metric("HDOP", f"{features.get('HDOP', 0.0):.2f}")
    col_q2.metric("VDOP", f"{features.get('VDOP', 0.0):.2f}")
    col_q3.metric("fix_integrity", f"{features.get('fix_integrity', 0.0):.3f}")
    col_q4.metric("sat_count_tot", f"{features.get('sat_count_tot', 0)}")
    churn_val = features.get('sat_churn')
    col_q5.metric("sat_churn", f"{churn_val:.3f}" if churn_val is not None else "N/A (Historical)")

    # Dataframe visualization
    st.dataframe(pd.DataFrame([features]), use_container_width=True)

# TAB 3: DETECTOR QUAD
with tab_detectors:
    st.subheader("Multi-Detector Anomaly Quad")
    d1, d2 = st.columns(2)
    with d1:
        st.markdown("#### Path 1: Physical Rules Engine")
        pr = outputs.get("physical_rules", {})
        st.write(f"**Max Severity**: `{pr.get('max_severity', 'INFO')}`")
        st.write(f"**Triggered Violations**: `{pr.get('triggered_count', 0)}`")
        if pr.get("triggered_rules"):
            st.json(pr["triggered_rules"])
        else:
            st.success("Zero physical kinematic invariants violated.")

        st.markdown("#### Path 3: Supervised XGBoost Classifier")
        xgb = outputs.get("xgboost", {})
        st.write(f"**Classification Status**: `{xgb.get('status', 'UNFITTED')}`")

    with d2:
        st.markdown("#### Path 2: Isolation Forest (Spatial Outlier)")
        ifo = outputs.get("isolation_forest", {})
        st.write(f"**Anomaly Score**: `{ifo.get('anomaly_score', 0.0):.4f}`")
        st.write(f"**Flagged Anomaly**: `{ifo.get('is_anomaly', False)}`")

        st.markdown("#### Path 4: LSTM Sequence Autoencoder")
        lstm = outputs.get("temporal_model", {})
        recon = lstm.get("reconstruction_error", 0.0)
        thresh = lstm.get("error_threshold", 0.0)
        st.write(f"**Reconstruction Error**: `{recon:.4f}` (Threshold: `{thresh:.4f}`)")
        st.write(f"**Temporal Anomaly**: `{lstm.get('is_anomaly', False)}`")

# TAB 4: 3-AGENT FINDINGS
with tab_agents:
    st.subheader("Autonomous 3-Agent SOC Deliberation")
    a1 = agents.get("agent_1_integrity", {})
    a2 = agents.get("agent_2_temporal_threat", {})
    a3 = agents.get("agent_3_master_soc", {})

    st.markdown("##### 🛡️ Agent 1 — GNSS Integrity Agent")
    st.markdown(f"<div class='agent-box'><b>Status:</b> {a1.get('integrity_assessment')}<br/>"
                f"<b>Kinematic Health:</b> {a1.get('kinematic_health', 1.0)*100:.1f}% | "
                f"<b>Geometry Health:</b> {a1.get('geometry_health', 1.0)*100:.1f}%<br/>"
                f"<b>Discard Recommended:</b> {a1.get('discard_recommended')}<br/>"
                f"<b>Explanation:</b> {a1.get('explanation')}</div>", unsafe_allow_html=True)

    st.markdown("##### ⏱️ Agent 2 — Temporal / Threat Agent")
    st.markdown(f"<div class='agent-box'><b>Threat Classification:</b> {a2.get('threat_classification')}<br/>"
                f"<b>Persistence Streak:</b> {a2.get('persistence_streak')} epoch(s) | "
                f"<b>Is Persistent:</b> {a2.get('is_persistent')}<br/>"
                f"<b>Explanation:</b> {a2.get('explanation')}</div>", unsafe_allow_html=True)

    st.markdown("##### 👑 Agent 3 — Master SOC Orchestrator")
    st.markdown(f"<div class='agent-box'><b>Binding Risk Level:</b> {a3.get('risk_level')}<br/>"
                f"<b>Status:</b> {a3.get('status')} | "
                f"<b>Confidence:</b> {a3.get('confidence', 1.0)*100:.1f}%<br/>"
                f"<b>Consensus Summary:</b> {a3.get('summary')}</div>", unsafe_allow_html=True)

# TAB 5: REGULATORY RAG
with tab_rag:
    st.subheader("Regulatory RAG Knowledge Base Sources")
    st.caption("Approved Grounding Standards: ICAO Annex 10, RTCA DO-229E, CISA Resilient PNT, MITRE ATT&CK for Space.")
    if rag_sources:
        for idx, src in enumerate(rag_sources):
            with st.expander(f"Source {idx+1}: {src['document']} — Section: {src['section']} (Sim: {src['similarity']:.3f})"):
                auths = src.get("regulatory_authorities", [])
                auth_html = "".join([f"<span class='rag-badge'>{a}</span>" for a in auths])
                st.markdown(f"**Regulatory Authorities**: {auth_html}", unsafe_allow_html=True)
    else:
        st.warning("No regulatory citations grounded for this event.")

# TAB 6: SECURITY QUERY TERMINAL
with tab_query:
    st.subheader("💬 Natural-Language Security Query Terminal")
    st.caption("Ask questions about this event, feature attribution, persistence, or regulatory compliance.")

    # Example Query Quick Buttons
    st.write("**Quick Query Prompts:**")
    q_col1, q_col2, q_col3 = st.columns(3)
    q1 = q_col1.button("Why was this event flagged?")
    q2 = q_col2.button("What features caused the anomaly?")
    q3 = q_col3.button("Is the anomaly persistent?")

    q_col4, q_col5, q_col6 = st.columns(3)
    q4 = q_col4.button("Show me the evidence behind this alert.")
    q5 = q_col5.button("What did the temporal model detect?")
    q6 = q_col6.button("Explain the navigation-quality degradation.")

    active_prompt = "Why was this event flagged?"
    if q1: active_prompt = "Why was this event flagged?"
    elif q2: active_prompt = "What features caused the anomaly?"
    elif q3: active_prompt = "Is the anomaly persistent?"
    elif q4: active_prompt = "Show me the evidence behind this alert."
    elif q5: active_prompt = "What did the temporal model detect?"
    elif q6: active_prompt = "Explain the navigation-quality degradation."

    user_query = st.text_input("Enter natural-language query:", value=active_prompt)

    if st.button("Submit Security Query", type="primary"):
        with st.spinner("Executing SOC deliberation, RAG grounding, and reasoning..."):
            ans = processor.process_query(
                query=user_query,
                event_id=selected_event_id,
                bundle=bundle
            )
            st.success("SOC Response Generated")
            st.markdown(f"### Answer:\n{ans['explanation']}")

            with st.expander("Inspect Full Structured JSON Response"):
                st.json(ans)
