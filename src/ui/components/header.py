"""
LOCUS GNSS Security Operations Center Persistent Header Component
Module: src.ui.components.header
Strictly no emojis. Clean technical SOC banner matching target specification.
"""

from datetime import datetime, timezone
from typing import Tuple
import streamlit as st

from src.ui.utils.state import get_selected_event, set_selected_event


def render_soc_persistent_header(data_service) -> str:
    """
    Render persistent LOCUS SOC top banner and global event selector.
    Matches layout:
    ┌─────────────────────────────────────────────────────────────┐
    │ [SHIELD] LOCUS   v5.5 SOC                                   │
    │ GNSS Cyber-Physical Security Operations Center              │
    │                                                             │
    │ THREAT RATING      SENSOR PROVENANCE       UTC              │
    │ DEFCON 4           REAL L89HA TELEMETRY    03:02:09 UTC     │
    │                                                             │
    │ FORENSIC INCIDENT EVENT                                     │
    │ [ evt_4_220 ▼ ]       [SYNC]                                │
    └─────────────────────────────────────────────────────────────┘
    """
    events = data_service.get_events()
    event_ids = [e["event_id"] for e in events] if events else ["NO DATA AVAILABLE"]

    current_event = get_selected_event()
    if current_event not in event_ids and event_ids:
        current_event = event_ids[0]
        set_selected_event(current_event)

    # Check connection / provenance
    conn_info = data_service.check_gnss_connection()
    is_live = conn_info.get("is_live", False)
    provenance = "REAL L89HA TELEMETRY (LIVE)" if is_live else "REAL L89HA TELEMETRY (REPLAY MODE)"

    # Inspect threat rating for current event via authoritative canonical assessment
    canonical = data_service.get_canonical_assessment(current_event)
    threat_str = canonical.get("defcon_display", "DEFCON 5 (NOMINAL)")
    badge_class = canonical.get("defcon_badge_class", "badge-normal")

    threat_color = "#f87171" if ("DEFCON 1" in threat_str or "DEFCON 2" in threat_str) else (
        "#fbbf24" if ("DEFCON 3" in threat_str or "DEFCON 4" in threat_str) else "#38bdf8"
    )

    utc_now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    # Render Header Banner
    st.markdown(
        f"""
    <div class="locus-persistent-header">
        <div class="locus-top-row">
            <div class="locus-title-box">
                <div class="locus-title-text">[SHIELD] LOCUS &nbsp; v5.5 SOC</div>
                <div class="locus-sub-text">GNSS Cyber-Physical Security Operations Center</div>
            </div>
            <div class="locus-telemetry-meta">
                <div class="locus-meta-block">
                    <span class="locus-meta-lbl">THREAT RATING</span>
                    <span class="locus-meta-val" style="color: {threat_color};">{threat_str}</span>
                </div>
                <div class="locus-meta-block">
                    <span class="locus-meta-lbl">SENSOR PROVENANCE</span>
                    <span class="locus-meta-val" style="color: #38bdf8;">{provenance}</span>
                </div>
                <div class="locus-meta-block">
                    <span class="locus-meta-lbl">UTC CLOCK</span>
                    <span class="locus-meta-val" style="color: #cbd5e1;">{utc_now}</span>
                </div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Global Forensic Incident Event Selector Bar
    col_sel1, col_sel2 = st.columns([5, 1])

    with col_sel1:
        wk = "global_header_event_select"
        if wk not in st.session_state or st.session_state[wk] not in event_ids:
            st.session_state[wk] = current_event

        def _on_header_event_change():
            chosen = st.session_state.get(wk)
            if chosen:
                set_selected_event(chosen)

        selected_id = st.selectbox(
            "FORENSIC INCIDENT EVENT:",
            options=event_ids,
            index=event_ids.index(current_event) if current_event in event_ids else 0,
            key=wk,
            on_change=_on_header_event_change,
        )

    with col_sel2:
        st.markdown("<div style='padding-top: 24px;'>", unsafe_allow_html=True)
        if st.button("SYNC", key="btn_header_sync_event", help="Synchronize active event across all SOC modules"):
            set_selected_event(selected_id)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    return selected_id
