"""
compensation.py
---------------
CompensationAnalyzer: the main orchestrator for per-employee and aggregate
compensation analysis.  Wraps salary_normalization, comparable_groups and
disparity_detection to produce dashboard-ready outputs.
"""

from __future__ import annotations

import datetime
import json
import logging
from typing import Optional

import numpy as np
import pandas as pd

from .salary_normalization import (
    REFERENCE_DATE,
    FX_TO_INR,
    CurrencyMissingError,
    ExpiredBandError,
    FTEError,
    normalize_salary,
    compute_compa_ratio,
    compute_band_position,
    classify_compa_ratio,
    validate_band_active,
)
from .comparable_groups import (
    build_comparable_groups,
    compute_group_statistics,
    find_comparable_peers,
    validate_group_comparability,
)

logger = logging.getLogger(__name__)


class CompensationAnalyzer:
    """Main compensation analysis orchestrator.

    On instantiation, loads all reference DataFrames and runs an initial
    normalization pass so that subsequent per-employee queries are fast
    (O(1) look-ups into pre-computed structures).

    Parameters
    ----------
    employees_df:
        Employee master table.
    salary_df:
        Salary records (one or more per employee; current record has null
        ``end_date``).
    bands_df:
        Compensation bands.
    tenure_df:
        Tenure records (one per employee).
    perf_df:
        Performance evidence records.
    roles_df:
        Role reference data.
    levels_df:
        Level reference data.
    locations_df:
        Location reference data.
    evaluation_date:
        The date used for band validity checks.  Defaults to
        :data:`~salary_normalization.REFERENCE_DATE`.
    """

    def __init__(
        self,
        employees_df: pd.DataFrame,
        salary_df: pd.DataFrame,
        bands_df: pd.DataFrame,
        tenure_df: pd.DataFrame,
        perf_df: pd.DataFrame,
        roles_df: pd.DataFrame,
        levels_df: pd.DataFrame,
        locations_df: pd.DataFrame,
        evaluation_date: datetime.date = REFERENCE_DATE,
    ) -> None:
        self.employees_df = employees_df.copy() if employees_df is not None else pd.DataFrame()
        self.salary_df = salary_df.copy() if salary_df is not None else pd.DataFrame()
        self.bands_df = bands_df.copy() if bands_df is not None else pd.DataFrame()
        self.tenure_df = tenure_df.copy() if tenure_df is not None else pd.DataFrame()
        self.perf_df = perf_df.copy() if perf_df is not None else pd.DataFrame()
        self.roles_df = roles_df.copy() if roles_df is not None else pd.DataFrame()
        self.levels_df = levels_df.copy() if levels_df is not None else pd.DataFrame()
        self.locations_df = locations_df.copy() if locations_df is not None else pd.DataFrame()
        self.evaluation_date = evaluation_date

        # Pre-compute comparable groups and their statistics
        self._groups_df: pd.DataFrame = pd.DataFrame()
        self._analysis_cache: dict[str, dict] = {}
        self._run_initial_normalization()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_initial_normalization(self) -> None:
        """Pre-compute comparable groups and cache for fast retrieval."""
        try:
            if not self.employees_df.empty and not self.tenure_df.empty:
                raw_groups = build_comparable_groups(
                    self.employees_df, self.tenure_df
                )
                if not raw_groups.empty and not self.roles_df.empty:
                    raw_groups = validate_group_comparability(raw_groups, self.roles_df)
                if not raw_groups.empty and not self.salary_df.empty:
                    raw_groups = compute_group_statistics(raw_groups, self.salary_df)
                self._groups_df = raw_groups
            logger.info(
                "Initial normalization complete. %d comparable groups built.",
                len(self._groups_df),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Error during initial normalization: %s", exc)

    def _get_current_salary(self, employee_id: str) -> Optional[pd.Series]:
        """Return the current (end_date is null) salary record for an employee."""
        if self.salary_df.empty:
            return None
        emp_sal = self.salary_df[self.salary_df["employee_id"] == employee_id]
        if emp_sal.empty:
            return None
        if "end_date" in emp_sal.columns:
            current = emp_sal[emp_sal["end_date"].isna()]
            if not current.empty:
                return current.iloc[-1]
        # Fallback: most recent by effective_date
        if "effective_date" in emp_sal.columns:
            return emp_sal.sort_values("effective_date").iloc[-1]
        return emp_sal.iloc[-1]

    def _get_latest_perf(self, employee_id: str) -> Optional[pd.Series]:
        """Return the most recent active performance record."""
        if self.perf_df.empty:
            return None
        emp_perf = self.perf_df[self.perf_df["employee_id"] == employee_id]
        if "is_active" in emp_perf.columns:
            emp_perf = emp_perf[emp_perf["is_active"] == True]  # noqa: E712
        if emp_perf.empty:
            return None
        if "review_date" in emp_perf.columns:
            return emp_perf.sort_values("review_date").iloc[-1]
        return emp_perf.iloc[-1]

    def _extract_documented_factors(self, perf_row: Optional[pd.Series]) -> list:
        """Parse documented_factors from a performance record."""
        if perf_row is None:
            return []
        raw = perf_row.get("documented_factors", "")
        if not raw or (isinstance(raw, float) and np.isnan(raw)):
            return []
        try:
            parsed = json.loads(str(raw))
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                return list(parsed.items())
        except (json.JSONDecodeError, TypeError):
            # Treat as free-text if not valid JSON
            return [str(raw)] if raw else []
        return []

    # ------------------------------------------------------------------
    # get_band_for_employee
    # ------------------------------------------------------------------

    def get_band_for_employee(
        self, employee_id: str, evaluation_date: datetime.date
    ) -> dict:
        """Find the applicable (active) compensation band for an employee.

        Looks up the employee's current salary record → band_id, then checks
        band validity on *evaluation_date*.

        Parameters
        ----------
        employee_id:
            Target employee.
        evaluation_date:
            Date on which band validity is assessed.

        Returns
        -------
        dict
            Band record as a dict plus a ``"is_active"`` key.

        Raises
        ------
        ExpiredBandError
            When the found band has already expired.
        ValueError
            When the employee or band record cannot be found.
        """
        sal_rec = self._get_current_salary(employee_id)
        if sal_rec is None:
            raise ValueError(f"No salary record found for employee '{employee_id}'.")

        band_id = sal_rec.get("band_id")
        if not band_id or (isinstance(band_id, float) and np.isnan(band_id)):
            raise ValueError(
                f"Salary record for '{employee_id}' has no associated band_id."
            )

        if self.bands_df.empty:
            raise ValueError("Bands DataFrame is empty; cannot look up band.")

        band_rows = self.bands_df[self.bands_df["band_id"] == band_id]
        if band_rows.empty:
            raise ValueError(f"Band '{band_id}' not found in bands_df.")

        band = band_rows.iloc[0]
        effective = band.get("effective_date")
        expiry = band.get("expiry_date")

        # Normalise date types
        if isinstance(effective, str):
            effective = datetime.date.fromisoformat(effective)
        if isinstance(expiry, str) and expiry:
            expiry = datetime.date.fromisoformat(expiry)
        elif isinstance(expiry, float) and np.isnan(expiry):
            expiry = None

        try:
            is_active, reason = validate_band_active(effective, expiry, evaluation_date)
        except ExpiredBandError:
            raise ExpiredBandError(
                band_id=str(band_id),
                expiry_date=expiry,
                evaluation_date=evaluation_date,
            )

        result = band.to_dict()
        result["is_active"] = is_active
        result["validity_reason"] = reason
        return result

    # ------------------------------------------------------------------
    # analyze_employee
    # ------------------------------------------------------------------

    def analyze_employee(self, employee_id: str) -> dict:
        """Run a full compensation analysis for a single employee.

        Parameters
        ----------
        employee_id:
            Target employee identifier.

        Returns
        -------
        dict
            Keys:

            ``employee_id``, ``current_salary``, ``normalized_salary``,
            ``fte_salary``, ``applicable_band``, ``compa_ratio``,
            ``band_position``, ``band_status``, ``comparable_group_id``,
            ``peer_median``, ``peer_p25``, ``peer_p75``,
            ``disparity_vs_peers_pct``, ``documented_factors``, ``flags``.
        """
        if employee_id in self._analysis_cache:
            return self._analysis_cache[employee_id]

        result: dict = {
            "employee_id": employee_id,
            "current_salary": None,
            "normalized_salary": None,
            "fte_salary": None,
            "applicable_band": None,
            "compa_ratio": None,
            "compa_ratio_classification": None,
            "band_position": None,
            "band_status": None,
            "comparable_group_id": None,
            "peer_median": None,
            "peer_p25": None,
            "peer_p75": None,
            "disparity_vs_peers_pct": None,
            "documented_factors": [],
            "flags": [],
        }

        # -- Employee existence check -------------------------------------------
        if self.employees_df.empty:
            result["flags"].append("EMPLOYEE_DATA_MISSING")
            return result

        emp_rows = self.employees_df[self.employees_df["employee_id"] == employee_id]
        if emp_rows.empty:
            result["flags"].append("EMPLOYEE_NOT_FOUND")
            return result
        emp = emp_rows.iloc[0]

        # -- Salary record -------------------------------------------------------
        sal_rec = self._get_current_salary(employee_id)
        if sal_rec is None:
            result["flags"].append("NO_SALARY_RECORD")
            return result

        raw_salary = sal_rec.get("annual_salary")
        currency = sal_rec.get("currency_code", "INR")
        fte_fraction = float(emp.get("fte_fraction", 1.0) or 1.0)

        result["current_salary"] = raw_salary

        norm = normalize_salary(
            annual_salary=float(raw_salary) if raw_salary is not None else 0.0,
            currency_code=str(currency),
            fte_fraction=fte_fraction,
            fx_rates=FX_TO_INR,
        )
        result["normalized_salary"] = norm["normalized_inr"]
        result["fte_salary"] = norm["fte_adjusted_inr"]
        if norm["errors"]:
            result["flags"].extend(norm["errors"])

        fte_salary = norm["fte_adjusted_inr"] or 0.0

        # -- Band analysis -------------------------------------------------------
        try:
            band = self.get_band_for_employee(employee_id, self.evaluation_date)
            result["applicable_band"] = band.get("band_id")

            band_min = float(band.get("band_min", 0) or 0)
            band_mid = float(band.get("band_mid", 0) or 0)
            band_max = float(band.get("band_max", 0) or 0)

            # Convert band currency to INR if needed
            band_ccy = band.get("currency_code", "INR")
            if band_ccy != "INR":
                band_min = normalize_salary(band_min, band_ccy, 1.0)["normalized_inr"] or band_min
                band_mid = normalize_salary(band_mid, band_ccy, 1.0)["normalized_inr"] or band_mid
                band_max = normalize_salary(band_max, band_ccy, 1.0)["normalized_inr"] or band_max

            if band_mid > 0:
                compa = compute_compa_ratio(fte_salary, band_mid)
                result["compa_ratio"] = round(compa, 4)
                result["compa_ratio_classification"] = classify_compa_ratio(compa)

            if band_max > band_min:
                pos, status = compute_band_position(fte_salary, band_min, band_max)
                result["band_position"] = round(pos, 6)
                result["band_status"] = status

        except ExpiredBandError as exc:
            result["flags"].append(f"EXPIRED_BAND:{exc.band_id}")
        except ValueError as exc:
            result["flags"].append(f"BAND_ERROR:{exc}")

        # -- Comparable group & peer stats ----------------------------------------
        if not self._groups_df.empty:
            peer_info = find_comparable_peers(
                employee_id=employee_id,
                employees_df=self.employees_df,
                salary_df=self.salary_df,
                tenure_df=self.tenure_df,
                groups_df=self._groups_df,
            )
            if peer_info["is_valid"]:
                grp_id = peer_info["group_id"]
                result["comparable_group_id"] = grp_id

                grp_row = self._groups_df[self._groups_df["group_id"] == grp_id]
                if not grp_row.empty:
                    g = grp_row.iloc[0]
                    result["peer_median"] = g.get("median_salary")
                    result["peer_p25"] = g.get("p25_salary")
                    result["peer_p75"] = g.get("p75_salary")

                    peer_median = g.get("median_salary")
                    if peer_median and float(peer_median) > 0 and fte_salary:
                        disparity = (
                            (fte_salary - float(peer_median)) / float(peer_median)
                        ) * 100.0
                        result["disparity_vs_peers_pct"] = round(disparity, 4)
            else:
                result["flags"].append(f"NO_COMPARABLE_GROUP:{peer_info['invalidity_reason']}")

        # -- Performance / documented factors ------------------------------------
        perf = self._get_latest_perf(employee_id)
        result["documented_factors"] = self._extract_documented_factors(perf)

        self._analysis_cache[employee_id] = result
        return result

    # ------------------------------------------------------------------
    # analyze_all
    # ------------------------------------------------------------------

    def analyze_all(self) -> pd.DataFrame:
        """Run :meth:`analyze_employee` for every employee in the dataset.

        Returns
        -------
        pd.DataFrame
            One row per employee; columns match the keys returned by
            :meth:`analyze_employee`.  ``flags`` and ``documented_factors``
            are serialised to JSON strings for DataFrame compatibility.
        """
        if self.employees_df.empty:
            logger.warning("employees_df is empty; returning empty analysis DataFrame.")
            return pd.DataFrame()

        records = []
        for emp_id in self.employees_df["employee_id"]:
            try:
                record = self.analyze_employee(str(emp_id))
                # Serialise list fields for tabular representation
                record = record.copy()
                record["flags"] = json.dumps(record.get("flags", []))
                record["documented_factors"] = json.dumps(
                    record.get("documented_factors", [])
                )
                records.append(record)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Failed to analyze employee '%s': %s", emp_id, exc
                )
                records.append({"employee_id": emp_id, "flags": json.dumps([str(exc)])})

        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # compare_employees
    # ------------------------------------------------------------------

    def compare_employees(self, employee_ids: list[str]) -> pd.DataFrame:
        """Side-by-side compensation comparison for a list of employees.

        Intended for the HR dashboard comparison page.

        Parameters
        ----------
        employee_ids:
            List of employee IDs to compare.

        Returns
        -------
        pd.DataFrame
            One row per employee; all analysis fields as columns.
        """
        if not employee_ids:
            return pd.DataFrame()

        records = []
        for emp_id in employee_ids:
            try:
                record = self.analyze_employee(str(emp_id)).copy()
                record["flags"] = json.dumps(record.get("flags", []))
                record["documented_factors"] = json.dumps(
                    record.get("documented_factors", [])
                )
                records.append(record)
            except Exception as exc:  # noqa: BLE001
                logger.error("compare_employees: error for '%s': %s", emp_id, exc)
                records.append({"employee_id": emp_id, "flags": json.dumps([str(exc)])})

        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # get_executive_summary
    # ------------------------------------------------------------------

    def get_executive_summary(self) -> dict:
        """Compute KPI metrics for the executive dashboard.

        Triggers a full :meth:`analyze_all` run if not already cached.

        Returns
        -------
        dict
            Keys:

            ``total_employees``, ``avg_compa_ratio``, ``below_band_count``,
            ``within_band_count``, ``above_band_count``, ``disparity_count``,
            ``pending_proposals_count``, ``salary_distribution_data``,
            ``compa_ratio_distribution_data``.
        """
        analysis_df = self.analyze_all()

        total = len(self.employees_df)
        avg_compa = None
        below_count = 0
        within_count = 0
        above_count = 0
        disparity_count = 0

        salary_distribution: list[float] = []
        compa_distribution: list[float] = []

        if not analysis_df.empty:
            if "compa_ratio" in analysis_df.columns:
                valid_compa = analysis_df["compa_ratio"].dropna()
                avg_compa = float(valid_compa.mean()) if not valid_compa.empty else None
                compa_distribution = valid_compa.tolist()

            if "band_status" in analysis_df.columns:
                below_count = int((analysis_df["band_status"] == "BELOW_BAND").sum())
                within_count = int((analysis_df["band_status"] == "WITHIN_BAND").sum())
                above_count = int((analysis_df["band_status"] == "ABOVE_BAND").sum())

            if "disparity_vs_peers_pct" in analysis_df.columns:
                disparity_count = int(
                    (analysis_df["disparity_vs_peers_pct"].abs() > 20.0).sum()
                )

            if "fte_salary" in analysis_df.columns:
                salary_distribution = analysis_df["fte_salary"].dropna().tolist()

        # Pending proposals
        pending_count = 0
        if not self.bands_df.empty:
            # Proposals are not stored in this class directly; derive from context
            pass

        return {
            "total_employees": total,
            "avg_compa_ratio": round(avg_compa, 4) if avg_compa is not None else None,
            "below_band_count": below_count,
            "within_band_count": within_count,
            "above_band_count": above_count,
            "disparity_count": disparity_count,
            "pending_proposals_count": pending_count,
            "salary_distribution_data": salary_distribution,
            "compa_ratio_distribution_data": compa_distribution,
        }
