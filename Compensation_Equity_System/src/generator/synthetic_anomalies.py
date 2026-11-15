"""
src/generator/synthetic_anomalies.py
====================================
Injects deliberate, labeled anomalies corresponding to the 5 mandatory negative scenarios:
1. SALARY_COMPARED_TO_EXPIRED_BAND
2. FTE_IGNORED
3. CURRENCY_CONVERSION_MISSING
4. ADJUSTMENT_WITHOUT_APPROVAL
5. INCOMPARABLE_ROLES_GROUPED

Also generates the isolated `data/ground_truth/ground_truth.csv` and `.json`.
Ground truth is strictly isolated from analytical inputs.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np

try:
    from .config import (
        ANOMALY_EXPIRED_BAND_INJECT_COUNT,
        ANOMALY_FTE_IGNORED_COUNT,
        ANOMALY_CURRENCY_MISSING_COUNT,
        ANOMALY_UNAPPROVED_ADJUSTMENT_COUNT,
        ANOMALY_INCOMPARABLE_GROUP_COUNT,
    )
except ImportError:
    from config import (
        ANOMALY_EXPIRED_BAND_INJECT_COUNT,
        ANOMALY_FTE_IGNORED_COUNT,
        ANOMALY_CURRENCY_MISSING_COUNT,
        ANOMALY_UNAPPROVED_ADJUSTMENT_COUNT,
        ANOMALY_INCOMPARABLE_GROUP_COUNT,
    )


def inject_expired_bands(
    df_salary: pd.DataFrame,
    df_bands: pd.DataFrame,
    n_anomalies: int = ANOMALY_EXPIRED_BAND_INJECT_COUNT,
    rng: np.random.RandomState = None,
) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Scenario 1: SALARY_COMPARED_TO_EXPIRED_BAND
    Select active salary records in 2025/2026 and reassign their band_id to an
    expired 2024 band (expiry_date < effective_date).
    """
    if rng is None:
        rng = np.random.RandomState(42)

    df_sal = df_salary.copy()
    expired_bands = df_bands[df_bands["is_active"] == False]
    if expired_bands.empty:
        # Fall back to any 2024 band and mark it expired in the past
        expired_bands = df_bands[df_bands["fiscal_year"] == 2024]

    target_salaries = df_sal[df_sal["effective_date"] >= "2025-01-01"]
    sample_size = min(n_anomalies, len(target_salaries), len(expired_bands))

    if sample_size == 0:
        return df_sal, []

    chosen_salary_indices = target_salaries.sample(
        n=sample_size, random_state=rng.randint(0, 2**31 - 1)
    ).index

    ground_truth_records = []
    timestamp = datetime.now().isoformat()

    for idx in chosen_salary_indices:
        expired_band_row = expired_bands.sample(
            n=1, random_state=rng.randint(0, 2**31 - 1)
        ).iloc[0]
        old_band_id = df_sal.at[idx, "band_id"]
        sal_id = df_sal.at[idx, "salary_id"]
        emp_id = df_sal.at[idx, "employee_id"]
        effective_date = df_sal.at[idx, "effective_date"]

        df_sal.at[idx, "band_id"] = expired_band_row["band_id"]

        ground_truth_records.append({
            "record_id": sal_id,
            "table_name": "salary_records",
            "employee_id": emp_id,
            "issue_type": "SALARY_COMPARED_TO_EXPIRED_BAND",
            "severity": "CRITICAL",
            "description": f"Salary effective {effective_date} evaluated against band {expired_band_row['band_id']} expired on {expired_band_row['expiry_date']}",
            "expected_decision": "REJECT_COMPARISON_USE_ACTIVE_BAND",
            "injected_at": timestamp,
        })

    return df_sal, ground_truth_records


