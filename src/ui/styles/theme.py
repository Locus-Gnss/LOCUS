"""
LOCUS GNSS Security Operations Center — Professional Dark SOC Theme
Module: src.ui.styles.theme
Focus: High-contrast, clean, technical SOC aesthetic. No emojis.
"""

import streamlit as st


def inject_custom_css():
    """
    Inject professional dark cybersecurity SOC stylesheet into Streamlit.
    Hides default Streamlit chrome, styles horizontal nav pills, dense metric cards,
    thin cyan borders, and glowing badges.
    """
    st.markdown(
        """
    <style>
        /* Base Dark Background */
        .stApp {
            background-color: #070b14;
            color: #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
        }

        /* Streamlit Top Header Bar & Deploy Button Suppression */
        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0px !important;
            min-height: 0px !important;
        }
        [data-testid="stToolbar"] {
            visibility: hidden !important;
            display: none !important;
        }
        #MainMenu {
            visibility: hidden !important;
            display: none !important;
        }
        footer {
            visibility: hidden !important;
            display: none !important;
        }
        div[data-testid="stDecoration"] {
            display: none !important;
        }
        div[data-testid="stStatusWidget"] {
            display: none !important;
        }
        .stDeployButton {
            display: none !important;
        }

        /* Layout Block Padding Reduction */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important;
        }

        /* Sidebar Styling (Suppressed or Minimal) */
        section[data-testid="stSidebar"] {
            background-color: #090e18;
            border-right: 1px solid #1a2333;
        }
        section[data-testid="stSidebar"] hr {
            border-color: #1a2333;
        }

        /* Persistent Top Header Banner */
        .locus-persistent-header {
            background: linear-gradient(135deg, #090e18 0%, #0d1527 100%);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-left: 4px solid #00f2fe;
            border-radius: 6px;
            padding: 12px 18px;
            margin-bottom: 12px;
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.05);
        }
        .locus-top-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }
        .locus-title-box {
            display: flex;
            flex-direction: column;
        }
        .locus-title-text {
            font-size: 19px;
            font-weight: 800;
            letter-spacing: 0.08em;
            color: #f8fafc;
            font-family: 'SF Mono', Monaco, monospace;
        }
        .locus-sub-text {
            font-size: 10px;
            font-weight: 600;
            color: #38bdf8;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-top: 2px;
        }
        .locus-telemetry-meta {
            display: flex;
            align-items: center;
            gap: 22px;
            font-family: 'SF Mono', Monaco, monospace;
        }
        .locus-meta-block {
            display: flex;
            flex-direction: column;
            text-align: right;
        }
        .locus-meta-lbl {
            font-size: 9px;
            font-weight: 700;
            color: #64748b;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }
        .locus-meta-val {
            font-size: 13px;
            font-weight: 700;
            color: #e2e8f0;
        }

        /* Horizontal Navigation Pills */
        [data-testid="stPills"] {
            background: #090e18 !important;
            border: 1px solid rgba(56, 189, 248, 0.25) !important;
            border-radius: 6px !important;
            padding: 6px 8px !important;
            gap: 6px !important;
            margin-bottom: 16px !important;
            display: flex !important;
            flex-wrap: wrap !important;
        }
        [data-testid="stPills"] button {
            background: #0d1527 !important;
            color: #94a3b8 !important;
            border: 1px solid #1e293b !important;
            font-family: 'SF Mono', Monaco, monospace !important;
            font-size: 10px !important;
            font-weight: 700 !important;
            letter-spacing: 0.05em !important;
            padding: 4px 10px !important;
            border-radius: 4px !important;
            transition: all 0.15s ease !important;
        }
        [data-testid="stPills"] button:hover {
            background: #13213d !important;
            color: #38bdf8 !important;
            border-color: #38bdf8 !important;
        }
        [data-testid="stPills"] button[aria-selected="true"] {
            background: #0284c7 !important;
            color: #ffffff !important;
            border-color: #00f2fe !important;
            box-shadow: 0 0 10px rgba(0, 242, 254, 0.4) !important;
        }

        /* Technical Metric / KPI Cards */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 10px;
            margin-bottom: 16px;
        }
        .kpi-card {
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 5px;
            padding: 12px;
            text-align: left;
            transition: border-color 0.15s ease;
        }
        .kpi-card:hover {
            border-color: #38bdf8;
        }
        .kpi-label {
            font-size: 9.5px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 4px;
        }
        .kpi-val {
            font-size: 18px;
            font-weight: 700;
            color: #f1f5f9;
            font-family: 'SF Mono', Monaco, monospace;
            letter-spacing: -0.02em;
        }
        .kpi-note {
            font-size: 9.5px;
            color: #94a3b8;
            margin-top: 4px;
            font-family: 'SF Mono', Monaco, monospace;
        }

        /* Status Badges */
        .badge {
            display: inline-block;
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 700;
            font-family: 'SF Mono', Monaco, monospace;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .badge-online {
            background: rgba(16, 185, 129, 0.15);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.4);
        }
        .badge-offline {
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.4);
        }
        .badge-ready {
            background: rgba(14, 165, 233, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(14, 165, 233, 0.4);
        }
        .badge-normal {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .badge-warning {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.4);
        }
        .badge-critical {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.4);
        }
        .badge-info {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        /* Panels and Containers */
        .soc-panel {
            background: #0d1527;
            border: 1px solid #1e293b;
            border-radius: 5px;
            padding: 14px 16px;
            margin-bottom: 14px;
        }
        .soc-panel-title {
            font-size: 11.5px;
            font-weight: 700;
            color: #cbd5e1;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 10px;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 6px;
            font-family: 'SF Mono', Monaco, monospace;
        }

        /* Data Tables */
        .stDataFrame, .stTable {
            border: 1px solid #1e293b;
            border-radius: 5px;
            background: #090e18;
        }

        /* Buttons */
        .stButton > button {
            background: #111a2e;
            color: #f1f5f9;
            border: 1px solid #1e293b;
            border-radius: 4px;
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 6px 14px;
            transition: all 0.15s ease;
            font-family: 'SF Mono', Monaco, monospace;
        }
        .stButton > button:hover {
            background: #0284c7;
            border-color: #38bdf8;
            color: #ffffff;
            box-shadow: 0 0 10px rgba(0, 242, 254, 0.3);
        }

        /* Inputs */
        .stTextInput > div > div > input,
        .stSelectbox > div > div,
        .stTextArea > div > div > textarea {
            background-color: #090e18 !important;
            border-color: #1e293b !important;
            color: #f1f5f9 !important;
            font-family: 'SF Mono', Monaco, monospace !important;
            font-size: 12px !important;
        }

        /* Section Header */
        .section-header {
            font-size: 14px;
            font-weight: 800;
            color: #f8fafc;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-top: 4px;
            margin-bottom: 12px;
            padding-bottom: 6px;
            border-bottom: 1px solid #1e293b;
            font-family: 'SF Mono', Monaco, monospace;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* Callouts */
        .soc-callout {
            background: #0a1120;
            border-left: 3px solid #38bdf8;
            padding: 10px 14px;
            border-radius: 0 4px 4px 0;
            font-size: 11.5px;
            color: #94a3b8;
            margin-bottom: 12px;
            line-height: 1.5;
        }

        /* Feature Cards (10-D Vector) */
        .feature-card {
            background: #0d1527;
            border: 1px solid #1e293b;
            border-radius: 5px;
            padding: 10px 12px;
            margin-bottom: 8px;
            min-height: 110px;
            transition: border-color 0.15s ease;
        }
        .feature-card:hover {
            border-color: #38bdf8;
        }

        /* Detector Cards */
        .detector-card {
            background: #0d1527;
            border: 1px solid #1e293b;
            border-radius: 5px;
            padding: 12px 14px;
            margin-bottom: 8px;
            min-height: 125px;
        }
        .det-title {
            font-size: 10px;
            font-weight: 800;
            color: #38bdf8;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-family: 'SF Mono', Monaco, monospace;
        }
        .det-score {
            font-size: 11px;
            color: #94a3b8;
            margin-top: 6px;
            font-family: 'SF Mono', Monaco, monospace;
        }
        .det-model {
            font-size: 9.5px;
            color: #475569;
            margin-top: 4px;
            font-family: 'SF Mono', Monaco, monospace;
        }

        /* Connected Pipeline Flow Grid */
        .pipeline-flow-container {
            background: #080d17;
            border: 1px solid #1e293b;
            border-radius: 6px;
            padding: 12px 14px;
            margin-bottom: 16px;
        }
        .pipeline-flow-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(115px, 1fr));
            gap: 6px;
            align-items: stretch;
        }
        .pipeline-stage-card {
            background: #0d1527;
            border: 1px solid #1e293b;
            border-radius: 4px;
            padding: 6px 8px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 64px;
            transition: all 0.15s ease;
        }
        .pipeline-stage-card.stage-done {
            border-left: 3px solid #10b981;
        }
        .pipeline-stage-card.stage-running {
            border-left: 3px solid #38bdf8;
        }
        .pipeline-stage-card.stage-waiting {
            border-left: 3px solid #475569;
            opacity: 0.7;
        }
        .stage-num-label {
            font-size: 8.5px;
            font-weight: 700;
            color: #64748b;
            font-family: 'SF Mono', Monaco, monospace;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .stage-title-text {
            font-size: 10px;
            font-weight: 700;
            color: #f1f5f9;
            letter-spacing: 0.02em;
            margin-top: 2px;
            margin-bottom: 2px;
        }

        /* Master Threat Verdict Banner */
        .verdict-banner-box {
            background: linear-gradient(90deg, #0d1527 0%, #111a30 100%);
            border: 1px solid #1e293b;
            border-radius: 6px;
            padding: 14px 18px;
            margin-bottom: 14px;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
