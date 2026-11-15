"""
src/services/reporting.py
=========================
Executive reporting, analytical aggregations, and governance compliance summaries.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


class CompensationReportingService:
    """Provides high-level reporting and analytics extraction for executive briefings."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.master_dir = self.data_dir / "master"
        self.trans_dir = self.data_dir / "transactions"

    def generate_executive_briefing(self) -> Dict:
        """Produce macro-level metrics for HR and executive leadership."""
        df_emp = pd.read_csv(self.trans_dir / "employees.csv")
        df_sal = pd.read_csv(self.trans_dir / "salary_records.csv")
        df_flags = pd.read_csv(self.trans_dir / "disparity_flags.csv")
        df_props = pd.read_csv(self.trans_dir / "adjustment_proposals.csv")

        latest_sal = (
            df_sal.sort_values("effective_date", ascending=False)
            .groupby("employee_id")
            .first()
            .reset_index()
        )

        total_emp = len(df_emp)
        avg_cr = float(latest_sal["compa_ratio"].mean()) if "compa_ratio" in latest_sal else 100.0
        below_band = int(len(latest_sal[latest_sal["compa_ratio"] < 80]))
        above_band = int(len(latest_sal[latest_sal["compa_ratio"] > 120]))
        within_band = total_emp - below_band - above_band

        flags_by_type = df_flags["issue_type"].value_counts().to_dict()
        flags_by_sev = df_flags["severity"].value_counts().to_dict()

        return {
            "timestamp": datetime.now().isoformat(),
            "total_headcount": total_emp,
            "average_compa_ratio": round(avg_cr, 2),
            "distribution": {
                "below_band": below_band,
                "within_band": within_band,
                "above_band": above_band,
            },
            "disparity_exceptions": {
                "total_flags": len(df_flags),
                "by_issue_type": flags_by_type,
                "by_severity": flags_by_sev,
            },
            "proposals": {
                "total_proposals": len(df_props),
                "implemented": int(len(df_props[df_props["final_status"] == "IMPLEMENTED"])),
                "pending_approval": int(len(df_props[df_props["final_status"] != "IMPLEMENTED"])),
            },
        }

    def export_summary_json(self, output_path: Path) -> Path:
        brief = self.generate_executive_briefing()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(brief, f, indent=2)
        return output_path
