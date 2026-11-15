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
import pandas as pd

_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dashboard.utils.data_loader import load_all_data
from dashboard.components.charts import approval_funnel
from dashboard.components.tables import format_inr, render_styled_dataframe
from src.engine.adjustment_engine import ProposalStateMachine

st.title("📑 Salary Adjustment Proposals & Governance Workflow")
st.markdown("Review data-driven adjustment recommendations, process managerial and HR approvals, and trace auditable governance histories.")

data = load_all_data()
df_props = data.get("adjustment_proposals", pd.DataFrame())
df_emp = data.get("employees", pd.DataFrame())
df_bands = data.get("compensation_bands", pd.DataFrame())

if df_props.empty:
    st.info("No adjustment proposals generated.")
    st.stop()

# Approval Funnel Chart & Summary Metrics
col_funnel, col_stats = st.columns([1, 1])

with col_funnel:
    st.plotly_chart(approval_funnel(df_props), use_container_width=True)

with col_stats:
    st.markdown("### 📊 Governance Pipeline Summary")
    total_count = len(df_props)
    pending_mgr = len(df_props[df_props["manager_approval"] == "PENDING"])
    approved_mgr = len(df_props[df_props["manager_approval"] == "APPROVED"])
    approved_hr = len(df_props[df_props["hr_approval"] == "APPROVED"])
    implemented = len(df_props[df_props["final_status"] == "IMPLEMENTED"])

    st.markdown(f"""
    - **Total Active Proposals:** {total_count:,}
    - **Pending Manager Review:** {pending_mgr:,}
    - **Manager Approved:** {approved_mgr:,}
    - **HR Partner Approved:** {approved_hr:,}
    - **Fully Implemented in Payroll:** {implemented:,}
    """)
    st.info("🔒 **Governance Policy**: A proposal requires dual-authorization (both Manager and HR Partner sign-offs) before it can be flagged as IMPLEMENTED.")

st.markdown("---")

# Main Proposals Table
st.markdown("### 📋 Adjustment Proposals Review Board")

filter_status = st.selectbox(
    "Filter by Status:",
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

st.markdown("---")

# Interactive Approval Console
st.markdown("### ✍️ Decision & Approval Console")

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
        st.markdown(f"#### 👤 Employee: {emp_row.get('full_name', emp_id)}")
        st.caption(f"Proposal: `{selected_prop_id}` • Role: {emp_row.get('role_name', 'N/A')} ({emp_row.get('level_code', 'N/A')})")
        st.markdown(f"""
        - **Current Annual Compensation:** {format_inr(prop_row['current_salary'])}
        - **Proposed Target Salary:** **{format_inr(prop_row['proposed_salary_recommended'])}** (+{prop_row['proposed_change_pct']:.1f}%)
        - **Target Range:** {format_inr(prop_row['proposed_salary_min'])} – {format_inr(prop_row['proposed_salary_max'])}
        - **Trigger Reason:** `{prop_row['trigger_type']}`
        - **Manager Sign-off:** `{prop_row['manager_approval']}` ({prop_row.get('manager_approval_date') or 'Pending'})
        - **HR Partner Sign-off:** `{prop_row['hr_approval']}` ({prop_row.get('hr_approval_date') or 'Pending'})
        - **Lifecycle Status:** `{prop_row['final_status']}`
        """)

        # Linked Evidence
        st.markdown("**Linked Performance & Market Evidence:**")
        try:
            ev = json.loads(str(prop_row.get("evidence_ids", "[]")))
            st.json(ev)
        except Exception:
            st.write(str(prop_row.get("evidence_ids", "[]")))

    with c2:
        st.markdown("#### ⚖️ Governance Actions")
        role_actor = st.radio("Acting User Role:", ["MANAGER", "HR_PARTNER", "ADMIN"], horizontal=True)
        decision = st.selectbox("Action to Execute:", ["APPROVE", "REJECT", "IMPLEMENT", "WITHDRAW"])
        justification_notes = st.text_area("Audit Justification Notes:", placeholder="Document business rationale for approval or rejection...")

        if st.button("🚀 Submit Decision"):
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
