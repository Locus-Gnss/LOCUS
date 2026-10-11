"""
LOCUS Plotly Visualizations & SOC Dark Charts
Module: src.ui.components.charts
Focus: Professional dark-theme scientific charts. Zero emojis.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

CHART_THEME_LAYOUT = {
    "paper_bgcolor": "#0b1120",
    "plot_bgcolor": "#0b1120",
    "font": {"color": "#94a3b8", "family": "Inter, sans-serif"},
    "margin": {"l": 40, "r": 20, "t": 35, "b": 35},
    "xaxis": {
        "gridcolor": "#1e293b",
        "zerolinecolor": "#334155",
        "showline": True,
        "linecolor": "#334155"
    },
    "yaxis": {
        "gridcolor": "#1e293b",
        "zerolinecolor": "#334155",
        "showline": True,
        "linecolor": "#334155"
    }
}


def render_trajectory_chart(df: pd.DataFrame, title: str = "GNSS TRAJECTORY (RECORDED / REPLAY DATA)"):
    """
    Render 2D planar GNSS coordinate trajectory.
    """
    if df.empty or "latitude" not in df.columns or "longitude" not in df.columns:
        st.info("NO DATA AVAILABLE FOR TRAJECTORY")
        return

    fig = go.Figure()

    # Track line
    fig.add_trace(go.Scatter(
        x=df["longitude"],
        y=df["latitude"],
        mode="lines+markers",
        name="Fix Sequence",
        line={"color": "#00f2fe", "width": 2},
        marker={"size": 4, "color": "#38bdf8"},
        hovertext=[f"Lat: {lat:.6f}<br>Lon: {lon:.6f}" for lat, lon in zip(df["latitude"], df["longitude"])],
        hoverinfo="text"
    ))

    # Mark Start and End
    fig.add_trace(go.Scatter(
        x=[df["longitude"].iloc[0]],
        y=[df["latitude"].iloc[0]],
        mode="markers",
        name="Start Epoch",
        marker={"size": 10, "color": "#10b981", "symbol": "diamond"}
    ))
    fig.add_trace(go.Scatter(
        x=[df["longitude"].iloc[-1]],
        y=[df["latitude"].iloc[-1]],
        mode="markers",
        name="Latest Epoch",
        marker={"size": 10, "color": "#f59e0b", "symbol": "square"}
    ))

    fig.update_layout(
        **CHART_THEME_LAYOUT,
        title={"text": title, "font": {"size": 12, "color": "#cbd5e1"}},
        xaxis_title="Longitude (deg)",
        yaxis_title="Latitude (deg)",
        legend={"orientation": "h", "y": 1.1, "x": 0.0}
    )
    st.plotly_chart(fig, use_container_width=True)


def render_velocity_timeline(df: pd.DataFrame):
    """
    Render speed / velocity timeline.
    """
    speed_col = "speed_kmh" if "speed_kmh" in df.columns else ("vel_kinematic" if "vel_kinematic" in df.columns else None)
    if df.empty or speed_col is None:
        st.info("NO DATA AVAILABLE FOR VELOCITY TIMELINE")
        return

    x_col = "timestamp" if "timestamp" in df.columns else ("timestamp_gnss" if "timestamp_gnss" in df.columns else df.index)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x_col] if isinstance(x_col, str) else x_col,
        y=df[speed_col],
        mode="lines",
        name=speed_col,
        line={"color": "#38bdf8", "width": 1.8},
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.08)"
    ))

    fig.update_layout(
        **CHART_THEME_LAYOUT,
        title={"text": f"VELOCITY TIMELINE ({speed_col})", "font": {"size": 12, "color": "#cbd5e1"}},
        xaxis_title="Time / Epoch",
        yaxis_title="Speed",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_satellite_timeline(df: pd.DataFrame):
    """
    Render satellite count timeline.
    """
    sat_col = "satellites_used" if "satellites_used" in df.columns else ("sat_count_tot" if "sat_count_tot" in df.columns else None)
    if df.empty or sat_col is None:
        st.info("NO DATA AVAILABLE FOR SATELLITE TIMELINE")
        return

    x_col = "timestamp" if "timestamp" in df.columns else ("timestamp_gnss" if "timestamp_gnss" in df.columns else df.index)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x_col] if isinstance(x_col, str) else x_col,
        y=df[sat_col],
        mode="lines+markers",
        name="Satellites",
        line={"color": "#10b981", "width": 1.8},
        marker={"size": 4}
    ))
    # Critical threshold reference line (e.g. min 4 satellites)
    fig.add_hline(y=4, line_dash="dash", line_color="#ef4444", annotation_text="Minimum 3D Fix (4 Sats)")

    fig.update_layout(
        **CHART_THEME_LAYOUT,
        title={"text": "SATELLITE COUNT TIMELINE", "font": {"size": 12, "color": "#cbd5e1"}},
        xaxis_title="Time / Epoch",
        yaxis_title="Satellites in Solution",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_dop_timeline(df: pd.DataFrame):
    """
    Render HDOP / VDOP dilution of precision timeline.
    """
    hdop_col = "hdop" if "hdop" in df.columns else ("HDOP" if "HDOP" in df.columns else None)
    vdop_col = "vdop" if "vdop" in df.columns else ("VDOP" if "VDOP" in df.columns else None)

    if df.empty or (hdop_col is None and vdop_col is None):
        st.info("NO DATA AVAILABLE FOR DOP TIMELINE")
        return

    x_col = "timestamp" if "timestamp" in df.columns else ("timestamp_gnss" if "timestamp_gnss" in df.columns else df.index)
    x_data = df[x_col] if isinstance(x_col, str) else x_col

    fig = go.Figure()
    if hdop_col:
        fig.add_trace(go.Scatter(
            x=x_data,
            y=df[hdop_col],
            mode="lines",
            name="HDOP",
            line={"color": "#f59e0b", "width": 1.8}
        ))
    if vdop_col:
        fig.add_trace(go.Scatter(
            x=x_data,
            y=df[vdop_col],
            mode="lines",
            name="VDOP",
            line={"color": "#a855f7", "width": 1.8}
        ))

    fig.add_hline(y=4.0, line_dash="dash", line_color="#f59e0b", annotation_text="HDOP Warning Limit (4.0)")
    fig.add_hline(y=8.0, line_dash="dash", line_color="#ef4444", annotation_text="HDOP Critical Limit (8.0)")

    fig.update_layout(
        **CHART_THEME_LAYOUT,
        title={"text": "DILUTION OF PRECISION (HDOP / VDOP)", "font": {"size": 12, "color": "#cbd5e1"}},
        xaxis_title="Time / Epoch",
        yaxis_title="DOP (Unitless)",
        legend={"orientation": "h", "y": 1.1, "x": 0.0}
    )
    st.plotly_chart(fig, use_container_width=True)


def render_feature_bar_chart(feature_records: List[Dict[str, Any]]):
    """
    Render 10-D canonical security feature status bar chart.
    """
    if not feature_records:
        st.info("NO DATA AVAILABLE FOR FEATURES")
        return

    names = [r["feature"] for r in feature_records]
    vals = [r["value"] for r in feature_records]
    statuses = [r["status"] for r in feature_records]

    colors = []
    for s in statuses:
        if s == "CRITICAL":
            colors.append("#ef4444")
        elif s == "WARNING":
            colors.append("#f59e0b")
        else:
            colors.append("#10b981")

    fig = go.Figure(go.Bar(
        x=names,
        y=vals,
        marker={"color": colors},
        hovertext=[f"{r['name']}: {r['value']} {r['unit']} [{r['status']}]" for r in feature_records],
        hoverinfo="text"
    ))

    fig.update_layout(
        **CHART_THEME_LAYOUT,
        title={"text": "CANONICAL 10-D FEATURE MAGNITUDES & INTEGRITY STATUS", "font": {"size": 12, "color": "#cbd5e1"}},
        xaxis_title="Canonical Feature",
        yaxis_title="Value",
        xaxis={"tickangle": -30}
    )
    st.plotly_chart(fig, use_container_width=True)
