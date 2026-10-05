"""
LOCUS Live & Replay GNSS Telemetry Panel
Module: src.ui.components.telemetry_panel
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def render_telemetry_panel(df_telemetry: pd.DataFrame, conn_info: dict):
    """
    Render live/historical telemetry metrics and time-series trend graphs.
    """
    st.subheader("GNSS Telemetry & Kinematic Dynamics")
    mode_text = conn_info.get("mode", "DATA MODE: GNSS REPLAY")
    source_text = conn_info.get("source", "Recorded L89HA Session")
    hw_status = conn_info.get("hardware_status", "Not Connected")
    st.caption(f"**{mode_text}** • Source: **{source_text}** • Live Hardware: **{hw_status}** • Telemetry Provenance: **REAL GNSS TELEMETRY (7Semi L89HA)**")

    if df_telemetry.empty:
        st.warning("No GNSS telemetry records available in processed dataset. Awaiting sensor stream.")
        return

    # User controls for sliding window
    c_ctrl1, c_ctrl2 = st.columns([2, 3])
    with c_ctrl1:
        window_size = st.select_slider(
            "Telemetry History Window (Epochs):",
            options=[50, 100, 200, 500, 1000],
            value=100
        )
    with c_ctrl2:
        sessions = sorted(df_telemetry["session_id"].unique()) if "session_id" in df_telemetry.columns else [1]
        selected_session = st.selectbox("Telemetry Session ID:", options=["All Sessions"] + [f"Session {s}" for s in sessions])

    filtered_df = df_telemetry.copy()
    if selected_session != "All Sessions":
        s_id = int(selected_session.replace("Session ", ""))
        filtered_df = filtered_df[filtered_df["session_id"] == s_id]

    # Slice tail
    tail_df = filtered_df.tail(window_size).copy()
    if tail_df.empty:
        st.info("No records found for the selected session.")
        return

    # Extract time column
    time_col = "timestamp_gnss" if "timestamp_gnss" in tail_df.columns else "timestamp_pc"
    tail_df["time_display"] = pd.to_datetime(tail_df[time_col], errors="coerce")

    # Current telemetry values grid
    latest = tail_df.iloc[-1]
    st.markdown("#### Real-Time Telemetry State Vector")
    t1, t2, t3, t4, t5 = st.columns(5)
    t1.metric("Latitude", f"{latest.get('latitude', 0.0):.6f} °N")
    t2.metric("Longitude", f"{latest.get('longitude', 0.0):.6f} °E")
    t3.metric("Altitude MSL", f"{latest.get('altitude_m', 0.0):.2f} m")
    t4.metric("Speed", f"{latest.get('speed_kmh', 0.0):.2f} km/h")
    t5.metric("Heading", f"{latest.get('heading_deg', 0.0):.1f} °")

    t6, t7, t8, t9, t10 = st.columns(5)
    t6.metric("Fix Quality", f"{int(latest.get('fix_quality', 0))}")
    t7.metric("Satellites Used", f"{int(latest.get('satellites_used', 0))}")
    sats_view = latest.get('satellites_in_view_clean', latest.get('satellites_in_view_raw', 0))
    t8.metric("Satellites in View", f"{int(sats_view) if pd.notna(sats_view) else 0}")
    t9.metric("HDOP", f"{latest.get('hdop', 0.0):.2f}")
    t10.metric("VDOP", f"{latest.get('vdop', 0.0):.2f}")

    st.markdown("---")
    st.markdown("#### Telemetry Trend Series")

    # Time series plots using Plotly
    time_series = tail_df["time_display"] if tail_df["time_display"].notna().all() else tail_df.index

    # Chart 1: Speed & Altitude
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(
        go.Scatter(x=time_series, y=tail_df["speed_kmh"], name="Speed (km/h)", line=dict(color="#38bdf8", width=2)),
        secondary_y=False
    )
    fig1.add_trace(
        go.Scatter(x=time_series, y=tail_df["altitude_m"], name="Altitude (m)", line=dict(color="#34d399", width=1.5, dash="dot")),
        secondary_y=True
    )
    fig1.update_layout(
        title="1. Speed & Altitude vs. Time",
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0f172a",
        font=dict(color="#94a3b8"),
        margin=dict(l=20, r=20, t=40, b=20),
        height=280,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig1.update_xaxes(gridcolor="#1e293b")
    fig1.update_yaxes(title_text="Speed (km/h)", gridcolor="#1e293b", secondary_y=False)
    fig1.update_yaxes(title_text="Altitude (m)", gridcolor="#1e293b", secondary_y=True)
    st.plotly_chart(fig1, use_container_width=True)

    # Charts 2 & 3: HDOP vs Time and Satellite Count vs Time
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        fig_hdop = go.Figure()
        fig_hdop.add_trace(go.Scatter(x=time_series, y=tail_df["hdop"], name="HDOP", line=dict(color="#f59e0b", width=2)))
        fig_hdop.add_trace(go.Scatter(x=time_series, y=tail_df["vdop"], name="VDOP", line=dict(color="#a855f7", width=1.5)))
        fig_hdop.add_hline(y=4.0, line_dash="dash", line_color="#ef4444", annotation_text="Degraded (HDOP=4.0)")
        fig_hdop.update_layout(
            title="2. HDOP & VDOP vs. Time",
            paper_bgcolor="#0b0f19",
            plot_bgcolor="#0f172a",
            font=dict(color="#94a3b8"),
            margin=dict(l=20, r=20, t=40, b=20),
            height=260
        )
        fig_hdop.update_xaxes(gridcolor="#1e293b")
        fig_hdop.update_yaxes(gridcolor="#1e293b")
        st.plotly_chart(fig_hdop, use_container_width=True)

    with col_c2:
        fig_sats = go.Figure()
        fig_sats.add_trace(go.Scatter(x=time_series, y=tail_df["satellites_used"], name="Satellites Used", line=dict(color="#10b981", width=2)))
        fig_sats.add_hline(y=4.0, line_dash="dash", line_color="#dc2626", annotation_text="Min Fix (4 PRNs)")
        fig_sats.update_layout(
            title="3. Satellite Count vs. Time",
            paper_bgcolor="#0b0f19",
            plot_bgcolor="#0f172a",
            font=dict(color="#94a3b8"),
            margin=dict(l=20, r=20, t=40, b=20),
            height=260
        )
        fig_sats.update_xaxes(gridcolor="#1e293b")
        fig_sats.update_yaxes(gridcolor="#1e293b")
        st.plotly_chart(fig_sats, use_container_width=True)

    # Chart 4: Heading vs Time
    fig_head = go.Figure()
    fig_head.add_trace(go.Scatter(x=time_series, y=tail_df["heading_deg"], name="Heading (°)", line=dict(color="#818cf8", width=2)))
    fig_head.update_layout(
        title="4. Heading Angle vs. Time",
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0f172a",
        font=dict(color="#94a3b8"),
        margin=dict(l=20, r=20, t=40, b=20),
        height=240
    )
    fig_head.update_xaxes(gridcolor="#1e293b")
    fig_head.update_yaxes(gridcolor="#1e293b")
    st.plotly_chart(fig_head, use_container_width=True)
