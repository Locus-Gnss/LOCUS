"""
LOCUS SOC Theme & Cybersecurity Styling
Module: src.ui.components.theme
"""

import streamlit as st


def inject_custom_css():
    """
    Inject professional dark cybersecurity SOC stylesheet.
    """
    st.markdown("""
    <style>
        /* Base Dark Background */
        .stApp {
            background-color: #0b0f19;
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        /* Top Navigation Banner */
        .soc-header {
            background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
            border-bottom: 2px solid #334155;
            padding: 14px 20px;
            border-radius: 8px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* KPI Metric Cards */
        .kpi-card {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 8px;
            padding: 14px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
            transition: border-color 0.2s ease;
        }
        .kpi-card:hover {
            border-color: #38bdf8;
        }
        .kpi-title {
            font-size: 11px;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 6px;
        }
        .kpi-value {
            font-size: 22px;
            font-weight: 800;
            color: #ffffff;
            font-family: "SF Mono", Monaco, "Cascadia Code", monospace;
        }
        .kpi-sub {
            font-size: 11px;
            color: #64748b;
            margin-top: 4px;
        }

        /* Semantic Status Badges */
        .badge-normal {
            background-color: #064e3b;
            color: #34d399;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 12px;
            border: 1px solid #059669;
        }
        .badge-warning {
            background-color: #78350f;
            color: #fbbf24;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 12px;
            border: 1px solid #d97706;
        }
        .badge-critical {
            background-color: #7f1d1d;
            color: #f87171;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 12px;
            border: 1px solid #dc2626;
        }
        .badge-info {
            background-color: #0c4a6e;
            color: #38bdf8;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 12px;
            border: 1px solid #0284c7;
        }

        /* Provenance Chip */
        .provenance-tag {
            background-color: #1e1b4b;
            color: #a5b4fc;
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 11px;
            font-family: monospace;
            border: 1px solid #4338ca;
            display: inline-block;
            margin-right: 6px;
            margin-bottom: 4px;
        }

        /* Flow Diagrams & Agent Boxes */
        .agent-container {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
        }
        .flow-step {
            display: flex;
            align-items: center;
            background: #111827;
            border-left: 4px solid #38bdf8;
            padding: 10px 14px;
            margin-bottom: 8px;
            border-radius: 0 6px 6px 0;
            font-size: 13px;
        }

        /* Alert Row Highlighting */
        .alert-row-critical {
            border-left: 4px solid #ef4444;
            background: #1c131a;
            padding: 10px;
            margin-bottom: 6px;
            border-radius: 0 6px 6px 0;
        }
        .alert-row-warning {
            border-left: 4px solid #f59e0b;
            background: #1c1813;
            padding: 10px;
            margin-bottom: 6px;
            border-radius: 0 6px 6px 0;
        }
        .alert-row-info {
            border-left: 4px solid #3b82f6;
            background: #131722;
            padding: 10px;
            margin-bottom: 6px;
            border-radius: 0 6px 6px 0;
        }

        /* RAG Citation Box */
        .citation-card {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
