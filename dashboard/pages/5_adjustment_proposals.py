"""
dashboard/pages/5_adjustment_proposals.py
========================================
Page 5: Compensation Adjustment Proposals & Governance Workflow
Evidence-based salary remediation, manager/HR approval controls,
and complete auditable decision history.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
import streamlit as st
import numpy as np
import pandas as pd

_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dashboard.utils.data_loader import load_all_data
from dashboard.components.charts import approval_funnel
from dashboard.components.styles import inject_custom_css
from dashboard.components.tables import format_inr, render_styled_dataframe
from src.engine.adjustment_engine import ProposalStateMachine

# Apply unified design system
inject_custom_css()

# Header (Inspired by Toota / Block AI)
st.markdown("""
<div style="margin-bottom: 22px;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
        <div>
            <div style="font-size: 0.8rem; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                Governance Workflow • Remediation Pipeline
            </div>
            <div style="font-size: 1.85rem; font-weight: 800; color: #0F172A; letter-spacing: -0.025em; line-height: 1.2;">
                Salary Adjustment Proposals & Governance Workflow
            </div>
            <div style="font-size: 0.92rem; color: #64748B; margin-top: 4px;">
                Review data-driven adjustment recommendations, process managerial and HR approvals, and trace auditable governance histories.
            </div>
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="metric-badge badge-success">Dual-Signoff Protocol</span>
            <span class="metric-badge badge-info">SOX Compliant</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

data = load_all_data()
df_props = data.get("adjustment_proposals", pd.DataFrame())
df_emp = data.get("employees", pd.DataFrame())
df_bands = data.get("compensation_bands", pd.DataFrame())

if df_props.empty:
    st.info("No adjustment proposals generated.")
    st.stop()

# Approval Funnel Chart & Summary Metrics Split
col_funnel, col_stats = st.columns([1, 1])

