"""
tests/test_compensation_engine.py
=================================
Unit tests for the CompensationAnalyzer orchestrator and peer analysis engine.
"""

from pathlib import Path
import pandas as pd
import pytest

from src.engine.compensation import CompensationAnalyzer

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def analyzer():
    df_emp = pd.read_csv(DATA_DIR / "transactions" / "employees.csv")
    df_sal = pd.read_csv(DATA_DIR / "transactions" / "salary_records.csv")
    df_bands = pd.read_csv(DATA_DIR / "master" / "compensation_bands.csv")
    df_tenure = pd.read_csv(DATA_DIR / "transactions" / "tenure.csv")
    df_perf = pd.read_csv(DATA_DIR / "transactions" / "performance_evidence.csv")
    df_roles = pd.read_csv(DATA_DIR / "master" / "roles.csv")
    df_levels = pd.read_csv(DATA_DIR / "master" / "levels.csv")
    df_locs = pd.read_csv(DATA_DIR / "master" / "locations.csv")
    df_groups = pd.read_csv(DATA_DIR / "transactions" / "comparable_groups.csv")

    return CompensationAnalyzer(
        employees_df=df_emp,
        salary_df=df_sal,
        bands_df=df_bands,
        tenure_df=df_tenure,
        perf_df=df_perf,
        roles_df=df_roles,
        levels_df=df_levels,
        locations_df=df_locs,
    )


def test_analyze_single_employee(analyzer):
    """Test detailed compensation breakdown for an active employee."""
    res = analyzer.analyze_employee("EMP-000001")
    assert res is not None
    assert res["employee_id"] == "EMP-000001"
    assert "compa_ratio" in res
    assert "band_position" in res
    assert "fte_salary" in res
    assert res["fte_salary"] > 0


def test_compare_multiple_employees(analyzer):
    """Test side-by-side comparison for multiple peers."""
    comp_df = analyzer.compare_employees(["EMP-000001", "EMP-000002"])
    assert len(comp_df) == 2
    assert "compa_ratio" in comp_df.columns
    assert "fte_salary" in comp_df.columns


def test_executive_summary_kpis(analyzer):
    """Test high-level executive KPI generation."""
    kpis = analyzer.get_executive_summary()
    assert kpis["total_employees"] > 0
    assert 50.0 < kpis["avg_compa_ratio"] < 150.0
    assert "below_band_count" in kpis
    assert "within_band_count" in kpis
    assert "above_band_count" in kpis


def test_analyze_all_subset():
    """Test batch analysis on a targeted employee subset."""
    df_emp = pd.read_csv(DATA_DIR / "transactions" / "employees.csv").head(10)
    df_sal = pd.read_csv(DATA_DIR / "transactions" / "salary_records.csv")
    df_bands = pd.read_csv(DATA_DIR / "master" / "compensation_bands.csv")
    df_tenure = pd.read_csv(DATA_DIR / "transactions" / "tenure.csv")
    df_perf = pd.read_csv(DATA_DIR / "transactions" / "performance_evidence.csv")
    df_roles = pd.read_csv(DATA_DIR / "master" / "roles.csv")
    df_levels = pd.read_csv(DATA_DIR / "master" / "levels.csv")
    df_locs = pd.read_csv(DATA_DIR / "master" / "locations.csv")

    sub_analyzer = CompensationAnalyzer(
        employees_df=df_emp,
        salary_df=df_sal,
        bands_df=df_bands,
        tenure_df=df_tenure,
        perf_df=df_perf,
        roles_df=df_roles,
        levels_df=df_levels,
        locations_df=df_locs,
    )

    batch_df = sub_analyzer.analyze_all()
    assert isinstance(batch_df, pd.DataFrame)
    assert len(batch_df) == 10
    assert "employee_id" in batch_df.columns
    assert "compa_ratio" in batch_df.columns
    assert "band_position" in batch_df.columns

