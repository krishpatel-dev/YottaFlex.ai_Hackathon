"""
Data Loader Utility — Compensation Intelligence Platform
Loads all CSV files from data/master/ and data/transactions/ directories.
Handles missing files gracefully by returning empty DataFrames with correct columns.
"""
import pandas as pd
import numpy as np
import os
from pathlib import Path
import streamlit as st
from typing import Optional

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent.parent.parent / "data"
MASTER_DIR = DATA_DIR / "master"
TRANSACTIONS_DIR = DATA_DIR / "transactions"

# ---------------------------------------------------------------------------
# Schema definitions — used to construct empty fallback DataFrames
# ---------------------------------------------------------------------------
TABLE_SCHEMAS: dict[str, list[str]] = {
    "employees": [
        "employee_id", "full_name", "gender", "role_id", "level_id",
        "location_id", "hire_date", "employment_type", "fte_fraction",
        "status", "manager_id", "created_at",
    ],
    "roles": [
        "role_id", "role_name", "role_family", "is_comparable_across_roles",
    ],
    "levels": [
        "level_id", "level_code", "level_name", "track", "rank_order",
    ],
    "locations": [
        "location_id", "city", "state", "country", "currency_code",
        "geo_multiplier", "timezone",
    ],
    "compensation_bands": [
        "band_id", "role_id", "level_id", "location_id", "band_min",
        "band_mid", "band_max", "currency_code", "fiscal_year",
        "effective_date", "expiry_date", "is_active",
    ],
    "salary_records": [
        "salary_id", "employee_id", "band_id", "annual_salary",
        "currency_code", "annual_salary_normalized", "annual_salary_fte",
        "effective_date", "end_date", "change_reason", "source", "created_at",
        "compa_ratio", "band_position", "band_status",
    ],
    "performance_evidence": [
        "perf_id", "employee_id", "review_period", "rating", "rating_label",
        "documented_factors", "reviewer_id", "review_date", "is_active",
    ],
    "tenure": [
        "tenure_id", "employee_id", "months_in_company",
        "months_in_current_role", "tenure_band", "last_calculated_at",
    ],
    "promotions": [
        "promo_id", "employee_id", "from_level_id", "to_level_id",
        "from_role_id", "to_role_id", "effective_date", "approved_by",
        "promo_type", "salary_adjustment_pct",
    ],
    "comparable_groups": [
        "group_id", "role_id", "level_id", "location_id", "tenure_band",
        "employment_type", "group_size", "group_median_salary",
        "group_mean_salary", "group_p25", "group_p75", "created_at",
    ],
    "adjustment_proposals": [
        "proposal_id", "employee_id", "trigger_type", "current_salary",
        "proposed_salary_min", "proposed_salary_max",
        "proposed_salary_recommended", "reason_code", "evidence_ids",
        "disparity_pct", "comparable_group_id", "manager_id",
        "manager_approval", "manager_approval_date", "hr_partner_id",
        "hr_approval", "hr_approval_date", "final_status",
        "created_at", "updated_at",
    ],
    "disparity_flags": [
        "flag_id", "employee_id", "comparable_group_id", "issue_type",
        "severity", "salary_difference", "disparity_pct", "detection_rule",
        "detection_timestamp", "investigation_status", "resolution_notes",
        "resolved_at", "expected_response", "actual_response",
    ],
}

# Map table name → CSV filename (try both master/ and transactions/)
TABLE_FILE_MAP: dict[str, tuple[str, str]] = {
    "employees":           ("master",       "employees.csv"),
    "roles":               ("master",       "roles.csv"),
    "levels":              ("master",       "levels.csv"),
    "locations":           ("master",       "locations.csv"),
    "compensation_bands":  ("master",       "compensation_bands.csv"),
    "salary_records":      ("transactions", "salary_records.csv"),
    "performance_evidence":("transactions", "performance_evidence.csv"),
    "tenure":              ("transactions", "tenure.csv"),
    "promotions":          ("transactions", "promotions.csv"),
    "comparable_groups":   ("transactions", "comparable_groups.csv"),
    "adjustment_proposals":("transactions", "adjustment_proposals.csv"),
    "disparity_flags":     ("transactions", "disparity_flags.csv"),
}


def _resolve_path(folder: str, filename: str) -> Path:
    if folder == "master":
        return MASTER_DIR / filename
    return TRANSACTIONS_DIR / filename


def _empty_df(table: str) -> pd.DataFrame:
    """Return an empty DataFrame with the correct column schema."""
    return pd.DataFrame(columns=TABLE_SCHEMAS.get(table, []))


def _safe_load(table: str) -> pd.DataFrame:
    """Load a single CSV; return empty-schema DataFrame on any failure."""
    folder, filename = TABLE_FILE_MAP[table]
    path = _resolve_path(folder, filename)
    if not path.exists():
        return _empty_df(table)
    try:
        df = pd.read_csv(path, low_memory=False)
        # Ensure all expected columns are present (fill missing with NaN)
        for col in TABLE_SCHEMAS.get(table, []):
            if col not in df.columns:
                df[col] = np.nan
        return df
    except Exception:
        return _empty_df(table)


