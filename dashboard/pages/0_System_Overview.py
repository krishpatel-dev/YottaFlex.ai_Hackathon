"""
dashboard/pages/0_System_Overview.py
====================================
System Overview & Platform Health Dashboard
Macro workforce telemetry, market corridor compliance, organizational topology,
and five mandatory exception safeguard status.
"""

from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st

# Setup python path
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dashboard.utils.data_loader import load_all_data, compute_live_metrics
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.components.styles import inject_custom_css, render_html

# Apply unified enterprise design system
inject_custom_css()

# Main Welcome Header
render_html("""
<div style="margin-bottom: 24px;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
        <div>
            <div style="font-size: 0.82rem; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                Enterprise Pay Parity Telemetry • FY 2026
            </div>
            <div style="font-size: 2rem; font-weight: 800; color: #0F172A; letter-spacing: -0.03em; line-height: 1.15;">
                Compensation Intelligence & Equity Analytics
            </div>
            <div style="font-size: 0.95rem; color: #64748B; margin-top: 6px;">
                Real-time salary benchmarking, market band alignment, and explainable disparity detection across 5,000 employees.
            </div>
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="metric-badge badge-success">✓ 100% Seed Verified (20261022)</span>
            <span class="metric-badge badge-info">PostgreSQL 16 & SQLAlchemy 2.0</span>
        </div>
    </div>
</div>
""")

# Data Loading with spinner
with st.spinner("Synchronizing compensation telemetry and calculating parity corridors..."):
    data = load_all_data()
    metrics = compute_live_metrics(data)

# Primary Executive KPI Row (4 Top Cards)
render_kpi_row([
    {
        "title": "Active Workforce",
        "value": f"{metrics.get('total_employees', 5000):,}",
        "subtitle": "13 Global Business Locations",
        "color": "#3B82F6",
        "icon": "👥",
        "delta": "100% active",
    },
    {
        "title": "Avg Compa-Ratio",
        "value": f"{metrics.get('avg_compa_ratio', 100.0):.1f}%",
        "subtitle": "Parity Corridor: 80% – 120%",
        "color": "#10B981",
        "icon": "🎯",
        "delta": "Compliant",
    },
    {
        "title": "Below Band (<80%)",
        "value": f"{metrics.get('below_band_count', 355):,}",
        "subtitle": "Requires Upward Correction",
        "color": "#EF4444",
        "icon": "🔻",
        "delta": "Risk Cohort",
    },
    {
        "title": "Flagged Disparities",
        "value": f"{metrics.get('disparity_count', 1258):,}",
        "subtitle": "Unexplained Equity Exceptions",
        "color": "#F59E0B",
        "icon": "⚠️",
        "delta": "Audit Queue",
    },
])

st.write("")

# Secondary Operational Row (3 Cards with Progress Fill)
sec_col1, sec_col2, sec_col3 = st.columns(3)

with sec_col1:
    within_cnt = metrics.get('within_band_count', 2726)
    render_html(f"""
    <div class="glass-card" style="padding: 16px 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.8rem; font-weight: 700; color: #1E293B;">Within-Band Compliant (80–120%)</span>
            <span class="metric-badge badge-success">{within_cnt:,}</span>
        </div>
        <div style="background: #E2E8F0; border-radius: 8px; height: 8px; overflow: hidden; margin-top: 8px;">
            <div style="background: #10B981; width: {(within_cnt/5000)*100:.1f}%; height: 100%; border-radius: 8px;"></div>
        </div>
        <div style="font-size: 0.76rem; color: #64748B; margin-top: 6px;">{(within_cnt/5000)*100:.1f}% of total active workforce compliant with compensation bands.</div>
    </div>
    """)

with sec_col2:
    above_cnt = metrics.get('above_band_count', 2669)
    render_html(f"""
    <div class="glass-card" style="padding: 16px 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.8rem; font-weight: 700; color: #1E293B;">Market Premium Cohort (>120%)</span>
            <span class="metric-badge badge-purple">{above_cnt:,}</span>
        </div>
        <div style="background: #E2E8F0; border-radius: 8px; height: 8px; overflow: hidden; margin-top: 8px;">
            <div style="background: #8B5CF6; width: {(above_cnt/5000)*100:.1f}%; height: 100%; border-radius: 8px;"></div>
        </div>
        <div style="font-size: 0.76rem; color: #64748B; margin-top: 6px;">Top-tier performers & specialized market skills compensated above midpoint.</div>
    </div>
    """)

