"""
dashboard/app.py
================
COMPENSATION INTELLIGENCE | Pay Equity & Compensation Analytics
Main entry point for the Streamlit Analytics Platform.
"""

from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st

# Setup python path
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dashboard.utils.data_loader import load_all_data, compute_live_metrics
from dashboard.components.kpi_cards import render_kpi_row

st.set_page_config(
    page_title="Compensation Intelligence | Pay Equity Analytics",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Enterprise CSS Styling
st.markdown("""
<style>
    /* Global styles */
    .main {
        background-color: #F8FAFC;
    }
    [data-testid="stSidebar"] {
        background-color: #0F172A;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0;
    }
    h1, h2, h3 {
        font-family: 'Inter', -apple-system, sans-serif;
        color: #0F172A;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border-top: 4px solid #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Branding
with st.sidebar:
    st.markdown("## ⚖️ Compensation Intelligence")
    st.markdown("**Pay Equity & Salary Benchmarking**")
    st.caption("v1.0.0 • Enterprise Edition")
    st.divider()
    st.markdown("""
    ### 📌 Navigation
    Use the pages menu above to explore:
    - **1. Executive Overview**: Key equity metrics & distribution
    - **2. Compensation Analysis**: Multi-dimensional role/level filters
    - **3. Employee Comparison**: Side-by-side peer equity audit
    - **4. Disparity Management**: 5 Exception scenarios & investigation
    - **5. Adjustment Proposals**: Salary change governance workflow
    """)
    st.divider()
    st.info("💡 **Audit Principle**: Disparities flag potential anomalies for human HR review; they do not automatically conclude discrimination.")

# Main Header
st.title("⚖️ Compensation Intelligence Platform")
st.subheader("Auditable Pay Equity Benchmarking & Unexplained Disparity Detection")

# System Health & Data Loading
with st.spinner("Loading compensation data and computing equity benchmarks..."):
    data = load_all_data()
    metrics = compute_live_metrics(data)

st.markdown("""
Welcome to the **Compensation Intelligence Platform**. This system continuously evaluates employee compensation 
against role family, career level, geographic market benchmarks, full-time equivalent hours, and documented job-related performance factors.
""")

st.divider()

# Top KPI Metric Row
kpi_items = [
    {
        "title": "Active Employees",
        "value": f"{metrics.get('total_employees', 5000):,}",
        "subtitle": "Across 13 Business Locations",
        "color": "#3B82F6",
        "icon": "👥",
    },
    {
        "title": "Avg Compa-Ratio",
        "value": f"{metrics.get('avg_compa_ratio', 100.0):.1f}%",
        "subtitle": "Target Market Corridor: 80% - 120%",
        "color": "#10B981",
        "icon": "🎯",
    },
    {
        "title": "Below Band (<80%)",
        "value": f"{metrics.get('below_band_count', 0):,}",
        "subtitle": "Requires Equity Review",
        "color": "#EF4444",
        "icon": "⚠️",
    },
    {
        "title": "Above Band (>120%)",
        "value": f"{metrics.get('above_band_count', 0):,}",
        "subtitle": "Market Premium / Over-band",
        "color": "#8B5CF6",
        "icon": "📈",
    },
    {
        "title": "Flagged Disparities",
        "value": f"{metrics.get('disparity_count', 0):,}",
        "subtitle": "Unexplained Equity Exceptions",
        "color": "#F59E0B",
        "icon": "🔍",
    },
    {
        "title": "Active Proposals",
        "value": f"{metrics.get('pending_proposals', 0):,}",
        "subtitle": "Pending Governance Approval",
        "color": "#6366F1",
        "icon": "📝",
    },
]

render_kpi_row(kpi_items)

st.divider()

# Quick Overview Columns
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🏢 Organizational Data Summary")
    st.markdown(f"""
    - **Total Active Headcount:** {metrics.get('total_employees', 5000):,}
    - **Roles Benchmarked:** 21 Distinct Roles across 8 Functional Families
    - **Career Progression Levels:** 10 Levels (IC: L1–L6 | Manager: M1–M4)
    - **Active Compensation Bands:** 8,190 Effective-dated Benchmarks (2024–2026)
    - **Point-in-Time Salary Records:** 19,846 Longitudinal Records
    - **Performance Appraisals:** 75,000 Semi-annual Reviews
    - **Validated Peer Groups:** 589 Comparable Homogeneous Clusters
    """)

with col2:
    st.markdown("### 🛡️ Five Mandatory Exception Safeguards")
    st.markdown("""
    The system continuously audits for 5 critical governance exceptions:
    1. 🔴 **Salary Evaluated Against Expired Band**: Detects outdated market benchmarks.
    2. 🟠 **FTE Normalization Ignored**: Detects part-time salaries compared without FTE scaling.
    3. 🔴 **Currency Conversion Missing**: Flags unmapped foreign currencies lacking official FX rates.
    4. 🔴 **Adjustment Applied Without Approval**: Detects payroll changes lacking HR sign-off.
    5. 🟡 **Incomparable Roles Grouped**: Flags invalid comparison clusters across disparate job families.
    """)

st.divider()

st.caption("Built with Python 3.11+, PostgreSQL 16 / SQLAlchemy 2.0, Streamlit, and Plotly. Deterministic Seed: `20261022`.")
