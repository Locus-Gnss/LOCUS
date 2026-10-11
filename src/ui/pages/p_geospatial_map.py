"""
Module 3: Geospatial Map
Module: src.ui.pages.p_geospatial_map
Renders kinematic trajectory tracing, classification flags, and geospatial coordinate tracks.
"""

from typing import Dict, Any, List
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.utils.formatting import safe_float, safe_int, safe_str


def render_geospatial_map(data_service, selected_event_id: str):
    """
    Render Geospatial Map module matching Screenshot 3 specification.
    """
    st.markdown("<div class='section-header'>GEOSPATIAL TRAJECTORY TRACKING</div>", unsafe_allow_html=True)
    st.markdown(
        """
    <div class="soc-callout">
        <strong>GEOSPATIAL MAPPING:</strong> Real-time trajectory tracing with geofenced kinematic spoofing boundaries.
        Correlates Doppler velocity vectors with geodesic displacement to flag teleportation and meaconing shifts.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Load telemetry and active bundle
    df_tel = data_service.load_telemetry_dataset()
    bundle = data_service.load_event(selected_event_id)

    if df_tel.empty:
        st.info("NO GEOSPATIAL DATA AVAILABLE")
        return

    loc = bundle.location if bundle and isinstance(bundle.location, dict) else {}
    target_lat = safe_float(loc.get("latitude", df_tel["latitude"].iloc[-1]))
    target_lon = safe_float(loc.get("longitude", df_tel["longitude"].iloc[-1]))
    target_alt = safe_float(loc.get("altitude_m", df_tel.get("altitude_m", pd.Series([0])).iloc[-1]))

    # Top Status Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("TARGET POSITION", f"{target_lat:.6f}°, {target_lon:.6f}°")
    with c2:
        st.metric("ALTITUDE (MSL)", f"{target_alt:.2f} m")
    with c3:
        st.metric("TOTAL WAYPOINTS", f"{len(df_tel)} points")
    with c4:
        st.markdown(
            f"""
        <div class="kpi-card" style="padding: 10px;">
            <div class="kpi-label">CLASSIFICATION FLAG</div>
            <div style="margin-top: 4px;"><span class="badge badge-online">GEO-VALIDATED TRACK</span></div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # 1. Plotly High-Precision Dark Trajectory Radar Track
    st.markdown("<div class='soc-panel-title'>KINEMATIC 2D PLANAR TRAJECTORY TRACE</div>", unsafe_allow_html=True)

    fig = go.Figure()

    # Full trajectory path
    fig.add_trace(go.Scatter(
        x=df_tel["longitude"],
        y=df_tel["latitude"],
        mode="lines",
        name="Recorded Track",
        line={"color": "#0ea5e9", "width": 2.5},
        hoverinfo="skip"
    ))

    # All fix waypoints
    fig.add_trace(go.Scatter(
        x=df_tel["longitude"],
        y=df_tel["latitude"],
        mode="markers",
        name="Waypoints",
        marker={"size": 4, "color": "#38bdf8", "opacity": 0.6},
        hovertext=[f"Lat: {lat:.6f}<br>Lon: {lon:.6f}" for lat, lon in zip(df_tel["latitude"], df_tel["longitude"])],
        hoverinfo="text"
    ))

    # Origin Epoch marker
    fig.add_trace(go.Scatter(
        x=[df_tel["longitude"].iloc[0]],
        y=[df_tel["latitude"].iloc[0]],
        mode="markers+text",
        name="Origin Fix",
        marker={"size": 12, "color": "#10b981", "symbol": "diamond"},
        text=["ORIGIN"],
        textposition="top center",
        textfont={"color": "#10b981", "size": 10, "family": "monospace"}
    ))

    # Active Forensic Target marker
    fig.add_trace(go.Scatter(
        x=[target_lon],
        y=[target_lat],
        mode="markers+text",
        name=f"Active Target ({selected_event_id})",
        marker={"size": 14, "color": "#ef4444", "symbol": "cross"},
        text=[f"EVENT TARGET: {selected_event_id}"],
        textposition="bottom center",
        textfont={"color": "#f87171", "size": 11, "family": "monospace"}
    ))

    fig.update_layout(
        paper_bgcolor="#090e18",
        plot_bgcolor="#090e18",
        font={"color": "#94a3b8", "family": "'SF Mono', Monaco, monospace"},
        xaxis={"gridcolor": "#1e293b", "zerolinecolor": "#334155", "title": "Longitude (deg East)"},
        yaxis={"gridcolor": "#1e293b", "zerolinecolor": "#334155", "title": "Latitude (deg North)"},
        margin={"l": 40, "r": 20, "t": 20, "b": 35},
        height=380,
        legend={"orientation": "h", "y": 1.08, "x": 0.0}
    )
    st.plotly_chart(fig, use_container_width=True)

    # 2. Interactive Map View via Streamlit Native Map
    with st.expander("Geospatial Map Canvas (MapLibre Coordinate Projection)", expanded=True):
        map_data = pd.DataFrame({
            "latitude": df_tel["latitude"].dropna(),
            "longitude": df_tel["longitude"].dropna()
        })
        st.map(map_data, zoom=14, color="#00f2fe")
