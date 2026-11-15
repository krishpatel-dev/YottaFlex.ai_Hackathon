"""
dashboard/pages/4_disparity_management.py
========================================
Page 4: Disparity & Exception Management Dashboard
Investigate the 5 mandatory negative exception scenarios, view audit evidence,
and manage the investigation resolution lifecycle.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
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
from dashboard.components.tables import format_inr, render_styled_dataframe

# Apply unified design system
inject_custom_css()

# Header (Inspired by Toota / Block AI)
st.markdown("""
<div style="margin-bottom: 22px;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
        <div>
            <div style="font-size: 0.8rem; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                Exception Governance • Compliance Telemetry
            </div>
            <div style="font-size: 1.85rem; font-weight: 800; color: #0F172A; letter-spacing: -0.025em; line-height: 1.2;">
                Disparity & Exception Management
            </div>
            <div style="font-size: 0.92rem; color: #64748B; margin-top: 4px;">
                Investigate compliance violations, unexplained pay gaps, and policy exceptions with complete evidentiary audit trails.
            </div>
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="metric-badge badge-danger">5 Mandatory Safeguards Active</span>
            <span class="metric-badge badge-warning">Audit Resolution Pipeline</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

data = load_all_data()
df_flags = data.get("disparity_flags", pd.DataFrame())
df_emp = data.get("employees", pd.DataFrame())

if df_flags.empty:
    st.info("No disparity flags recorded.")
    st.stop()

# Summary Metrics by Exception Scenario
issue_types = [
    "SALARY_COMPARED_TO_EXPIRED_BAND",
    "FTE_IGNORED",
    "CURRENCY_CONVERSION_MISSING",
    "ADJUSTMENT_WITHOUT_APPROVAL",
    "INCOMPARABLE_ROLES_GROUPED",
    "UNEXPLAINED_DISPARITY",
]

# Render 6 Exception Inventory Cards
summary_cols = st.columns(6)

card_configs = [
    {"type": "SALARY_COMPARED_TO_EXPIRED_BAND", "label": "Expired Band", "badge": "badge-danger", "color": "#EF4444", "icon": "⏳"},
    {"type": "FTE_IGNORED", "label": "FTE Ignored", "badge": "badge-warning", "color": "#F59E0B", "icon": "⏱️"},
    {"type": "CURRENCY_CONVERSION_MISSING", "label": "FX Missing", "badge": "badge-danger", "color": "#EF4444", "icon": "💱"},
    {"type": "ADJUSTMENT_WITHOUT_APPROVAL", "label": "Unapproved", "badge": "badge-danger", "color": "#EF4444", "icon": "🚫"},
    {"type": "INCOMPARABLE_ROLES_GROUPED", "label": "Incomparable", "badge": "badge-warning", "color": "#F59E0B", "icon": "🔀"},
    {"type": "UNEXPLAINED_DISPARITY", "label": "Unexplained", "badge": "badge-purple", "color": "#8B5CF6", "icon": "⚠️"},
]

for idx, cfg in enumerate(card_configs):
    count = len(df_flags[df_flags["issue_type"] == cfg["type"]])
    with summary_cols[idx]:
        st.markdown(f"""
        <div class="glass-card" style="padding: 14px 16px; margin-bottom: 16px; border-top: 3px solid {cfg['color']};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase;">{cfg['label']}</span>
                <span>{cfg['icon']}</span>
            </div>
            <div style="font-size: 1.55rem; font-weight: 800; color: #0F172A; margin: 2px 0;">{count:,}</div>
            <span class="metric-badge {cfg['badge']}" style="padding: 2px 6px; font-size: 0.68rem;">Active Cases</span>
        </div>
        """, unsafe_allow_html=True)

