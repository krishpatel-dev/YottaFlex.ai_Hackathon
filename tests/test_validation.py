"""
tests/test_validation.py
========================
Automated validation of database relational integrity, arithmetic consistency,
and deterministic seed reproducibility.
"""

from pathlib import Path
import pandas as pd
import pytest

from src.validation.integrity import DataIntegrityValidator
from src.validation.business_rules import (
    validate_band_arithmetic,
    validate_fte_range,
    validate_compa_ratio_accuracy,
    validate_promotion_rank_order,
)
from src.validation.reproducibility import verify_generator_reproducibility

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_full_data_integrity_suite():
    """Verify all 30 relational, PK, FK, and enum integrity checks pass."""
    validator = DataIntegrityValidator(DATA_DIR)
    report = validator.run_all()
    assert report.all_passed is True
    assert report.failed_checks == 0
    assert report.passed_checks == 30


def test_band_monotonic_arithmetic():
    """Verify band_min < band_mid < band_max for every single band."""
    df_bands = pd.read_csv(DATA_DIR / "master" / "compensation_bands.csv")
    result = validate_band_arithmetic(df_bands)
    assert result.passed is True
    assert result.violating_records == 0


def test_fte_bounds():
    """Verify 0 < FTE <= 1.0 for all employees."""
    df_emp = pd.read_csv(DATA_DIR / "transactions" / "employees.csv")
    result = validate_fte_range(df_emp)
    assert result.passed is True
    assert result.violating_records == 0


def test_promotion_seniority_advancement():
    """Verify that promotions advance employee seniority strictly forward."""
    df_promo = pd.read_csv(DATA_DIR / "transactions" / "promotions.csv")
    df_levels = pd.read_csv(DATA_DIR / "master" / "levels.csv")
    result = validate_promotion_rank_order(df_promo, df_levels)
    assert result.passed is True
    assert result.violating_records == 0


def test_compa_ratio_arithmetic_on_clean_data():
    """Verify compa-ratio formula equality across all clean rows."""
    df_sal = pd.read_csv(DATA_DIR / "transactions" / "salary_records.csv")
    df_bands = pd.read_csv(DATA_DIR / "master" / "compensation_bands.csv")
    df_emp = pd.read_csv(DATA_DIR / "transactions" / "employees.csv")
    df_gt = pd.read_csv(DATA_DIR / "ground_truth" / "ground_truth.csv")

    result = validate_compa_ratio_accuracy(df_sal, df_bands, df_emp, df_gt)
    assert result.passed is True
    assert result.violating_records == 0


def test_deterministic_reproducibility_checksums():
    """Verify repeated execution with same seed produces identical file checksums."""
    passed, _ = verify_generator_reproducibility(seed=20261022, scale="starter")
    assert passed is True
