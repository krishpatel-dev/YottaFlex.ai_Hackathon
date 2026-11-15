"""
dashboard/pages/1_executive_overview.py
======================================
Page 1: Executive Overview Dashboard
Key performance indicators, organization-wide salary and compa-ratio distributions,
and recent exception audit activity.
"""

from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st
import pandas as pd

_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dashboard.utils.data_loader import load_all_data
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.components.styles import inject_custom_css, render_html
from dashboard.components.charts import (
    compa_ratio_distribution,
    salary_distribution_histogram,
    salary_by_location_bar,
    salary_by_role_boxplot,
)
from dashboard.components.tables import format_inr, render_styled_dataframe

# Apply unified design system
inject_custom_css()

# Header (Inspired by Toota / Block AI)
render_html("""
<div style="margin-bottom: 22px;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
        <div>
            <div style="font-size: 0.8rem; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                Executive Summary • FY 2026 Audit
            </div>
            <div style="font-size: 1.85rem; font-weight: 800; color: #0F172A; letter-spacing: -0.025em; line-height: 1.2;">
                Executive Compensation & Pay Equity Overview
            </div>
            <div style="font-size: 0.92rem; color: #64748B; margin-top: 4px;">
                Macro-level compensation intelligence, market parity distribution, and exception telemetry.
            </div>
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="metric-badge badge-success">● Audit Engine Active</span>
            <span class="metric-badge badge-info">Benchmark: FY2026</span>
        </div>
    </div>
</div>
""")

# Load Data
data = load_all_data()
df_emp = data.get("employees", pd.DataFrame())
df_sal = data.get("salary_records", pd.DataFrame())
df_flags = data.get("disparity_flags", pd.DataFrame())
df_props = data.get("adjustment_proposals", pd.DataFrame())
df_bands = data.get("compensation_bands", pd.DataFrame())

# Sidebar Filters
with st.sidebar:
    render_html("""
    <div style="font-size: 0.8rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px;">
        🔍 Global Filters
    </div>
    """)
    loc_col = "location_code" if "location_code" in df_emp.columns else ("location_id" if "location_id" in df_emp.columns else None)
    loc_options = ["All"] + sorted(df_emp[loc_col].dropna().unique().tolist()) if loc_col and not df_emp.empty else ["All"]
    selected_loc = st.selectbox("Location", loc_options)

    fam_col = "role_family" if "role_family" in df_emp.columns else None
    fam_options = ["All"] + sorted(df_emp[fam_col].dropna().unique().tolist()) if fam_col and not df_emp.empty else ["All"]
    selected_fam = st.selectbox("Role Family", fam_options)

# Filter data
filtered_emp = df_emp.copy()
if loc_col and selected_loc != "All":
    filtered_emp = filtered_emp[filtered_emp[loc_col] == selected_loc]
if fam_col and selected_fam != "All":
    filtered_emp = filtered_emp[filtered_emp[fam_col] == selected_fam]

filtered_sal = df_sal[df_sal["employee_id"].isin(filtered_emp["employee_id"])] if not df_sal.empty else df_sal

# Compute KPIs
total_emp = len(filtered_emp)
latest_sal = (
    filtered_sal.sort_values("effective_date", ascending=False)
    .groupby("employee_id")
    .first()
    .reset_index()
) if not filtered_sal.empty else pd.DataFrame()

avg_cr = latest_sal["compa_ratio"].mean() if not latest_sal.empty and "compa_ratio" in latest_sal else 100.0
below_band = len(latest_sal[latest_sal["compa_ratio"] < 80]) if not latest_sal.empty and "compa_ratio" in latest_sal else 0
above_band = len(latest_sal[latest_sal["compa_ratio"] > 120]) if not latest_sal.empty and "compa_ratio" in latest_sal else 0
within_band = total_emp - below_band - above_band

filtered_flags = df_flags[df_flags["employee_id"].isin(filtered_emp["employee_id"])] if not df_flags.empty else df_flags
open_disparities = len(filtered_flags[filtered_flags["investigation_status"] == "OPEN"])

filtered_props = df_props[df_props["employee_id"].isin(filtered_emp["employee_id"])] if not df_props.empty else df_props
pending_props = len(filtered_props[filtered_props["final_status"] == "OPEN"])

# Primary Executive KPI Row (4 Top Cards)
render_kpi_row([
    {
        "title": "Filtered Headcount",
        "value": f"{total_emp:,}",
        "subtitle": "Active Employees in Cohort",
        "color": "#3B82F6",
        "icon": "👥",
        "delta": "Live cohort",
    },
    {
        "title": "Avg Compa-Ratio",
        "value": f"{avg_cr:.1f}%",
        "subtitle": "Market Parity Baseline: 100%",
        "color": "#10B981",
        "icon": "⚖️",
        "delta": "Parity target 80–120%",
    },
    {
        "title": "Open Disparities",
        "value": f"{open_disparities:,}",
        "subtitle": "Exceptions Requiring HR Audit",
        "color": "#F59E0B",
        "icon": "⚠️",
        "delta": "Audit Queue",
    },
    {
        "title": "Pending Proposals",
        "value": f"{pending_props:,}",
        "subtitle": "In Governance Pipeline",
        "color": "#6366F1",
        "icon": "📑",
        "delta": "Dual-Approval Required",
    },
])

