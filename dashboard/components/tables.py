"""
dashboard/components/tables.py
==============================
Reusable table rendering utilities with status badges, INR formatting,
and clean data presentation for the Streamlit dashboard.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import pandas as pd
import streamlit as st


def format_inr(val: float) -> str:
    """Format numeric salary as Indian Rupee Lakhs (e.g. ₹12.50 LPA)."""
    if pd.isna(val) or val is None:
        return "N/A"
    try:
        val_f = float(val)
        lpa = val_f / 100_000.0
        return f"₹{lpa:,.2f} LPA"
    except (ValueError, TypeError):
        return str(val)


def render_styled_dataframe(df: pd.DataFrame, height: int = 400) -> None:
    """Display an interactive dataframe with column configuration."""
    st.dataframe(
        df,
        width="stretch",
        height=height,
        hide_index=True,
    )


def render_flag_badge(issue_type: str, severity: str) -> str:
    """Generate HTML badge for disparity flags."""
    color_map = {
        "CRITICAL": "#EF4444",
        "HIGH": "#F97316",
        "MEDIUM": "#F59E0B",
        "LOW": "#6B7280",
    }
    bg_color = color_map.get(severity, "#6B7280")
    return f"""<span style="background-color: {bg_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">{severity}</span>"""


def render_status_badge(status: str) -> str:
    """Generate HTML badge for proposal / investigation statuses."""
    color_map = {
        "APPROVED": "#10B981",
        "IMPLEMENTED": "#3B82F6",
        "OPEN": "#F59E0B",
        "PENDING_HR": "#8B5CF6",
        "PENDING_MANAGER": "#F59E0B",
        "REJECTED": "#EF4444",
        "WITHDRAWN": "#6B7280",
        "RESOLVED": "#10B981",
        "UNDER_REVIEW": "#3B82F6",
        "DISMISSED": "#6B7280",
    }
    bg_color = color_map.get(status, "#6B7280")
    return f"""<span style="background-color: {bg_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">{status}</span>"""
