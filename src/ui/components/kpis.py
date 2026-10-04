"""
LOCUS SOC Primary Executive KPI Cards
Module: src.ui.components.kpis
"""

import streamlit as st


def render_kpi_cards(
    telemetry: dict,
    security_status: str = "NORMAL",
    defcon_level: str = "DEFCON_5",
    active_alerts_count: int = 0,
    is_live: bool = False
):
    """
    Render the 6 mandatory high-visibility SOC KPI cards.
    """
    has_tel = telemetry.get("has_data", False)

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    # 1. GNSS Status
    with col1:
        if is_live:
            gnss_val = "CONNECTED"
            gnss_sub = "LIVE HARDWARE"
            gnss_color = "#34d399"
        elif has_tel:
            gnss_val = "CONNECTED"
            gnss_sub = "HISTORICAL REPLAY"
            gnss_color = "#38bdf8"
        else:
            gnss_val = "NO LIVE DATA"
            gnss_sub = "AWAITING SENSOR"
            gnss_color = "#f87171"

        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>1. GNSS Status</div>
            <div class='kpi-value' style='color: {gnss_color}; font-size: 17px;'>{gnss_val}</div>
            <div class='kpi-sub'>{gnss_sub}</div>
        </div>
        """, unsafe_allow_html=True)

    # 2. Security Status
    with col2:
        sec_color = "#34d399"
        if "CRITICAL" in security_status or "1" in defcon_level:
            sec_color = "#f87171"
        elif "WARNING" in security_status or "SUSPECTED" in security_status or "2" in defcon_level or "3" in defcon_level:
            sec_color = "#fbbf24"

        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>2. Security Status</div>
            <div class='kpi-value' style='color: {sec_color}; font-size: 16px;'>{security_status}</div>
            <div class='kpi-sub'>{defcon_level}</div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Satellites
    with col3:
        sats_val = f"{telemetry.get('satellites_used', 0)}" if has_tel else "NO DATA"
        sats_in_view = telemetry.get('satellites_in_view', 0) if has_tel else 0
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>3. Satellites</div>
            <div class='kpi-value' style='color: #ffffff;'>{sats_val}</div>
            <div class='kpi-sub'>Visible: {sats_in_view} PRNs</div>
        </div>
        """, unsafe_allow_html=True)

    # 4. HDOP
    with col4:
        hdop_val = f"{telemetry.get('hdop', 0.0):.2f}" if has_tel else "NO DATA"
        hdop_num = telemetry.get('hdop', 1.0) if has_tel else 1.0
        hdop_color = "#34d399" if hdop_num < 2.5 else ("#fbbf24" if hdop_num < 5.0 else "#f87171")
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>4. HDOP</div>
            <div class='kpi-value' style='color: {hdop_color};'>{hdop_val}</div>
            <div class='kpi-sub'>VDOP: {telemetry.get('vdop', 0.0):.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    # 5. Current Speed
    with col5:
        speed_val = f"{telemetry.get('speed_kmh', 0.0):.1f} km/h" if has_tel else "NO DATA"
        speed_mps = telemetry.get('speed_kmh', 0.0) / 3.6 if has_tel else 0.0
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>5. Speed</div>
            <div class='kpi-value' style='color: #ffffff; font-size: 18px;'>{speed_val}</div>
            <div class='kpi-sub'>{speed_mps:.2f} m/s</div>
        </div>
        """, unsafe_allow_html=True)

    # 6. Active Alerts
    with col6:
        alerts_color = "#34d399" if active_alerts_count == 0 else ("#fbbf24" if active_alerts_count < 3 else "#f87171")
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>6. Active Alerts</div>
            <div class='kpi-value' style='color: {alerts_color};'>{active_alerts_count}</div>
            <div class='kpi-sub'>Forensic Incidents</div>
        </div>
        """, unsafe_allow_html=True)
