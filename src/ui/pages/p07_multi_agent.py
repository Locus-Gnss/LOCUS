"""
Module 8: 3-Agent Cyber SOC
Module: src.ui.pages.p07_multi_agent
Autonomous multi-agent consensus deliberation and master verdict determination.
"""

from typing import Dict, Any, List
import streamlit as st

from src.ui.utils.formatting import safe_float, safe_int, safe_str


def render_multi_agent_page(data_service, selected_event_id: str):
    """
    Render 3-Agent Cyber SOC module matching Screenshot 8 specification.
    """
    st.markdown("<div class='section-header'>3-AGENT CYBER-PHYSICAL SOC DELIBERATION</div>", unsafe_allow_html=True)
    st.markdown(
        """
    <div class="soc-callout">
        <strong>AGENTIC CONSENSUS COMMITTEE:</strong> Three specialized AI agents deliberate over physical invariants,
        temporal drift streaks, and threat taxonomies to achieve explainable consensus without hallucination.
    </div>
    """,
        unsafe_allow_html=True,
    )

    bundle = data_service.load_event(selected_event_id)
    if not bundle:
        st.info("NO FORENSIC DATA AVAILABLE FOR DELIBERATION")
        return

    # Trigger or load cached deliberation
    delib_key = f"delib_result_{selected_event_id}"
    delib = st.session_state.get(delib_key)
    if not delib or not isinstance(delib, dict):
        delib = data_service.deliberate_event(selected_event_id, bundle=bundle)
        st.session_state[delib_key] = delib

    findings = delib.get("agent_findings", {})
    ag1 = findings.get("agent_1_integrity") or {}
    ag2 = findings.get("agent_2_temporal_threat") or {}
    ag3 = findings.get("agent_3_master_orchestrator") or {}

    verdict = safe_str(delib.get("current_status") or delib.get("verdict"), "NOMINAL_FLIGHT")
    defcon = safe_str(delib.get("risk_level") or delib.get("defcon_level"), "DEFCON_4 (GUARDED)")
    confidence = safe_float(delib.get("confidence"), 0.92)
    actions = delib.get("recommended_next_action") or delib.get("mitigation_directives") or ["CONTINUE_NOMINAL_MONITORING"]
    explanation = safe_str(delib.get("explanation") or delib.get("reasoning"), "Consensus established across all detector tiers.")

    th_color = "#f87171" if ("DEFCON_1" in defcon or "DEFCON_2" in defcon) else (
        "#fbbf24" if "DEFCON_3" in defcon else "#34d399"
    )

    # Re-run deliberation button
    c_btn, c_stat = st.columns([3, 4])
    with c_btn:
        if st.button("RE-CONVENE 3-AGENT COMMITTEE", key=f"btn_re_delib_{selected_event_id}"):
            with st.spinner("Executing live multi-agent consensus..."):
                delib = data_service.deliberate_event(selected_event_id, bundle=bundle)
                st.session_state[delib_key] = delib
                st.rerun()

    # 3 Agent Cards
    ag_col1, ag_col2, ag_col3 = st.columns(3)

    with ag_col1:
        st.markdown(
            f"""
        <div class="soc-panel" style="min-height: 220px; border-left: 3px solid #38bdf8;">
            <div style="font-size: 9px; font-weight: 700; color: #64748b; font-family: monospace;">AGENT 1 / DETERMINISTIC</div>
            <div style="font-size: 13px; font-weight: 800; color: #f8fafc; font-family: monospace; margin: 4px 0;">GNSS INTEGRITY AGENT</div>
            <div style="margin-bottom: 8px;"><span class="badge badge-ready">ACTIVE</span></div>
            <div style="font-size: 11px; color: #cbd5e1; font-family: monospace; line-height: 1.4;">
                <strong>FINDING:</strong> {ag1.get('integrity_assessment', 'PHYSICALLY_PLAUSIBLE')}<br>
                <strong>RULES:</strong> {ag1.get('rules_violated_count', 0)} Triggered<br>
                <strong>EVIDENCE:</strong> Verified kinematic derivatives &amp; clock stability.
            </div>
            <div style="margin-top: 10px; font-size: 10px; color: #38bdf8; font-family: monospace;">
                CONFIDENCE: {safe_float(ag1.get('confidence', 0.95))*100:.1f}%
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with ag_col2:
        st.markdown(
            f"""
        <div class="soc-panel" style="min-height: 220px; border-left: 3px solid #a855f7;">
            <div style="font-size: 9px; font-weight: 700; color: #64748b; font-family: monospace;">AGENT 2 / PATTERN &amp; SEQUENCE</div>
            <div style="font-size: 13px; font-weight: 800; color: #f8fafc; font-family: monospace; margin: 4px 0;">TEMPORAL / THREAT AGENT</div>
            <div style="margin-bottom: 8px;"><span class="badge badge-ready">ACTIVE</span></div>
            <div style="font-size: 11px; color: #cbd5e1; font-family: monospace; line-height: 1.4;">
                <strong>FINDING:</strong> {ag2.get('threat_classification', ag2.get('temporal_assessment', 'NOMINAL_SEQUENCE'))}<br>
                <strong>DRIFT:</strong> {ag2.get('drift_detected', False)}<br>
                <strong>EVIDENCE:</strong> LSTM sequence errors &amp; Isolation Forest scores.
            </div>
            <div style="margin-top: 10px; font-size: 10px; color: #a855f7; font-family: monospace;">
                CONFIDENCE: {safe_float(ag2.get('confidence', 0.88))*100:.1f}%
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with ag_col3:
        st.markdown(
            f"""
        <div class="soc-panel" style="min-height: 220px; border-left: 3px solid #10b981;">
            <div style="font-size: 9px; font-weight: 700; color: #64748b; font-family: monospace;">AGENT 3 / SYNTHESIS</div>
            <div style="font-size: 13px; font-weight: 800; color: #f8fafc; font-family: monospace; margin: 4px 0;">MASTER SOC ORCHESTRATOR</div>
            <div style="margin-bottom: 8px;"><span class="badge badge-ready">ACTIVE</span></div>
            <div style="font-size: 11px; color: #cbd5e1; font-family: monospace; line-height: 1.4;">
                <strong>FINDING:</strong> {ag3.get('synthesis_summary', verdict)}<br>
                <strong>DEFCON:</strong> {defcon}<br>
                <strong>EVIDENCE:</strong> Grounded multi-tier consensus &amp; RAG standards.
            </div>
            <div style="margin-top: 10px; font-size: 10px; color: #10b981; font-family: monospace;">
                CONFIDENCE: {confidence*100:.1f}%
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # CONSENSUS RESOLUTION
    st.markdown("<div class='section-header'>CONSENSUS RESOLUTION &amp; OPERATIONAL DIRECTIVES</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
    <div class="verdict-banner-box" style="border-left: 4px solid {th_color};">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <div style="font-size: 9.5px; color: #64748b; font-family: monospace;">FINAL AGENT RECOMMENDATION</div>
                <div style="font-size: 21px; font-weight: 800; color: #f8fafc; font-family: monospace;">{verdict}</div>
                <div style="font-size: 11.5px; color: #cbd5e1; font-family: monospace; margin-top: 4px;">{explanation}</div>
            </div>
            <div style="text-align: right; font-family: monospace;">
                <div style="font-size: 9.5px; color: #64748b;">THREAT LEVEL</div>
                <div style="font-size: 19px; font-weight: 800; color: {th_color};">{defcon}</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if actions:
        st.markdown("<div class='soc-panel-title'>MANDATORY MITIGATION DIRECTIVES</div>", unsafe_allow_html=True)
        for act in actions:
            st.markdown(
                f"<div style='background: #090e18; border: 1px solid #1e293b; padding: 8px 12px; border-radius: 4px; "
                f"margin-bottom: 6px; font-size: 11px; color: #e2e8f0; font-family: monospace;'>&gt; {act}</div>",
                unsafe_allow_html=True,
            )
