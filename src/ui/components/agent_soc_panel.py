"""
LOCUS 3-Agent Security Operations Center Panel
Module: src.ui.components.agent_soc_panel
"""

import streamlit as st


def render_agent_soc_panel(agent_findings: dict):
    """
    Render autonomous 3-agent deliberative hierarchy and visual consensus workflow:
    Telemetry -> Agent 1 -> Agent 2 -> Master SOC Orchestrator -> Final Verdict.
    """
    st.subheader("🤖 Autonomous 3-Agent Security Intelligence Hierarchy")
    st.caption("Collaborative Deliberation • Physics-First Priority • Multi-Epoch Sequence Tracking • Binding DEFCON Rating")

    # Visual Workflow Diagram
    st.markdown(
        """
        <div style='background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-bottom: 20px;'>
            <div style='font-size: 13px; font-weight: 700; color: #94a3b8; margin-bottom: 8px;'>DELIBERATIVE WORKFLOW:</div>
            <div style='display: flex; justify-content: space-between; align-items: center; font-family: monospace; font-size: 13px; flex-wrap: wrap; gap: 8px;'>
                <span class='provenance-tag'>1. Telemetry & Evidence</span>
                <span>➔</span>
                <span class='provenance-tag' style='background-color: #064e3b; color: #34d399;'>2. Agent 1: Integrity</span>
                <span>➔</span>
                <span class='provenance-tag' style='background-color: #78350f; color: #fbbf24;'>3. Agent 2: Temporal Threat</span>
                <span>➔</span>
                <span class='provenance-tag' style='background-color: #1e1b4b; color: #a5b4fc;'>4. Regulatory RAG</span>
                <span>➔</span>
                <span class='provenance-tag' style='background-color: #7f1d1d; color: #f87171;'>5. Master SOC Orchestrator</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    a1 = agent_findings.get("agent_1_integrity", {})
    a2 = agent_findings.get("agent_2_temporal_threat", {})
    a3 = agent_findings.get("agent_3_master_soc", {})

    # Agent 1: GNSS Integrity Agent
    st.markdown("#### 🛡️ AGENT 1 — GNSS Integrity Agent")
    with st.container():
        a1_status = a1.get("integrity_assessment", "NOMINAL")
        badge1 = "badge-normal" if "NOMINAL" in a1_status else "badge-critical"
        st.markdown(
            f"""
            <div class='agent-container' style='border-left: 4px solid #10b981;'>
                <div style='display: flex; justify-content: space-between;'>
                    <b>Assessment:</b> <span class='{badge1}'>{a1_status}</span>
                    <span>Confidence: <b>{a1.get('confidence', 1.0)*100:.1f}%</b></span>
                </div>
                <div style='margin-top: 8px; color: #cbd5e1;'>
                    <b>Role:</b> Physical Invariant Verification, Fix Integrity, Geometry Degradation & Constellation Churn<br/>
                    <b>Kinematic Health:</b> {a1.get('kinematic_health', 1.0)*100:.1f}% | 
                    <b>Geometry Health:</b> {a1.get('geometry_health', 1.0)*100:.1f}% | 
                    <b>Discard Recommended:</b> <code>{a1.get('discard_recommended')}</code>
                </div>
                <div style='margin-top: 8px; background: #111827; padding: 8px; border-radius: 4px; font-size: 13px;'>
                    <b>Integrity Explanation:</b> {a1.get('explanation', 'Kinematic bounds nominal.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Agent 2: Temporal / Threat Agent
    st.markdown("#### ⏱️ AGENT 2 — Temporal / Threat Agent")
    with st.container():
        a2_status = a2.get("threat_classification", a2.get("temporal_assessment", "BENIGN"))
        badge2 = "badge-normal" if "BENIGN" in a2_status else "badge-warning"
        st.markdown(
            f"""
            <div class='agent-container' style='border-left: 4px solid #f59e0b;'>
                <div style='display: flex; justify-content: space-between;'>
                    <b>Assessment:</b> <span class='{badge2}'>{a2_status}</span>
                    <span>Confidence: <b>{a2.get('confidence', 1.0)*100:.1f}%</b></span>
                </div>
                <div style='margin-top: 8px; color: #cbd5e1;'>
                    <b>Role:</b> Sequence Persistence Tracking, LSTM Reconstruction Error, Multi-Detector Convergence<br/>
                    <b>Persistence Streak:</b> {a2.get('persistence_count', a2.get('persistence_streak', 0))} epoch(s) | 
                    <b>Convergence:</b> {a2.get('detector_convergence', 0.0)*100:.1f}% | 
                    <b>Is Persistent:</b> <code>{a2.get('persistence_count', 0) >= 3 or a2.get('is_persistent', False)}</code>
                </div>
                <div style='margin-top: 8px; background: #111827; padding: 8px; border-radius: 4px; font-size: 13px;'>
                    <b>Threat Explanation:</b> {a2.get('explanation', a2.get('pattern_description', 'No temporal drift detected.'))}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Agent 3: Master SOC Orchestrator
    st.markdown("#### 👑 AGENT 3 — Master SOC Orchestrator")
    with st.container():
        a3_status = a3.get("status", "NOMINAL")
        a3_risk = a3.get("risk_level", "DEFCON_5")
        badge3 = "badge-normal" if "5" in a3_risk else ("badge-warning" if "3" in a3_risk or "4" in a3_risk else "badge-critical")
        st.markdown(
            f"""
            <div class='agent-container' style='border-left: 4px solid #ef4444;'>
                <div style='display: flex; justify-content: space-between;'>
                    <b>Binding Verdict:</b> <span class='{badge3}'>{a3_status} ({a3_risk})</span>
                    <span>Consensus Confidence: <b>{a3.get('confidence', 1.0)*100:.1f}%</b></span>
                </div>
                <div style='margin-top: 8px; color: #cbd5e1;'>
                    <b>Role:</b> Consensus Synthesis, Invariant Priority Enforcement, Conflict Resolution, DEFCON Assignment<br/>
                    <b>Consensus Ratio:</b> {a3.get('consensus_ratio', 1.0)*100:.1f}% | 
                    <b>Conflict Resolved:</b> <code>{a3.get('conflict_resolved', True)}</code>
                </div>
                <div style='margin-top: 8px; background: #111827; padding: 8px; border-radius: 4px; font-size: 13px;'>
                    <b>Executive Summary:</b> {a3.get('summary', 'Consensus achieved across multi-detector quad.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
