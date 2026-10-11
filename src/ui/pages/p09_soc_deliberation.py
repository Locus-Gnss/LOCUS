"""
Page 9: SOC Deliberation
Module: src.ui.pages.p09_soc_deliberation
Executes multi-agent consensus deliberation and DEFCON determination for a selected forensic event.
Displays:
- DECISION
- THREAT LEVEL
- CONFIDENCE
- SUPPORTING EVIDENCE
- AGENT FINDINGS
- REASONING / CONTEXT
Zero fabricated results, strictly no emojis.
"""

from typing import Dict, Any, List
import streamlit as st

from src.ui.utils.state import get_selected_event, set_selected_event
from src.ui.utils.formatting import safe_float, safe_int, safe_str


def render_soc_deliberation_page(data_service):
    """
    Render SOC Deliberation Page.
    """
    st.markdown("<div class='section-header'>SOC MULTI-AGENT DELIBERATION CONSOLE</div>", unsafe_allow_html=True)
    st.markdown(
        """
    <div class="soc-callout">
        <strong>DELIBERATION ENGINE:</strong>
        Synthesizes raw physical invariant rule checks, unsupervised Isolation Forest anomaly scores,
        temporal autoencoder reconstruction errors, and regulatory RAG citations into an authoritative Master SOC verdict.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 1. Event Selector (Preserves Global State)
    events = data_service.get_events()
    event_ids = [e["event_id"] for e in events] if events else ["NO DATA AVAILABLE"]

    current_event = get_selected_event()
    if "delib_event_select" not in st.session_state:
        st.session_state["delib_event_select"] = current_event if current_event in event_ids else (event_ids[0] if event_ids else "")
    elif st.session_state["delib_event_select"] not in event_ids and event_ids:
        st.session_state["delib_event_select"] = event_ids[0]

    def on_delib_event_pick():
        picked = st.session_state.get("delib_event_select")
        if picked:
            set_selected_event(picked)

    c_sel1, c_sel2 = st.columns([3, 1])
    with c_sel1:
        chosen_event = st.selectbox(
            "Select Forensic Event to Deliberate:",
            options=event_ids,
            key="delib_event_select",
            on_change=on_delib_event_pick
        )
    with c_sel2:
        run_btn = st.button("Run SOC Deliberation", key="btn_run_delib")

    if chosen_event == "NO DATA AVAILABLE":
        st.info("NO DATA AVAILABLE FOR DELIBERATION")
        return

    # Load bundle
    bundle = data_service.load_event(chosen_event)
    if not bundle:
        st.warning(f"Forensic bundle for '{chosen_event}' not found.")
        return

    # Deliberation Execution with Per-Event Session Cache
    cache_key = f"delib_result_{chosen_event}"
    result = None

    if run_btn:
        with st.spinner(f"Executing 3-agent deliberation for {chosen_event}..."):
            result = data_service.deliberate_event(chosen_event, bundle=bundle)
            st.session_state[cache_key] = result
    elif cache_key in st.session_state:
        result = st.session_state[cache_key]

    if not result or not isinstance(result, dict):
        st.info(f"Click 'Run SOC Deliberation' above to convene the 3-Agent SOC on event {chosen_event}.")
        return

    st.markdown("<hr style='border-color: #1e293b; margin: 18px 0;'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>MASTER SOC VERDICT & CONSENSUS RATING</div>", unsafe_allow_html=True)

    # Extract Fields
    decision = safe_str(result.get("current_status") or result.get("verdict"), "VERDICT DECLARED")
    threat_level = safe_str(result.get("risk_level") or result.get("defcon_level"), "DEFCON_3")
    confidence = safe_float(result.get("confidence"), 0.85)
    explanation = safe_str(result.get("explanation") or result.get("reasoning"), "")
    agent_findings = result.get("agent_findings") if isinstance(result.get("agent_findings"), dict) else {}
    evidence_list = result.get("evidence") if isinstance(result.get("evidence"), list) else []
    actions = result.get("recommended_next_action") if isinstance(result.get("recommended_next_action"), list) else []

    # Top Verdict Metrics
    v1, v2, v3, v4 = st.columns(4)
    with v1:
        st.metric("FINAL DECISION", decision)
    with v2:
        th_color = "#f87171" if "DEFCON_1" in threat_level or "CRITICAL" in threat_level else (
            "#fbbf24" if "DEFCON_2" in threat_level or "DEFCON_3" in threat_level else "#34d399"
        )
        st.markdown(
            f"""
        <div class="kpi-card" style="padding: 10px;">
            <div class="kpi-label">THREAT LEVEL</div>
            <div class="kpi-val" style="color: {th_color}; font-size: 18px;">{threat_level}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with v3:
        st.metric("CONFIDENCE SCORE", f"{confidence * 100:.1f}%")
    with v4:
        st.metric("EVIDENCE ARTIFACTS", str(len(evidence_list)))

    # REASONING & MASTER SOC CONTEXT
    st.markdown("<div class='soc-panel-title'>REASONING / CONTEXTUAL SYNTHESIS</div>", unsafe_allow_html=True)
    if explanation:
        st.markdown(
            f"""
        <div class="soc-panel" style="font-size: 13px; line-height: 1.6; color: #f1f5f9; border-left: 3px solid #00f2fe;">
            {explanation}
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.info("NO DETAILED EXPLANATION GENERATED")

    # AGENT FINDINGS BREAKDOWN
    st.markdown("<div class='soc-panel-title'>INDIVIDUAL AGENT FINDINGS</div>", unsafe_allow_html=True)
    if agent_findings:
        f_cols = st.columns(len(agent_findings))
        for idx, (ag_name, finding) in enumerate(agent_findings.items()):
            col_target = f_cols[idx] if idx < len(f_cols) else st
            with col_target:
                st.markdown(
                    f"""
                <div class="soc-panel">
                    <div style="font-weight: 700; color: #38bdf8; font-size: 11px; margin-bottom: 6px;">
                        {ag_name.replace('_', ' ').upper()}
                    </div>
                """,
                    unsafe_allow_html=True,
                )
                if isinstance(finding, dict):
                    for fk, fv in finding.items():
                        st.markdown(f"<div style='font-size: 11px;'><strong>{fk}:</strong> {fv}</div>", unsafe_allow_html=True)
                else:
                    st.write(str(finding))
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("NO INDIVIDUAL AGENT FINDINGS RETURNED")

    # MANDATORY NEXT ACTIONS & MITIGATIONS
    st.markdown("<div class='soc-panel-title'>MANDATORY NEXT ACTIONS & MITIGATION DIRECTIVES</div>", unsafe_allow_html=True)
    if actions:
        for a in actions:
            st.markdown(
                f"""
            <div style="background: #0d1527; border: 1px solid #1e293b; padding: 8px 12px; border-radius: 4px; margin-bottom: 6px; font-size: 12px; color: #e2e8f0; font-family: monospace;">
                &gt; {a}
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.write("No mandatory directives required.")
