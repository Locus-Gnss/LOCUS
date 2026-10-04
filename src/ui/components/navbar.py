"""
LOCUS SOC Top Navigation Bar
Module: src.ui.components.navbar
"""

from datetime import datetime, timezone
import streamlit as st


def render_navbar(conn_info: dict, system_status: str = "OPERATIONAL", defcon_level: str = "DEFCON_5"):
    """
    Render top executive cybersecurity header bar.
    """
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    is_live = conn_info.get("is_live", False)
    mode_text = conn_info.get("mode", "HISTORICAL / REPLAY MODE")
    prov_text = conn_info.get("provenance", "REAL GNSS TELEMETRY")

    col_title, col_meta = st.columns([3, 2])

    with col_title:
        st.markdown(
            """
            <div style='display: flex; align-items: baseline; gap: 12px;'>
                <span style='font-size: 26px; font-weight: 800; letter-spacing: -0.02em; color: #38bdf8;'>🛰️ LOCUS</span>
                <span style='font-size: 16px; font-weight: 600; color: #cbd5e1;'>GNSS Security Operations Center</span>
                <span class='badge-info'>v1.1 SOC</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.caption("Live Observation, Cybersecurity & Unified Security for GNSS | 3-Agent SOC & Regulatory RAG")

    with col_meta:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**System**<br/><span class='badge-normal'>● {system_status}</span>", unsafe_allow_html=True)
        with c2:
            badge_class = "badge-normal" if is_live else "badge-info"
            st.markdown(f"**Mode**<br/><span class='{badge_class}'>● {mode_text}</span>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"**UTC Time**<br/><code style='font-size: 11px;'>{now_utc}</code>", unsafe_allow_html=True)

    # Secondary Data Provenance Banner
    st.markdown(
        f"""
        <div style='background: #0f172a; border: 1px solid #1e293b; padding: 6px 12px; border-radius: 6px; margin-bottom: 12px; font-size: 12px; display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <span style='color: #94a3b8; font-weight: 600;'>DATA PROVENANCE:</span>
                <span class='provenance-tag'>{prov_text}</span>
                <span class='provenance-tag'>CANONICAL 10-D FEATURES</span>
                <span class='provenance-tag'>MULTI-DETECTOR QUAD</span>
            </div>
            <div style='color: #64748b; font-size: 11px;'>
                Zero-Fabrication Guard Active • Sensor Data Read-Only
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
