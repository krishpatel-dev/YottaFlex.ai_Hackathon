"""
dashboard/pages/2_compensation_analysis.py
=========================================
Page 2: Compensation Analysis Dashboard
Multi-dimensional salary benchmarking by role, career level, geography,
and granular compa-ratio evaluation.
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
from dashboard.components.styles import inject_custom_css
from dashboard.components.charts import (
    salary_by_level_bar,
    band_position_scatter,
    compa_ratio_distribution,
    salary_by_role_boxplot,
)
from dashboard.components.tables import format_inr, render_styled_dataframe

# Apply unified design system
inject_custom_css()

# Header (Inspired by Toota / Block AI)
st.markdown("""
<div style="margin-bottom: 22px;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
        <div>
            <div style="font-size: 0.8rem; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                Cohort Intelligence • Band Alignment
            </div>
            <div style="font-size: 1.85rem; font-weight: 800; color: #0F172A; letter-spacing: -0.025em; line-height: 1.2;">
                Compensation Benchmarking & Band Position Analysis
            </div>
            <div style="font-size: 0.92rem; color: #64748B; margin-top: 4px;">
                Inspect base compensation ranges, market alignment, and band penetration across cohorts.
            </div>
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="metric-badge badge-info">10 Career Levels</span>
            <span class="metric-badge badge-purple">8,190 Active Bands</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

data = load_all_data()
df_emp = data.get("employees", pd.DataFrame())
df_sal = data.get("salary_records", pd.DataFrame())
df_bands = data.get("compensation_bands", pd.DataFrame())

# Sidebar Filters
with st.sidebar:
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px;">
        🎛️ Analysis Filters
    </div>
    """, unsafe_allow_html=True)
    role_col = "role_name" if "role_name" in df_emp.columns else ("role_id" if "role_id" in df_emp.columns else None)
    roles = ["All"] + sorted(df_emp[role_col].dropna().unique().tolist()) if role_col and not df_emp.empty else ["All"]
    selected_role = st.selectbox("Role", roles)

    levels = ["All"] + ["L1", "L2", "L3", "L4", "L5", "L6", "M1", "M2", "M3", "M4"]
    selected_level = st.selectbox("Career Level", levels)

    loc_col = "location_code" if "location_code" in df_emp.columns else ("location_id" if "location_id" in df_emp.columns else None)
    locations = ["All"] + sorted(df_emp[loc_col].dropna().unique().tolist()) if loc_col and not df_emp.empty else ["All"]
    selected_loc = st.selectbox("Location", locations)

    emp_types = ["All", "FULL_TIME", "PART_TIME"]
    selected_emp_type = st.selectbox("Employment Type", emp_types)

    cr_filter = st.slider("Compa-Ratio Range (%)", min_value=40, max_value=180, value=(60, 140))

# Filter cohort
filtered_emp = df_emp.copy()
if role_col and selected_role != "All":
    filtered_emp = filtered_emp[filtered_emp[role_col] == selected_role]
if "level_code" in filtered_emp.columns and selected_level != "All":
    filtered_emp = filtered_emp[filtered_emp["level_code"] == selected_level]
if loc_col and selected_loc != "All":
    filtered_emp = filtered_emp[filtered_emp[loc_col] == selected_loc]
if "employment_type" in filtered_emp.columns and selected_emp_type != "All":
    filtered_emp = filtered_emp[filtered_emp["employment_type"] == selected_emp_type]

latest_sal = (
    df_sal[df_sal["employee_id"].isin(filtered_emp["employee_id"])]
    .sort_values("effective_date", ascending=False)
    .groupby("employee_id")
    .first()
    .reset_index()
) if not df_sal.empty else pd.DataFrame()

if not latest_sal.empty:
    latest_sal = latest_sal[
        (latest_sal["compa_ratio"] >= cr_filter[0]) &
        (latest_sal["compa_ratio"] <= cr_filter[1])
    ]

# Summary KPI Cards for active cohort
cohort_count = len(latest_sal)
cohort_median = (latest_sal["annual_salary_fte"].median() / 100_000.0) if not latest_sal.empty and "annual_salary_fte" in latest_sal else 0.0
cohort_cr = latest_sal["compa_ratio"].mean() if not latest_sal.empty and "compa_ratio" in latest_sal else 100.0
oob_count = len(latest_sal[(latest_sal["compa_ratio"] < 80) | (latest_sal["compa_ratio"] > 120)]) if not latest_sal.empty and "compa_ratio" in latest_sal else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(render_kpi_row([{
        "title": "Cohort Population",
        "value": f"{cohort_count:,}",
        "subtitle": "Matching Active Filters",
        "color": "#3B82F6",
        "icon": "👥",
        "delta": "Segmented",
    }]), unsafe_allow_html=True)

with c2:
    st.markdown(render_kpi_row([{
        "title": "Median FTE Salary",
        "value": f"₹{cohort_median:.2f} L",
        "subtitle": "Annualized Compensation",
        "color": "#10B981",
        "icon": "💰",
        "delta": "50th Percentile",
    }]), unsafe_allow_html=True)

with c3:
    st.markdown(render_kpi_row([{
        "title": "Avg Compa-Ratio",
        "value": f"{cohort_cr:.1f}%",
        "subtitle": "Midpoint Alignment",
        "color": "#8B5CF6",
        "icon": "🎯",
        "delta": "Corridor 80–120%",
    }]), unsafe_allow_html=True)

with c4:
    st.markdown(render_kpi_row([{
        "title": "Out-of-Band Count",
        "value": f"{oob_count:,}",
        "subtitle": f"{(oob_count/cohort_count*100) if cohort_count else 0:.1f}% of Segment",
        "color": "#EF4444" if oob_count > 0 else "#10B981",
        "icon": "⚠️",
        "delta": "Requires Audit",
    }]), unsafe_allow_html=True)

st.write("")

# Charts Row 1
col1, col2 = st.columns(2)
with col1:
    st.markdown("""<div class="plotly-card">""", unsafe_allow_html=True)
    st.plotly_chart(salary_by_level_bar(latest_sal, filtered_emp), width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("""<div class="plotly-card">""", unsafe_allow_html=True)
    st.plotly_chart(band_position_scatter(latest_sal, filtered_emp), width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

# Out-of-Band Analysis Table
st.markdown("""
<div class="glass-card" style="margin-top: 10px;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.25rem;">⚠️</span>
            <div>
                <span style="font-size: 1.05rem; font-weight: 800; color: #0F172A;">Cohort Out-of-Band Exceptions (&lt;80% or &gt;120%)</span>
                <div style="font-size: 0.78rem; color: #64748B;">Employees whose compensation falls outside the standard 80%–120% market midpoint corridor.</div>
            </div>
        </div>
        <span class="metric-badge badge-danger">Band Penetration Exception</span>
    </div>
