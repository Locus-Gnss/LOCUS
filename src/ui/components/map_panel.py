"""
LOCUS Geospatial GNSS Map & Trajectory Visualizer
Module: src.ui.components.map_panel
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


def render_map_panel(df_telemetry: pd.DataFrame, alerts: list = None):
    """
    Render geospatial trajectory map with classified points:
    NORMAL (Green), WARNING (Amber), ANOMALY (Red).
    """
    st.subheader("Geospatial Trajectory & Anomaly Mapping")
    st.caption("OpenStreetMap Tile Layer • Real Coordinate Track • Kinematic Anomaly Overlays")

    if df_telemetry.empty:
        st.info("Empty State: No geographic coordinates available in current dataset. Trajectory cannot be rendered.")
        return

    # Filter out missing lat/lon
    valid_geo = df_telemetry.dropna(subset=["latitude", "longitude"]).copy()
    valid_geo = valid_geo[(valid_geo["latitude"] != 0.0) & (valid_geo["longitude"] != 0.0)]

    if valid_geo.empty:
        st.warning("All records in current session contain zero/invalid coordinates (No GNSS fix).")
        return

    # Slice recent trajectory
    col_w, col_stat = st.columns([2, 3])
    with col_w:
        points_limit = st.slider("Visible Track Points:", min_value=20, max_value=500, value=150, step=10)

    track_df = valid_geo.tail(points_limit).copy()

    # Determine status of each point based on speed/hdop or alert overlay
    def classify_point(row):
        hdop = row.get("hdop", 1.0)
        speed = row.get("speed_kmh", 0.0)
        if hdop > 6.0 or speed > 150.0:
            return "ANOMALY"
        elif hdop > 3.0 or speed > 90.0:
            return "WARNING"
        return "NORMAL"

    track_df["security_status"] = track_df.apply(classify_point, axis=1)

    # Status counts
    counts = track_df["security_status"].value_counts()
    with col_stat:
        st.markdown(
            f"""
            <div style='display: flex; gap: 14px; margin-top: 24px;'>
                <span class='badge-normal'>NORMAL: {counts.get('NORMAL', 0)} pts</span>
                <span class='badge-warning'>WARNING: {counts.get('WARNING', 0)} pts</span>
                <span class='badge-critical'>ANOMALY: {counts.get('ANOMALY', 0)} pts</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Color mapping
    color_map = {
        "NORMAL": "#10b981",
        "WARNING": "#f59e0b",
        "ANOMALY": "#ef4444"
    }

    center_lat = float(track_df["latitude"].iloc[-1])
    center_lon = float(track_df["longitude"].iloc[-1])

    fig = go.Figure()

    # Base trajectory line
    fig.add_trace(go.Scattermap(
        lat=track_df["latitude"],
        lon=track_df["longitude"],
        mode="lines",
        line=dict(width=2, color="#38bdf8"),
        name="Trajectory Track",
        hoverinfo="skip"
    ))

    # Classified points
    for status_label, color_code in color_map.items():
        subset = track_df[track_df["security_status"] == status_label]
        if not subset.empty:
            hover_text = [
                f"<b>Epoch:</b> {r.get('epoch_id')}<br/>"
                f"<b>Status:</b> {status_label}<br/>"
                f"<b>Speed:</b> {r.get('speed_kmh', 0.0):.1f} km/h<br/>"
                f"<b>HDOP:</b> {r.get('hdop', 0.0):.2f}<br/>"
                f"<b>Sats:</b> {int(r.get('satellites_used', 0))}"
                for _, r in subset.iterrows()
            ]
            fig.add_trace(go.Scattermap(
                lat=subset["latitude"],
                lon=subset["longitude"],
                mode="markers",
                marker=dict(size=7 if status_label == "NORMAL" else 11, color=color_code),
                name=status_label,
                text=hover_text,
                hoverinfo="text"
            ))

    # Current Antenna Position Marker
    fig.add_trace(go.Scattermap(
        lat=[center_lat],
        lon=[center_lon],
        mode="markers",
        marker=dict(size=14, color="#ffffff", symbol="circle"),
        name="Current Position",
        text=[f"Current Fix: {center_lat:.6f}, {center_lon:.6f}"],
        hoverinfo="text"
    ))

    # Alert markers if provided
    if alerts:
        anom_lats = []
        anom_lons = []
        anom_texts = []
        for alt in alerts:
            loc = alt.get("location", {})
            if loc.get("latitude") and loc.get("longitude"):
                anom_lats.append(loc["latitude"])
                anom_lons.append(loc["longitude"])
                anom_texts.append(f"<b>ALERT:</b> {alt.get('alert_id')}<br/><b>Type:</b> {alt.get('event_type')}<br/><b>Severity:</b> {alt.get('severity')}")

        if anom_lats:
            fig.add_trace(go.Scattermap(
                lat=anom_lats,
                lon=anom_lons,
                mode="markers",
                marker=dict(size=13, color="#ef4444", symbol="triangle"),
                name="Flagged Alerts",
                text=anom_texts,
                hoverinfo="text"
            ))

    fig.update_layout(
        map=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=16
        ),
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0f172a",
        font=dict(color="#94a3b8"),
        margin=dict(l=0, r=0, t=10, b=0),
        height=450,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(15, 23, 42, 0.8)"
        )
    )

    st.plotly_chart(fig, use_container_width=True)
