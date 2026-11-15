"""
dashboard/pages/3_employee_comparison.py
=======================================
Page 3: Side-by-Side Employee Compensation Comparison
Investigate pay differentials, peer comparability, performance justifications,
and multi-dimensional equity gaps.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dashboard.utils.data_loader import load_all_data
from dashboard.components.charts import employee_comparison_radar
from dashboard.components.tables import format_inr

st.title("👥 Side-by-Side Peer Compensation Audit")
st.markdown("Compare 2 to 4 employees to audit salary parity, verify comparability factors, and identify documented justifications.")

data = load_all_data()
df_emp = data.get("employees", pd.DataFrame())
df_sal = data.get("salary_records", pd.DataFrame())
df_bands = data.get("compensation_bands", pd.DataFrame())
df_perf = data.get("performance_evidence", pd.DataFrame())
df_tenure = data.get("tenure", pd.DataFrame())
df_promo = data.get("promotions", pd.DataFrame())

# Employee Search & Multi-Select
emp_options = df_emp.apply(
    lambda r: f"{r['employee_id']} - {r['full_name']} ({r['role_name']}, {r['level_code']})",
    axis=1
).tolist() if not df_emp.empty else []

default_selection = emp_options[:2] if len(emp_options) >= 2 else []
selected_labels = st.multiselect(
    "Select 2 to 4 Employees to Compare:",
    options=emp_options,
    default=default_selection,
    max_selections=4,
)

selected_ids = [label.split(" - ")[0] for label in selected_labels]

if len(selected_ids) < 2:
    st.info("👆 Please select at least two employees from the search box above to begin side-by-side comparison.")
else:
    # Gather detailed profile for each selected employee
    profiles = []
    radar_data = []

    for eid in selected_ids:
        emp = df_emp[df_emp["employee_id"] == eid].iloc[0]
        # Latest salary
        emp_salaries = df_sal[df_sal["employee_id"] == eid].sort_values("effective_date", ascending=False)
        sal = emp_salaries.iloc[0] if not emp_salaries.empty else {}

        # Band
        band_id = sal.get("band_id")
        band = df_bands[df_bands["band_id"] == band_id].iloc[0] if band_id and not df_bands[df_bands["band_id"] == band_id].empty else {}

        # Latest Perf
        emp_perf = df_perf[df_perf["employee_id"] == eid].sort_values("review_date", ascending=False)
        latest_p = emp_perf.iloc[0] if not emp_perf.empty else {}

        # Tenure
        emp_ten = df_tenure[df_tenure["employee_id"] == eid]
        ten = emp_ten.iloc[0] if not emp_ten.empty else {}

        # Promotions
        emp_promos = df_promo[df_promo["employee_id"] == eid]
        promo_count = len(emp_promos)

        profile = {
            "employee_id": eid,
            "full_name": emp["full_name"],
            "role_name": emp["role_name"],
            "role_family": emp["role_family"],
            "level_code": emp["level_code"],
            "location_code": emp["location_code"],
            "employment_type": emp["employment_type"],
            "fte_fraction": float(emp.get("fte_fraction", 1.0)),
            "hire_date": emp["hire_date"],
            "annual_salary_raw": float(sal.get("annual_salary", 0)),
            "annual_salary_fte": float(sal.get("annual_salary_fte", 0)),
            "currency_code": sal.get("currency_code", "INR"),
            "band_id": band_id,
            "band_min": float(band.get("band_min", 0)),
            "band_mid": float(band.get("band_mid", 0)),
            "band_max": float(band.get("band_max", 0)),
            "compa_ratio": float(sal.get("compa_ratio", 100.0)),
            "perf_rating": float(latest_p.get("rating", 3.0)),
            "perf_label": latest_p.get("rating_label", "MEETS"),
            "perf_factors": latest_p.get("documented_factors", "[]"),
            "months_in_company": int(ten.get("months_in_company", 12)),
            "tenure_band": ten.get("tenure_band", "1-3YR"),
            "promotions_count": promo_count,
        }
        profiles.append(profile)

        radar_data.append({
            "full_name": profile["full_name"],
            "employee_id": profile["employee_id"],
            "compa_ratio": profile["compa_ratio"],
            "performance_rating": profile["perf_rating"],
            "band_position": (profile["annual_salary_fte"] - profile["band_min"]) / max(1, (profile["band_max"] - profile["band_min"])),
            "months_in_company": profile["months_in_company"],
            "relative_peer_pct": min(100, (profile["compa_ratio"] / 120.0) * 100),
        })

    st.markdown("### 📋 Side-by-Side Comparison Profile")
    cols = st.columns(len(profiles))

    for idx, (col, p) in enumerate(zip(cols, profiles)):
        with col:
            st.markdown(f"#### 👤 {p['full_name']}")
            st.caption(f"ID: `{p['employee_id']}` • {p['role_name']}")
            st.metric("Annual Salary (FTE)", format_inr(p["annual_salary_fte"]))
            st.metric("Compa-Ratio", f"{p['compa_ratio']:.1f}%")
            st.markdown(f"""
            - **Career Level:** `{p['level_code']}`
            - **Location:** `{p['location_code']}`
            - **Employment Type:** `{p['employment_type']}` ({p['fte_fraction']:.2f} FTE)
            - **Tenure:** {p['months_in_company']} months (`{p['tenure_band']}`)
            - **Performance Rating:** {p['perf_rating']:.1f} / 5.0 (`{p['perf_label']}`)
            - **Promotions:** {p['promotions_count']} received
            - **Market Midpoint:** {format_inr(p['band_mid'])}
            - **Band Range:** {format_inr(p['band_min'])} - {format_inr(p['band_max'])}
            """)

    st.markdown("---")

    # Radar Comparison Chart
    col_chart, col_eval = st.columns([1, 1])

    with col_chart:
        st.plotly_chart(employee_comparison_radar(radar_data), use_container_width=True)

    with col_eval:
        st.markdown("### ⚖️ Comparability & Justification Analysis")

        # Compare pair A vs B
        pA, pB = profiles[0], profiles[1]
        sal_diff = abs(pA["annual_salary_fte"] - pB["annual_salary_fte"])
        higher_emp = pA if pA["annual_salary_fte"] >= pB["annual_salary_fte"] else pB
        lower_emp = pB if higher_emp == pA else pA

        st.markdown(f"""
        **Salary Delta:**  
        **{higher_emp['full_name']}** earns **{format_inr(sal_diff)}** more than **{lower_emp['full_name']}**.
        """)

        # Check Comparability Factors
        same_role = (pA["role_family"] == pB["role_family"])
        same_level = (pA["level_code"] == pB["level_code"])
        same_loc = (pA["location_code"] == pB["location_code"])
        same_tenure = (pA["tenure_band"] == pB["tenure_band"])

        st.markdown("#### 1. Peer Comparability Factors")
        if same_role and same_level and same_loc:
            st.success("✅ **Directly Comparable Peers**: Same role family, career level, and business location.")
        else:
            reasons = []
            if not same_role: reasons.append(f"Different role families ({pA['role_family']} vs {pB['role_family']})")
            if not same_level: reasons.append(f"Different career levels ({pA['level_code']} vs {pB['level_code']})")
            if not same_loc: reasons.append(f"Different locations ({pA['location_code']} vs {pB['location_code']})")
            st.warning(f"⚠️ **Incomparable Baseline**: {'; '.join(reasons)}.")

        st.markdown("#### 2. Documented Justification Analysis")
        justifications = []
        if higher_emp["perf_rating"] >= 4.5 and lower_emp["perf_rating"] < 4.0:
            justifications.append(f"Higher documented performance rating: {higher_emp['perf_rating']} ({higher_emp['perf_label']}) vs {lower_emp['perf_rating']} ({lower_emp['perf_label']})")
        if higher_emp["promotions_count"] > lower_emp["promotions_count"]:
            justifications.append(f"Promotion history: {higher_emp['promotions_count']} promotions vs {lower_emp['promotions_count']}")
        if higher_emp["months_in_company"] > lower_emp["months_in_company"] + 12:
            justifications.append(f"Longer tenure: {higher_emp['months_in_company']} months vs {lower_emp['months_in_company']} months")

        if justifications:
            st.info("💡 **Documented Explanations Found:**\n" + "\n".join([f"- {j}" for j in justifications]))
        else:
            st.error("🚨 **POTENTIAL UNEXPLAINED DISPARITY**: No documented performance or tenure factors fully justify the compensation gap. Flagged for HR compensation partner audit.")
