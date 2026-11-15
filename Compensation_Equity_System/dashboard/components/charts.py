"""
dashboard/components/charts.py
==============================
Reusable, interactive Plotly visualization components styled for the
Compensation Intelligence & Pay Equity Analytics Platform.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Design system color tokens
PALETTE = {
    "primary": "#3B82F6",      # Bright Blue
    "secondary": "#6366F1",    # Indigo
    "success": "#10B981",      # Emerald Green
    "warning": "#F59E0B",      # Amber
    "critical": "#EF4444",     # Crimson Red
    "purple": "#8B5CF6",       # Violet
    "dark_navy": "#0F172A",
    "card_bg": "#FFFFFF",
    "grid_color": "#E2E8F0",
    "text_dark": "#1E293B",
    "text_muted": "#64748B",
}


def base_layout(fig: go.Figure, title: str = "", height: int = 400) -> go.Figure:
    """Apply consistent styling across all charts."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>",
            "font": {"size": 16, "color": PALETTE["text_dark"], "family": "Inter, sans-serif"},
            "x": 0.02,
            "xanchor": "left",
        },
        height=height,
        paper_bgcolor=PALETTE["card_bg"],
        plot_bgcolor="rgba(248, 250, 252, 0.5)",
        margin=dict(l=40, r=40, t=60, b=40),
        font=dict(color=PALETTE["text_muted"], size=12, family="Inter, sans-serif"),
        xaxis=dict(
            showgrid=True,
            gridcolor=PALETTE["grid_color"],
            zeroline=False,
            titlefont=dict(size=12, color=PALETTE["text_dark"]),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=PALETTE["grid_color"],
            zeroline=False,
            titlefont=dict(size=12, color=PALETTE["text_dark"]),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
    )
    return fig


def compa_ratio_distribution(salary_df: pd.DataFrame) -> go.Figure:
    """
    Histogram of employee compa-ratios with colored equity zones:
    - Below 80%: Underpaid (Red zone)
    - 80% to 120%: Target corridor (Green zone)
    - Above 120%: Premium (Purple zone)
    """
    df = salary_df.copy()
    if "compa_ratio" not in df.columns or df["compa_ratio"].dropna().empty:
        fig = go.Figure()
        return base_layout(fig, "Compa-Ratio Distribution (No Data)")

    ratios = df["compa_ratio"].dropna()
    # Filter out extreme anomalies for clean visualization
    ratios = ratios[(ratios > 40) & (ratios < 200)]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=ratios,
        nbinsx=40,
        marker=dict(
            color=PALETTE["primary"],
            line=dict(color="#1D4ED8", width=1),
        ),
        name="Employees",
        hovertemplate="Compa-Ratio: %{x:.1f}%<br>Count: %{y:,}<extra></extra>",
    ))

    # Add vertical reference threshold lines
    fig.add_vline(x=80, line_width=2, line_dash="dash", line_color=PALETTE["critical"],
                  annotation_text="80% (Underpaid Threshold)", annotation_position="top left",
                  annotation_font=dict(color=PALETTE["critical"], size=10))
    fig.add_vline(x=100, line_width=2, line_dash="solid", line_color=PALETTE["success"],
                  annotation_text="100% (Market Midpoint)", annotation_position="top",
                  annotation_font=dict(color=PALETTE["success"], size=10))
    fig.add_vline(x=120, line_width=2, line_dash="dash", line_color=PALETTE["purple"],
                  annotation_text="120% (Upper Band Limit)", annotation_position="top right",
                  annotation_font=dict(color=PALETTE["purple"], size=10))

    fig.update_xaxes(title="Compa-Ratio (%)", range=[50, 150])
    fig.update_yaxes(title="Number of Employees")
    return base_layout(fig, "Compa-Ratio Distribution & Market Parity Corridor")


def salary_distribution_histogram(salary_df: pd.DataFrame) -> go.Figure:
    """Histogram of normalized annual compensation in Lakhs (LPA INR)."""
    df = salary_df.copy()
    if df.empty or "annual_salary_fte" not in df.columns:
        return base_layout(go.Figure(), "Salary Distribution (No Data)")

    # Convert to LPA
    salaries_lpa = df["annual_salary_fte"].dropna() / 100_000.0

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=salaries_lpa,
        nbinsx=45,
        marker=dict(color=PALETTE["secondary"], line=dict(color="#4338CA", width=1)),
        hovertemplate="Salary: ₹%{x:.1f} LPA<br>Count: %{y:,}<extra></extra>",
    ))
    median_val = salaries_lpa.median()
    fig.add_vline(x=median_val, line_width=2, line_dash="dash", line_color=PALETTE["warning"],
                  annotation_text=f"Median: ₹{median_val:.1f} LPA", annotation_position="top right")

    fig.update_xaxes(title="FTE Normalized Salary (₹ LPA)")
    fig.update_yaxes(title="Employee Count")
    return base_layout(fig, "Annual Compensation Distribution (₹ Lakhs per Annum)")


