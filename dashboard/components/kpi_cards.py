"""
KPI Cards Component — Compensation Intelligence Platform
Renders HTML/CSS KPI cards and status/severity badges via st.markdown().
"""
from __future__ import annotations

import re
import streamlit as st
from typing import Optional
from dashboard.components.styles import render_html


# ---------------------------------------------------------------------------
# KPI Card
# ---------------------------------------------------------------------------

def render_kpi_card(
    title: str,
    value: str,
    subtitle: str = "",
    color: str = "#3B82F6",
    icon: str = "📊",
    delta: Optional[str] = None,
) -> str:
    """
    Returns an elegant, modern Dribbble-inspired HTML KPI card.
    Features: soft pastel icon chip, uppercase micro-header, bold typography,
    trend pill badge, and subtle bottom accent bar.
    """
    if delta:
        is_negative = delta.startswith("-") or "risk" in delta.lower() or "under" in delta.lower()
        badge_bg = "#FEE2E2" if is_negative else "#DCFCE7"
        badge_fg = "#991B1B" if is_negative else "#166534"
        arrow = "↓" if is_negative else "↑"
        delta_html = f'<span style="background:{badge_bg};color:{badge_fg};font-size:0.72rem;font-weight:700;padding:3px 8px;border-radius:20px;display:inline-flex;align-items:center;gap:2px;">{arrow} {delta}</span>'
    else:
        delta_html = '<span style="color:#94A3B8;font-size:0.85rem;font-weight:600;">↗</span>'

    subtitle_html = f'<div style="font-size:0.78rem;font-weight:500;color:#64748B;margin-top:3px;">{subtitle}</div>' if subtitle else ""

    html = (
        f'<div style="background:#FFFFFF;border-radius:16px;border:1px solid #E2E8F0;padding:18px 20px 16px 20px;'
        f'box-shadow:0 4px 16px rgba(15,23,42,0.03);min-height:125px;display:flex;flex-direction:column;'
        f'justify-content:space-between;position:relative;overflow:hidden;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;">'
        f'<div style="width:38px;height:38px;border-radius:12px;background:{color}18;color:{color};'
        f'display:flex;align-items:center;justify-content:center;font-size:1.25rem;">{icon}</div>'
        f'{delta_html}'
        f'</div>'
        f'<div style="margin-top:10px;">'
        f'<div style="font-size:0.75rem;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:0.05em;">{title}</div>'
        f'<div style="font-size:1.85rem;font-weight:800;color:#0F172A;letter-spacing:-0.02em;line-height:1.15;margin-top:2px;">{value}</div>'
        f'{subtitle_html}'
        f'</div>'
        f'<div style="position:absolute;bottom:0;left:0;right:0;height:3px;background:linear-gradient(90deg,{color},{color}33);"></div>'
        f'</div>'
    )
    return html


def render_kpi_row(metrics: list[dict]) -> None:
    """
    Render a row of KPI cards using st.columns().
    Each dict may have: title, value, subtitle, color, icon, delta.
    """
    if not metrics:
        return
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        card_html = render_kpi_card(
            title=m.get("title", ""),
            value=str(m.get("value", "—")),
            subtitle=m.get("subtitle", ""),
            color=m.get("color", "#3B82F6"),
            icon=m.get("icon", "📊"),
            delta=m.get("delta"),
        )
        with col:
            render_html(card_html)


# ---------------------------------------------------------------------------
# Status & Severity Badges
# ---------------------------------------------------------------------------

_STATUS_STYLES: dict[str, tuple[str, str]] = {
    "OPEN":        ("#FEF3C7", "#92400E"),
    "APPROVED":    ("#D1FAE5", "#065F46"),
    "REJECTED":    ("#FEE2E2", "#991B1B"),
    "IMPLEMENTED": ("#DBEAFE", "#1E40AF"),
    "WITHDRAWN":   ("#F1F5F9", "#475569"),
    "UNDER_REVIEW":("#EDE9FE", "#5B21B6"),
    "RESOLVED":    ("#D1FAE5", "#065F46"),
    "DISMISSED":   ("#F1F5F9", "#475569"),
    "PENDING":     ("#FEF3C7", "#92400E"),
}

_SEVERITY_STYLES: dict[str, tuple[str, str]] = {
    "CRITICAL": ("#FEE2E2", "#991B1B"),
    "HIGH":     ("#FFEDD5", "#9A3412"),
    "MEDIUM":   ("#FEF3C7", "#92400E"),
    "LOW":      ("#F1F5F9", "#475569"),
}


