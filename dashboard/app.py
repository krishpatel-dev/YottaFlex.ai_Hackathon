"""
dashboard/app.py
================
COMPENSATION INTELLIGENCE | Pay Equity & Compensation Analytics
Master Application Orchestrator & Native Multipage Router.
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

from dashboard.components.styles import inject_custom_css, render_html

# Page configuration
st.set_page_config(
    page_title="Compensation Intelligence | Pay Equity Analytics",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply unified Dribbble-inspired styling
inject_custom_css()

# Native Multipage Navigation using Streamlit 1.36+ st.navigation
# Completely eliminates filename "app" flicker, tab title mismatches, and transition unmounts
pages = [
    st.Page(
        str(_CURRENT_DIR / "pages" / "0_System_Overview.py"),
        title="System Overview",
        icon="⚖️",
        default=True,
    ),
    st.Page(
        str(_CURRENT_DIR / "pages" / "1_Executive_Overview.py"),
        title="Executive Overview",
        icon="📊",
    ),
    st.Page(
        str(_CURRENT_DIR / "pages" / "2_Compensation_Analysis.py"),
        title="Compensation Analysis",
        icon="📈",
    ),
    st.Page(
        str(_CURRENT_DIR / "pages" / "3_Employee_Comparison.py"),
        title="Employee Comparison",
        icon="👥",
    ),
    st.Page(
        str(_CURRENT_DIR / "pages" / "4_Disparity_Management.py"),
        title="Disparity Management",
        icon="🔍",
    ),
    st.Page(
        str(_CURRENT_DIR / "pages" / "5_Adjustment_Proposals.py"),
        title="Adjustment Proposals",
        icon="📝",
    ),
]

pg = st.navigation(pages)

# Persistent Sidebar Branding
with st.sidebar:
    render_html("""
    <div style="padding: 10px 0 16px 0;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="background: #2563EB; color: white; width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; font-weight: 800;">
                ⚖️
            </div>
            <div>
                <div style="font-weight: 800; font-size: 1.05rem; color: #FFFFFF; letter-spacing: -0.02em;">CompIntel OS</div>
                <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">Pay Equity Intelligence</div>
            </div>
        </div>
    </div>
    """)

# Execute active page
pg.run()