def salary_by_role_boxplot(salary_df: pd.DataFrame, emp_df: pd.DataFrame) -> go.Figure:
    """Boxplot displaying salary spread across role families."""
    if salary_df.empty or emp_df.empty:
        return base_layout(go.Figure(), "Salary by Role Family (No Data)")

    latest_sal = (
        salary_df.sort_values("effective_date", ascending=False)
        .groupby("employee_id")
        .first()
        .reset_index()
    )
    merged = emp_df.merge(latest_sal[["employee_id", "annual_salary_fte"]], on="employee_id")
    merged["salary_lpa"] = merged["annual_salary_fte"] / 100_000.0

    fig = px.box(
        merged,
        x="role_family",
        y="salary_lpa",
        color="role_family",
        points="outliers",
        labels={"role_family": "Role Family", "salary_lpa": "Salary (₹ LPA)"},
    )
    fig.update_traces(showlegend=False)
    return base_layout(fig, "Compensation Spread by Functional Job Family", height=450)


def salary_by_level_bar(salary_df: pd.DataFrame, emp_df: pd.DataFrame) -> go.Figure:
    """Mean and median salary by career level."""
    if salary_df.empty or emp_df.empty:
        return base_layout(go.Figure(), "Salary by Career Level (No Data)")

    latest_sal = (
        salary_df.sort_values("effective_date", ascending=False)
        .groupby("employee_id")
        .first()
        .reset_index()
    )
    merged = emp_df.merge(latest_sal[["employee_id", "annual_salary_fte"]], on="employee_id")
    merged["salary_lpa"] = merged["annual_salary_fte"] / 100_000.0

    summary = (
        merged.groupby("level_code")["salary_lpa"]
        .agg(["median", "mean"])
        .reset_index()
    )

    # Sort by rank order
    order = ["L1", "L2", "L3", "L4", "L5", "L6", "M1", "M2", "M3", "M4"]
    summary["sort_key"] = summary["level_code"].apply(lambda x: order.index(x) if x in order else 99)
    summary = summary.sort_values("sort_key")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=summary["level_code"],
        y=summary["median"],
        name="Median (₹ LPA)",
        marker_color=PALETTE["primary"],
        hovertemplate="Level %{x}<br>Median: ₹%{y:.2f} LPA<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=summary["level_code"],
        y=summary["mean"],
        name="Mean (₹ LPA)",
        marker_color=PALETTE["purple"],
        hovertemplate="Level %{x}<br>Mean: ₹%{y:.2f} LPA<extra></extra>",
    ))

    fig.update_layout(barmode="group")
    fig.update_xaxes(title="Career Level")
    fig.update_yaxes(title="Salary (₹ LPA)")
    return base_layout(fig, "Compensation Progression Across Career Levels", height=420)


