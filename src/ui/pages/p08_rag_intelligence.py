"""
Module 9: Regulatory RAG
Module: src.ui.pages.p08_rag_intelligence
Dedicated regulatory knowledge retrieval and aviation standards grounding interface.
"""

from typing import Dict, Any, List
import streamlit as st

from src.ui.utils.formatting import safe_float, safe_int, safe_str


def render_rag_intelligence_page(data_service, selected_event_id: str):
    """
    Render Regulatory RAG module matching Screenshot 9 specification.
    """
    st.markdown("<div class='section-header'>REGULATORY RAG INTELLIGENCE</div>", unsafe_allow_html=True)
    st.markdown(
        """
    <div class="soc-callout">
        <strong>PROVENANCE: CONTEXTUAL SECURITY KNOWLEDGE</strong><br>
        This engine retrieves regulatory standards, avionics certifications, and cyber-physical defense literature
        (ICAO Annex 10, RTCA DO-229E, MITRE ATT&CK for Space, CISA GNSS Guidelines).<br>
        <strong>DISTINCTION:</strong> RAG outputs provide normative standards and guidance. They are <strong>NOT</strong> raw GNSS sensor telemetry.
    </div>
    """,
        unsafe_allow_html=True,
    )

    bundle = data_service.load_event(selected_event_id)
    pr = bundle.physical_rules if bundle and isinstance(bundle.physical_rules, dict) else {}
    ifo = bundle.isolation_forest if bundle and isinstance(bundle.isolation_forest, dict) else {}

    # Event-grounded default query
    if pr.get("triggered_count", 0) > 0:
        default_query = "What are the RTCA DO-229E limits on kinematic acceleration and speed-of-sound invariant violations?"
    elif ifo.get("is_anomaly", False):
        default_query = "What are the ICAO Annex 10 standards for GNSS spatial anomaly detection and spoofing containment?"
    else:
        default_query = "What are the RTCA DO-229E and ICAO standards for GNSS integrity monitoring and HDOP thresholds?"

    rag_key = f"rag_query_{selected_event_id}"
    if rag_key not in st.session_state:
        st.session_state[rag_key] = default_query

    st.markdown("<div class='soc-panel-title'>SECURITY STANDARDS QUERY</div>", unsafe_allow_html=True)

    col_q1, col_q2, col_q3 = st.columns([5, 1, 1])
    with col_q1:
        query_input = st.text_input(
            "Regulatory / Security Query:",
            value=st.session_state[rag_key],
            key=f"rag_input_field_{selected_event_id}"
        )
    with col_q2:
        top_k = st.selectbox("Top Chunks:", options=[1, 2, 3, 5], index=2, key=f"rag_topk_{selected_event_id}")
    with col_q3:
        st.markdown("<div style='padding-top: 24px;'>", unsafe_allow_html=True)
        search_clicked = st.button("SEARCH RAG", key=f"btn_rag_search_{selected_event_id}")
        st.markdown("</div>", unsafe_allow_html=True)

    # Suggested inquiries
    sq1, sq2, sq3 = st.columns(3)
    with sq1:
        if st.button("Avionics HDOP Thresholds", key=f"sq1_{selected_event_id}"):
            st.session_state[rag_key] = "What are the RTCA DO-229E standards on HDOP and RAIM fault containment?"
            st.rerun()
    with sq2:
        if st.button("MITRE Space TTPs", key=f"sq2_{selected_event_id}"):
            st.session_state[rag_key] = "What are the MITRE ATT&CK for Space TTPs for GNSS spoofing and meaconing?"
            st.rerun()
    with sq3:
        if st.button("Kinematic Physical Limits", key=f"sq3_{selected_event_id}"):
            st.session_state[rag_key] = "What is the speed of sound physical limit for civil kinematic tracking?"
            st.rerun()

    # Query result
    result_key = f"rag_result_cache_{selected_event_id}"
    if search_clicked:
        with st.spinner("Retrieving normative standards from vector store..."):
            res = data_service.query_rag(query=query_input, top_k=top_k)
            st.session_state[result_key] = res
    elif result_key in st.session_state:
        res = st.session_state[result_key]
    else:
        res = data_service.query_rag(query=st.session_state[rag_key], top_k=top_k)
        st.session_state[result_key] = res

    if not res:
        st.info("NO RAG KNOWLEDGE AVAILABLE")
        return

    citations = res.get("citations", [])
    standards = res.get("regulatory_standards", [])
    is_grounded = res.get("is_grounded", False)
    g_badge = "<span class='badge badge-online'>GROUNDED CITATIONS</span>" if is_grounded else "<span class='badge badge-warning'>PARTIAL MATCH</span>"

    st.markdown("<hr style='border-color: #1e293b; margin: 14px 0 10px 0;'>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-size: 11px; font-family: monospace; margin-bottom: 8px;'>"
        f"GROUNDING: {g_badge} &nbsp;|&nbsp; CITATIONS RETRIEVED: <strong>{len(citations)}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if standards:
        std_badges = " ".join(f"<span class='badge badge-info'>{s}</span>" for s in standards)
        st.markdown(f"<div style='margin-bottom: 12px;'>{std_badges}</div>", unsafe_allow_html=True)

    for idx, cit in enumerate(citations):
        title = cit.get("title") or cit.get("document") or f"Standard Citation {idx + 1}"
        source = cit.get("source", "Aeronautical Standards Repository")
        content = cit.get("content") or cit.get("text", "")
        sim = cit.get("score") or cit.get("similarity")
        sim_str = f" | Similarity: {sim:.3f}" if sim is not None else ""

        st.markdown(
            f"""
        <div class="soc-panel" style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 700; color: #f8fafc; font-size: 12.5px; font-family: monospace;">[{idx + 1}] {title}</span>
                <span style="font-size: 10px; color: #64748b; font-family: monospace;">SOURCE: {source}{sim_str}</span>
            </div>
            <div style="font-size: 11.5px; line-height: 1.5; color: #cbd5e1; background: #080c14; padding: 10px 12px; border-radius: 4px; border: 1px solid #1a2333; font-family: monospace;">
                {content}
            </div>
            <div style="font-size: 10px; color: #38bdf8; margin-top: 6px; font-family: monospace;">
                SECURITY INTERPRETATION: Mandates detection threshold boundaries applied to {selected_event_id}.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
