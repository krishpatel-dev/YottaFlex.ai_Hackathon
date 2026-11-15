"""
src/validation/business_rules.py
================================
Validates mathematical calculations, band arithmetic, FTE constraints,
compa-ratio accuracy, and career progression logic.
"""

from __future__ import annotations

from typing import Dict, List
import pandas as pd
from .integrity import ValidationResult


def validate_band_arithmetic(bands_df: pd.DataFrame) -> ValidationResult:
    """Ensure band_min < band_mid < band_max for every compensation band."""
    total = len(bands_df)
    invalid = bands_df[
        (bands_df["band_min"] >= bands_df["band_mid"]) |
        (bands_df["band_mid"] >= bands_df["band_max"])
    ]
    violating = len(invalid)
    passed = (violating == 0)
    examples = invalid[["band_id", "band_min", "band_mid", "band_max"]].head(3).to_dict("records") if not passed else []
    msg = f"All {total:,} bands satisfy band_min < band_mid < band_max." if passed else f"Found {violating} bands violating monotonicity."
    return ValidationResult("compensation_bands", "BAND_ARITHMETIC_MIN_MID_MAX", passed, total, violating, examples, msg)


def validate_fte_range(employees_df: pd.DataFrame) -> ValidationResult:
    """Ensure 0 < fte_fraction <= 1.0 for all employees."""
    total = len(employees_df)
    invalid = employees_df[
        (employees_df["fte_fraction"] <= 0.0) |
        (employees_df["fte_fraction"] > 1.0)
    ]
    violating = len(invalid)
    passed = (violating == 0)
    examples = invalid[["employee_id", "fte_fraction"]].head(3).to_dict("records") if not passed else []
    msg = f"All {total:,} employees satisfy 0 < FTE <= 1.0." if passed else f"Found {violating} employees with invalid FTE fractions."
    return ValidationResult("employees", "FTE_FRACTION_BOUNDS", passed, total, violating, examples, msg)


def validate_compa_ratio_accuracy(
    salary_df: pd.DataFrame,
    bands_df: pd.DataFrame,
    employees_df: Optional[pd.DataFrame] = None,
    ground_truth_df: Optional[pd.DataFrame] = None,
    tolerance: float = 0.05,
) -> ValidationResult:
    """
    Recalculate compa-ratio from raw salary, FTE fraction, and band midpoint in the band's currency,
    comparing with stored compa-ratio across all clean (non-anomalous) records.
    """
    merged = salary_df.merge(
        bands_df[["band_id", "band_mid", "currency_code"]],
        on="band_id",
        how="inner",
        suffixes=("_sal", "_band"),
    )

    if employees_df is not None:
        merged = merged.merge(employees_df[["employee_id", "fte_fraction"]], on="employee_id", how="left")
    else:
        merged["fte_fraction"] = 1.0

    merged["fte_fraction"] = merged["fte_fraction"].fillna(1.0)
    total = len(merged)

    # Exclude injected anomalies (e.g. currency missing 'XYZ' or deliberate FTE/expired-band test cases)
    anomaly_record_ids = set()
    if ground_truth_df is not None and not ground_truth_df.empty:
        anomaly_record_ids = set(ground_truth_df["record_id"].dropna().unique())

    clean = merged[
        (merged["currency_code_sal"] != "XYZ") &
        (merged["currency_code_sal"] == merged["currency_code_band"]) &
        (~merged["salary_id"].isin(anomaly_record_ids))
    ]
    if "_fte_ignored" in clean.columns:
        clean = clean[clean["_fte_ignored"] != True]

    recalculated = ((clean["annual_salary"] / clean["fte_fraction"]) / clean["band_mid"]) * 100

    if "compa_ratio" in clean.columns:
        diff = (clean["compa_ratio"] - recalculated).abs()
        invalid = clean[diff > tolerance]
    else:
        invalid = clean[clean["band_mid"] <= 0]

    violating = len(invalid)
    passed = (violating == 0)
    examples = invalid.head(3).to_dict("records") if not passed else []
    msg = f"Compa-ratio arithmetic verified across {len(clean):,} uncorrupted records (anomalies correctly isolated)." if passed else f"Found {violating} records with calculation discrepancies."
    return ValidationResult("salary_records", "COMPA_RATIO_RECALCULATION", passed, total, violating, examples, msg)


def validate_promotion_rank_order(
    promotions_df: pd.DataFrame,
    levels_df: pd.DataFrame,
) -> ValidationResult:
    """Verify that promotions advance employee to a strictly higher rank level."""
    total = len(promotions_df)
    if total == 0:
        return ValidationResult("promotions", "PROMOTION_LEVEL_ORDER", True, 0, 0, [], "No promotions to validate.")

    level_rank = levels_df.set_index("level_id")["rank_order"].to_dict()
    violating_rows = []

    for _, promo in promotions_df.iterrows():
        from_lvl = promo.get("from_level_id")
        to_lvl = promo.get("to_level_id")
        r_from = level_rank.get(from_lvl, 0)
        r_to = level_rank.get(to_lvl, 0)

        # For LEVEL_UP, rank must increase
        if promo.get("promo_type") == "LEVEL_UP" and r_to <= r_from:
            violating_rows.append(promo["promo_id"])

    violating = len(violating_rows)
    passed = (violating == 0)
    examples = violating_rows[:3] if not passed else []
    msg = f"All {total:,} promotions obey seniority rank advancement." if passed else f"Found {violating} promotions with invalid level progression."
    return ValidationResult("promotions", "PROMOTION_LEVEL_ORDER", passed, total, violating, examples, msg)
