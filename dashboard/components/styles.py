"""
dashboard/components/styles.py
==============================
Shared Dribbble-inspired enterprise CSS styling and layout decorators.
Inspired by modern human capital management dashboards (HRoom, Block AI, Toota).
"""

import re
import streamlit as st


def render_html(html_str: str) -> None:
    """
    Safely render HTML without Markdown converting indented lines to code blocks.
    Removes leading whitespace from all lines and strips HTML comments.
    """
    if not html_str:
        return
    cleaned = re.sub(r'<!--.*?-->', '', html_str, flags=re.DOTALL)
    cleaned = re.sub(r'^[ \t]+', '', cleaned, flags=re.MULTILINE).strip()
    st.markdown(cleaned, unsafe_allow_html=True)


def inject_custom_css() -> None:
    """Inject modern enterprise theme styles across all dashboard pages."""
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');

        /* Root Canvas */
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #0F172A;
        }

        .stApp {
            background-color: #F8FAFC !important;
        }

        /* Top Header & Page Titles */
        h1 {
            font-size: 1.85rem !important;
            font-weight: 800 !important;
            color: #0F172A !important;
            letter-spacing: -0.025em !important;
            margin-bottom: 0.25rem !important;
        }

        h2 {
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            color: #1E293B !important;
            letter-spacing: -0.02em !important;
        }

        h3 {
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            color: #1E293B !important;
        }

        /* Sidebar Luxury Dark Theme */
        [data-testid="stSidebar"] {
            background-color: #0B0F19 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div:not([data-baseweb="select"] *) {
            color: #E2E8F0;
        }

        [data-testid="stSidebarNav"] {
            padding-top: 0.8rem !important;
        }

        [data-testid="stSidebarNav"] span {
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            color: #E2E8F0 !important;
            text-transform: capitalize !important;
        }

        [data-testid="stSidebarNav"] li div {
            border-radius: 10px !important;
            margin-bottom: 4px !important;
            transition: all 0.2s ease !important;
        }

        [data-testid="stSidebarNav"] li div:hover {
            background-color: rgba(255, 255, 255, 0.08) !important;
        }

        /* Sidebar Selectbox & Input Controls — High-Contrast Dark Slate */
        [data-testid="stSidebar"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] div[data-baseweb="input"] > div {
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
        }

        [data-testid="stSidebar"] div[data-baseweb="select"] *,
        [data-testid="stSidebar"] div[data-baseweb="input"] * {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        [data-testid="stSidebar"] div[data-baseweb="select"] input,
        [data-testid="stSidebar"] div[data-baseweb="input"] input {
            color: #FFFFFF !important;
            background-color: transparent !important;
        }

        [data-testid="stSidebar"] div[data-baseweb="select"] svg {
            fill: #94A3B8 !important;
        }

        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stTextInput label {
            color: #CBD5E1 !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.04em !important;
        }

        [data-testid="stSidebar"] .stSlider label {
            color: #CBD5E1 !important;
            font-weight: 600 !important;
        }

        /* Popover dropdown menu */
        div[data-baseweb="popover"] ul {
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
        }

        div[data-baseweb="popover"] li * {
            color: #F8FAFC !important;
            font-weight: 500 !important;
        }

        div[data-baseweb="popover"] li:hover {
            background-color: #334155 !important;
        }

        /* Main Content Select Boxes, Inputs & Textareas — Crisp White Cards */
        [data-testid="stMain"] div[data-baseweb="select"] > div,
        [data-testid="stMain"] div[data-baseweb="input"] > div,
        [data-testid="stMain"] div[data-baseweb="textarea"] > div,
        .main div[data-baseweb="select"] > div,
        .main div[data-baseweb="input"] > div,
        .main div[data-baseweb="textarea"] > div {
            border-radius: 10px !important;
            border: 1px solid #CBD5E1 !important;
            background-color: #FFFFFF !important;
        }

        [data-testid="stMain"] div[data-baseweb="select"] *,
        [data-testid="stMain"] div[data-baseweb="input"] *,
        [data-testid="stMain"] div[data-baseweb="textarea"] *,
        .main div[data-baseweb="select"] *,
        .main div[data-baseweb="input"] *,
        .main div[data-baseweb="textarea"] * {
            color: #0F172A !important;
            font-weight: 600 !important;
        }

        [data-testid="stMain"] input,
        [data-testid="stMain"] textarea,
        .main input,
        .main textarea {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }

        /* Glassmorphic White Container Cards */
        .glass-card {
            background: #FFFFFF;
            border-radius: 16px;
            border: 1px solid #E2E8F0;
            padding: 22px 24px;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.03);
            margin-bottom: 20px;
        }

        /* Metric Chips */
        .metric-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
        }

        .badge-success { background: #ECFDF5; color: #047857; }
        .badge-warning { background: #FFFBEB; color: #B45309; }
        .badge-danger  { background: #FEF2F2; color: #B91C1C; }
        .badge-info    { background: #EFF6FF; color: #1D4ED8; }
        .badge-purple  { background: #F5F3FF; color: #6D28D9; }

        /* Button Styling */
        .stButton > button {
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.25rem !important;
            transition: all 0.2s ease !important;
            border: 1px solid #CBD5E1 !important;
        }

        .stButton > button[kind="primary"] {
            background: #2563EB !important;
            color: #FFFFFF !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
        }

        .stButton > button[kind="primary"]:hover {
            background: #1D4ED8 !important;
            transform: translateY(-1px) !important;
        }

        /* Dataframe table styling */
        [data-testid="stDataFrame"] {
            border-radius: 14px !important;
            border: 1px solid #E2E8F0 !important;
            overflow: hidden !important;
            background: #FFFFFF !important;
        }

        /* Clean Plotly Containers */
        .plotly-card {
            background: #FFFFFF;
            border-radius: 16px;
            border: 1px solid #E2E8F0;
            padding: 18px 20px 14px 20px;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03);
            margin-bottom: 20px;
        }
    </style>
    """
    render_html(css)
