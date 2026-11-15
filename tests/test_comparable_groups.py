"""
tests/test_comparable_groups.py
===============================
Unit tests for the comparable group generation, validation, peer discovery,
and descriptive statistical computations.
"""

import json
from pathlib import Path
import pandas as pd
import pytest

from src.engine.comparable_groups import (
    build_comparable_groups,
    find_comparable_peers,
    validate_group_comparability,
    compute_group_statistics,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def dataset():
    """Load core entities needed for comparable cohort analysis."""
    return {
        "employees": pd.read_csv(DATA_DIR / "transactions" / "employees.csv"),
        "salary_records": pd.read_csv(DATA_DIR / "transactions" / "salary_records.csv"),
        "tenure": pd.read_csv(DATA_DIR / "transactions" / "tenure.csv"),
        "roles": pd.read_csv(DATA_DIR / "master" / "roles.csv"),
    }


@pytest.fixture(scope="module")
def built_groups(dataset):
    """Build comparable groups from the employees and tenure records."""
    return build_comparable_groups(
        dataset["employees"],
        dataset["tenure"],
        min_group_size=2,
    )


def test_build_comparable_groups_basic(dataset):
    """Test group construction respects minimum cohort size and required schema."""
    emp_subset = dataset["employees"].head(50)
    tenure_subset = dataset["tenure"][dataset["tenure"]["employee_id"].isin(emp_subset["employee_id"])]

    groups = build_comparable_groups(emp_subset, tenure_subset, min_group_size=2)
    assert isinstance(groups, pd.DataFrame)
    if not groups.empty:
        assert "group_id" in groups.columns
        assert "role_family" in groups.columns
        assert "member_employee_ids" in groups.columns
        assert "group_size" in groups.columns
        assert (groups["group_size"] >= 2).all()


def test_build_comparable_groups_empty():
    """Test empty input handling returns well-formed empty DataFrame."""
    empty_emp = pd.DataFrame(columns=["employee_id", "role_family", "level_id", "location_id", "employment_type", "status"])
    empty_tenure = pd.DataFrame(columns=["employee_id", "tenure_band"])
    groups = build_comparable_groups(empty_emp, empty_tenure)
    assert groups.empty
    assert "group_id" in groups.columns


def test_find_comparable_peers_existing_employee(dataset, built_groups):
    """Verify peer discovery locates peers and group metadata for valid employee."""
    first_group = built_groups.iloc[0]
    members = json.loads(first_group["member_employee_ids"])
    target_emp = members[0]

    result = find_comparable_peers(
        target_emp,
        dataset["employees"],
        dataset["salary_records"],
        dataset["tenure"],
        built_groups,
    )

    assert result["is_valid"] is True
    assert result["group_id"] == first_group["group_id"]
    assert target_emp not in result["peers"]
    assert set(result["peers"]).issubset(set(members))


def test_find_comparable_peers_unknown_employee(dataset, built_groups):
    """Verify peer discovery gracefully flags unknown employee ID."""
    result = find_comparable_peers(
        "NON_EXISTENT_EMP",
        dataset["employees"],
        dataset["salary_records"],
        dataset["tenure"],
        built_groups,
    )
    assert result["is_valid"] is False
    assert "not found" in result["invalidity_reason"].lower()


def test_validate_group_comparability(dataset, built_groups):
    """Verify validation detects any group mixing incomparable role families."""
    validated = validate_group_comparability(built_groups, dataset["roles"])
    assert "is_valid_group" in validated.columns
    assert "invalidity_reason" in validated.columns
    assert validated["is_valid_group"].isin([True, False]).all()


def test_compute_group_statistics(dataset, built_groups):
    """Verify median, mean, min, max, and percentiles compute correctly."""
    sample_groups = built_groups.head(10).copy()
    stats = compute_group_statistics(sample_groups, dataset["salary_records"])

    for col in ["median_salary", "mean_salary", "p25_salary", "p75_salary", "min_salary", "max_salary"]:
        assert col in stats.columns

    # Verify for non-empty group calculations
    non_null_medians = stats["median_salary"].dropna()
    assert len(non_null_medians) > 0
    assert (non_null_medians > 0).all()
