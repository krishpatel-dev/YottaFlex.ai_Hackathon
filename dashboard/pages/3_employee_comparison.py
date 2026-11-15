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
from dashboard.components.styles import inject_custom_css, render_html
from dashboard.components.tables import format_inr

# Apply unified design system
inject_custom_css()

# Header (Inspired by Toota / Block AI)
render_html("""
<div style="margin-bottom: 22px;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
        <div>
            <div style="font-size: 0.8rem; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                Peer Audit • Equity Diagnostics
            </div>
            <div style="font-size: 1.85rem; font-weight: 800; color: #0F172A; letter-spacing: -0.025em; line-height: 1.2;">
                Side-by-Side Peer Compensation Audit
            </div>
            <div style="font-size: 0.92rem; color: #64748B; margin-top: 4px;">
                Compare 2 to 4 employees to audit salary parity, verify comparability factors, and identify documented justifications.
            </div>
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="metric-badge badge-purple">Multi-Dimensional Radar</span>
            <span class="metric-badge badge-info">Explainable Justifications</span>
        </div>
    </div>
</div>
""")

data = load_all_data()
df_emp = data.get("employees", pd.DataFrame())
df_sal = data.get("salary_records", pd.DataFrame())
df_bands = data.get("compensation_bands", pd.DataFrame())
df_perf = data.get("performance_evidence", pd.DataFrame())
df_tenure = data.get("tenure", pd.DataFrame())
df_promo = data.get("promotions", pd.DataFrame())