def salary_by_location_bar(salary_df: pd.DataFrame, emp_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart comparing median salary by business location."""
    if salary_df.empty or emp_df.empty:
        return base_layout(go.Figure(), "Salary by Location (No Data)")

    latest_sal = (
        salary_df.sort_values("effective_date", ascending=False)
        .groupby("employee_id")
        .first()
        .reset_index()
    )
    merged = emp_df.merge(latest_sal[["employee_id", "annual_salary_fte"]], on="employee_id")
    merged["salary_lpa"] = merged["annual_salary_fte"] / 100_000.0

    loc_summary = (
        merged.groupby("location_code")["salary_lpa"]
        .median()
        .reset_index()
        .sort_values("salary_lpa", ascending=True)
    )

    fig = go.Figure(go.Bar(
        x=loc_summary["salary_lpa"],
        y=loc_summary["location_code"],
        orientation="h",
        marker=dict(
            color=loc_summary["salary_lpa"],
            colorscale="Blues",
            line=dict(color="#1E3A8A", width=1),
        ),
        hovertemplate="Location: %{y}<br>Median: ₹%{x:.2f} LPA<extra></extra>",
    ))
    fig.update_xaxes(title="Median Salary (₹ LPA)")
    fig.update_yaxes(title="Location Code")
    return base_layout(fig, "Geographic Salary Benchmarks (Median LPA)", height=450)


def band_position_scatter(salary_df: pd.DataFrame, emp_df: pd.DataFrame) -> go.Figure:
    """Scatter plot: Tenure vs Compa-Ratio with colored status markers."""
    if salary_df.empty or emp_df.empty:
        return base_layout(go.Figure(), "Tenure vs Compa-Ratio (No Data)")

    latest_sal = (
        salary_df.sort_values("effective_date", ascending=False)
        .groupby("employee_id")
        .first()
        .reset_index()
    )
    merged = emp_df.merge(latest_sal[["employee_id", "compa_ratio", "annual_salary_fte"]], on="employee_id")
    merged = merged.dropna(subset=["compa_ratio"])

    # Categorize band status
    def get_status(cr):
        if cr < 80:
            return "Below Band (<80%)"
        elif cr > 120:
            return "Above Band (>120%)"
        return "Within Band (80-120%)"

    merged["Band Status"] = merged["compa_ratio"].apply(get_status)

    color_map = {
        "Below Band (<80%)": PALETTE["critical"],
        "Within Band (80-120%)": PALETTE["success"],
        "Above Band (>120%)": PALETTE["purple"],
    }

    # Sample for snappy scatter performance if > 2,000
    plot_df = merged.sample(min(2000, len(merged)), random_state=42)

    fig = px.scatter(
        plot_df,
        x="fte_fraction",
        y="compa_ratio",
        color="Band Status",
        color_discrete_map=color_map,
        hover_data=["employee_id", "role_family", "level_code", "location_code"],
        labels={"fte_fraction": "FTE Fraction", "compa_ratio": "Compa-Ratio (%)"},
        opacity=0.7,
    )
    return base_layout(fig, "Tenure & FTE Position vs Compa-Ratio", height=420)


def approval_funnel(proposals_df: pd.DataFrame) -> go.Figure:
    """Governance pipeline stage funnel for adjustment proposals."""
    if proposals_df.empty:
        return base_layout(go.Figure(), "Adjustment Approval Pipeline (No Data)")

    total = len(proposals_df)
    mgr_app = len(proposals_df[proposals_df["manager_approval"] == "APPROVED"])
    hr_app = len(proposals_df[proposals_df["hr_approval"] == "APPROVED"])
    impl = len(proposals_df[proposals_df["final_status"] == "IMPLEMENTED"])

    stages = ["Generated Proposals", "Manager Approved", "HR Approved", "Implemented in Payroll"]
    counts = [total, mgr_app, hr_app, impl]

    fig = go.Figure(go.Funnel(
        y=stages,
        x=counts,
        textinfo="value+percent initial",
        marker=dict(color=[PALETTE["primary"], PALETTE["secondary"], PALETTE["warning"], PALETTE["success"]]),
    ))
    return base_layout(fig, "Salary Adjustment Governance Funnel", height=380)


def employee_comparison_radar(peers_data: List[Dict]) -> go.Figure:
    """Radar chart comparing 2-4 selected employees across multiple equity dimensions."""
    categories = [
        "Compa-Ratio",
        "Performance Rating",
        "Band Penetration",
        "Experience/Tenure",
        "Salary Relative to Group"
    ]

    fig = go.Figure()
    colors = [PALETTE["primary"], PALETTE["success"], PALETTE["purple"], PALETTE["warning"]]

    for idx, peer in enumerate(peers_data):
        c = colors[idx % len(colors)]
        name = peer.get("full_name", peer.get("employee_id", f"Emp {idx+1}"))

        # Normalized 0-100 scale values for radar
        cr_norm = min(100, max(0, peer.get("compa_ratio", 100)))
        perf_norm = min(100, max(0, (peer.get("performance_rating", 3.0) / 5.0) * 100))
        band_pos = min(100, max(0, peer.get("band_position", 0.5) * 100))
        tenure_norm = min(100, max(0, (peer.get("months_in_company", 24) / 60.0) * 100))
        sal_norm = min(100, max(0, peer.get("relative_peer_pct", 50.0)))

        values = [cr_norm, perf_norm, band_pos, tenure_norm, sal_norm]
        values.append(values[0])  # close loop

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill="toself",
            name=name,
            line=dict(color=c, width=2),
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
    )
    return base_layout(fig, "Multi-Dimensional Employee Equity Benchmark", height=450)
