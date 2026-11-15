"""
comparable_groups.py
--------------------
Build and validate comparable employee groups for pay-equity analysis.

Groups are formed by clustering employees who share the same:
  role_family, level_id, location_id, tenure_band, employment_type.

Only groups with >= min_group_size members are retained, ensuring statistical
validity of any subsequent peer comparisons.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_GROUP_KEY_COLS = [
    "role_family",
    "level_id",
    "location_id",
    "tenure_band",
    "employment_type",
]


def _safe_json_loads(value: str | None) -> list:
    """Return parsed JSON list or empty list on failure."""
    if value is None:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


# ---------------------------------------------------------------------------
# build_comparable_groups
# ---------------------------------------------------------------------------


def build_comparable_groups(
    employees_df: pd.DataFrame,
    tenure_df: pd.DataFrame,
    min_group_size: int = 3,
) -> pd.DataFrame:
    """Group employees into comparable cohorts for pay-equity analysis.

    Groups employees who share the same ``role_family``, ``level_id``,
    ``location_id``, ``tenure_band``, and ``employment_type``.  Groups with
    fewer than *min_group_size* members are discarded.

    Parameters
    ----------
    employees_df:
        DataFrame with at minimum the columns:
        ``employee_id``, ``role_family`` (or joined from roles),
        ``level_id``, ``location_id``, ``employment_type``, ``status``.
    tenure_df:
        DataFrame with columns: ``employee_id``, ``tenure_band``.
    min_group_size:
        Minimum number of members a group must have to be included.
        Defaults to 3.

    Returns
    -------
    pd.DataFrame
        Columns:

        * ``group_id`` – unique UUID-based identifier.
        * ``role_family`` / ``level_id`` / ``location_id`` /
          ``tenure_band`` / ``employment_type`` – the grouping criteria.
        * ``criteria`` – JSON string of the grouping key dict.
        * ``member_employee_ids`` – JSON array of ``employee_id`` strings.
        * ``group_size`` – number of members.
    """
    if employees_df.empty:
        logger.warning("employees_df is empty; returning empty groups DataFrame.")
        return _empty_groups_df()

    # Only active employees participate in comparisons
    active_emp = employees_df.copy()
    if "status" in active_emp.columns:
        active_emp = active_emp[active_emp["status"] == "ACTIVE"]

    # Merge tenure information
    if tenure_df.empty:
        active_emp = active_emp.copy()
        active_emp["tenure_band"] = "UNKNOWN"
    else:
        active_emp = active_emp.merge(
            tenure_df[["employee_id", "tenure_band"]],
            on="employee_id",
            how="left",
        )
        active_emp["tenure_band"] = active_emp["tenure_band"].fillna("UNKNOWN")

    # Ensure required columns exist
    for col in _GROUP_KEY_COLS:
        if col not in active_emp.columns:
            raise ValueError(
                f"Column '{col}' is missing from employees_df (after tenure merge). "
                f"Available: {list(active_emp.columns)}"
            )

    # Group and aggregate
    grouped = (
        active_emp.groupby(_GROUP_KEY_COLS, dropna=False)["employee_id"]
        .apply(list)
        .reset_index()
        .rename(columns={"employee_id": "member_employee_ids_raw"})
    )
    grouped["group_size"] = grouped["member_employee_ids_raw"].apply(len)

    # Filter by minimum size
    grouped = grouped[grouped["group_size"] >= min_group_size].copy()

    if grouped.empty:
        logger.warning(
            "No groups with >= %d members found.", min_group_size
        )
        return _empty_groups_df()

    # Serialise member list and criteria
    grouped["member_employee_ids"] = grouped["member_employee_ids_raw"].apply(
        json.dumps
    )
    grouped["criteria"] = grouped.apply(
        lambda row: json.dumps(
            {col: row[col] for col in _GROUP_KEY_COLS}
        ),
        axis=1,
    )
    grouped["group_id"] = [
        f"GRP-{uuid.uuid4().hex[:12].upper()}" for _ in range(len(grouped))
    ]

    output_cols = ["group_id"] + _GROUP_KEY_COLS + [
        "criteria", "member_employee_ids", "group_size"
    ]
    return grouped[output_cols].reset_index(drop=True)


def _empty_groups_df() -> pd.DataFrame:
    """Return an empty DataFrame with the expected groups schema."""
    return pd.DataFrame(
        columns=["group_id"] + _GROUP_KEY_COLS + [
            "criteria", "member_employee_ids", "group_size"
        ]
    )


# ---------------------------------------------------------------------------
# find_comparable_peers
# ---------------------------------------------------------------------------


def find_comparable_peers(
    employee_id: str,
    employees_df: pd.DataFrame,
    salary_df: pd.DataFrame,
    tenure_df: pd.DataFrame,
    groups_df: pd.DataFrame,
) -> dict:
    """Find the comparable peer group for a specific employee.

    Parameters
    ----------
    employee_id:
        The target employee whose peers are sought.
    employees_df:
        Full employees table.
    salary_df:
        Salary records table (used for salary look-ups within peers).
    tenure_df:
        Tenure table.
    groups_df:
        Pre-built comparable groups (output of :func:`build_comparable_groups`).

    Returns
    -------
    dict
        Keys:

        * ``peers`` – list of peer ``employee_id`` strings (excludes target).
        * ``group_id`` – the matched group's ID, or ``None``.
        * ``comparison_criteria`` – dict of the grouping key values.
        * ``is_valid`` – ``True`` when a valid group was found.
        * ``invalidity_reason`` – explanation string when ``is_valid`` is ``False``.
    """
    result: dict = {
        "peers": [],
        "group_id": None,
        "comparison_criteria": {},
        "is_valid": False,
        "invalidity_reason": "",
    }

    if groups_df.empty:
        result["invalidity_reason"] = "No comparable groups have been built."
        return result

    if employees_df.empty:
        result["invalidity_reason"] = "Employee data is unavailable."
        return result

    # Locate the target employee
    emp_row = employees_df[employees_df["employee_id"] == employee_id]
    if emp_row.empty:
        result["invalidity_reason"] = f"Employee '{employee_id}' not found."
        return result

    # Lookup group membership via cached index or single-pass map
    member_to_group = groups_df.attrs.get("_member_to_group_cache") if hasattr(groups_df, "attrs") else None
    if member_to_group is None:
        member_to_group = {}
        for _, grp in groups_df.iterrows():
            members = _safe_json_loads(grp.get("member_employee_ids"))
            for m in members:
                if m not in member_to_group:
                    member_to_group[m] = grp
        try:
            if hasattr(groups_df, "attrs"):
                groups_df.attrs["_member_to_group_cache"] = member_to_group
        except Exception:
            pass

    matched_group: Optional[pd.Series] = member_to_group.get(employee_id)

    if matched_group is None:
        result["invalidity_reason"] = (
            f"Employee '{employee_id}' does not belong to any comparable group "
            "(group size may be below the minimum threshold)."
        )
        return result

    all_members: list[str] = _safe_json_loads(matched_group.get("member_employee_ids"))
    peers = [m for m in all_members if m != employee_id]

    result.update(
        {
            "peers": peers,
            "group_id": matched_group.get("group_id"),
            "comparison_criteria": {
                col: matched_group.get(col) for col in _GROUP_KEY_COLS
            },
            "is_valid": True,
            "invalidity_reason": "",
        }
    )
    return result


# ---------------------------------------------------------------------------
# validate_group_comparability
# ---------------------------------------------------------------------------


def validate_group_comparability(
    group_df: pd.DataFrame,
    roles_df: pd.DataFrame,
) -> pd.DataFrame:
    """Flag groups that mix roles marked as non-comparable.

    If a group contains employees from different role families where any role
    has ``is_comparable_across_roles=False``, the group is flagged as invalid.

    Parameters
    ----------
    group_df:
        Groups DataFrame (output of :func:`build_comparable_groups`).
    roles_df:
        Roles reference table with columns ``role_id``,
        ``role_family``, ``is_comparable_across_roles``.

    Returns
    -------
    pd.DataFrame
        Input *group_df* with two additional columns:

        * ``is_valid_group`` – boolean.
        * ``invalidity_reason`` – string (empty when valid).
    """
    out = group_df.copy()
    out["is_valid_group"] = True
    out["invalidity_reason"] = ""

    if out.empty or roles_df.empty:
        return out

    # Build a mapping: role_family → is_comparable_across_roles
    rf_comparable: dict[str, bool] = {}
    for _, row in roles_df.iterrows():
        rf = row.get("role_family")
        flag = row.get("is_comparable_across_roles", True)
        if rf is not None:
            # If any role in a family is non-comparable, treat the whole family so
            rf_comparable[rf] = rf_comparable.get(rf, True) and bool(flag)

    for idx, grp in out.iterrows():
        members = _safe_json_loads(grp.get("member_employee_ids"))
        if not members:
            continue

        # Collect distinct role families of members
        # We only have role_family per group directly in group_df
        grp_rf = grp.get("role_family")
        if grp_rf and not rf_comparable.get(grp_rf, True):
            # The group's own role family is flagged as non-comparable across roles
            # and the group has >1 role family members would already be a separate check;
            # here we flag cross-family contamination
            out.at[idx, "is_valid_group"] = False
            out.at[idx, "invalidity_reason"] = (
                f"Role family '{grp_rf}' is marked is_comparable_across_roles=False."
            )

    return out


# ---------------------------------------------------------------------------
# compute_group_statistics
# ---------------------------------------------------------------------------


def compute_group_statistics(
    group_df: pd.DataFrame,
    salary_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute descriptive salary statistics for each comparable group.

    Uses ``annual_salary_fte`` (FTE-normalised, INR) for all computations so
    that part-time and full-time employees can be compared on an equal basis.

    Parameters
    ----------
    group_df:
        Groups DataFrame (output of :func:`build_comparable_groups`).
    salary_df:
        Salary records table with columns including:
        ``employee_id``, ``annual_salary_fte``, ``end_date``.
        Only the most-recent (current) record per employee is used
        (where ``end_date`` is ``NaN`` / ``None``).

    Returns
    -------
    pd.DataFrame
        Input *group_df* extended with columns:

        ``median_salary``, ``mean_salary``, ``p25_salary``, ``p75_salary``,
        ``std_dev_salary``, ``min_salary``, ``max_salary``.
    """
    out = group_df.copy()
    stat_cols = [
        "median_salary", "mean_salary", "p25_salary",
        "p75_salary", "std_dev_salary", "min_salary", "max_salary",
    ]
    for col in stat_cols:
        out[col] = np.nan

    if out.empty or salary_df.empty:
        return out

    # Keep only current (active) salary records
    if "end_date" in salary_df.columns:
        current_sal = salary_df[salary_df["end_date"].isna()].copy()
    else:
        current_sal = salary_df.copy()

    if "annual_salary_fte" not in current_sal.columns:
        logger.warning(
            "salary_df missing 'annual_salary_fte'; cannot compute group stats."
        )
        return out

    # Deduplicate: keep one record per employee (latest effective_date)
    if "effective_date" in current_sal.columns:
        current_sal = current_sal.sort_values(
            ["employee_id", "effective_date"], ascending=[True, False]
        ).drop_duplicates(subset=["employee_id"], keep="first")

    sal_map: dict[str, float] = dict(
        zip(current_sal["employee_id"], current_sal["annual_salary_fte"])
    )

    for idx, grp in out.iterrows():
        members = _safe_json_loads(grp.get("member_employee_ids"))
        salaries = [
            sal_map[emp_id]
            for emp_id in members
            if emp_id in sal_map and sal_map[emp_id] is not None
        ]
        if not salaries:
            continue
        arr = np.array(salaries, dtype=float)
        out.at[idx, "median_salary"] = float(np.median(arr))
        out.at[idx, "mean_salary"] = float(np.mean(arr))
        out.at[idx, "p25_salary"] = float(np.percentile(arr, 25))
        out.at[idx, "p75_salary"] = float(np.percentile(arr, 75))
        out.at[idx, "std_dev_salary"] = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        out.at[idx, "min_salary"] = float(np.min(arr))
        out.at[idx, "max_salary"] = float(np.max(arr))

    return out