def inject_fte_ignored(
    df_salary: pd.DataFrame,
    df_emp: pd.DataFrame,
    n_anomalies: int = ANOMALY_FTE_IGNORED_COUNT,
    rng: np.random.RandomState = None,
) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Scenario 2: FTE_IGNORED
    For part-time employees (fte_fraction < 1.0), overwrite annual_salary_fte with raw
    annual_salary_normalized, simulating the error where part-time hours were ignored.
    """
    if rng is None:
        rng = np.random.RandomState(42)

    df_sal = df_salary.copy()
    part_time_emp_ids = df_emp[df_emp["employment_type"] == "PART_TIME"]["employee_id"].unique()
    pt_salaries = df_sal[df_sal["employee_id"].isin(part_time_emp_ids)]

    sample_size = min(n_anomalies, len(pt_salaries))
    if sample_size == 0:
        return df_sal, []

    chosen_indices = pt_salaries.sample(
        n=sample_size, random_state=rng.randint(0, 2**31 - 1)
    ).index

    ground_truth_records = []
    timestamp = datetime.now().isoformat()

    for idx in chosen_indices:
        emp_id = df_sal.at[idx, "employee_id"]
        sal_id = df_sal.at[idx, "salary_id"]
        emp_row = df_emp[df_emp["employee_id"] == emp_id].iloc[0]
        fte = emp_row["fte_fraction"]

        # Overwrite annual_salary_fte with unadjusted annual_salary_normalized
        raw_norm = df_sal.at[idx, "annual_salary_normalized"]
        df_sal.at[idx, "annual_salary_fte"] = raw_norm

        ground_truth_records.append({
            "record_id": sal_id,
            "table_name": "salary_records",
            "employee_id": emp_id,
            "issue_type": "FTE_IGNORED",
            "severity": "HIGH",
            "description": f"Part-time employee (FTE={fte}) salary not normalized to full-time equivalent; compared as raw amount ₹{raw_norm:,.0f}",
            "expected_decision": "NORMALIZE_BY_FTE_FRACTION",
            "injected_at": timestamp,
        })

    return df_sal, ground_truth_records


def inject_currency_missing(
    df_salary: pd.DataFrame,
    n_anomalies: int = ANOMALY_CURRENCY_MISSING_COUNT,
    rng: np.random.RandomState = None,
) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Scenario 3: CURRENCY_CONVERSION_MISSING
    Set currency_code to 'XYZ' (an unknown, unmapped currency code) on selected salary records.
    """
    if rng is None:
        rng = np.random.RandomState(42)

    df_sal = df_salary.copy()
    sample_size = min(n_anomalies, len(df_sal))
    if sample_size == 0:
        return df_sal, []

    chosen_indices = df_sal.sample(
        n=sample_size, random_state=rng.randint(0, 2**31 - 1)
    ).index

    ground_truth_records = []
    timestamp = datetime.now().isoformat()

    for idx in chosen_indices:
        sal_id = df_sal.at[idx, "salary_id"]
        emp_id = df_sal.at[idx, "employee_id"]
        orig_curr = df_sal.at[idx, "currency_code"]

        df_sal.at[idx, "currency_code"] = "XYZ"

        ground_truth_records.append({
            "record_id": sal_id,
            "table_name": "salary_records",
            "employee_id": emp_id,
            "issue_type": "CURRENCY_CONVERSION_MISSING",
            "severity": "CRITICAL",
            "description": f"Currency code 'XYZ' lacks an exchange rate mapping to INR; cannot be validly compared",
            "expected_decision": "HALT_COMPARISON_FLAG_MISSING_FX",
            "injected_at": timestamp,
        })

    return df_sal, ground_truth_records


