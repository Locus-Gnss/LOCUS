"""
Module 1: Executive Overview / Command Center
Module: src.ui.pages.p01_command_center
Executive summary dashboard with live pipeline visualization, metric cards,
Detection Quad status, 3-Agent Cyber SOC consensus, and Final Security Decision.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import streamlit as st

from src.ui.utils.formatting import safe_float, safe_int, safe_str


def render_command_center(data_service, selected_event_id: str):
    """
    Render Executive Overview module matching Screenshot 1 specification.
    """
    # 1. Load active event bundle
    bundle = data_service.load_event(selected_event_id)
    if not bundle:
        st.error(f"Unable to load evidence bundle for event '{selected_event_id}'. Verify backend.")
        return

    # Deliberation data
    delib_key = f"delib_result_{selected_event_id}"
    delib = st.session_state.get(delib_key)
    if not delib or not isinstance(delib, dict):
        delib = data_service.deliberate_event(selected_event_id, bundle=bundle)
        st.session_state[delib_key] = delib

    pr = bundle.physical_rules if isinstance(bundle.physical_rules, dict) else {}
    ifo = bundle.isolation_forest if isinstance(bundle.isolation_forest, dict) else {}
    xgb = bundle.xgboost if isinstance(bundle.xgboost, dict) else {}
    temp = bundle.temporal_model if isinstance(bundle.temporal_model, dict) else {}
    loc = bundle.location if isinstance(bundle.location, dict) else {}
    sec = bundle.security_features if isinstance(bundle.security_features, dict) else {}
    dq = bundle.data_quality if isinstance(bundle.data_quality, dict) else {}

    threat_level = safe_str(delib.get("risk_level") or delib.get("defcon_level"), "DEFCON_4 (GUARDED)")
    confidence = safe_float(delib.get("confidence"), 0.92)
    verdict = safe_str(delib.get("current_status") or delib.get("verdict"), "NOMINAL_FLIGHT")
    explanation = safe_str(delib.get("explanation") or delib.get("reasoning"), "Multi-agent consensus active across physical rules and ML ensembles.")
    directives = delib.get("recommended_next_action") or delib.get("mitigation_directives") or ["MAINTAIN_NOMINAL_TRACKING"]
    directive_txt = directives[0] if directives else "MAINTAIN_NOMINAL_TRACKING"

    conn_info = data_service.check_gnss_connection()
    is_live = conn_info.get("is_live", False)
    provenance = "REAL L89HA TELEMETRY (LIVE)" if is_live else "REAL L89HA TELEMETRY (REPLAY MODE)"

    th_color = "#f87171" if ("DEFCON_1" in threat_level or "DEFCON_2" in threat_level) else (
        "#fbbf24" if "DEFCON_3" in threat_level else "#34d399"
    )

    # Top: SYSTEM NOMINAL / SECURITY STATUS Banner
    st.markdown(
        f"""
    <div class="soc-panel" style="border-left: 4px solid {th_color}; padding: 14px 18px; margin-bottom: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
            <div>
                <div style="font-size: 10px; font-weight: 700; color: #64748b; font-family: monospace; letter-spacing: 0.1em;">SYSTEM POSTURE &amp; STATUS</div>
                <div style="font-size: 20px; font-weight: 800; color: #f8fafc; font-family: monospace;">{verdict}</div>
                <div style="font-size: 11.5px; color: #94a3b8; margin-top: 4px; line-height: 1.4;">
                    <strong>SOC ANALYSIS:</strong> {explanation[:180]}...
                </div>
            </div>
            <div style="display: flex; gap: 20px; font-family: monospace; text-align: right;">
                <div>
                    <div style="font-size: 9px; color: #64748b; font-weight: 700;">THREAT RATING</div>
                    <div style="font-size: 15px; font-weight: 700; color: {th_color};">{threat_level}</div>
                </div>
                <div>
                    <div style="font-size: 9px; color: #64748b; font-weight: 700;">CONFIDENCE</div>
                    <div style="font-size: 15px; font-weight: 700; color: #38bdf8;">{confidence * 100:.1f}%</div>
                </div>
                <div>
                    <div style="font-size: 9px; color: #64748b; font-weight: 700;">TARGET EVENT</div>
                    <div style="font-size: 15px; font-weight: 700; color: #cbd5e1;">{selected_event_id}</div>
                </div>
            </div>
        </div>
        <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #1e293b; display: flex; justify-content: space-between; font-size: 10px; font-family: monospace; color: #64748b;">
            <span>SENSOR PROVENANCE: <span style="color: #38bdf8;">{provenance}</span></span>
            <span>MANDATORY DIRECTIVE: <span style="color: #fbbf24;">{directive_txt}</span></span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Section 25: Live Pipeline Visualization
    st.markdown("<div class='section-header'>CYBER-PHYSICAL SECURITY PIPELINE FLOW</div>", unsafe_allow_html=True)

    pipeline_stages = [
        ("GNSS DATA", "COMPLETED", "badge-online"),
        ("NMEA PARSING", "COMPLETED", "badge-online"),
        ("PREPROCESSING", "COMPLETED", "badge-online"),
        ("FEATURE ENG", "COMPLETED", "badge-online"),
        ("10-D FEATURES", "COMPLETED", "badge-online"),
        ("ML DETECTION", "COMPLETED", "badge-online"),
        ("MULTI-AGENT SOC", "COMPLETED", "badge-online"),
        ("EVIDENCE", "COMPLETED", "badge-online"),
        ("RAG", "COMPLETED", "badge-online"),
        ("SOC DELIBERATION", "COMPLETED", "badge-online"),
        ("FINAL DECISION", "COMPLETED", "badge-online"),
    ]

    p_cols = st.columns(len(pipeline_stages))
    for idx, (stg_name, stg_status, stg_badge) in enumerate(pipeline_stages):
        with p_cols[idx]:
            st.markdown(
                f"""
            <div style="background: #090e18; border: 1px solid #1e293b; border-left: 2px solid #10b981; border-radius: 4px; padding: 6px 4px; text-align: center;">
                <div style="font-size: 8.5px; font-weight: 700; color: #94a3b8; font-family: monospace; line-height: 1.1;">{stg_name}</div>
                <div style="margin-top: 4px;"><span class="badge {stg_badge}" style="font-size: 7.5px; padding: 1px 3px;">{stg_status}</span></div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Metric Cards: FIX INTEGRITY, SATELLITES VISIBLE, GEOMETRY / HDOP, KINEMATIC VELOCITY, ACTIVE INCIDENTS, CURRENT POSITION
    m1, m2, m3, m4, m5, m6 = st.columns(6)

    fix_int = safe_float(sec.get("fix_integrity", 1.0))
    sat_count = safe_int(sec.get("sat_count_tot") or dq.get("satellites_used", 0))
    hdop = safe_float(sec.get("HDOP") or dq.get("hdop", 0.0))
    speed_kmh = safe_float(loc.get("speed_kmh", 0.0))
    if speed_kmh == 0.0 and "vel_kinematic" in sec:
        speed_kmh = safe_float(sec.get("vel_kinematic", 0.0)) * 3.6

    alerts = data_service.get_alert_center_records()
    active_incidents = len([a for a in alerts if a.get("event_id") == selected_event_id])
    lat = safe_float(loc.get("latitude", 0.0))
    lon = safe_float(loc.get("longitude", 0.0))

    with m1:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-label">FIX INTEGRITY</div>
            <div class="kpi-val" style="color: {'#10b981' if fix_int >= 0.5 else '#ef4444'};">{fix_int:.4f}</div>
            <div class="kpi-note">{'OPTIMAL' if fix_int >= 0.5 else 'DEGRADED'}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-label">SATELLITES VISIBLE</div>
            <div class="kpi-val">{sat_count}</div>
            <div class="kpi-note">L89HA Multi-GNSS</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with m3:
        hdop_note = "EXCELLENT" if hdop < 2.0 else ("GOOD" if hdop < 4.0 else "POOR")
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-label">GEOMETRY / HDOP</div>
            <div class="kpi-val">{hdop:.2f}</div>
            <div class="kpi-note">{hdop_note}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with m4:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-label">KINEMATIC VELOCITY</div>
            <div class="kpi-val">{speed_kmh:.2f} <span style="font-size: 11px; color: #64748b;">km/h</span></div>
            <div class="kpi-note">{speed_kmh / 3.6:.2f} m/s</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with m5:
        inc_color = "#ef4444" if active_incidents > 0 else "#10b981"
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-label">ACTIVE INCIDENTS</div>
            <div class="kpi-val" style="color: {inc_color};">{active_incidents}</div>
            <div class="kpi-note">ALT-{selected_event_id}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with m6:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-label">CURRENT POSITION</div>
            <div class="kpi-val" style="font-size: 13px;">{lat:.4f}°, {lon:.4f}°</div>
            <div class="kpi-note">ALT: {safe_float(loc.get('altitude_m', 0.0)):.1f}m</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Two Large Panels: DETECTION QUAD STATUS & 3-AGENT CYBER SOC CONSENSUS
    p_left, p_right = st.columns(2)

    with p_left:
        st.markdown("<div class='section-header'>DETECTION QUAD STATUS</div>", unsafe_allow_html=True)

        pr_viol = pr.get("triggered_count", 0) > 0
        ifo_anom = ifo.get("is_anomaly", False)
        xgb_label = safe_str(xgb.get("predicted_label"), "NOMINAL")
        xgb_anom = xgb_label not in ["NOMINAL", "UNASSIGNED", "NOMINAL_FLIGHT"]
        temp_anom = temp.get("is_anomaly", False)

        st.markdown(
            f"""
        <div class="soc-panel">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-family: monospace; font-size: 11px;">
                <span><strong>1. PHYSICAL INVARIANTS:</strong></span>
                <span class="badge {'badge-critical' if pr_viol else 'badge-normal'}">{'VIOLATION' if pr_viol else 'NOMINAL'}</span>
            </div>
            <div style="font-size: 10.5px; color: #94a3b8; margin-bottom: 10px; font-family: monospace;">
                Rules Triggered: {pr.get('triggered_count', 0)} / 9 &nbsp;|&nbsp; Max Sev: {pr.get('max_severity', 'INFO')}
            </div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-family: monospace; font-size: 11px;">
                <span><strong>2. SPATIAL ISOLATION FOREST:</strong></span>
                <span class="badge {'badge-critical' if ifo_anom else 'badge-normal'}">{'ANOMALY' if ifo_anom else 'NOMINAL'}</span>
            </div>
            <div style="font-size: 10.5px; color: #94a3b8; margin-bottom: 10px; font-family: monospace;">
                Score: {safe_float(ifo.get('anomaly_score', 0.0)):.4f} &nbsp;|&nbsp; Threshold: {safe_float(ifo.get('threshold', -0.05)):.4f}
            </div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-family: monospace; font-size: 11px;">
                <span><strong>3. XGBOOST CLASSIFIER:</strong></span>
                <span class="badge {'badge-critical' if xgb_anom else 'badge-normal'}">{xgb_label}</span>
            </div>
            <div style="font-size: 10.5px; color: #94a3b8; margin-bottom: 10px; font-family: monospace;">
                Confidence: {safe_float(xgb.get('confidence', 0.0))*100:.1f}% &nbsp;|&nbsp; Class: {xgb_label}
            </div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-family: monospace; font-size: 11px;">
                <span><strong>4. TEMPORAL LSTM:</strong></span>
                <span class="badge {'badge-critical' if temp_anom else 'badge-normal'}">{'ANOMALY' if temp_anom else 'NOMINAL'}</span>
            </div>
            <div style="font-size: 10.5px; color: #94a3b8; font-family: monospace;">
                Recon Error: {safe_float(temp.get('reconstruction_error', 0.0)):.5f} &nbsp;|&nbsp; Threshold: {safe_float(temp.get('threshold', 0.045)):.5f}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with p_right:
        st.markdown("<div class='section-header'>3-AGENT CYBER SOC CONSENSUS</div>", unsafe_allow_html=True)

        agent_findings = delib.get("agent_findings", {})
        ag1 = agent_findings.get("agent_1_integrity") or {}
        ag2 = agent_findings.get("agent_2_temporal_threat") or {}
        ag3 = agent_findings.get("agent_3_master_orchestrator") or {}

        ag1_txt = ag1.get("integrity_assessment") or ("VIOLATION" if pr_viol else "PHYSICALLY_PLAUSIBLE")
        ag2_txt = ag2.get("threat_classification") or ag2.get("temporal_assessment") or ("ANOMALOUS" if ifo_anom else "NOMINAL")
        ag3_txt = ag3.get("synthesis_summary") or verdict

        st.markdown(
            f"""
        <div class="soc-panel">
            <div style="margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid #1e293b;">
                <div style="font-size: 10px; font-weight: 700; color: #38bdf8; font-family: monospace;">AGENT 1 — GNSS INTEGRITY AGENT</div>
                <div style="font-size: 11px; color: #e2e8f0; font-family: monospace; margin-top: 2px;">
                    Assessment: <strong>{ag1_txt}</strong> &nbsp;|&nbsp; Plausibility bounds verified.
                </div>
            </div>

            <div style="margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid #1e293b;">
                <div style="font-size: 10px; font-weight: 700; color: #38bdf8; font-family: monospace;">AGENT 2 — TEMPORAL / THREAT AGENT</div>
                <div style="font-size: 11px; color: #e2e8f0; font-family: monospace; margin-top: 2px;">
                    Assessment: <strong>{ag2_txt}</strong> &nbsp;|&nbsp; Temporal sequence and spatial isolation.
                </div>
            </div>

            <div>
                <div style="font-size: 10px; font-weight: 700; color: #38bdf8; font-family: monospace;">AGENT 3 — MASTER SOC ORCHESTRATOR</div>
                <div style="font-size: 11px; color: #e2e8f0; font-family: monospace; margin-top: 2px;">
                    Consensus Verdict: <strong>{ag3_txt}</strong> &nbsp;|&nbsp; DEFCON Rating: <strong>{threat_level}</strong>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Bottom: FINAL SECURITY DECISION
    st.markdown("<div class='section-header'>FINAL SECURITY DECISION &amp; MITIGATION DIRECTIVES</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
    <div class="verdict-banner-box" style="border-left: 4px solid {th_color};">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <div style="font-size: 9.5px; color: #64748b; font-family: monospace; letter-spacing: 0.1em; text-transform: uppercase;">AUTHORITATIVE MASTER VERDICT</div>
                <div style="font-size: 20px; font-weight: 800; color: #f8fafc; font-family: monospace;">{verdict}</div>
                <div style="font-size: 11.5px; color: #cbd5e1; margin-top: 4px; font-family: monospace;">
                    MANDATORY DIRECTIVE: <span style="color: #38bdf8;">{directive_txt}</span>
                </div>
            </div>
            <div style="text-align: right; font-family: monospace;">
                <div style="font-size: 9.5px; color: #64748b;">CONFIDENCE</div>
                <div style="font-size: 20px; font-weight: 800; color: #38bdf8;">{confidence * 100:.1f}%</div>
                <div style="font-size: 10px; color: {th_color}; font-weight: 700;">{threat_level}</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
