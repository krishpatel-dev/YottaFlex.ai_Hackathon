"""
dashboard/components/styles.py
==============================
Shared Dribbble-inspired enterprise CSS styling and layout decorators.
Inspired by modern human capital management dashboards (HRoom, Block AI, Toota).
"""

import streamlit as st


def inject_custom_css() -> None:
    """Inject modern enterprise theme styles across all dashboard pages."""
    st.markdown("""
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

        [data-testid="stSidebar"] * {
            color: #E2E8F0 !important;
        }

        [data-testid="stSidebarNav"] {
            padding-top: 1rem !important;
        }

        [data-testid="stSidebarNav"] span {
            font-size: 0.88rem !important;
            font-weight: 500 !important;
        }

        [data-testid="stSidebarNav"] li div {
            border-radius: 10px !important;
            margin-bottom: 4px !important;
            transition: all 0.2s ease !important;
        }

        [data-testid="stSidebarNav"] li div:hover {
            background-color: rgba(255, 255, 255, 0.06) !important;
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

        /* Interactive Widgets Styling */
        div[data-baseweb="select"] > div {
            border-radius: 10px !important;
            border: 1px solid #CBD5E1 !important;
            background-color: #FFFFFF !important;
        }

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
    """, unsafe_allow_html=True)
