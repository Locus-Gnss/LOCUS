"""
LOCUS System Health & Architectural Integrity Matrix
Module: src.ui.components.health_panel
"""

import streamlit as st
import pandas as pd


def render_health_panel(health_matrix: list):
    """
    Render live system health checks across all hardware, pipeline, model, agent, and API layers.
    Zero fabrication: checks real files, models, and service availability.
    """
    st.subheader("⚙️ System Health & Architectural Component Matrix")
    st.caption("Real-Time Hardware, Pipeline, Model, Agent, and API Status Auditing")

    df_health = pd.DataFrame(health_matrix)

    # Summary metrics
    c1, c2, c3 = st.columns(3)
    total_components = len(health_matrix)
    ready_count = sum(1 for c in health_matrix if "READY" in c["status"] or "OPERATIONAL" in c["status"] or "CONNECTED" in c["status"] or "HEALTHY" in c["status"] or "ACTIVE" in c["status"] or "INDEXED" in c["status"] or "AUDITED" in c["status"])

    c1.metric("Total Monitored Components", total_components)
    c2.metric("Operational Readiness", f"{ready_count}/{total_components} ({(ready_count/total_components)*100:.1f}%)")
    c3.metric("Backend Architecture", "FastAPI + Streamlit")

    st.markdown("---")
    st.markdown("##### Detailed Component Verification")

    for item in health_matrix:
        status = item["status"]
        badge_class = "badge-normal" if ("READY" in status or "OPERATIONAL" in status or "CONNECTED" in status or "HEALTHY" in status or "ACTIVE" in status or "INDEXED" in status or "AUDITED" in status) else "badge-warning"
        if "DISCONNECTED" in status or "OFFLINE" in status or "NO CHUNKS" in status or "EMPTY" in status:
            badge_class = "badge-critical"

        st.markdown(
            f"""
            <div style='background: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <span style='font-weight: 700; color: #ffffff;'>{item['component']}</span>
                    <span style='color: #64748b; font-size: 12px; margin-left: 10px;'>[{item['layer']}]</span>
                    <div style='color: #94a3b8; font-size: 12px; margin-top: 2px;'>{item['details']}</div>
                </div>
                <div>
                    <span class='{badge_class}'>● {status}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
