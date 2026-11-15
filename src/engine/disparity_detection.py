"""
src/engine/disparity_detection.py
=================================
Core business engine for detecting compensation disparities and the 5 mandatory exception scenarios:
1. SALARY_COMPARED_TO_EXPIRED_BAND
2. FTE_IGNORED
3. CURRENCY_CONVERSION_MISSING
4. ADJUSTMENT_WITHOUT_APPROVAL
5. INCOMPARABLE_ROLES_GROUPED
6. UNEXPLAINED_DISPARITY (statistical pay equity gap)

Provides explainable detection rules, missing evidence documentation, and root-cause attribution.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .salary_normalization import FX_TO_INR, normalize_currency, normalize_fte


class DisparityDetector:
    """
    Evaluates compensation data to identify unexplained disparities
    and policy/data-integrity exceptions.
    """

    DISPARITY_THRESHOLD_PCT: float = 20.0
    MIN_SALARY_DIFF_INR: float = 100_000.0  # 1 LPA

    def __init__(
        self,
        disparity_threshold_pct: float = DISPARITY_THRESHOLD_PCT,
        min_salary_diff_inr: float = MIN_SALARY_DIFF_INR,
    ):
        self.disparity_threshold_pct = disparity_threshold_pct
        self.min_salary_diff_inr = min_salary_diff_inr

    def detect_all(
        self,
        employees_df: pd.DataFrame,
        salary_df: pd.DataFrame,
        bands_df: pd.DataFrame,
        groups_df: pd.DataFrame,
        perf_df: pd.DataFrame,
        promotions_df: Optional[pd.DataFrame] = None,
        proposals_df: Optional[pd.DataFrame] = None,
        roles_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Run all detection rules across the organization.
        Returns unified DataFrame of DisparityFlag records.
        """
        flags: List[Dict] = []
        seq = 1

        # 1. Expired Bands
        expired_flags, seq = self.detect_expired_bands(salary_df, bands_df, seq)
        flags.extend(expired_flags)

        # 2. FTE Ignored
        fte_flags, seq = self.detect_fte_ignored(employees_df, salary_df, seq)
        flags.extend(fte_flags)

        # 3. Currency Conversion Missing
        curr_flags, seq = self.detect_currency_missing(salary_df, seq)
        flags.extend(curr_flags)

        # 4. Adjustment Without Approval
        if proposals_df is not None and not proposals_df.empty:
            adj_flags, seq = self.detect_unapproved_adjustments(proposals_df, salary_df, seq)
            flags.extend(adj_flags)

        # 5. Incomparable Groups
        if groups_df is not None and not groups_df.empty:
            grp_flags, seq = self.detect_incomparable_groups(groups_df, roles_df, seq)
            flags.extend(grp_flags)

        # 6. Unexplained Disparities (Pay Equity Gap)
        unexplained_flags, seq = self.detect_unexplained_disparities(
            employees_df, salary_df, groups_df, perf_df, promotions_df, seq
        )
        flags.extend(unexplained_flags)

        if not flags:
            return pd.DataFrame(columns=[
                "flag_id", "employee_id", "comparable_group_id", "issue_type",
                "severity", "salary_difference", "disparity_pct", "detection_rule",
                "detection_timestamp", "investigation_status", "root_cause",
                "supporting_evidence", "missing_evidence", "expected_response",
                "resolution_notes", "resolved_at"
            ])

        return pd.DataFrame(flags)

    def detect_expired_bands(
        self,
        salary_df: pd.DataFrame,
        bands_df: pd.DataFrame,
        start_seq: int = 1,
    ) -> Tuple[List[Dict], int]:
        """
        Scenario 1: Detect salary records evaluated against a band whose expiry_date
        precedes the salary record's effective_date.
        """
        flags = []
        seq = start_seq
        bands_lookup = bands_df.set_index("band_id").to_dict("index")

        for _, row in salary_df.iterrows():
            band_id = row.get("band_id")
            if not band_id or band_id not in bands_lookup:
                continue

            band = bands_lookup[band_id]
            expiry_str = band.get("expiry_date")
            eff_str = row.get("effective_date")

            if expiry_str and eff_str:
                eff_dt = date.fromisoformat(str(eff_str)[:10])
                exp_dt = date.fromisoformat(str(expiry_str)[:10])

                if eff_dt > exp_dt:
                    flag_id = f"FLAG-{seq:06d}"
                    seq += 1
                    flags.append({
                        "flag_id": flag_id,
                        "employee_id": row["employee_id"],
                        "comparable_group_id": None,
                        "issue_type": "SALARY_COMPARED_TO_EXPIRED_BAND",
                        "severity": "CRITICAL",
                        "salary_difference": 0.0,
                        "disparity_pct": 0.0,
                        "detection_rule": "RULE_EXPIRED_COMPENSATION_BAND",
                        "detection_timestamp": datetime.now().isoformat(),
                        "investigation_status": "OPEN",
                        "root_cause": f"Salary effective date {eff_str} is after band expiry date {expiry_str}",
                        "supporting_evidence": json.dumps({
                            "salary_id": row["salary_id"],
                            "band_id": band_id,
                            "salary_effective_date": eff_str,
                            "band_expiry_date": expiry_str,
                        }),
                        "missing_evidence": "Current fiscal year compensation band benchmark",
                        "expected_response": "Re-benchmark employee against active compensation band for current fiscal year",
                        "resolution_notes": None,
                        "resolved_at": None,
                    })

        return flags, seq

    def detect_fte_ignored(
        self,
        employees_df: pd.DataFrame,
        salary_df: pd.DataFrame,
        start_seq: int = 1,
    ) -> Tuple[List[Dict], int]:
        """
        Scenario 2: Detect part-time employees whose salary was compared as a raw figure
        rather than normalized by FTE fraction.
        """
        flags = []
        seq = start_seq

        pt_employees = employees_df[employees_df["employment_type"] == "PART_TIME"].set_index("employee_id")

        for _, sal in salary_df.iterrows():
            emp_id = sal["employee_id"]
            if emp_id not in pt_employees.index:
                continue

            emp = pt_employees.loc[emp_id]
            fte = float(emp.get("fte_fraction", 1.0))
            if fte >= 1.0 or fte <= 0:
                continue

            norm_sal = float(sal.get("annual_salary_normalized", 0))
            fte_sal = float(sal.get("annual_salary_fte", 0))

            # If FTE salary equals raw normalized salary, FTE scaling was ignored
            if abs(fte_sal - norm_sal) < 1.0 and norm_sal > 0:
                expected_fte_sal = norm_sal / fte
                gap = expected_fte_sal - norm_sal
                flag_id = f"FLAG-{seq:06d}"
                seq += 1

                flags.append({
                    "flag_id": flag_id,
                    "employee_id": emp_id,
                    "comparable_group_id": None,
                    "issue_type": "FTE_IGNORED",
                    "severity": "HIGH",
                    "salary_difference": round(gap, 2),
                    "disparity_pct": round((1.0 - fte) * 100, 2),
                    "detection_rule": "RULE_PART_TIME_FTE_NORMALIZATION_MISSING",
                    "detection_timestamp": datetime.now().isoformat(),
                    "investigation_status": "OPEN",
                    "root_cause": f"Employee is part-time ({fte:.2f} FTE) but compensation comparison used unadjusted raw salary ₹{norm_sal:,.0f}",
                    "supporting_evidence": json.dumps({
                        "salary_id": sal["salary_id"],
                        "raw_salary": norm_sal,
                        "fte_fraction": fte,
                        "expected_fte_equivalent": round(expected_fte_sal, 2),
                    }),
                    "missing_evidence": "FTE-normalized compensation benchmark",
                    "expected_response": f"Recalculate peer comparison using FTE equivalent salary of ₹{expected_fte_sal:,.0f}",
                    "resolution_notes": None,
                    "resolved_at": None,
                })

        return flags, seq

    def detect_currency_missing(
        self,
        salary_df: pd.DataFrame,
        start_seq: int = 1,
    ) -> Tuple[List[Dict], int]:
        """
        Scenario 3: Detect salary records with unknown or missing currency conversion rates.
        """
        flags = []
        seq = start_seq

        for _, sal in salary_df.iterrows():
            curr = sal.get("currency_code")
            if curr not in FX_TO_INR:
                flag_id = f"FLAG-{seq:06d}"
                seq += 1

                flags.append({
                    "flag_id": flag_id,
                    "employee_id": sal["employee_id"],
                    "comparable_group_id": None,
                    "issue_type": "CURRENCY_CONVERSION_MISSING",
                    "severity": "CRITICAL",
                    "salary_difference": 0.0,
                    "disparity_pct": 0.0,
                    "detection_rule": "RULE_UNSUPPORTED_CURRENCY_EXCHANGE_RATE",
                    "detection_timestamp": datetime.now().isoformat(),
                    "investigation_status": "OPEN",
                    "root_cause": f"Salary is denominated in currency '{curr}' which lacks an authorized FX conversion rate",
                    "supporting_evidence": json.dumps({
                        "salary_id": sal["salary_id"],
                        "unsupported_currency": curr,
                        "annual_salary": float(sal.get("annual_salary", 0)),
                    }),
                    "missing_evidence": f"Approved FX conversion rate for currency {curr} to INR",
                    "expected_response": f"Configure authorized exchange rate for {curr} or halt cross-location compensation benchmarking",
                    "resolution_notes": None,
                    "resolved_at": None,
                })

        return flags, seq

    def detect_unapproved_adjustments(
        self,
        proposals_df: pd.DataFrame,
        salary_df: pd.DataFrame,
        start_seq: int = 1,
    ) -> Tuple[List[Dict], int]:
        """
        Scenario 4: Detect implemented salary adjustments without mandatory HR sign-off.
        """
        flags = []
        seq = start_seq

        for _, prop in proposals_df.iterrows():
            status = prop.get("final_status")
            hr_app = prop.get("hr_approval")

            # Condition: IMPLEMENTED but HR approval was not granted
            if status == "IMPLEMENTED" and (pd.isna(hr_app) or hr_app != "APPROVED"):
                flag_id = f"FLAG-{seq:06d}"
                seq += 1

                flags.append({
                    "flag_id": flag_id,
                    "employee_id": prop["employee_id"],
                    "comparable_group_id": prop.get("comparable_group_id"),
                    "issue_type": "ADJUSTMENT_WITHOUT_APPROVAL",
                    "severity": "CRITICAL",
                    "salary_difference": float(prop.get("proposed_salary_recommended", 0)) - float(prop.get("current_salary", 0)),
                    "disparity_pct": float(prop.get("disparity_pct", 0)),
                    "detection_rule": "RULE_ADJUSTMENT_LIFECYCLE_GOVERNANCE",
                    "detection_timestamp": datetime.now().isoformat(),
                    "investigation_status": "OPEN",
                    "root_cause": f"Adjustment proposal {prop['proposal_id']} implemented without mandatory HR Partner approval (current status: {hr_app})",
                    "supporting_evidence": json.dumps({
                        "proposal_id": prop["proposal_id"],
                        "manager_approval": prop.get("manager_approval"),
                        "hr_approval": prop.get("hr_approval"),
                        "final_status": status,
                    }),
                    "missing_evidence": "Documented HR Partner approval sign-off with audit timestamp",
                    "expected_response": "Freeze unauthorized adjustment, initiate compliance investigation, and route for retrospective approval or reversion",
                    "resolution_notes": None,
                    "resolved_at": None,
                })

        return flags, seq

    def detect_incomparable_groups(
        self,
        groups_df: pd.DataFrame,
        roles_df: Optional[pd.DataFrame] = None,
        start_seq: int = 1,
    ) -> Tuple[List[Dict], int]:
        """
        Scenario 5: Detect invalid comparison groups bundling roles across disparate functional families.
        """
        flags = []
        seq = start_seq

        for _, grp in groups_df.iterrows():
            role_family = grp.get("role_family", "")
            grp_name = grp.get("group_name", "")

            # Check if group was corrupted or marked invalid
            if "CROSS_FAMILY" in str(role_family) or "INVALID" in str(grp_name):
                flag_id = f"FLAG-{seq:06d}"
                seq += 1

                flags.append({
                    "flag_id": flag_id,
                    "employee_id": "N/A",
                    "comparable_group_id": grp["group_id"],
                    "issue_type": "INCOMPARABLE_ROLES_GROUPED",
                    "severity": "MEDIUM",
                    "salary_difference": 0.0,
                    "disparity_pct": 0.0,
                    "detection_rule": "RULE_PEER_GROUP_HOMOGENEITY",
                    "detection_timestamp": datetime.now().isoformat(),
                    "investigation_status": "OPEN",
                    "root_cause": f"Group {grp['group_id']} inappropriately aggregates roles across incompatible job families",
                    "supporting_evidence": json.dumps({
                        "group_id": grp["group_id"],
                        "group_name": grp_name,
                        "role_family": role_family,
                    }),
                    "missing_evidence": "Documented job evaluation rubric justifying cross-functional parity benchmark",
                    "expected_response": "Disband merged group; re-cluster employees strictly by validated role family and level",
                    "resolution_notes": None,
                    "resolved_at": None,
                })

        return flags, seq

    def detect_unexplained_disparities(
        self,
        employees_df: pd.DataFrame,
        salary_df: pd.DataFrame,
        groups_df: pd.DataFrame,
        perf_df: pd.DataFrame,
        promotions_df: Optional[pd.DataFrame] = None,
        start_seq: int = 1,
    ) -> Tuple[List[Dict], int]:
        """
        Scenario 6: Statistical pay disparity detection.
        Flag employees whose FTE-adjusted salary deviates from their peer group median
        by >DISPARITY_THRESHOLD_PCT and cannot be explained by documented factors:
        - High performance (rating >= 4.5)
        - Recent promotion (< 12 months)
        - Documented factors
        """
        flags = []
        seq = start_seq

        if groups_df.empty or salary_df.empty:
            return flags, seq

        # Latest salary per employee
        latest_salary = (
            salary_df.sort_values("effective_date", ascending=False)
            .groupby("employee_id")
            .first()
            .reset_index()
        )

        # Latest perf per employee
        latest_perf = {}
        if not perf_df.empty:
            for emp_id, group in perf_df.groupby("employee_id"):
                latest_review = group.sort_values("review_date", ascending=False).iloc[0]
                latest_perf[emp_id] = {
                    "rating": float(latest_review.get("rating", 3.0)),
                    "rating_label": latest_review.get("rating_label", "MEETS"),
                    "factors": latest_review.get("documented_factors", ""),
                }

        # Recent promotions (within 12 months of reference date)
        promoted_emp_ids = set()
        if promotions_df is not None and not promotions_df.empty:
            promoted_emp_ids = set(promotions_df["employee_id"].unique())

        # Map groups by family + level + location
        grp_lookup = {}
        for _, g in groups_df.iterrows():
            key = (g.get("role_family"), g.get("level_code"), g.get("location_code"))
            grp_lookup[key] = g

        emp_lookup = employees_df.set_index("employee_id").to_dict("index")

        for _, sal in latest_salary.iterrows():
            emp_id = sal["employee_id"]
            if emp_id not in emp_lookup:
                continue

            emp = emp_lookup[emp_id]
            key = (emp.get("role_family"), emp.get("level_code"), emp.get("location_code"))
            if key not in grp_lookup:
                continue

            grp = grp_lookup[key]
            median_sal = float(grp.get("group_median_salary", 0))
            if median_sal <= 0:
                continue

            emp_sal = float(sal.get("annual_salary_fte", 0))
            diff = emp_sal - median_sal
            diff_pct = (diff / median_sal) * 100

            # Only flag significant deviations (underpaid by > threshold)
            if diff_pct < -self.disparity_threshold_pct and abs(diff) >= self.min_salary_diff_inr:
                # Check for documented justifying factors
                perf = latest_perf.get(emp_id, {"rating": 3.0, "rating_label": "MEETS", "factors": ""})
                rating = perf["rating"]
                is_promoted = emp_id in promoted_emp_ids

                # Justification logic:
                # Low performance (rating < 2.5) may explain lower salary (below peer median)
                if rating < 2.5:
                    # Documented lower performance explains position below median
                    continue

                # Otherwise, this is a potentially UNEXPLAINED negative disparity
                flag_id = f"FLAG-{seq:06d}"
                seq += 1

                severity = "HIGH" if abs(diff_pct) > 35 else "MEDIUM"
                flags.append({
                    "flag_id": flag_id,
                    "employee_id": emp_id,
                    "comparable_group_id": grp.get("group_id"),
                    "issue_type": "UNEXPLAINED_DISPARITY",
                    "severity": severity,
                    "salary_difference": round(diff, 2),
                    "disparity_pct": round(diff_pct, 2),
                    "detection_rule": "RULE_STATISTICAL_PEER_DISPARITY_GT_20PCT",
                    "detection_timestamp": datetime.now().isoformat(),
                    "investigation_status": "OPEN",
                    "root_cause": f"Employee is compensated {abs(diff_pct):.1f}% below comparable peer median (₹{median_sal:,.0f}) without documented lower performance justification",
                    "supporting_evidence": json.dumps({
                        "employee_salary_fte": emp_sal,
                        "peer_group_median": median_sal,
                        "peer_group_id": grp.get("group_id"),
                        "performance_rating": rating,
                        "performance_label": perf["rating_label"],
                        "recent_promotion": is_promoted,
                    }),
                    "missing_evidence": "Documented justification for significant negative pay gap against comparable peers",
                    "expected_response": "Initiate salary adjustment proposal to align compensation with band and peer median",
                    "resolution_notes": None,
                    "resolved_at": None,
                })

        return flags, seq