def _badge(label: str, bg: str, fg: str, bold: bool = True) -> str:
    weight = "700" if bold else "500"
    return (
        f'<span style="'
        f'background:{bg};color:{fg};padding:2px 10px;border-radius:12px;'
        f'font-size:0.75rem;font-weight:{weight};white-space:nowrap;">'
        f'{label}</span>'
    )


def render_status_badge(status: str) -> str:
    """Returns colored HTML badge for status values."""
    s = (status or "").upper()
    bg, fg = _STATUS_STYLES.get(s, ("#F1F5F9", "#475569"))
    return _badge(s, bg, fg)


def render_severity_badge(severity: str) -> str:
    """Returns colored HTML badge for severity values: CRITICAL/HIGH/MEDIUM/LOW."""
    s = (severity or "").upper()
    bg, fg = _SEVERITY_STYLES.get(s, ("#F1F5F9", "#475569"))
    return _badge(s, bg, fg)


def render_band_status_badge(band_status: str) -> str:
    """Returns colored HTML badge for band status: BELOW/WITHIN/ABOVE."""
    s = (band_status or "").upper()
    styles = {
        "BELOW":  ("#FEE2E2", "#991B1B"),
        "WITHIN": ("#D1FAE5", "#065F46"),
        "ABOVE":  ("#EDE9FE", "#5B21B6"),
    }
    bg, fg = styles.get(s, ("#F1F5F9", "#475569"))
    return _badge(s, bg, fg)


def render_metric_delta(value: float, suffix: str = "%", invert: bool = False) -> str:
    """Render a delta string with arrow icon."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return ""
    positive_good = not invert
    if v > 0:
        arrow = "▲"
        color = "#10B981" if positive_good else "#EF4444"
        sign = "+"
    elif v < 0:
        arrow = "▼"
        color = "#EF4444" if positive_good else "#10B981"
        sign = ""
    else:
        return f'<span style="color:#64748B;">→ 0{suffix}</span>'
    return f'<span style="color:{color};">{arrow} {sign}{v:.1f}{suffix}</span>'


# ---------------------------------------------------------------------------
# Progress / Band Position Bar
# ---------------------------------------------------------------------------

def render_band_position_bar(band_position: float, band_status: str = "") -> str:
    """Render an inline HTML progress bar representing band position."""
    try:
        pos = float(band_position)
    except (TypeError, ValueError):
        return "<em style='color:#94A3B8;'>N/A</em>"

    pct = min(max(pos * 100, 0), 130)

    if band_status.upper() == "BELOW" or pos < 0:
        bar_color = "#EF4444"
    elif band_status.upper() == "ABOVE" or pos > 1:
        bar_color = "#8B5CF6"
    else:
        bar_color = "#10B981"

    bar_width = min(pct, 100)

    return (
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'<div style="flex:1;background:#E2E8F0;border-radius:4px;height:8px;position:relative;">'
        f'<div style="width:{bar_width:.0f}%;background:{bar_color};height:8px;border-radius:4px;"></div>'
        f'<div style="position:absolute;left:50%;top:-4px;width:2px;height:16px;background:#94A3B8;"></div>'
        f'</div>'
        f'<span style="font-size:0.75rem;color:#475569;min-width:36px;">{pos:.2f}</span>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Profile mini-card (used in comparison page)
# ---------------------------------------------------------------------------

def render_profile_mini_card(label: str, value: str, icon: str = "") -> str:
    """Small labeled info cell for profile cards."""
    icon_html = f'<span style="margin-right:4px;">{icon}</span>' if icon else ""
    return (
        f'<div style="margin-bottom:6px;">'
        f'<span style="font-size:0.72rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.04em;">{label}</span><br>'
        f'<span style="font-size:0.9rem;font-weight:600;color:#1E293B;">{icon_html}{value or "—"}</span>'
        f'</div>'
    )


def render_section_header(title: str, subtitle: str = "") -> None:
    """Render a styled section header."""
    sub_html = f'<p style="color:#64748B;font-size:0.85rem;margin:0;">{subtitle}</p>' if subtitle else ""
    render_html(
        f'<div style="margin-bottom:16px;">'
        f'<h3 style="margin:0;color:#1E293B;font-size:1.15rem;">{title}</h3>'
        f'{sub_html}'
        f'</div>'
    )