@st.cache_data(ttl=300)
def load_all_data() -> dict[str, pd.DataFrame]:
    """
    Load all CSV files. Return dict keyed by table name.
    Handles missing files gracefully — returns empty DataFrame with correct columns.
    Tables: employees, roles, levels, locations, compensation_bands,
            salary_records, performance_evidence, tenure, promotions,
            comparable_groups, adjustment_proposals, disparity_flags
    """
    data: dict[str, pd.DataFrame] = {}
    for table in TABLE_FILE_MAP:
        data[table] = _safe_load(table)

    # Post-load type coercions — silent on error
    _coerce_types(data)
    return data


def _coerce_types(data: dict[str, pd.DataFrame]) -> None:
    """Best-effort type coercions on the loaded DataFrames."""
    numeric_cols = {
        "salary_records": ["annual_salary", "annual_salary_normalized",
                           "annual_salary_fte", "compa_ratio", "band_position"],
        "compensation_bands": ["band_min", "band_mid", "band_max", "geo_multiplier"],
        "disparity_flags": ["salary_difference", "disparity_pct"],
        "adjustment_proposals": ["current_salary", "proposed_salary_min",
                                 "proposed_salary_max", "proposed_salary_recommended",
                                 "disparity_pct"],
        "comparable_groups": ["group_median_salary", "group_mean_salary",
                               "group_p25", "group_p75"],
        "performance_evidence": ["rating"],
        "tenure": ["months_in_company", "months_in_current_role"],
        "locations": ["geo_multiplier"],
    }
    for table, cols in numeric_cols.items():
        df = data.get(table)
        if df is None or df.empty:
            continue
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    date_cols = {
        "salary_records": ["effective_date", "end_date"],
        "compensation_bands": ["effective_date", "expiry_date"],
        "employees": ["hire_date"],
        "tenure": ["last_calculated_at"],
        "promotions": ["effective_date"],
        "performance_evidence": ["review_date"],
        "disparity_flags": ["detection_timestamp", "resolved_at"],
        "adjustment_proposals": ["manager_approval_date", "hr_approval_date",
                                  "created_at", "updated_at"],
    }
    for table, cols in date_cols.items():
        df = data.get(table)
        if df is None or df.empty:
            continue
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")


# ---------------------------------------------------------------------------
# Employee helpers
# ---------------------------------------------------------------------------

@st.cache_data
def get_current_salary(salary_df: pd.DataFrame, employee_id: str) -> dict:
    """
    Get the most recent active salary record for an employee.
    'Active' = end_date is NaT/null or in the future.
    Returns {} if not found.
    """
    if salary_df.empty or employee_id not in salary_df["employee_id"].values:
        return {}
    emp_sal = salary_df[salary_df["employee_id"] == employee_id].copy()
    # Active records: end_date is null
    active = emp_sal[emp_sal["end_date"].isna()]
    if active.empty:
        active = emp_sal  # fall back to any record
    # Sort by effective_date descending
    if "effective_date" in active.columns:
        active = active.sort_values("effective_date", ascending=False)
    row = active.iloc[0]
    return row.to_dict()


@st.cache_data
def get_employee_full_profile(employee_id: str, data: dict) -> dict:
    """
    Merge employee record with their current salary, applicable band,
    tenure data, and latest performance record.
    Returns {} if employee not found.
    """
    emp_df = data.get("employees", pd.DataFrame())
    if emp_df.empty or employee_id not in emp_df["employee_id"].values:
        return {}

    emp_row = emp_df[emp_df["employee_id"] == employee_id].iloc[0].to_dict()

    # Current salary
    sal = get_current_salary(data.get("salary_records", pd.DataFrame()), employee_id)
    emp_row.update({f"sal_{k}": v for k, v in sal.items()})

    # Role info
    roles_df = data.get("roles", pd.DataFrame())
    if not roles_df.empty and "role_id" in emp_row:
        role_rows = roles_df[roles_df["role_id"] == emp_row["role_id"]]
        if not role_rows.empty:
            emp_row.update({f"role_{k}": v for k, v in role_rows.iloc[0].to_dict().items()})

    # Level info
    levels_df = data.get("levels", pd.DataFrame())
    if not levels_df.empty and "level_id" in emp_row:
        lvl_rows = levels_df[levels_df["level_id"] == emp_row["level_id"]]
        if not lvl_rows.empty:
            emp_row.update({f"level_{k}": v for k, v in lvl_rows.iloc[0].to_dict().items()})

    # Location info
    locs_df = data.get("locations", pd.DataFrame())
    if not locs_df.empty and "location_id" in emp_row:
        loc_rows = locs_df[locs_df["location_id"] == emp_row["location_id"]]
        if not loc_rows.empty:
            emp_row.update({f"loc_{k}": v for k, v in loc_rows.iloc[0].to_dict().items()})

    # Band info
    bands_df = data.get("compensation_bands", pd.DataFrame())
    if not bands_df.empty and "sal_band_id" in emp_row:
        band_rows = bands_df[bands_df["band_id"] == emp_row.get("sal_band_id")]
        if not band_rows.empty:
            emp_row.update({f"band_{k}": v for k, v in band_rows.iloc[0].to_dict().items()})

    # Tenure
    tenure_df = data.get("tenure", pd.DataFrame())
    if not tenure_df.empty and employee_id in tenure_df.get("employee_id", pd.Series()).values:
        t_row = tenure_df[tenure_df["employee_id"] == employee_id].iloc[0].to_dict()
        emp_row.update({f"tenure_{k}": v for k, v in t_row.items()})

    # Latest performance
    perf_df = data.get("performance_evidence", pd.DataFrame())
    if not perf_df.empty and employee_id in perf_df.get("employee_id", pd.Series()).values:
        emp_perf = perf_df[perf_df["employee_id"] == employee_id].copy()
        if "review_date" in emp_perf.columns:
            emp_perf = emp_perf.sort_values("review_date", ascending=False)
        p_row = emp_perf.iloc[0].to_dict()
        emp_row.update({f"perf_{k}": v for k, v in p_row.items()})

    return emp_row