st.write("")

# Secondary Operational Row (3 Corridor Cards with Progress Bars)
cor_c1, cor_c2, cor_c3 = st.columns(3)

with cor_c1:
    pct_within = (within_band / total_emp * 100) if total_emp else 0
    render_html(f"""
    <div class="glass-card" style="padding: 16px 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.82rem; font-weight: 700; color: #1E293B;">Within Band Compliant (80%–120%)</span>
            <span class="metric-badge badge-success">{within_band:,}</span>
        </div>
        <div style="background: #E2E8F0; border-radius: 8px; height: 8px; overflow: hidden; margin-top: 8px;">
            <div style="background: #10B981; width: {pct_within:.1f}%; height: 100%; border-radius: 8px;"></div>
        </div>
        <div style="font-size: 0.76rem; color: #64748B; margin-top: 6px;">{pct_within:.1f}% of cohort compensated within target market corridor.</div>
    </div>
    """)

with cor_c2:
    pct_below = (below_band / total_emp * 100) if total_emp else 0
    render_html(f"""
    <div class="glass-card" style="padding: 16px 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.82rem; font-weight: 700; color: #1E293B;">Below Band Corridor (&lt;80%)</span>
            <span class="metric-badge badge-danger">{below_band:,}</span>
        </div>
        <div style="background: #E2E8F0; border-radius: 8px; height: 8px; overflow: hidden; margin-top: 8px;">
            <div style="background: #EF4444; width: {pct_below:.1f}%; height: 100%; border-radius: 8px;"></div>
        </div>
        <div style="font-size: 0.76rem; color: #64748B; margin-top: 6px;">{pct_below:.1f}% requires upward salary adjustment to reach band minimum.</div>
    </div>
    """)

with cor_c3:
    pct_above = (above_band / total_emp * 100) if total_emp else 0
    render_html(f"""
    <div class="glass-card" style="padding: 16px 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.82rem; font-weight: 700; color: #1E293B;">Market Premium Cohort (&gt;120%)</span>
            <span class="metric-badge badge-purple">{above_band:,}</span>
        </div>
        <div style="background: #E2E8F0; border-radius: 8px; height: 8px; overflow: hidden; margin-top: 8px;">
            <div style="background: #8B5CF6; width: {pct_above:.1f}%; height: 100%; border-radius: 8px;"></div>
        </div>
        <div style="font-size: 0.76rem; color: #64748B; margin-top: 6px;">{pct_above:.1f}% top performers or high-demand market specializations.</div>
    </div>
    """)

# Visualizations Row 1
col1, col2 = st.columns(2)
with col1:
    render_html("""<div class="plotly-card">""")
    st.plotly_chart(compa_ratio_distribution(latest_sal), width="stretch")
    render_html("</div>")

with col2:
    render_html("""<div class="plotly-card">""")
    st.plotly_chart(salary_distribution_histogram(latest_sal), width="stretch")
    render_html("</div>")

# Visualizations Row 2
col3, col4 = st.columns(2)
with col3:
    render_html("""<div class="plotly-card">""")
    st.plotly_chart(salary_by_role_boxplot(latest_sal, filtered_emp), width="stretch")
    render_html("</div>")

with col4:
    render_html("""<div class="plotly-card">""")
    st.plotly_chart(salary_by_location_bar(latest_sal, filtered_emp), width="stretch")
    render_html("</div>")

# Recent Exception Activity Table
render_html("""
<div class="glass-card" style="margin-top: 10px;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.25rem;">🚨</span>
            <div>
                <span style="font-size: 1.05rem; font-weight: 800; color: #0F172A;">Recent Disparity & Compliance Exceptions</span>
                <div style="font-size: 0.78rem; color: #64748B;">Latest flagged records requiring investigation or remediation.</div>
            </div>
        </div>
        <span class="metric-badge badge-warning">Audit Telemetry</span>
    </div>
""")

if not filtered_flags.empty:
    display_flags = filtered_flags.head(15)[[
        "flag_id", "employee_id", "issue_type", "severity", "salary_difference",
        "disparity_pct", "investigation_status", "root_cause"
    ]].copy()
    display_flags["salary_difference"] = display_flags["salary_difference"].apply(format_inr)
    display_flags["disparity_pct"] = display_flags["disparity_pct"].apply(lambda x: f"{x:.1f}%")
    render_styled_dataframe(display_flags, height=350)
else:
    st.success("No active disparity exceptions detected in the selected cohort.")

render_html("</div>")
