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
from dashboard.components.tables import format_inr, render_styled_dataframe

st.title("🚨 Disparity & Exception Management")
st.markdown("Investigate compliance violations, unexplained pay gaps, and policy exceptions with complete evidentiary audit trails.")

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

st.markdown("### 📊 Exception Inventory by Governance Category")
summary_cols = st.columns(6)

for idx, itype in enumerate(issue_types):
    count = len(df_flags[df_flags["issue_type"] == itype])
    with summary_cols[idx]:
        short_name = itype.replace("SALARY_COMPARED_TO_", "").replace("_CONVERSION", "").replace("_ROLES", "")
        st.metric(short_name, f"{count:,}")

st.markdown("---")

# Filters & Search
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    type_filter = st.selectbox("Filter by Exception Category", ["All"] + issue_types)
with col_f2:
    sev_filter = st.selectbox("Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
with col_f3:
    status_filter = st.selectbox("Investigation Status", ["All", "OPEN", "UNDER_REVIEW", "RESOLVED", "DISMISSED"])

filtered = df_flags.copy()
if type_filter != "All":
    filtered = filtered[filtered["issue_type"] == type_filter]
if sev_filter != "All":
    filtered = filtered[filtered["severity"] == sev_filter]
if status_filter != "All":
    filtered = filtered[filtered["investigation_status"] == status_filter]

# Search Bar
search_term = st.text_input("🔍 Search by Flag ID or Employee ID:", "")
if search_term:
    filtered = filtered[
        filtered["flag_id"].str.contains(search_term, case=False, na=False) |
        filtered["employee_id"].str.contains(search_term, case=False, na=False)
    ]

st.caption(f"Showing **{len(filtered):,}** matching exception records.")

# Main Interactive Exceptions Table
display_df = filtered[[
    "flag_id", "employee_id", "issue_type", "severity", "salary_difference",
    "disparity_pct", "investigation_status", "root_cause"
]].copy()
display_df["salary_difference"] = display_df["salary_difference"].apply(format_inr)
display_df["disparity_pct"] = display_df["disparity_pct"].apply(lambda x: f"{x:.1f}%")

render_styled_dataframe(display_df, height=350)

st.markdown("---")

# Deep-Dive Investigation Panel
st.markdown("### 🔎 Investigation & Remediation Console")

selected_flag_id = st.selectbox(
    "Select an Exception Record to Inspect & Update:",
    options=filtered["flag_id"].tolist() if not filtered.empty else ["None"],
)

if selected_flag_id != "None" and not filtered.empty:
    record = filtered[filtered["flag_id"] == selected_flag_id].iloc[0]
    emp_id = record["employee_id"]

    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown(f"#### 📄 Exception Details: `{record['flag_id']}`")
        st.markdown(f"""
        - **Target Employee:** `{emp_id}`
        - **Exception Category:** `{record['issue_type']}`
        - **Severity Rating:** `{record['severity']}`
        - **Detection Rule:** `{record['detection_rule']}`
        - **Detection Timestamp:** `{record['detection_timestamp']}`
        - **Current Status:** `{record['investigation_status']}`
        - **Root Cause Analysis:** {record['root_cause']}
        - **Expected System Response:** {record['expected_response']}
        """)

        # Supporting Evidence JSON
        st.markdown("**Supporting Evidence Payload:**")
        try:
            ev_json = json.loads(str(record.get("supporting_evidence", "{}")))
            st.json(ev_json)
        except Exception:
            st.code(str(record.get("supporting_evidence", "")))

    with c2:
        st.markdown("#### ✍️ Update Investigation State")
        new_status = st.selectbox(
            "Change Status:",
            ["OPEN", "UNDER_REVIEW", "RESOLVED", "DISMISSED"],
            index=["OPEN", "UNDER_REVIEW", "RESOLVED", "DISMISSED"].index(record["investigation_status"])
        )
        notes = st.text_area(
            "Investigation Notes / Justification:",
            value=record.get("resolution_notes") or "",
            placeholder="Document HR audit findings, interview notes, or rationale..."
        )

        if st.button("💾 Save Investigation Update"):
            # Update in-memory dataframe and session state
            idx = df_flags[df_flags["flag_id"] == selected_flag_id].index
            if not idx.empty:
                df_flags.at[idx[0], "investigation_status"] = new_status
                df_flags.at[idx[0], "resolution_notes"] = notes
                if new_status in ("RESOLVED", "DISMISSED"):
                    df_flags.at[idx[0], "resolved_at"] = datetime.now().isoformat()
                st.success(f"Successfully updated {selected_flag_id} to {new_status}!")
                st.rerun()
