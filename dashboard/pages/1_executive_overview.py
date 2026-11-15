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

from dashboard.utils.data_loader import load_all_data, compute_live_metrics
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.components.charts import (
    compa_ratio_distribution,
    salary_distribution_histogram,
    salary_by_location_bar,
    salary_by_role_boxplot,
)
from dashboard.components.tables import format_inr, render_styled_dataframe

st.title("📊 Executive Compensation & Pay Equity Overview")
st.markdown("Macro-level compensation intelligence, market parity distribution, and exception telemetry.")

# Load Data
data = load_all_data()
df_emp = data.get("employees", pd.DataFrame())
df_sal = data.get("salary_records", pd.DataFrame())
df_flags = data.get("disparity_flags", pd.DataFrame())
df_props = data.get("adjustment_proposals", pd.DataFrame())
df_bands = data.get("compensation_bands", pd.DataFrame())

# Sidebar Filters
with st.sidebar:
    st.markdown("### 🔍 Global Filters")
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

# KPI Cards
kpis = [
    {"title": "Filtered Headcount", "value": f"{total_emp:,}", "subtitle": "Total Active Employees", "color": "#3B82F6", "icon": "👥"},
    {"title": "Avg Compa-Ratio", "value": f"{avg_cr:.1f}%", "subtitle": "Parity Baseline = 100%", "color": "#10B981", "icon": "⚖️"},
    {"title": "Below Band (<80%)", "value": f"{below_band:,}", "subtitle": f"{(below_band/total_emp*100) if total_emp else 0:.1f}% of cohort", "color": "#EF4444", "icon": "🔻"},
    {"title": "Within Band", "value": f"{within_band:,}", "subtitle": f"{(within_band/total_emp*100) if total_emp else 0:.1f}% compliant", "color": "#10B981", "icon": "✅"},
    {"title": "Above Band (>120%)", "value": f"{above_band:,}", "subtitle": f"{(above_band/total_emp*100) if total_emp else 0:.1f}% premium", "color": "#8B5CF6", "icon": "🔺"},
    {"title": "Open Disparities", "value": f"{open_disparities:,}", "subtitle": "Exceptions Requiring HR Audit", "color": "#F59E0B", "icon": "⚠️"},
    {"title": "Pending Proposals", "value": f"{pending_props:,}", "subtitle": "In Approval Pipeline", "color": "#6366F1", "icon": "📑"},
]
render_kpi_row(kpis)

st.markdown("---")

# Visualizations Row 1
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(compa_ratio_distribution(latest_sal), use_container_width=True)
with col2:
    st.plotly_chart(salary_distribution_histogram(latest_sal), use_container_width=True)

# Visualizations Row 2
col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(salary_by_role_boxplot(latest_sal, filtered_emp), use_container_width=True)
with col4:
    st.plotly_chart(salary_by_location_bar(latest_sal, filtered_emp), use_container_width=True)

st.markdown("---")

# Recent Exception Activity Table
st.markdown("### 🚨 Recent Disparity & Compliance Exceptions")
st.caption("Latest 15 flagged records requiring investigation or remediation.")

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
