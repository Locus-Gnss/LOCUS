"""
LOCUS Natural-Language SOC Assistant & Security Query Terminal
Module: src.ui.components.query_terminal
"""

import streamlit as st


def render_query_terminal(processor, event_id: str, bundle=None):
    """
    Render natural-language security query terminal supporting all standard operator prompts.
    Displays end-to-end deliberative flow:
    USER QUERY -> LOCUS ANALYSIS -> EVIDENCE -> AGENT FINDINGS -> RAG CONTEXT -> FINAL ANSWER.
    """
    st.subheader("💬 Autonomous SOC Security Assistant")
    st.caption("Natural-Language Threat Intelligence • Physics-Grounded Explanations • Full Audit Traceability")

    st.markdown("##### Quick Operator Prompts:")
    q_col1, q_col2, q_col3 = st.columns(3)
    p1 = q_col1.button("Why was this event flagged?")
    p2 = q_col2.button("What features caused the anomaly?")
    p3 = q_col3.button("Is the anomaly persistent?")

    q_col4, q_col5, q_col6 = st.columns(3)
    p4 = q_col4.button("Show me the evidence behind this alert.")
    p5 = q_col5.button("What did the temporal model detect?")
    p6 = q_col6.button("Explain the navigation-quality degradation.")

    active_prompt = "Why was this event flagged?"
    if p1: active_prompt = "Why was this event flagged?"
    elif p2: active_prompt = "What features caused the anomaly?"
    elif p3: active_prompt = "Is the anomaly persistent?"
    elif p4: active_prompt = "Show me the evidence behind this alert."
    elif p5: active_prompt = "What did the temporal model detect?"
    elif p6: active_prompt = "Explain the navigation-quality degradation."

    user_query = st.text_input("Enter natural-language security inquiry:", value=active_prompt)

    if st.button("Submit Inquiry to SOC Agent Hierarchy", type="primary"):
        with st.spinner("Executing end-to-end SOC deliberation, RAG grounding, and response synthesis..."):
            ans = processor.process_query(
                query=user_query,
                event_id=event_id,
                bundle=bundle
            )

            # Visual Flow: USER QUERY -> LOCUS ANALYSIS -> EVIDENCE -> AGENT FINDINGS -> RAG CONTEXT -> FINAL ANSWER
            st.markdown(
                f"""
                <div style='background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-top: 14px;'>
                    <div style='font-size: 13px; font-weight: 700; color: #94a3b8; margin-bottom: 8px;'>INQUIRY RESOLUTION PIPELINE:</div>
                    <div class='flow-step'>
                        <span style='min-width: 140px; font-weight: 700; color: #38bdf8;'>1. USER QUERY:</span>
                        <code>"{user_query}"</code>
                    </div>
                    <div class='flow-step'>
                        <span style='min-width: 140px; font-weight: 700; color: #10b981;'>2. LOCUS ANALYSIS:</span>
                        <span>Event: <b>{ans.get('event', {}).get('event_id')}</b> | Status: <b>{ans.get('current_status')}</b> ({ans.get('risk_level')}) | Confidence: <b>{ans.get('confidence', 1.0)*100:.1f}%</b></span>
                    </div>
                    <div class='flow-step'>
                        <span style='min-width: 140px; font-weight: 700; color: #f59e0b;'>3. EVIDENCE:</span>
                        <span>{len(ans.get('evidence', []))} verified records cited from immutable Evidence Bundle</span>
                    </div>
                    <div class='flow-step'>
                        <span style='min-width: 140px; font-weight: 700; color: #a855f7;'>4. AGENT FINDINGS:</span>
                        <span>Agent 1 (Integrity: {ans.get('agent_findings', {}).get('agent_1_integrity', {}).get('integrity_assessment')}) • Agent 2 (Threat: {ans.get('agent_findings', {}).get('agent_2_temporal_threat', {}).get('threat_classification', ans.get('agent_findings', {}).get('agent_2_temporal_threat', {}).get('temporal_assessment'))})</span>
                    </div>
                    <div class='flow-step'>
                        <span style='min-width: 140px; font-weight: 700; color: #38bdf8;'>5. RAG CONTEXT:</span>
                        <span>{len(ans.get('rag_sources', []))} regulatory citations grounded</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Final Answer
            st.markdown("#### 🎯 Grounded SOC Answer:")
            st.info(ans.get("explanation", "No explanation available."))

            # Recommended Actions
            st.markdown("#### 🛡️ Mandated Operator Actions:")
            for act in ans.get("recommended_next_action", []):
                st.markdown(f"- **`{act}`**")

            with st.expander("🔍 Inspect Full Structured JSON Response"):
                st.json(ans)
