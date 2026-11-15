"""
tests/test_reporting.py
=======================
Unit tests for the CompensationReportingService and executive artifact generation.
"""

import json
from pathlib import Path
import pytest

from src.services.reporting import CompensationReportingService

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def reporting_service():
    return CompensationReportingService(data_dir=DATA_DIR)


def test_generate_executive_briefing(reporting_service):
    """Test macro-level executive summary dictionary output structure."""
    brief = reporting_service.generate_executive_briefing()
    assert isinstance(brief, dict)
    assert "timestamp" in brief
    assert "total_headcount" in brief
    assert brief["total_headcount"] > 0
    assert "average_compa_ratio" in brief
    assert "distribution" in brief
    assert "below_band" in brief["distribution"]
    assert "within_band" in brief["distribution"]
    assert "above_band" in brief["distribution"]
    assert "disparity_exceptions" in brief
    assert "proposals" in brief


def test_export_summary_json(reporting_service, tmp_path):
    """Test exporting the executive briefing to a JSON file."""
    output_file = tmp_path / "executive_briefing.json"
    exported_path = reporting_service.export_summary_json(output_file)

    assert exported_path.exists()
    with open(exported_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "total_headcount" in data
    assert data["total_headcount"] > 0
    assert "distribution" in data
