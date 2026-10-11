"""
Module 2: Live Telemetry
Module: src.ui.pages.p02_telemetry
Inspects real-time and historical GNSS telemetry records, time-series charts, and observation table.
"""

from typing import Dict, Any, List
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.utils.formatting import safe_float, safe_int, safe_str


def render_telemetry_page(data_service, selected_event_id: str):
    """
    Render Live Telemetry module matching Screenshot 2 specification.
    """
    st.markdown("<div class='section-header'>LIVE GNSS TELEMETRY &amp; EPOCH STREAM</div>", unsafe_allow_html=True)
    st.markdown(
        """
    <div class="soc-callout">
        <strong>DATA STREAM:</strong> High-frequency multi-sentence NMEA stream aggregates (GGA, RMC, GSA, GSV).
        Sensor provenance: 7Semi L89HA Multi-Constellation GNSS receiver (Civilian GPS / GLONASS / Galileo / BeiDou).
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 1. Load telemetry dataset
    df_tel = data_service.load_telemetry_dataset()
    if df_tel.empty:
        st.info("NO DATA AVAILABLE FOR TELEMETRY STREAM")
        return

    # Extract latest fix metrics
    latest = data_service.get_latest_telemetry_metrics()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("SPEED", f"{safe_float(latest.get('speed_kmh')):.2f} km/h")
    with c2:
        st.metric("HDOP", f"{safe_float(latest.get('hdop')):.2f}")
    with c3:
        st.metric("ALTITUDE", f"{safe_float(latest.get('altitude_m')):.1f} m")
    with c4:
        st.metric("SATS USED", str(safe_int(latest.get("satellites_used"))))
    with c5:
        st.metric("HEADING", f"{safe_float(latest.get('heading_deg')):.1f}°")
    with c6:
        fix_map = {0: "INVALID", 1: "SPS / 3D", 2: "DGPS / SBAS"}
        st.metric("FIX INTEGRITY", fix_map.get(safe_int(latest.get("fix_quality")), "SPS / 3D"))

    st.markdown("<hr style='border-color: #1e293b; margin: 14px 0;'>", unsafe_allow_html=True)

    # 2. Metric / Chart Selector: [SPEED] [HDOP] [ALTITUDE] [SATELLITES]
    st.markdown("<div class='soc-panel-title'>TIME-SERIES TELEMETRY OSCILLOSCOPE</div>", unsafe_allow_html=True)

    sel_col1, sel_col2 = st.columns([3, 1])
    with sel_col1:
        chart_metric = st.pills(
            "Telemetry Metric:",
            options=["SPEED", "HDOP", "ALTITUDE", "SATELLITES"],
            default="SPEED",
            key="tel_chart_metric_pill",
            label_visibility="collapsed"
        )
    with sel_col2:
        num_points = st.selectbox("Points Limit:", options=[100, 250, 500, 1000], index=1, key="tel_points_limit")

    plot_df = df_tel.tail(num_points).copy()
    x_axis = plot_df["timestamp_gnss"] if "timestamp_gnss" in plot_df.columns else plot_df.index

    fig = go.Figure()

    if chart_metric == "SPEED":
        y_vals = plot_df["speed_kmh"] if "speed_kmh" in plot_df.columns else plot_df.get("vel_kinematic", 0.0) * 3.6
        fig.add_trace(go.Scatter(
            x=x_axis,
            y=y_vals,
            mode="lines",
            name="Speed (km/h)",
            line={"color": "#00f2fe", "width": 2},
            fill="tozeroy",
            fillcolor="rgba(0, 242, 254, 0.08)"
        ))
        fig.update_layout(yaxis_title="Speed (km/h)")

    elif chart_metric == "HDOP":
        y_vals = plot_df["hdop"] if "hdop" in plot_df.columns else plot_df.get("HDOP", 0.0)
        fig.add_trace(go.Scatter(
            x=x_axis,
            y=y_vals,
            mode="lines",
            name="HDOP",
            line={"color": "#fbbf24", "width": 2}
        ))
        fig.add_hline(y=4.0, line_dash="dash", line_color="#ef4444", annotation_text="HDOP Critical Limit (4.0)")
        fig.update_layout(yaxis_title="HDOP (Unitless)")

    elif chart_metric == "ALTITUDE":
        y_vals = plot_df["altitude_m"] if "altitude_m" in plot_df.columns else 0.0
        fig.add_trace(go.Scatter(
            x=x_axis,
            y=y_vals,
            mode="lines",
            name="Altitude (m)",
            line={"color": "#38bdf8", "width": 2},
            fill="tozeroy",
            fillcolor="rgba(56, 189, 248, 0.08)"
        ))
        fig.update_layout(yaxis_title="Altitude (m)")

    elif chart_metric == "SATELLITES":
        sat_col = "satellites_used" if "satellites_used" in plot_df.columns else "sat_count_tot"
        y_vals = plot_df[sat_col] if sat_col in plot_df.columns else 8
        fig.add_trace(go.Scatter(
            x=x_axis,
            y=y_vals,
            mode="lines+markers",
            name="Satellites Used",
            line={"color": "#10b981", "width": 2},
            marker={"size": 4}
        ))
        fig.add_hline(y=4.0, line_dash="dash", line_color="#ef4444", annotation_text="Minimum Trilateration (4 SVs)")
        fig.update_layout(yaxis_title="Satellites Visible")

    fig.update_layout(
        paper_bgcolor="#090e18",
        plot_bgcolor="#090e18",
        font={"color": "#94a3b8", "family": "'SF Mono', Monaco, monospace"},
        margin={"l": 40, "r": 20, "t": 20, "b": 35},
        xaxis={"gridcolor": "#1e293b", "zerolinecolor": "#334155"},
        yaxis={"gridcolor": "#1e293b", "zerolinecolor": "#334155"},
        height=320
    )
    st.plotly_chart(fig, use_container_width=True)

    # 3. RECENT TELEMETRY OBSERVATIONS Table
    st.markdown("<div class='soc-panel-title'>RECENT TELEMETRY OBSERVATIONS</div>", unsafe_allow_html=True)

    # Format observation table with exact requested columns
    obs_rows = []
    for idx, row in plot_df.tail(20).iterrows():
        ts = str(row.get("timestamp_gnss") or row.get("timestamp_pc") or f"Epoch {idx}")
        lat = safe_float(row.get("latitude", 0.0))
        lon = safe_float(row.get("longitude", 0.0))
        alt = safe_float(row.get("altitude_m", 0.0))
        spd = safe_float(row.get("speed_kmh", 0.0))
        hdg = safe_float(row.get("heading_deg", 0.0))
        hdop_val = safe_float(row.get("hdop", 0.0) or row.get("HDOP", 0.0))
        sats = safe_int(row.get("satellites_used", 0) or row.get("sat_count_tot", 0))

        obs_rows.append({
            "Epoch / Time": ts,
            "Latitude": f"{lat:.6f}",
            "Longitude": f"{lon:.6f}",
            "Altitude": f"{alt:.1f} m",
            "Speed": f"{spd:.2f} km/h",
            "Heading": f"{hdg:.1f}°",
            "HDOP": f"{hdop_val:.2f}",
            "Satellites Used": sats
        })

    df_obs = pd.DataFrame(obs_rows)
    st.dataframe(df_obs, use_container_width=True, hide_index=True)