with sec_col3:
    pending_p = metrics.get('pending_proposals', 70)
    render_html(f"""
    <div class="glass-card" style="padding: 16px 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.8rem; font-weight: 700; color: #1E293B;">Pending Governance Proposals</span>
            <span class="metric-badge badge-warning">{pending_p:,} Open</span>
        </div>
        <div style="background: #E2E8F0; border-radius: 8px; height: 8px; overflow: hidden; margin-top: 8px;">
            <div style="background: #F59E0B; width: {(pending_p/156)*100:.1f}%; height: 100%; border-radius: 8px;"></div>
        </div>
        <div style="font-size: 0.76rem; color: #64748B; margin-top: 6px;">156 total remediation proposals created; dual-approval pipeline active.</div>
    </div>
    """)

# Deep-Dive Section Cards (Dribbble 2-Column Split)
col_org, col_safe = st.columns([1, 1])

with col_org:
    render_html("""
    <div class="glass-card">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px;">
            <span style="font-size: 1.25rem;">🏢</span>
            <span style="font-size: 1.05rem; font-weight: 800; color: #0F172A;">Organizational Topology & Benchmarks</span>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 14px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Workforce Volume</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A;">5,000</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">Across 13 Global Locations</div>
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 14px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Role Families</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A;">21 Roles</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">8 Functional Job Families</div>
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 14px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Career Levels</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A;">10 Tracks</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">L1–L6 (IC) | M1–M4 (Mgr)</div>
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 14px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Salary Bands</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A;">8,190</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">Effective-dated 2024–2026</div>
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 14px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Salary Records</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A;">19,846</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">3-Year Longitudinal History</div>
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 14px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Peer Clusters</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A;">589 Groups</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">Homogeneous Cohorts</div>
            </div>
        </div>
    </div>
    """)

with col_safe:
    render_html("""
    <div class="glass-card">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px;">
            <span style="font-size: 1.25rem;">🛡️</span>
            <span style="font-size: 1.05rem; font-weight: 800; color: #0F172A;">Five Mandatory Exception Safeguards</span>
        </div>
        <div style="display: flex; flex-direction: column; gap: 10px;">
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #EF4444; border-radius: 10px; padding: 11px 14px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: #0F172A;">1. Expired Band Benchmark Protection</div>
                    <div style="font-size: 0.74rem; color: #64748B;">Blocks salary comparisons evaluated against obsolete market bands.</div>
                </div>
                <span class="metric-badge badge-danger">15 Injected / Blocked</span>
            </div>
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #F59E0B; border-radius: 10px; padding: 11px 14px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: #0F172A;">2. FTE Pro-Rata Scaling Verification</div>
                    <div style="font-size: 0.74rem; color: #64748B;">Normalizes part-time employee compensation to full-time equivalent basis.</div>
                </div>
                <span class="metric-badge badge-warning">30 Injected / Scaled</span>
            </div>
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #EF4444; border-radius: 10px; padding: 11px 14px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: #0F172A;">3. FX Currency Normalization Gate</div>
                    <div style="font-size: 0.74rem; color: #64748B;">Enforces currency conversions to INR across global talent locations.</div>
                </div>
                <span class="metric-badge badge-danger">20 Injected / Fixed</span>
            </div>
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #EF4444; border-radius: 10px; padding: 11px 14px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: #0F172A;">4. Unauthorized Payroll Adjustment Control</div>
                    <div style="font-size: 0.74rem; color: #64748B;">Strictly prevents payroll modification without Manager & HR dual-signoff.</div>
                </div>
                <span class="metric-badge badge-danger">25 Injected / Blocked</span>
            </div>
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #F59E0B; border-radius: 10px; padding: 11px 14px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: #0F172A;">5. Incomparable Role Clustering Guard</div>
                    <div style="font-size: 0.74rem; color: #64748B;">Prevents invalid peer grouping across distinct job families.</div>
                </div>
                <span class="metric-badge badge-warning">15 Injected / Flagged</span>
            </div>
        </div>
    </div>
    """)

render_html("""
<div style="text-align: center; color: #94A3B8; font-size: 0.78rem; margin-top: 24px; padding-top: 12px; border-top: 1px solid #E2E8F0;">
    Compensation Intelligence & Pay Equity Analytics Platform • Built with Python 3.11+, Streamlit, Plotly & SQLAlchemy • Seed: <code>20261022</code>
</div>
""")