# ---------------------------------------------------------------------------
# KPI metrics
# ---------------------------------------------------------------------------

def compute_live_metrics(data: dict) -> dict:
    """
    Compute all KPI metrics from loaded DataFrames.
    Returns a dict with:
      total_employees, avg_compa_ratio,
      below_band_count, within_band_count, above_band_count,
      disparity_count, pending_proposals,
      exception_counts (by issue_type)
    """
    metrics: dict = {}

    # Employee count
    emp_df = data.get("employees", pd.DataFrame())
    active_emp = (
        emp_df[emp_df["status"] == "ACTIVE"] if not emp_df.empty and "status" in emp_df.columns
        else emp_df
    )
    metrics["total_employees"] = len(active_emp)

    # Salary / compa ratio
    sal_df = data.get("salary_records", pd.DataFrame())
    # Only active records (end_date null)
    if not sal_df.empty:
        active_sal = sal_df[sal_df["end_date"].isna()] if "end_date" in sal_df.columns else sal_df
    else:
        active_sal = pd.DataFrame()

    if not active_sal.empty and "compa_ratio" in active_sal.columns:
        metrics["avg_compa_ratio"] = round(active_sal["compa_ratio"].mean() * 100, 1)
    else:
        metrics["avg_compa_ratio"] = None

    # Band status breakdown
    if not active_sal.empty and "band_status" in active_sal.columns:
        band_counts = active_sal["band_status"].value_counts()
        metrics["below_band_count"]  = int(band_counts.get("BELOW", 0))
        metrics["within_band_count"] = int(band_counts.get("WITHIN", 0))
        metrics["above_band_count"]  = int(band_counts.get("ABOVE", 0))
    else:
        metrics["below_band_count"]  = 0
        metrics["within_band_count"] = 0
        metrics["above_band_count"]  = 0

    # Open disparity flags
    disp_df = data.get("disparity_flags", pd.DataFrame())
    if not disp_df.empty and "investigation_status" in disp_df.columns:
        metrics["disparity_count"] = int(
            (disp_df["investigation_status"] == "OPEN").sum()
        )
    else:
        metrics["disparity_count"] = 0

    # Pending proposals
    prop_df = data.get("adjustment_proposals", pd.DataFrame())
    if not prop_df.empty and "final_status" in prop_df.columns:
        metrics["pending_proposals"] = int(
            (prop_df["final_status"] == "OPEN").sum()
        )
    else:
        metrics["pending_proposals"] = 0

    # Exception counts by issue_type
    if not disp_df.empty and "issue_type" in disp_df.columns:
        metrics["exception_counts"] = disp_df["issue_type"].value_counts().to_dict()
    else:
        metrics["exception_counts"] = {}

    return metrics


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_inr(val) -> str:
    """Format a numeric value as Indian Rupee LPA string. e.g. 1250000 → '₹12.5 LPA'"""
    try:
        lpa = float(val) / 100_000
        return f"₹{lpa:.1f} LPA"
    except (TypeError, ValueError):
        return "₹— LPA"


def format_pct(val, decimals: int = 1) -> str:
    """Format as percentage string."""
    try:
        return f"{float(val):.{decimals}f}%"
    except (TypeError, ValueError):
        return "—%"


def get_data_health(data: dict) -> dict[str, bool]:
    """Return a dict of table → has_data for system health display."""
    return {table: not df.empty for table, df in data.items()}
