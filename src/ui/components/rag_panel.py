"""
LOCUS Regulatory RAG Knowledge & Technical Standards Panel
Module: src.ui.components.rag_panel
"""

import streamlit as st


def render_rag_panel(rag_sources: list, rag_engine=None, service=None):
    """
    Render technical regulatory grounding panel with verified standards (ICAO, RTCA, CISA, MITRE).
    Provides standalone regulatory search and grounded citations.
    """
    rag_target = service or rag_engine
    st.subheader("Regulatory RAG Knowledge & Standards Grounding")
    st.caption("Aviation Standards & Cyber Doctrine • ICAO Annex 10 • RTCA DO-229E • CISA PNT • MITRE ATT&CK for Space")

    # Critical Invariant Notice
    st.markdown(
        """
        <div style='background: #1e1b4b; border: 1px solid #4338ca; border-radius: 6px; padding: 10px 14px; margin-bottom: 16px; font-size: 13px;'>
            <span style='color: #a5b4fc; font-weight: 700;'>CRITICAL ARCHITECTURAL INVARIANT:</span>
            <span style='color: #cbd5e1;'>
                The RAG subsystem provides <b>technical grounding and regulatory context</b>. 
                It is <b>NOT</b> the source of actual sensor measurements. Actual telemetry and anomaly thresholds originate strictly from sensor hardware and the Evidence Bundle.
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1. Grounded Citations for Current Event
    st.markdown("#### 1. Grounded Citations for Current Event")
    if rag_sources:
        for idx, src in enumerate(rag_sources):
            auths = src.get("regulatory_authorities", src.get("authority", ["REGULATORY_STANDARD"]))
            if isinstance(auths, str):
                auths = [auths]
            auth_html = "".join([f"<span class='provenance-tag' style='background:#0c4a6e; color:#38bdf8;'>{a}</span>" for a in auths])

            with st.expander(f"Citation {idx+1}: {src.get('document', src.get('source_document', 'Standard Document'))} — Section: {src.get('section', 'General')}"):
                st.markdown(f"**Regulatory Authorities**: {auth_html}", unsafe_allow_html=True)
                sim = src.get('similarity', src.get('relevance_score'))
                if sim is not None:
                    st.write(f"**Relevance Similarity**: `{float(sim):.4f}`")
                st.markdown(f"**Verified Technical Excerpt:**")
                st.info(src.get("content", src.get("snippet", "Regulatory standard excerpt grounding the observed anomaly.")))
    else:
        st.info("No specific regulatory documents were matched for this particular nominal event.")

    st.markdown("---")

    # 2. Interactive Knowledge Base Search
    st.markdown("#### 2. Query Regulatory Standards Directly")
    st.caption("Ask technical questions on GNSS spoofing, jamming, RAIM thresholds, or DO-229E compliance.")

    sample_rag_queries = [
        "What does RTCA DO-229E specify for HDOP and geometry degradation?",
        "What are the indicators of GNSS spoofing according to CISA?",
        "How is RAIM Fault Detection and Exclusion (FDE) defined in ICAO Annex 10?",
        "What MITRE ATT&CK for Space tactics apply to GNSS receiver manipulation?"
    ]

    selected_sq = st.selectbox("Sample Regulatory Prompts:", sample_rag_queries)
    custom_rag_q = st.text_input("Enter custom regulatory question:", value=selected_sq)

    if st.button("Query Knowledge Base", type="primary") and rag_target:
        with st.spinner("Retrieving regulatory standards from indexed vector store..."):
            if hasattr(rag_target, "query_rag"):
                res = rag_target.query_rag(query=custom_rag_q, top_k=3)
            elif hasattr(rag_target, "query"):
                res = rag_target.query(text=custom_rag_q, top_k=3)
            else:
                res = {"is_grounded": False}

            if res.get("is_grounded"):
                st.success("Regulatory Grounding Retrieved")
                st.write("**Referenced Standards:**", ", ".join(res.get("regulatory_standards", [])))
                for c in res.get("citations", []):
                    st.markdown(f"""
                    <div class='citation-card'>
                        <b>Document:</b> <code>{c.get('source_document')}</code> | <b>Section:</b> <code>{c.get('section')}</code><br/>
                        <b>Authority:</b> <span class='badge-info'>{c.get('authority')}</span> | <b>Score:</b> {c.get('similarity', 0.0):.4f}<br/>
                        <div style='margin-top: 6px; font-size: 13px; color: #cbd5e1;'>{c.get('content')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Insufficient knowledge context: No indexed regulatory documents matched this query with sufficient similarity.")