def inject_unapproved_adjustments(
    df_proposals: pd.DataFrame,
    df_salary: pd.DataFrame,
    n_anomalies: int = ANOMALY_UNAPPROVED_ADJUSTMENT_COUNT,
    rng: np.random.RandomState = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict]]:
    """
    Scenario 4: ADJUSTMENT_WITHOUT_APPROVAL
    Set proposal final_status='IMPLEMENTED' while hr_approval is NULL / PENDING,
    and update salary record change_reason to 'ADJUSTMENT' without required sign-off.
    """
    if rng is None:
        rng = np.random.RandomState(42)

    df_prop = df_proposals.copy()
    df_sal = df_salary.copy()

    sample_size = min(n_anomalies, len(df_prop))
    if sample_size == 0:
        return df_prop, df_sal, []

    chosen_prop_indices = df_prop.sample(
        n=sample_size, random_state=rng.randint(0, 2**31 - 1)
    ).index

    ground_truth_records = []
    timestamp = datetime.now().isoformat()

    for idx in chosen_prop_indices:
        prop_id = df_prop.at[idx, "proposal_id"]
        emp_id = df_prop.at[idx, "employee_id"]

        # Deliberately violate approval lifecycle
        df_prop.at[idx, "manager_approval"] = "APPROVED"
        df_prop.at[idx, "hr_approval"] = "PENDING"
        df_prop.at[idx, "hr_approval_date"] = None
        df_prop.at[idx, "final_status"] = "IMPLEMENTED"

        # Reflect unapproved adjustment in the salary records
        emp_salaries = df_sal[df_sal["employee_id"] == emp_id]
        if not emp_salaries.empty:
            sal_idx = emp_salaries.sort_values("effective_date", ascending=False).index[0]
            df_sal.at[sal_idx, "change_reason"] = "ADJUSTMENT"

        ground_truth_records.append({
            "record_id": prop_id,
            "table_name": "adjustment_proposals",
            "employee_id": emp_id,
            "issue_type": "ADJUSTMENT_WITHOUT_APPROVAL",
            "severity": "CRITICAL",
            "description": f"Salary adjustment proposal {prop_id} implemented without mandatory HR Partner approval",
            "expected_decision": "FLAG_UNAUTHORIZED_CHANGE_REQUIRE_REVERT_OR_HR_APPROVAL",
            "injected_at": timestamp,
        })

    return df_prop, df_sal, ground_truth_records


def inject_incomparable_groups(
    df_groups: pd.DataFrame,
    df_roles: pd.DataFrame,
    n_anomalies: int = ANOMALY_INCOMPARABLE_GROUP_COUNT,
    rng: np.random.RandomState = None,
) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Scenario 5: INCOMPARABLE_ROLES_GROUPED
    Group non-comparable roles (e.g. Software Engineer and Product Manager) together
    into a single comparable group without documented rationale.
    """
    if rng is None:
        rng = np.random.RandomState(42)

    df_grp = df_groups.copy()
    sample_size = min(n_anomalies, len(df_grp))
    if sample_size == 0:
        return df_grp, []

    chosen_grp_indices = df_grp.sample(
        n=sample_size, random_state=rng.randint(0, 2**31 - 1)
    ).index

    ground_truth_records = []
    timestamp = datetime.now().isoformat()

    for idx in chosen_grp_indices:
        grp_id = df_grp.at[idx, "group_id"]
        # Intentionally contaminate role family comparison
        df_grp.at[idx, "role_family"] = "CROSS_FAMILY_INVALID"
        df_grp.at[idx, "group_name"] = f"INVALID_MERGE_{grp_id}"

        ground_truth_records.append({
            "record_id": grp_id,
            "table_name": "comparable_groups",
            "employee_id": "N/A",
            "issue_type": "INCOMPARABLE_ROLES_GROUPED",
            "severity": "MEDIUM",
            "description": f"Group {grp_id} bundles incomparable role families without documented organizational rationale",
            "expected_decision": "DISBAND_GROUP_SPLIT_BY_FUNCTIONAL_FAMILY",
            "injected_at": timestamp,
        })

    return df_grp, ground_truth_records


def export_ground_truth(
    records: List[Dict],
    output_dir: Path,
) -> Path:
    """
    Write all injected ground truth records to data/ground_truth/ground_truth.csv and .json.
    """
    gt_dir = output_dir / "ground_truth"
    gt_dir.mkdir(parents=True, exist_ok=True)

    df_gt = pd.DataFrame(records)
    csv_path = gt_dir / "ground_truth.csv"
    json_path = gt_dir / "ground_truth.json"

    df_gt.to_csv(csv_path, index=False)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    return csv_path
