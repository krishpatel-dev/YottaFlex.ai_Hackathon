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
from dashboard.components.charts import (
    salary_by_level_bar,
    band_position_scatter,
    compa_ratio_distribution,
    salary_by_role_boxplot,
)
from dashboard.components.tables import format_inr, render_styled_dataframe

st.title("📈 Compensation Benchmarking & Band Position Analysis")
st.markdown("Inspect base compensation ranges, market alignment, and band penetration across cohorts.")

data = load_all_data()
df_emp = data.get("employees", pd.DataFrame())
df_sal = data.get("salary_records", pd.DataFrame())
df_bands = data.get("compensation_bands", pd.DataFrame())

# Sidebar Filters
with st.sidebar:
    st.markdown("### 🎛️ Analysis Filters")
    roles = ["All"] + sorted(df_emp["role_name"].dropna().unique().tolist()) if not df_emp.empty else ["All"]
    selected_role = st.selectbox("Role", roles)

    levels = ["All"] + ["L1", "L2", "L3", "L4", "L5", "L6", "M1", "M2", "M3", "M4"]
    selected_level = st.selectbox("Career Level", levels)

    locations = ["All"] + sorted(df_emp["location_code"].dropna().unique().tolist()) if not df_emp.empty else ["All"]
    selected_loc = st.selectbox("Location", locations)

    emp_types = ["All", "FULL_TIME", "PART_TIME"]
    selected_emp_type = st.selectbox("Employment Type", emp_types)

    cr_filter = st.slider("Compa-Ratio Range (%)", min_value=40, max_value=180, value=(60, 140))

# Filter cohort
filtered_emp = df_emp.copy()
if selected_role != "All":
    filtered_emp = filtered_emp[filtered_emp["role_name"] == selected_role]
if selected_level != "All":
    filtered_emp = filtered_emp[filtered_emp["level_code"] == selected_level]
if selected_loc != "All":
    filtered_emp = filtered_emp[filtered_emp["location_code"] == selected_loc]
if selected_emp_type != "All":
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

st.info(f"Displaying **{len(latest_sal):,}** employees matching active filter criteria.")

# Charts Row 1
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(salary_by_level_bar(latest_sal, filtered_emp), use_container_width=True)
with col2:
    st.plotly_chart(band_position_scatter(latest_sal, filtered_emp), use_container_width=True)

st.markdown("---")

# Out-of-Band Analysis Table
st.markdown("### ⚠️ Cohort Out-of-Band Exceptions (<80% or >120%)")
st.caption("Employees whose compensation falls outside the standard 80%–120% market midpoint corridor.")

merged_details = latest_sal.merge(
    filtered_emp[["employee_id", "full_name", "role_name", "level_code", "location_code", "employment_type", "fte_fraction"]],
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
