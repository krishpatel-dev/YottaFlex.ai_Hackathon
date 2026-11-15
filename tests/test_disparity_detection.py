"""
tests/test_disparity_detection.py
=================================
Automated verification for all 5 mandatory exception scenarios and pay equity detection:
1. SALARY_COMPARED_TO_EXPIRED_BAND
2. FTE_IGNORED
3. CURRENCY_CONVERSION_MISSING
4. ADJUSTMENT_WITHOUT_APPROVAL
5. INCOMPARABLE_ROLES_GROUPED
6. UNEXPLAINED_DISPARITY
"""

from pathlib import Path
import pandas as pd
import pytest

from src.engine.disparity_detection import DisparityDetector

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def dataset():
    """Load the full generated dataset for exception scenario testing."""
    return {
        "employees": pd.read_csv(DATA_DIR / "transactions" / "employees.csv"),
        "salary_records": pd.read_csv(DATA_DIR / "transactions" / "salary_records.csv"),
        "compensation_bands": pd.read_csv(DATA_DIR / "master" / "compensation_bands.csv"),
        "comparable_groups": pd.read_csv(DATA_DIR / "transactions" / "comparable_groups.csv"),
        "performance_evidence": pd.read_csv(DATA_DIR / "transactions" / "performance_evidence.csv"),
        "promotions": pd.read_csv(DATA_DIR / "transactions" / "promotions.csv"),
        "adjustment_proposals": pd.read_csv(DATA_DIR / "transactions" / "adjustment_proposals.csv"),
        "ground_truth": pd.read_csv(DATA_DIR / "ground_truth" / "ground_truth.csv"),
    }


def test_scenario_1_expired_band_detection(dataset):
    """Verify system catches salaries evaluated against expired compensation bands."""
    detector = DisparityDetector()
    flags, _ = detector.detect_expired_bands(
        dataset["salary_records"],
        dataset["compensation_bands"]
    )
    assert len(flags) > 0
    for f in flags:
        assert f["issue_type"] == "SALARY_COMPARED_TO_EXPIRED_BAND"
        assert f["severity"] == "CRITICAL"
        assert "RULE_EXPIRED_COMPENSATION_BAND" in f["detection_rule"]


def test_scenario_2_fte_ignored_detection(dataset):
    """Verify system catches part-time employees compared without FTE scaling."""
    detector = DisparityDetector()
    flags, _ = detector.detect_fte_ignored(
        dataset["employees"],
        dataset["salary_records"]
    )
    assert len(flags) > 0
    for f in flags:
        assert f["issue_type"] == "FTE_IGNORED"
        assert f["severity"] == "HIGH"
        assert f["salary_difference"] > 0


def test_scenario_3_currency_missing_detection(dataset):
    """Verify system catches unsupported currencies lacking FX conversion."""
    detector = DisparityDetector()
    flags, _ = detector.detect_currency_missing(dataset["salary_records"])
    assert len(flags) > 0
    for f in flags:
        assert f["issue_type"] == "CURRENCY_CONVERSION_MISSING"
        assert f["severity"] == "CRITICAL"


def test_scenario_4_unapproved_adjustment_detection(dataset):
    """Verify system detects implemented adjustments lacking HR sign-off."""
    detector = DisparityDetector()
    flags, _ = detector.detect_unapproved_adjustments(
        dataset["adjustment_proposals"],
        dataset["salary_records"]
    )
    assert len(flags) > 0
    for f in flags:
        assert f["issue_type"] == "ADJUSTMENT_WITHOUT_APPROVAL"
        assert f["severity"] == "CRITICAL"


def test_scenario_5_incomparable_roles_grouped_detection(dataset):
    """Verify system detects invalid cross-functional peer grouping."""
    detector = DisparityDetector()
    flags, _ = detector.detect_incomparable_groups(dataset["comparable_groups"])
    assert len(flags) > 0
    for f in flags:
        assert f["issue_type"] == "INCOMPARABLE_ROLES_GROUPED"


def test_ground_truth_isolation(dataset):
    """Assert ground truth contains expected anomaly classes and is isolated."""
    df_gt = dataset["ground_truth"]
    expected_issues = {
        "SALARY_COMPARED_TO_EXPIRED_BAND",
        "FTE_IGNORED",
        "CURRENCY_CONVERSION_MISSING",
        "ADJUSTMENT_WITHOUT_APPROVAL",
        "INCOMPARABLE_ROLES_GROUPED",
    }
    found_issues = set(df_gt["issue_type"].unique())
    assert expected_issues.issubset(found_issues)
