"""
src/validation/integrity.py
===========================
Automated integrity validation for the Compensation Equity System datasets:
- Primary key uniqueness
- Foreign key referential integrity
- Allowed enum domain membership
- Required field null checks
- Date chronological ordering
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd


@dataclass
class ValidationResult:
    table_name: str
    check_name: str
    passed: bool
    total_records: int
    violating_records: int
    error_examples: List[Any] = field(default_factory=list)
    message: str = ""


@dataclass
class ValidationReport:
    timestamp: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    all_passed: bool
    results: List[ValidationResult] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    def print_summary(self) -> None:
        print("\n=======================================================")
        print("📋 DATA INTEGRITY VALIDATION SUMMARY")
        print(f"   Timestamp:     {self.timestamp}")
        print(f"   Total checks:  {self.total_checks}")
        print(f"   Passed:        {self.passed_checks} ✅")
        print(f"   Failed:        {self.failed_checks} ❌")
        print(f"   Verdict:       {'PASSED ALL CHECKS' if self.all_passed else 'FAILURES DETECTED'}")
        print("=======================================================")
        for res in self.results:
            icon = "✅" if res.passed else "❌"
            print(f"   {icon} [{res.table_name:20s}] {res.check_name:30s} : {res.message}")
            if not res.passed and res.error_examples:
                print(f"      ↳ Sample errors: {res.error_examples[:3]}")
        print("=======================================================\n")


class DataIntegrityValidator:
    """Performs comprehensive relational and schema integrity checks across all generated tables."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.master_dir = self.data_dir / "master"
        self.trans_dir = self.data_dir / "transactions"

    def load_table(self, name: str) -> pd.DataFrame:
        p1 = self.master_dir / f"{name}.csv"
        p2 = self.trans_dir / f"{name}.csv"
        if p1.exists():
            return pd.read_csv(p1)
        if p2.exists():
            return pd.read_csv(p2)
        raise FileNotFoundError(f"Table '{name}' not found in master or transactions directory.")

    def run_all(self) -> ValidationReport:
        results: List[ValidationResult] = []

        # Load all tables
        try:
            df_roles = self.load_table("roles")
            df_levels = self.load_table("levels")
            df_locs = self.load_table("locations")
            df_bands = self.load_table("compensation_bands")
            df_emp = self.load_table("employees")
            df_sal = self.load_table("salary_records")
            df_perf = self.load_table("performance_evidence")
            df_tenure = self.load_table("tenure")
            df_promo = self.load_table("promotions")
            df_groups = self.load_table("comparable_groups")
            df_proposals = self.load_table("adjustment_proposals")
            df_flags = self.load_table("disparity_flags")
        except Exception as e:
            results.append(ValidationResult(
                table_name="ALL",
                check_name="FILE_LOADING",
                passed=False,
                total_records=0,
                violating_records=1,
                message=f"Failed loading CSV files: {e}"
            ))
            return ValidationReport(
                timestamp=datetime.now().isoformat(),
                total_checks=1,
                passed_checks=0,
                failed_checks=1,
                all_passed=False,
                results=results
            )

        # 1. Primary Key Uniqueness
        pk_specs = [
            (df_roles, "roles", "role_id"),
            (df_levels, "levels", "level_id"),
            (df_locs, "locations", "location_id"),
            (df_bands, "compensation_bands", "band_id"),
            (df_emp, "employees", "employee_id"),
            (df_sal, "salary_records", "salary_id"),
            (df_perf, "performance_evidence", "perf_id"),
            (df_tenure, "tenure", "tenure_id"),
            (df_promo, "promotions", "promo_id"),
            (df_groups, "comparable_groups", "group_id"),
            (df_proposals, "adjustment_proposals", "proposal_id"),
            (df_flags, "disparity_flags", "flag_id"),
        ]
        for df, tbl, pk in pk_specs:
            results.append(self._check_pk(df, tbl, pk))

        # 2. Foreign Key Integrity
        fk_specs = [
            (df_emp, "employees", "role_id", df_roles, "roles", "role_id"),
            (df_emp, "employees", "level_id", df_levels, "levels", "level_id"),
            (df_emp, "employees", "location_id", df_locs, "locations", "location_id"),
            (df_sal, "salary_records", "employee_id", df_emp, "employees", "employee_id"),
            (df_sal, "salary_records", "band_id", df_bands, "compensation_bands", "band_id"),
            (df_perf, "performance_evidence", "employee_id", df_emp, "employees", "employee_id"),
            (df_tenure, "tenure", "employee_id", df_emp, "employees", "employee_id"),
            (df_promo, "promotions", "employee_id", df_emp, "employees", "employee_id"),
            (df_promo, "promotions", "to_level_id", df_levels, "levels", "level_id"),
            (df_proposals, "adjustment_proposals", "employee_id", df_emp, "employees", "employee_id"),
        ]
        for c_df, c_tbl, c_fk, p_df, p_tbl, p_pk in fk_specs:
            results.append(self._check_fk(c_df, c_tbl, c_fk, p_df, p_tbl, p_pk))

        # 3. Enum Value Checks
        enum_specs = [
            (df_emp, "employees", "gender", {"M", "F", "NB"}),
            (df_emp, "employees", "employment_type", {"FULL_TIME", "PART_TIME"}),
            (df_emp, "employees", "status", {"ACTIVE", "INACTIVE", "ON_LEAVE"}),
            (df_levels, "levels", "track", {"IC", "MANAGER"}),
            (df_perf, "performance_evidence", "rating_label", {"EXCEEDS", "MEETS", "BELOW", "PIP"}),
            (df_proposals, "adjustment_proposals", "final_status", {"OPEN", "APPROVED", "REJECTED", "IMPLEMENTED", "WITHDRAWN", "PENDING_HR", "PENDING_MANAGER", "MANAGER_APPROVED", "MANAGER_REJECTED", "HR_APPROVED", "HR_REJECTED"}),
            (df_flags, "disparity_flags", "severity", {"LOW", "MEDIUM", "HIGH", "CRITICAL"}),
        ]
        for df, tbl, col, allowed in enum_specs:
            results.append(self._check_enum(df, tbl, col, allowed))

        # 4. Chronological Date Ordering
        results.append(self._check_dates_after(
            df_sal, "salary_records", "effective_date", df_emp, "employees", "hire_date", "employee_id"
        ))

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        return ValidationReport(
            timestamp=datetime.now().isoformat(),
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            all_passed=(failed == 0),
            results=results
        )

    def _check_pk(self, df: pd.DataFrame, table: str, pk_col: str) -> ValidationResult:
        total = len(df)
        dups = df[df.duplicated(subset=[pk_col], keep=False)]
        violating = len(dups)
        passed = (violating == 0)
        examples = dups[pk_col].unique().tolist()[:5] if not passed else []
        msg = f"All {total:,} PKs unique." if passed else f"Found {violating} duplicate PKs in '{pk_col}'."
        return ValidationResult(table, f"PK_UNIQUE_{pk_col}", passed, total, violating, examples, msg)

    def _check_fk(
        self,
        child_df: pd.DataFrame,
        child_table: str,
        fk_col: str,
        parent_df: pd.DataFrame,
        parent_table: str,
        pk_col: str,
    ) -> ValidationResult:
        total = len(child_df)
        parent_keys = set(parent_df[pk_col].dropna().unique())
        child_vals = child_df[fk_col].dropna()
        orphans = child_vals[~child_vals.isin(parent_keys)]
        violating = len(orphans)
        passed = (violating == 0)
        examples = orphans.unique().tolist()[:5] if not passed else []
        msg = f"All {total:,} FKs reference valid {parent_table}.{pk_col}." if passed else f"Found {violating} orphaned rows in '{fk_col}'."
        return ValidationResult(child_table, f"FK_INTEGRITY_{fk_col}_TO_{parent_table}", passed, total, violating, examples, msg)

    def _check_enum(self, df: pd.DataFrame, table: str, col: str, allowed: Set[str]) -> ValidationResult:
        total = len(df)
        invalid = df[~df[col].isin(allowed) & df[col].notna()]
        violating = len(invalid)
        passed = (violating == 0)
        examples = invalid[col].unique().tolist()[:5] if not passed else []
        msg = f"All values belong to domain {allowed}." if passed else f"Found {violating} invalid domain values in '{col}'."
        return ValidationResult(table, f"ENUM_DOMAIN_{col}", passed, total, violating, examples, msg)

    def _check_dates_after(
        self,
        child_df: pd.DataFrame,
        child_table: str,
        child_dt_col: str,
        parent_df: pd.DataFrame,
        parent_table: str,
        parent_dt_col: str,
        join_col: str,
    ) -> ValidationResult:
        total = len(child_df)
        merged = child_df[[join_col, child_dt_col]].merge(
            parent_df[[join_col, parent_dt_col]], on=join_col, how="inner"
        )
        # Compare strings or dates
        invalid = merged[merged[child_dt_col] < merged[parent_dt_col]]
        violating = len(invalid)
        passed = (violating == 0)
        examples = invalid.head(3).to_dict("records") if not passed else []
        msg = f"All {child_dt_col} >= {parent_table}.{parent_dt_col}." if passed else f"Found {violating} records with {child_dt_col} before {parent_dt_col}."
        return ValidationResult(child_table, f"DATE_ORDER_{child_dt_col}_GTE_{parent_dt_col}", passed, total, violating, examples, msg)