# Filters & Search Card
st.markdown("""<div class="glass-card" style="padding: 18px 20px 10px 20px;">""", unsafe_allow_html=True)
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    type_filter = st.selectbox("Filter by Exception Category", ["All"] + issue_types)
with col_f2:
    sev_filter = st.selectbox("Severity Rating", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
with col_f3:
    status_filter = st.selectbox("Investigation Status", ["All", "OPEN", "UNDER_REVIEW", "RESOLVED", "DISMISSED"])

search_term = st.text_input("🔍 Search by Flag ID or Employee ID:", "")
st.markdown("</div>", unsafe_allow_html=True)

filtered = df_flags.copy()
if type_filter != "All":
    filtered = filtered[filtered["issue_type"] == type_filter]
if sev_filter != "All":
    filtered = filtered[filtered["severity"] == sev_filter]
if status_filter != "All":
    filtered = filtered[filtered["investigation_status"] == status_filter]

if search_term:
    filtered = filtered[
        filtered["flag_id"].str.contains(search_term, case=False, na=False) |
        filtered["employee_id"].str.contains(search_term, case=False, na=False)
    ]

# Main Interactive Exceptions Table
st.markdown(f"""
<div class="glass-card" style="margin-top: 10px;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.25rem;">📑</span>
            <div>
                <span style="font-size: 1.05rem; font-weight: 800; color: #0F172A;">Exception Inventory Ledger</span>
                <div style="font-size: 0.78rem; color: #64748B;">Showing {len(filtered):,} matching exception records out of {len(df_flags):,} total cases.</div>
            </div>
        </div>
        <span class="metric-badge badge-info">Auditable Ledger</span>
    </div>
""", unsafe_allow_html=True)

if "root_cause" not in filtered.columns:
    filtered["root_cause"] = filtered.get("detection_rule", "Disparity detected")

display_cols = [
    "flag_id", "employee_id", "issue_type", "severity", "salary_difference",
    "disparity_pct", "investigation_status", "root_cause"
]
display_df = filtered[[c for c in display_cols if c in filtered.columns]].copy()
if "salary_difference" in display_df.columns:
    display_df["salary_difference"] = display_df["salary_difference"].apply(format_inr)
if "disparity_pct" in display_df.columns:
    display_df["disparity_pct"] = display_df["disparity_pct"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%")

render_styled_dataframe(display_df, height=350)
st.markdown("</div>", unsafe_allow_html=True)

# Deep-Dive Investigation Panel
st.markdown("""
<div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin: 20px 0 12px 0;">
    🔎 Investigation & Remediation Console
</div>
""", unsafe_allow_html=True)

selected_flag_id = st.selectbox(
    "Select an Exception Record to Inspect & Update:",
    options=filtered["flag_id"].tolist() if not filtered.empty else ["None"],
)

if selected_flag_id != "None" and not filtered.empty:
    record = filtered[filtered["flag_id"] == selected_flag_id].iloc[0]
    emp_id = record.get("employee_id", "Unknown")

    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown(f"""
        <div class="glass-card">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <div style="font-weight: 800; font-size: 1.05rem; color: #0F172A;">📄 Exception Dossier: <code>{record.get('flag_id')}</code></div>
                <span class="metric-badge badge-warning">{record.get('severity')}</span>
            </div>
            <div style="font-size: 0.85rem; line-height: 1.6; color: #1E293B;">
                <div>• <b>Target Employee:</b> <code>{emp_id}</code></div>
                <div>• <b>Exception Category:</b> <code>{record.get('issue_type')}</code></div>
                <div>• <b>Detection Rule:</b> <code>{record.get('detection_rule')}</code></div>
                <div>• <b>Detection Timestamp:</b> {record.get('detection_timestamp')}</div>
                <div>• <b>Current Status:</b> <span class="metric-badge badge-info">{record.get('investigation_status')}</span></div>
                <div style="margin-top: 8px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Root Cause Analysis</div>
                    <div style="font-size: 0.84rem; color: #0F172A; margin-top: 2px;">{record.get('root_cause', record.get('detection_rule', 'N/A'))}</div>
                </div>
                <div style="margin-top: 8px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Expected System Response</div>
                    <div style="font-size: 0.84rem; color: #0F172A; margin-top: 2px;">{record.get('expected_response', 'N/A')}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size: 0.82rem; font-weight: 700; color: #64748B; margin-top: 10px; margin-bottom: 4px;'>SUPPORTING EVIDENCE PAYLOAD:</div>", unsafe_allow_html=True)
        try:
            ev_json = json.loads(str(record.get("supporting_evidence", "{}")))
            st.json(ev_json)
        except Exception:
            st.code(str(record.get("supporting_evidence", "")))
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="glass-card">
            <div style="font-weight: 800; font-size: 1.05rem; color: #0F172A; margin-bottom: 12px;">
                ✍️ Update Investigation State
            </div>
        """, unsafe_allow_html=True)

        curr_status = record.get("investigation_status", "OPEN")
        status_opts = ["OPEN", "UNDER_REVIEW", "RESOLVED", "DISMISSED"]
        status_idx = status_opts.index(curr_status) if curr_status in status_opts else 0

        new_status = st.selectbox("Change Status:", status_opts, index=status_idx)
        notes = st.text_area(
            "Investigation Notes / Justification:",
            value=record.get("resolution_notes") or "",
            placeholder="Document HR audit findings, employee interview notes, or remediation rationale..."
        )

        if st.button("💾 Save Investigation Update", type="primary"):
            idx = df_flags[df_flags["flag_id"] == selected_flag_id].index
            if not idx.empty:
                df_flags.at[idx[0], "investigation_status"] = new_status
                df_flags.at[idx[0], "resolution_notes"] = notes
                if new_status in ("RESOLVED", "DISMISSED"):
                    df_flags.at[idx[0], "resolved_at"] = datetime.now().isoformat()
                st.success(f"Successfully updated {selected_flag_id} to {new_status}!")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
