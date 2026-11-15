"""
src/validation/reproducibility.py
=================================
Automated verification of deterministic seed reproducibility:
- Executes generation twice with identical seed
- Compares row counts and MD5 file hashes
- Produces reproducibility verification report
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path
from typing import Dict, Tuple

# Project root resolution
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.generator.generate import compute_md5, run_pipeline


def verify_generator_reproducibility(
    seed: int = 20261022,
    scale: str = "starter",
    temp_dir: Path = None,
) -> Tuple[bool, Dict[str, Dict]]:
    """
    Execute generation twice with identical seed and verify 100% bit-for-bit checksum equality.
    """
    if temp_dir is None:
        temp_dir = _PROJECT_ROOT / "tests" / "temp_reproducibility"

    temp_dir.mkdir(parents=True, exist_ok=True)
    run1_dir = temp_dir / "run_1"
    run2_dir = temp_dir / "run_2"

    try:
        print(f"\n🔬 Initiating 2x Reproducibility Test (Seed: {seed}, Scale: {scale})...")
        run_pipeline(seed=seed, scale=scale, output_dir=run1_dir)
        run_pipeline(seed=seed, scale=scale, output_dir=run2_dir)

        files_to_compare = [
            "master/roles.csv",
            "master/levels.csv",
            "master/locations.csv",
            "master/compensation_bands.csv",
            "transactions/employees.csv",
            "transactions/salary_records.csv",
            "transactions/performance_evidence.csv",
            "transactions/tenure.csv",
            "transactions/promotions.csv",
            "transactions/comparable_groups.csv",
            "transactions/adjustment_proposals.csv",
            "transactions/disparity_flags.csv",
        ]

        results = {}
        all_passed = True

        print("\n📊 Checksum Comparison Table (MD5):")
        print("--------------------------------------------------------------------------------")
        for rel_str in files_to_compare:
            f1 = run1_dir / rel_str
            f2 = run2_dir / rel_str

            if not f1.exists() or not f2.exists():
                results[rel_str] = {"status": "MISSING_FILE", "match": False}
                all_passed = False
                continue

            h1 = compute_md5(f1)
            h2 = compute_md5(f2)
            match = (h1 == h2)
            if not match:
                all_passed = False

            results[rel_str] = {
                "hash_run_1": h1,
                "hash_run_2": h2,
                "match": match,
                "status": "IDENTICAL" if match else "MISMATCH",
            }

            status_label = "MATCH ✅" if match else "MISMATCH ❌"
            print(f"   {rel_str:35s} | {h1[:10]}... == {h2[:10]}... | {status_label}")

        print("--------------------------------------------------------------------------------\n")
        return all_passed, results

    finally:
        # Clean up temporary test directories
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    passed, _ = verify_generator_reproducibility()
    sys.exit(0 if passed else 1)
