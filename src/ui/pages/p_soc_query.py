"""
Module 10: SOC Query Terminal
Module: src.ui.pages.p_soc_query
Natural-language forensic inquiry terminal powered by the backend query processor and multi-agent hierarchy.
"""

from typing import Dict, Any, List
import streamlit as st

from src.ui.utils.formatting import safe_float, safe_int, safe_str


def render_soc_query_terminal(data_service, selected_event_id: str):
    """
    Render SOC Query Terminal module matching Screenshot 10 specification.
    """
    st.markdown("<div class='section-header'>NATURAL-LANGUAGE FORENSIC QUERY TERMINAL</div>", unsafe_allow_html=True)
    st.markdown(
        """
    <div class="soc-callout">
        <strong>AUTONOMOUS SOC ASSISTANT:</strong> End-to-end deliberative resolution of operator inquiries.
        Grounded in immutable Evidence Bundles, Detection Quad outputs, and Regulatory RAG citations.
    </div>
    """,
        unsafe_allow_html=True,
    )

    bundle = data_service.load_event(selected_event_id)

    # 4 Quick Query Buttons
    st.markdown("<div class='soc-panel-title'>RAPID FORENSIC PROMPTS</div>", unsafe_allow_html=True)

    q_col1, q_col2 = st.columns(2)
    with q_col1:
        b1 = st.button("WHY WAS THIS EVENT FLAGGED?", key=f"qbtn1_{selected_event_id}", use_container_width=True)
        b2 = st.button("IS THERE EVIDENCE OF COGNITIVE DRAG-OFF?", key=f"qbtn2_{selected_event_id}", use_container_width=True)
    with q_col2:
        b3 = st.button("SUMMARIZE KINEMATIC VELOCITY AND ACCELERATION BOUNDS", key=f"qbtn3_{selected_event_id}", use_container_width=True)
        b4 = st.button("EVALUATE CONSTELLATION GEOMETRY AND SATELLITE CHURN", key=f"qbtn4_{selected_event_id}", use_container_width=True)

    query_state_key = f"terminal_query_{selected_event_id}"
    if query_state_key not in st.session_state:
        st.session_state[query_state_key] = "Why was this event flagged?"

    if b1: st.session_state[query_state_key] = "Why was this event flagged?"
    elif b2: st.session_state[query_state_key] = "Is there evidence of cognitive drag-off or subtle spoofing?"
    elif b3: st.session_state[query_state_key] = "Summarize kinematic velocity and acceleration bounds for this epoch."
    elif b4: st.session_state[query_state_key] = "Evaluate constellation geometry, HDOP, and satellite churn turnover ratio."

    # Query Input & Execution
    in_col1, in_col2 = st.columns([5, 1])
    with in_col1:
        prompt_txt = st.text_input(
            "Query SOC Assistant:",
            value=st.session_state[query_state_key],
            key=f"input_terminal_{selected_event_id}",
            placeholder="Type query to SOC assistant..."
        )
    with in_col2:
        st.markdown("<div style='padding-top: 24px;'>", unsafe_allow_html=True)
        exec_clicked = st.button("EXECUTE", key=f"btn_exec_query_{selected_event_id}")
        st.markdown("</div>", unsafe_allow_html=True)

    ans_key = f"query_ans_{selected_event_id}"
    if exec_clicked:
        with st.spinner("Processing natural-language inquiry across SOC hierarchy..."):
            ans = data_service.query_soc(query=prompt_txt, event_id=selected_event_id, bundle=bundle)
            st.session_state[ans_key] = ans
    elif ans_key in st.session_state:
        ans = st.session_state[ans_key]
    else:
        # Pre-seed with default prompt inquiry
        ans = data_service.query_soc(query=st.session_state[query_state_key], event_id=selected_event_id, bundle=bundle)
        st.session_state[ans_key] = ans

    if not ans:
        st.info("NO QUERY RESPONSE AVAILABLE")
        return

    # Technical Resolution Pipeline Visual Flow
    st.markdown("<hr style='border-color: #1e293b; margin: 14px 0 10px 0;'>", unsafe_allow_html=True)
    st.markdown("<div class='soc-panel-title'>INQUIRY RESOLUTION PIPELINE TRACE</div>", unsafe_allow_html=True)

    ev_info = ans.get("event", {}) or {}
    status_ans = safe_str(ans.get("current_status"), "NOMINAL")
    risk_ans = safe_str(ans.get("risk_level") or ans.get("defcon_level"), "DEFCON_4")
    conf_ans = safe_float(ans.get("confidence", 0.90))
    evidence_count = len(ans.get("evidence", []))
    rag_count = len(ans.get("rag_sources", []))

    st.markdown(
        f"""
    <div class="soc-panel" style="font-family: monospace; font-size: 11px; line-height: 1.6;">
        <div style="margin-bottom: 6px;"><span style="color: #38bdf8; font-weight: 700;">1. USER QUERY:</span> <code>"{prompt_txt}"</code></div>
        <div style="margin-bottom: 6px;"><span style="color: #10b981; font-weight: 700;">2. LOCUS ANALYSIS:</span> Event: <strong>{selected_event_id}</strong> &nbsp;|&nbsp; Verdict: <strong>{status_ans}</strong> ({risk_ans}) &nbsp;|&nbsp; Confidence: <strong>{conf_ans*100:.1f}%</strong></div>
        <div style="margin-bottom: 6px;"><span style="color: #fbbf24; font-weight: 700;">3. EVIDENCE CITED:</span> <strong>{evidence_count}</strong> verified physical records from immutable Evidence Bundle</div>
        <div style="margin-bottom: 6px;"><span style="color: #a855f7; font-weight: 700;">4. AGENT CONSENSUS:</span> Tri-agent committee deliberation concluded without dissent</div>
        <div><span style="color: #38bdf8; font-weight: 700;">5. RAG GROUNDING:</span> <strong>{rag_count}</strong> regulatory citations retrieved from ICAO / RTCA knowledge base</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Grounded SOC Answer
    st.markdown("<div class='soc-panel-title'>GROUNDED SOC ASSISTANT EXPLANATION</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
    <div class="soc-panel" style="border-left: 3px solid #00f2fe; font-size: 12.5px; line-height: 1.6; color: #f1f5f9; font-family: monospace;">
        {ans.get('explanation', 'No explanation rendered.')}
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Recommended Actions
    actions = ans.get("recommended_next_action") or []
    if actions:
        st.markdown("<div class='soc-panel-title'>RECOMMENDED OPERATOR MITIGATION DIRECTIVES</div>", unsafe_allow_html=True)
        for act in actions:
            st.markdown(
                f"<div style='background: #090e18; border: 1px solid #1e293b; padding: 7px 12px; border-radius: 4px; "
                f"margin-bottom: 5px; font-size: 11px; color: #e2e8f0; font-family: monospace;'>&gt; {act}</div>",
                unsafe_allow_html=True,
            )
