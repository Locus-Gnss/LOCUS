"""
LOCUS SOC Theme & Cybersecurity Styling
Module: src.ui.components.theme
Ultra-premium dark cybersecurity SOC design tokens, glassmorphic cards, and cyan neon highlights.
"""

import streamlit as st


def inject_custom_css():
    """
    Inject professional dark cybersecurity SOC stylesheet.
    """
    st.markdown("""
    <style>
        /* Base Dark Cyber Background */
        .stApp {
            background-color: #070a12;
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        /* Streamlit Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0a0e1a;
            border-right: 1px solid #1a2234;
        }
        section[data-testid="stSidebar"] .stRadio label {
            color: #cbd5e1;
            font-size: 13px;
            font-weight: 500;
            padding: 4px 8px;
            border-radius: 4px;
            transition: all 0.15s ease-in-out;
        }
        section[data-testid="stSidebar"] .stRadio label:hover {
            color: #00f2fe;
            background-color: #111827;
        }

        /* Top Persistent Navigation Banner */
        .soc-header {
            background: linear-gradient(90deg, #0b1120 0%, #111c30 100%);
            border: 1px solid #1e293b;
            border-left: 4px solid #00f2fe;
            padding: 14px 20px;
            border-radius: 8px;
            margin-bottom: 14px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5);
        }

        /* KPI Metric Cards */
        .kpi-card {
            background: linear-gradient(180deg, #0f172a 0%, #0b1120 100%);
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 14px 10px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
            transition: all 0.2s ease;
        }
        .kpi-card:hover {
            border-color: #00f2fe;
            box-shadow: 0 0 12px rgba(0, 242, 254, 0.2);
            transform: translateY(-1px);
        }
        .kpi-title {
            font-size: 10.5px;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 6px;
        }
        .kpi-value {
            font-size: 20px;
            font-weight: 800;
            color: #ffffff;
            font-family: "SF Mono", Monaco, "Cascadia Code", monospace;
            letter-spacing: -0.02em;
        }
        .kpi-sub {
            font-size: 11px;
            color: #64748b;
            margin-top: 4px;
            font-family: monospace;
        }

        /* Semantic Status Badges */
        .badge-normal, .badge-online {
            background-color: #064e3b;
            color: #34d399;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 11px;
            border: 1px solid #059669;
            display: inline-block;
        }
        .badge-warning {
            background-color: #78350f;
            color: #fbbf24;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 11px;
            border: 1px solid #d97706;
            display: inline-block;
        }
        .badge-critical {
            background-color: #7f1d1d;
            color: #f87171;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 11px;
            border: 1px solid #dc2626;
            display: inline-block;
        }
        .badge-info {
            background-color: #0c4a6e;
            color: #38bdf8;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 11px;
            border: 1px solid #0284c7;
            display: inline-block;
        }

        /* Provenance Chip */
        .provenance-tag {
            background-color: #111827;
            color: #38bdf8;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10.5px;
            font-family: monospace;
            border: 1px solid #1e293b;
            display: inline-block;
            margin-right: 6px;
            margin-bottom: 4px;
            letter-spacing: 0.04em;
        }

        /* Flow Diagrams & Agent Boxes */
        .agent-container {
            background-color: #0b1120;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
        }
        .flow-step {
            display: flex;
            align-items: center;
            background: #111827;
            border-left: 4px solid #00f2fe;
            padding: 10px 14px;
            margin-bottom: 8px;
            border-radius: 0 6px 6px 0;
            font-size: 13px;
        }

        /* Technical Section Header */
        .section-header {
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #00f2fe;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 6px;
            margin-top: 14px;
            margin-bottom: 12px;
        }

        /* Technical Callouts */
        .soc-panel {
            background: #0d1322;
            border: 1px solid #1e293b;
            border-radius: 8px;
        }
        .soc-callout {
            background: #0f172a;
            border: 1px solid #1e293b;
            border-left: 3px solid #38bdf8;
            padding: 10px 14px;
            border-radius: 4px;
            font-size: 12px;
            color: #cbd5e1;
            margin-bottom: 12px;
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
            background-color: #0b1120;
            border: 1px solid #1e293b;
            border-left: 3px solid #00f2fe;
            border-radius: 6px;
            padding: 14px;
            margin-bottom: 10px;
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #070a12;
        }
        ::-webkit-scrollbar-thumb {
            background: #1e293b;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #38bdf8;
        }
    </style>
    """, unsafe_allow_html=True)