with col_funnel:
    st.markdown("""<div class="plotly-card">""", unsafe_allow_html=True)
    st.plotly_chart(approval_funnel(df_props), width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

with col_stats:
    total_count = len(df_props)
    pending_mgr = len(df_props[df_props["manager_approval"] == "PENDING"])
    approved_mgr = len(df_props[df_props["manager_approval"] == "APPROVED"])
    approved_hr = len(df_props[df_props["hr_approval"] == "APPROVED"])
    implemented = len(df_props[df_props["final_status"] == "IMPLEMENTED"])

    st.markdown(f"""
    <div class="glass-card" style="padding: 20px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.2rem;">📊</span>
                <span style="font-weight: 800; font-size: 1.05rem; color: #0F172A;">Governance Pipeline Telemetry</span>
            </div>
            <span class="metric-badge badge-info">{total_count:,} Proposals</span>
        </div>

        <div style="display: flex; flex-direction: column; gap: 10px;">
            <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 3px;">
                    <span style="font-weight: 600; color: #1E293B;">Pending Manager Review</span>
                    <span style="font-weight: 700; color: #F59E0B;">{pending_mgr:,} ({pending_mgr/total_count*100:.1f}%)</span>
                </div>
                <div style="background: #E2E8F0; border-radius: 6px; height: 6px; overflow: hidden;">
                    <div style="background: #F59E0B; width: {pending_mgr/total_count*100:.1f}%; height: 100%;"></div>
                </div>
            </div>

            <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 3px;">
                    <span style="font-weight: 600; color: #1E293B;">Manager Approved (Awaiting HR)</span>
                    <span style="font-weight: 700; color: #3B82F6;">{approved_mgr:,} ({approved_mgr/total_count*100:.1f}%)</span>
                </div>
                <div style="background: #E2E8F0; border-radius: 6px; height: 6px; overflow: hidden;">
                    <div style="background: #3B82F6; width: {approved_mgr/total_count*100:.1f}%; height: 100%;"></div>
                </div>
            </div>

            <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 3px;">
                    <span style="font-weight: 600; color: #1E293B;">HR Partner Sign-off Granted</span>
                    <span style="font-weight: 700; color: #8B5CF6;">{approved_hr:,} ({approved_hr/total_count*100:.1f}%)</span>
                </div>
                <div style="background: #E2E8F0; border-radius: 6px; height: 6px; overflow: hidden;">
                    <div style="background: #8B5CF6; width: {approved_hr/total_count*100:.1f}%; height: 100%;"></div>
                </div>
            </div>

            <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 3px;">
                    <span style="font-weight: 600; color: #1E293B;">Fully Implemented in Payroll</span>
                    <span style="font-weight: 700; color: #10B981;">{implemented:,} ({implemented/total_count*100:.1f}%)</span>
                </div>
                <div style="background: #E2E8F0; border-radius: 6px; height: 6px; overflow: hidden;">
                    <div style="background: #10B981; width: {implemented/total_count*100:.1f}%; height: 100%;"></div>
                </div>
            </div>
        </div>

        <div style="margin-top: 14px; background: #EFF6FF; border: 1px solid #DBEAFE; border-radius: 10px; padding: 10px 12px; font-size: 0.78rem; color: #1E40AF; line-height: 1.4;">
            🔒 <b>Governance Policy:</b> Dual authorization is enforced. Both Manager and HR Partner sign-offs are strictly required prior to payroll execution.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main Proposals Table
st.markdown("""
<div class="glass-card" style="margin-top: 10px;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.25rem;">📋</span>
            <div>
                <span style="font-size: 1.05rem; font-weight: 800; color: #0F172A;">Adjustment Proposals Review Board</span>
                <div style="font-size: 0.78rem; color: #64748B;">Audit proposed compensation revisions and verify approval state history.</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

filter_status = st.selectbox(
    "Filter Proposals by Status:",
    ["All", "OPEN", "PENDING_HR", "IMPLEMENTED", "REJECTED", "WITHDRAWN"]
)

filtered_proposals = df_props.copy()
if filter_status != "All":
    filtered_proposals = filtered_proposals[filtered_proposals["final_status"] == filter_status]

if "proposed_change_pct" not in filtered_proposals.columns:
    curr = pd.to_numeric(filtered_proposals.get("current_salary", 0), errors="coerce").replace(0, np.nan)
    rec = pd.to_numeric(filtered_proposals.get("proposed_salary_recommended", 0), errors="coerce")
    filtered_proposals["proposed_change_pct"] = ((rec - curr) / curr * 100).fillna(0.0).round(1)

prop_cols = [
    "proposal_id", "employee_id", "trigger_type", "current_salary",
    "proposed_salary_recommended", "proposed_change_pct", "manager_approval",
    "hr_approval", "final_status"
]
display_props = filtered_proposals[[c for c in prop_cols if c in filtered_proposals.columns]].copy()

if "current_salary" in display_props.columns:
    display_props["current_salary"] = display_props["current_salary"].apply(format_inr)
if "proposed_salary_recommended" in display_props.columns:
    display_props["proposed_salary_recommended"] = display_props["proposed_salary_recommended"].apply(format_inr)
if "proposed_change_pct" in display_props.columns:
    display_props["proposed_change_pct"] = display_props["proposed_change_pct"].apply(lambda x: f"+{x:.1f}%" if pd.notna(x) else "+0.0%")

render_styled_dataframe(display_props, height=350)
st.markdown("</div>", unsafe_allow_html=True)

# Interactive Approval Console
st.markdown("""
<div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin: 20px 0 12px 0;">
    ✍️ Decision & Approval Console
</div>
""", unsafe_allow_html=True)

selected_prop_id = st.selectbox(
    "Select a Proposal to Review or Authorize:",
    options=filtered_proposals["proposal_id"].tolist() if not filtered_proposals.empty else ["None"]
)

if selected_prop_id != "None" and not filtered_proposals.empty:
    prop_row = df_props[df_props["proposal_id"] == selected_prop_id].iloc[0]
    emp_id = prop_row["employee_id"]
    emp_row = df_emp[df_emp["employee_id"] == emp_id].iloc[0] if not df_emp[df_emp["employee_id"] == emp_id].empty else {}

    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown(f"""
        <div class="glass-card">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <div style="font-weight: 800; font-size: 1.05rem; color: #0F172A;">👤 Target: <b>{emp_row.get('full_name', emp_id)}</b></div>
                <span class="metric-badge badge-purple">{prop_row['final_status']}</span>
            </div>
            <div style="font-size: 0.8rem; color: #64748B; margin-bottom: 12px;">
                Proposal: <code>{selected_prop_id}</code> • Role: {emp_row.get('role_name', 'N/A')} ({emp_row.get('level_code', 'N/A')})
            </div>

            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; margin-bottom: 12px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>
                        <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase;">Current Compensation</div>
                        <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A;">{format_inr(prop_row['current_salary'])}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase;">Proposed Target Salary</div>
                        <div style="font-size: 1.25rem; font-weight: 800; color: #10B981;">{format_inr(prop_row['proposed_salary_recommended'])} <span style="font-size: 0.8rem; color: #2563EB;">(+{prop_row.get('proposed_change_pct', 0):.1f}%)</span></div>
                    </div>
                </div>
                <div style="font-size: 0.76rem; color: #64748B; margin-top: 6px;">
                    Target Range: {format_inr(prop_row['proposed_salary_min'])} – {format_inr(prop_row['proposed_salary_max'])}
                </div>
            </div>

            <div style="font-size: 0.84rem; line-height: 1.7; color: #1E293B;">
                <div>• <b>Trigger Reason:</b> <code>{prop_row['trigger_type']}</code></div>
                <div>• <b>Manager Sign-off:</b> <code>{prop_row['manager_approval']}</code> ({prop_row.get('manager_approval_date') or 'Pending'})</div>
                <div>• <b>HR Partner Sign-off:</b> <code>{prop_row['hr_approval']}</code> ({prop_row.get('hr_approval_date') or 'Pending'})</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size: 0.82rem; font-weight: 700; color: #64748B; margin-top: 10px; margin-bottom: 4px;'>LINKED PERFORMANCE & MARKET EVIDENCE:</div>", unsafe_allow_html=True)
        try:
            ev = json.loads(str(prop_row.get("evidence_ids", "[]")))
            st.json(ev)
        except Exception:
            st.write(str(prop_row.get("evidence_ids", "[]")))
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="glass-card">
            <div style="font-weight: 800; font-size: 1.05rem; color: #0F172A; margin-bottom: 12px;">
                ⚖️ Governance Actions
            </div>
        """, unsafe_allow_html=True)

        role_actor = st.radio("Acting User Role:", ["MANAGER", "HR_PARTNER", "ADMIN"], horizontal=True)
        decision = st.selectbox("Action to Execute:", ["APPROVE", "REJECT", "IMPLEMENT", "WITHDRAW"])
        justification_notes = st.text_area(
            "Audit Justification Notes:",
            placeholder="Document formal business rationale for approval or rejection..."
        )

        if st.button("🚀 Submit Decision", type="primary"):
            prop_dict = prop_row.to_dict()
            try:
                if decision == "APPROVE":
                    target = "MANAGER_APPROVED" if role_actor == "MANAGER" else "HR_APPROVED"
                elif decision == "REJECT":
                    target = "MANAGER_REJECTED" if role_actor == "MANAGER" else "HR_REJECTED"
                elif decision == "IMPLEMENT":
                    target = "IMPLEMENTED"
                else:
                    target = "WITHDRAWN"

                updated_prop, audit_evt = ProposalStateMachine.transition(
                    prop_dict,
                    target_state=target,
                    actor_id="USER-CURRENT",
                    actor_role=role_actor,
                    notes=justification_notes,
                )

                # Persist in dataframe
                idx = df_props[df_props["proposal_id"] == selected_prop_id].index[0]
                for k, v in updated_prop.items():
                    df_props.at[idx, k] = v

                st.success(f"Action '{decision}' executed! Status is now {updated_prop['final_status']}.")
                st.rerun()

            except ValueError as ve:
                st.error(f"❌ Governance Policy Violation: {ve}")

        st.markdown("</div>", unsafe_allow_html=True)
