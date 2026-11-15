"""
tests/test_normalization.py
===========================
Unit tests for salary normalization, currency conversion, FTE adjustment,
compa-ratio, and band position calculations.
"""

import pytest
from datetime import date
from src.engine.salary_normalization import (
    normalize_currency,
    normalize_fte,
    normalize_salary,
    compute_compa_ratio,
    compute_band_position,
    classify_compa_ratio,
    CurrencyMissingError,
    FTEError,
    validate_band_active,
    ExpiredBandError,
)


def test_currency_normalization_supported():
    # 1000 USD to INR @ 83.5 = 83,500 INR
    assert normalize_currency(1000.0, "USD", "INR") == 83500.0
    # INR to INR = unchanged
    assert normalize_currency(500000.0, "INR", "INR") == 500000.0


def test_currency_normalization_unsupported():
    with pytest.raises(CurrencyMissingError):
        normalize_currency(1000.0, "XYZ", "INR", raise_on_missing=True)


def test_fte_normalization_part_time():
    # 5 LPA at 0.5 FTE = 10 LPA FTE equivalent
    assert normalize_fte(500000.0, 0.5) == 1000000.0
    # Full time (1.0) = unchanged
    assert normalize_fte(1200000.0, 1.0) == 1200000.0


def test_fte_normalization_invalid():
    with pytest.raises(FTEError):
        normalize_fte(500000.0, 0.0)
    with pytest.raises(FTEError):
        normalize_fte(500000.0, 1.5)


def test_compa_ratio_calculation():
    # 8 LPA salary against 10 LPA midpoint = 80.0%
    cr = compute_compa_ratio(800000.0, 1000000.0)
    assert cr == 80.0
    assert classify_compa_ratio(cr) == "BELOW"

    # 10 LPA salary against 10 LPA midpoint = 100.0%
    cr_target = compute_compa_ratio(1000000.0, 1000000.0)
    assert cr_target == 100.0
    assert classify_compa_ratio(cr_target) == "TARGET"


def test_band_position_calculation():
    # Band: 7 LPA to 13 LPA (midpoint 10 LPA)
    # Salary 10 LPA -> 50% penetration (0.50)
    pos, status = compute_band_position(1000000.0, 700000.0, 1300000.0)
    assert pos == 0.5
    assert status == "WITHIN_BAND"

    # Salary 6 LPA -> below band
    pos_low, status_low = compute_band_position(600000.0, 700000.0, 1300000.0)
    assert pos_low < 0.0
    assert status_low == "BELOW_BAND"

    # Salary 14 LPA -> above band
    pos_high, status_high = compute_band_position(1400000.0, 700000.0, 1300000.0)
    assert pos_high > 1.0
    assert status_high == "ABOVE_BAND"


def test_validate_band_active():
    eff = date(2025, 1, 1)
    exp = date(2025, 12, 31)

    # Valid evaluation date
    is_valid, msg = validate_band_active(eff, exp, date(2025, 6, 1))
    assert is_valid is True

    # Expired evaluation date
    with pytest.raises(ExpiredBandError):
        validate_band_active(eff, exp, date(2026, 6, 1))