""", unsafe_allow_html=True)

desired_emp_cols = ["employee_id", "full_name", "role_name", "level_code", "location_code", "employment_type", "fte_fraction"]
avail_emp_cols = [c for c in desired_emp_cols if c in filtered_emp.columns]
merged_details = latest_sal.merge(
    filtered_emp[avail_emp_cols],
    on="employee_id"
)
merged_details = merged_details.merge(
    df_bands[["band_id", "band_min", "band_mid", "band_max"]],
    on="band_id",
    how="left"
)

out_of_band = merged_details[
    (merged_details["compa_ratio"] < 80) | (merged_details["compa_ratio"] > 120)
].copy()

if not out_of_band.empty:
    out_of_band["Status"] = out_of_band["compa_ratio"].apply(
        lambda x: "🔻 BELOW BAND" if x < 80 else "🔺 ABOVE BAND"
    )
    display_oob = out_of_band[[
        "employee_id", "full_name", "role_name", "level_code", "location_code",
        "employment_type", "annual_salary_fte", "band_mid", "compa_ratio", "Status"
    ]].copy()
    display_oob["annual_salary_fte"] = display_oob["annual_salary_fte"].apply(format_inr)
    display_oob["band_mid"] = display_oob["band_mid"].apply(format_inr)
    display_oob["compa_ratio"] = display_oob["compa_ratio"].apply(lambda x: f"{x:.1f}%")
    render_styled_dataframe(display_oob, height=400)
else:
    st.success("All employees in the filtered cohort are strictly within the 80%–120% compensation corridor.")

st.markdown("</div>", unsafe_allow_html=True)