# Employee Search & Multi-Select
emp_options = df_emp.apply(
    lambda r: f"{r['employee_id']} - {r.get('full_name', 'Employee')} ({r.get('role_name', r.get('role_id', 'Role'))}, {r.get('level_code', r.get('level_id', 'Level'))})",
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
        emp_salaries = df_sal[df_sal["employee_id"] == eid].sort_values("effective_date", ascending=False)
        sal = emp_salaries.iloc[0] if not emp_salaries.empty else {}

        band_id = sal.get("band_id")
        band = df_bands[df_bands["band_id"] == band_id].iloc[0] if band_id and not df_bands[df_bands["band_id"] == band_id].empty else {}

        emp_perf = df_perf[df_perf["employee_id"] == eid].sort_values("review_date", ascending=False)
        latest_p = emp_perf.iloc[0] if not emp_perf.empty else {}

        emp_ten = df_tenure[df_tenure["employee_id"] == eid]
        ten = emp_ten.iloc[0] if not emp_ten.empty else {}

        emp_promos = df_promo[df_promo["employee_id"] == eid]
        promo_count = len(emp_promos)

        profile = {
            "employee_id": eid,
            "full_name": emp.get("full_name", eid),
            "role_name": emp.get("role_name", emp.get("role_id", "N/A")),
            "role_family": emp.get("role_family", "N/A"),
            "level_code": emp.get("level_code", emp.get("level_id", "N/A")),
            "location_code": emp.get("location_code", emp.get("location_id", "N/A")),
            "employment_type": emp.get("employment_type", "FULL_TIME"),
            "fte_fraction": float(emp.get("fte_fraction", 1.0) or 1.0),
            "hire_date": emp.get("hire_date", "2024-01-01"),
            "annual_salary_raw": float(sal.get("annual_salary", 0) or 0),
            "annual_salary_fte": float(sal.get("annual_salary_fte", 0) or 0),
            "currency_code": sal.get("currency_code", "INR"),
            "band_id": band_id,
            "band_min": float(band.get("band_min", 0) or 0),
            "band_mid": float(band.get("band_mid", 0) or 0),
            "band_max": float(band.get("band_max", 0) or 0),
            "compa_ratio": float(sal.get("compa_ratio", 100.0) or 100.0),
            "perf_rating": float(latest_p.get("rating", 3.0) or 3.0),
            "perf_label": latest_p.get("rating_label", "MEETS"),
            "perf_factors": latest_p.get("documented_factors", "[]"),
            "months_in_company": int(ten.get("months_in_company", 12) or 12),
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

    render_html("""
    <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin: 18px 0 12px 0;">
        Side-by-Side Employee Dossier
    </div>
    """)

    cols = st.columns(len(profiles))

    avatar_gradients = [
        "linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)",
        "linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)",
        "linear-gradient(135deg, #10B981 0%, #047857 100%)",
        "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
    ]

    for idx, (col, p) in enumerate(zip(cols, profiles)):
        grad = avatar_gradients[idx % len(avatar_gradients)]
        initials = "".join([part[0] for part in p["full_name"].split()[:2]]).upper() or "EM"
        b_min = p["band_min"]
        b_max = p["band_max"]
        b_range = max(1.0, b_max - b_min)
        penetration_pct = max(0.0, min(100.0, (p["annual_salary_fte"] - b_min) / b_range * 100.0))

        cr_badge_class = "badge-success" if 80 <= p["compa_ratio"] <= 120 else ("badge-danger" if p["compa_ratio"] < 80 else "badge-purple")
        cr_status_text = "Midpoint Parity" if 80 <= p["compa_ratio"] <= 120 else ("Below Band" if p["compa_ratio"] < 80 else "Market Premium")

        card_html = (
            f'<div class="glass-card" style="padding: 20px; position: relative; border-top: 4px solid #3B82F6;">'
            f'<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 14px;">'
            f'<div style="width: 44px; height: 44px; border-radius: 12px; background: {grad}; color: white; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">{initials}</div>'
            f'<div>'
            f'<div style="font-weight: 800; font-size: 1.15rem; color: #0F172A; line-height: 1.2;">{p["full_name"]}</div>'
            f'<div style="font-size: 0.78rem; color: #64748B;"><code>{p["employee_id"]}</code> • {p["role_name"]}</div>'
            f'</div>'
            f'</div>'
            f'<div style="margin: 14px 0 10px 0; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px;">'
            f'<div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">FTE Normalized Compensation</div>'
            f'<div style="font-size: 1.7rem; font-weight: 800; color: #0F172A; margin: 2px 0 6px 0;">{format_inr(p["annual_salary_fte"])}</div>'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'<span class="metric-badge {cr_badge_class}">{p["compa_ratio"]:.1f}% Compa-Ratio</span>'
            f'<span style="font-size: 0.75rem; color: #64748B;">{cr_status_text}</span>'
            f'</div>'
            f'</div>'
            f'<div style="margin-bottom: 16px;">'
            f'<div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: #64748B; margin-bottom: 4px;">'
            f'<span>Band Min ({format_inr(b_min)})</span>'
            f'<span style="font-weight: 700; color: #1E293B;">Penetration: {penetration_pct:.0f}%</span>'
            f'<span>Max ({format_inr(b_max)})</span>'
            f'</div>'
            f'<div style="background: #E2E8F0; border-radius: 6px; height: 6px; overflow: hidden;">'
            f'<div style="background: linear-gradient(90deg, #3B82F6, #10B981); width: {penetration_pct:.1f}%; height: 100%;"></div>'
            f'</div>'
            f'</div>'
            f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.8rem;">'
            f'<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 10px;">'
            f'<div style="font-size: 0.7rem; color: #64748B;">Level & Location</div>'
            f'<div style="font-weight: 700; color: #0F172A;">{p["level_code"]} • {p["location_code"]}</div>'
            f'</div>'
            f'<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 10px;">'
            f'<div style="font-size: 0.7rem; color: #64748B;">Employment Type</div>'
            f'<div style="font-weight: 700; color: #0F172A;">{p["employment_type"]} ({p["fte_fraction"]:.1f} FTE)</div>'
            f'</div>'
            f'<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 10px;">'
            f'<div style="font-size: 0.7rem; color: #64748B;">Tenure</div>'
            f'<div style="font-weight: 700; color: #0F172A;">{p["months_in_company"]} mos ({p["tenure_band"]})</div>'
            f'</div>'
            f'<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 10px;">'
            f'<div style="font-size: 0.7rem; color: #64748B;">Performance</div>'
            f'<div style="font-weight: 700; color: #0F172A;">⭐ {p["perf_rating"]:.1f} ({p["perf_label"]})</div>'
            f'</div>'
            f'</div>'
            f'<div style="margin-top: 10px; font-size: 0.76rem; color: #64748B; display: flex; justify-content: space-between;">'
            f'<span>Promotions: <b>{p["promotions_count"]}</b></span>'
            f'<span>Market Mid: <b>{format_inr(p["band_mid"])}</b></span>'
            f'</div>'
            f'</div>'
        )
        with col:
            render_html(card_html)

    # Radar Comparison Chart & Evaluation Split
    col_chart, col_eval = st.columns([1, 1])

    with col_chart:
        render_html("""<div class="plotly-card">""")
        st.plotly_chart(employee_comparison_radar(radar_data), width="stretch")
        render_html("</div>")

    with col_eval:
        pA, pB = profiles[0], profiles[1]
        sal_diff = abs(pA["annual_salary_fte"] - pB["annual_salary_fte"])
        higher_emp = pA if pA["annual_salary_fte"] >= pB["annual_salary_fte"] else pB
        lower_emp = pB if higher_emp == pA else pA

        same_role = (pA["role_family"] == pB["role_family"])
        same_level = (pA["level_code"] == pB["level_code"])
        same_loc = (pA["location_code"] == pB["location_code"])
        same_tenure = (pA["tenure_band"] == pB["tenure_band"])

        comparable_badge = "badge-success" if (same_role and same_level and same_loc) else "badge-warning"
        comparable_label = "Comparable Cohort" if (same_role and same_level and same_loc) else "Incomparable Baseline"

        render_html(f"""
        <div class="glass-card" style="margin-bottom: 14px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.15rem;">⚖️</span>
                    <span style="font-weight: 800; font-size: 1rem; color: #0F172A;">Peer Comparability Audit</span>
                </div>
                <span class="metric-badge {comparable_badge}">{comparable_label}</span>
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                <div style="font-size: 0.74rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Observed Salary Delta</div>
                <div style="font-size: 1.3rem; font-weight: 800; color: #0F172A; margin: 2px 0;">
                    <b>{higher_emp['full_name']}</b> earns <span style="color: #2563EB;">+{format_inr(sal_diff)}</span> more than <b>{lower_emp['full_name']}</b>
                </div>
            </div>
        """)

        if same_role and same_level and same_loc:
            st.success("✅ **Directly Comparable Peers**: Both individuals share identical role families, career levels, and business locations.")
        else:
            reasons = []
            if not same_role: reasons.append(f"Different role families ({pA['role_family']} vs {pB['role_family']})")
            if not same_level: reasons.append(f"Different career levels ({pA['level_code']} vs {pB['level_code']})")
            if not same_loc: reasons.append(f"Different business locations ({pA['location_code']} vs {pB['location_code']})")
            st.warning(f"⚠️ **Incomparable Baseline Factors**: {'; '.join(reasons)}.")

        render_html("</div>")

        # Documented Justification Card
        justifications = []
        if higher_emp["perf_rating"] >= 4.5 and lower_emp["perf_rating"] < 4.0:
            justifications.append(f"Superior Performance Record: {higher_emp['perf_rating']} ({higher_emp['perf_label']}) vs {lower_emp['perf_rating']} ({lower_emp['perf_label']})")
        if higher_emp["promotions_count"] > lower_emp["promotions_count"]:
            justifications.append(f"Career Progression: {higher_emp['promotions_count']} documented promotions vs {lower_emp['promotions_count']}")
        if higher_emp["months_in_company"] > lower_emp["months_in_company"] + 12:
            justifications.append(f"Tenured Service: {higher_emp['months_in_company']} months vs {lower_emp['months_in_company']} months")

        render_html("""
        <div class="glass-card">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.15rem;">📋</span>
                    <span style="font-weight: 800; font-size: 1rem; color: #0F172A;">Documented Equity Justification Analysis</span>
                </div>
            </div>
        """)

        if justifications:
            st.info("💡 **Documented Explanations Identified:**\n" + "\n".join([f"- {j}" for j in justifications]))
        else:
            st.error("🚨 **POTENTIAL UNEXPLAINED DISPARITY**: No documented performance or tenure factors fully justify the compensation gap. Flagged for HR compensation partner audit.")

        render_html("</div>")
