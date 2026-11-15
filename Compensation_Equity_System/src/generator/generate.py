"""
src/generator/generate.py
=========================
Command-line orchestrator for synthetic employee compensation data generation.

Usage:
    python src/generator/generate.py --seed 20261022 --scale full
    python src/generator/generate.py --seed 20261022 --scale starter
    python src/generator/generate.py --seed 20261022 --scale starter --reproducibility-check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from faker import Faker

# Handle path resolutions
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

try:
    from .config import SEED, SCALE_CONFIGS
    from .master_data import (
        generate_roles,
        generate_levels,
        generate_locations,
        generate_compensation_bands,
    )
    from .salary_history import (
        generate_employees,
        generate_salary_records,
        generate_performance_evidence,
        generate_tenure,
        generate_promotions,
        generate_comparable_groups,
        generate_adjustment_proposals,
        generate_disparity_flags,
    )
    from .synthetic_anomalies import (
        inject_expired_bands,
        inject_fte_ignored,
        inject_currency_missing,
        inject_unapproved_adjustments,
        inject_incomparable_groups,
        export_ground_truth,
    )
except ImportError:
    from config import SEED, SCALE_CONFIGS
    from master_data import (
        generate_roles,
        generate_levels,
        generate_locations,
        generate_compensation_bands,
    )
    from salary_history import (
        generate_employees,
        generate_salary_records,
        generate_performance_evidence,
        generate_tenure,
        generate_promotions,
        generate_comparable_groups,
        generate_adjustment_proposals,
        generate_disparity_flags,
    )
    from synthetic_anomalies import (
        inject_expired_bands,
        inject_fte_ignored,
        inject_currency_missing,
        inject_unapproved_adjustments,
        inject_incomparable_groups,
        export_ground_truth,
    )


def compute_md5(file_path: Path) -> str:
    """Compute MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_pipeline(
    seed: int,
    scale: str,
    output_dir: Path,
) -> Dict[str, pd.DataFrame]:
    """
    Execute the full generation and anomaly injection pipeline.
    Returns dictionary of generated DataFrames.
    """
    scale_cfg = SCALE_CONFIGS.get(scale, SCALE_CONFIGS["full"])
    n_employees = scale_cfg["num_employees"]

    print(f"\n=======================================================")
    print(f"🚀 GENERATING SYNTHETIC DATASET")
    print(f"   Seed:        {seed}")
    print(f"   Scale:       {scale} ({n_employees:,} employees)")
    print(f"   Output dir:  {output_dir}")
    print(f"=======================================================\n")

    # Seed all RNGs deterministically
    random.seed(seed)
    np.random.seed(seed)
    rng = np.random.RandomState(seed)

    faker_in = Faker("en_IN")
    faker_in.seed_instance(seed)

    faker_en = Faker("en_US")
    faker_en.seed_instance(seed)

    master_dir = output_dir / "master"
    trans_dir = output_dir / "transactions"
    master_dir.mkdir(parents=True, exist_ok=True)
    trans_dir.mkdir(parents=True, exist_ok=True)

    # 1. Master Data
    print("⏳ [1/10] Generating master data (Roles, Levels, Locations)...")
    df_roles = generate_roles()
    df_levels = generate_levels()
    df_locations = generate_locations()

    print("⏳ [2/10] Generating effective-dated Compensation Bands...")
    df_bands = generate_compensation_bands(df_roles, df_levels, df_locations, rng)

    # 2. Employees
    print(f"⏳ [3/10] Generating {n_employees:,} Employees with demographic distributions...")
    df_emp = generate_employees(n_employees, df_roles, df_levels, df_locations, rng, faker_in, faker_en)

    # 3. Base Salary Records
    print("⏳ [4/10] Generating 3-year point-in-time Salary Records with currency & FTE...")
    df_salary = generate_salary_records(df_emp, df_bands, rng)

    # 4. Career Progression Promotions (returns updated df_salary with PROMOTION records)
    print("⏳ [5/10] Simulating career progression Promotions...")
    df_promotions, df_salary = generate_promotions(df_emp, df_salary, df_bands, df_levels, rng, n_employees)

    # 5. Tenure (takes df_emp and df_promotions)
    print("⏳ [6/10] Calculating continuous service Tenure records...")
    df_tenure = generate_tenure(df_emp, df_promotions)

    # 6. Performance Evidence
    print("⏳ [7/10] Generating semi-annual Performance Evidence ratings & factors...")
    df_perf = generate_performance_evidence(df_emp, rng)

    # 7. Comparable Peer Groups (takes df_emp, df_salary, df_tenure)
    print("⏳ [8/10] Building Comparable Peer Groups...")
    df_groups = generate_comparable_groups(df_emp, df_salary, df_tenure)

    # 8. Adjustment Proposals
    print("⏳ [9/10] Generating Adjustment Proposals for under-band salaries...")
    df_proposals = generate_adjustment_proposals(df_emp, df_salary, df_bands, df_perf, df_groups, rng)

    # 9. Disparity Flags
    print("⏳ [10/10] Scanning and creating baseline Disparity Flags...")
    df_flags = generate_disparity_flags(df_emp, df_salary, df_groups, df_perf, rng)

    # 6. Inject 5 Negative Exception Scenarios (Ground Truth)
    print("\n⚠️ Injecting 5 mandatory negative exception scenarios & building Ground Truth...")
    gt_records = []

    # Scenario 1: Expired Band
    df_salary, gt_expired = inject_expired_bands(df_salary, df_bands, rng=rng)
    gt_records.extend(gt_expired)

    # Scenario 2: FTE Ignored
    df_salary, gt_fte = inject_fte_ignored(df_salary, df_emp, rng=rng)
    gt_records.extend(gt_fte)

    # Scenario 3: Currency Missing
    df_salary, gt_curr = inject_currency_missing(df_salary, rng=rng)
    gt_records.extend(gt_curr)

    # Scenario 4: Unapproved Adjustment
    df_proposals, df_salary, gt_adj = inject_unapproved_adjustments(df_proposals, df_salary, rng=rng)
    gt_records.extend(gt_adj)

    # Scenario 5: Incomparable Roles Grouped
    df_groups, gt_grp = inject_incomparable_groups(df_groups, df_roles, rng=rng)
    gt_records.extend(gt_grp)

    # Export Ground Truth separately
    gt_csv_path = export_ground_truth(gt_records, output_dir)
    print(f"   ✓ Exported {len(gt_records)} ground-truth anomaly labels to {gt_csv_path}")

    # Export Master Data
    df_roles.to_csv(master_dir / "roles.csv", index=False)
    df_levels.to_csv(master_dir / "levels.csv", index=False)
    df_locations.to_csv(master_dir / "locations.csv", index=False)
    df_bands.to_csv(master_dir / "compensation_bands.csv", index=False)

    # Export Transactions
    df_emp.to_csv(trans_dir / "employees.csv", index=False)
    df_salary.to_csv(trans_dir / "salary_records.csv", index=False)
    df_perf.to_csv(trans_dir / "performance_evidence.csv", index=False)
    df_tenure.to_csv(trans_dir / "tenure.csv", index=False)
    df_promotions.to_csv(trans_dir / "promotions.csv", index=False)
    df_groups.to_csv(trans_dir / "comparable_groups.csv", index=False)
    df_proposals.to_csv(trans_dir / "adjustment_proposals.csv", index=False)
    df_flags.to_csv(trans_dir / "disparity_flags.csv", index=False)

    # Also export JSON copies for full spec compliance
    exports_dir = output_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    df_emp.head(100).to_json(exports_dir / "employees_sample.json", orient="records", indent=2)
    df_bands.head(100).to_json(exports_dir / "compensation_bands_sample.json", orient="records", indent=2)

    # Write Manifest
    manifest = {
        "generator_version": "1.0.0",
        "generated_at": datetime.now().isoformat(),
        "seed": seed,
        "scale": scale,
        "tables": {
            "roles": len(df_roles),
            "levels": len(df_levels),
            "locations": len(df_locations),
            "compensation_bands": len(df_bands),
            "employees": len(df_emp),
            "salary_records": len(df_salary),
            "performance_evidence": len(df_perf),
            "tenure": len(df_tenure),
            "promotions": len(df_promotions),
            "comparable_groups": len(df_groups),
            "adjustment_proposals": len(df_proposals),
            "disparity_flags": len(df_flags),
            "ground_truth_anomalies": len(gt_records),
        },
    }
    with open(output_dir / "source_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n✅ GENERATION COMPLETE!")
    for table_name, count in manifest["tables"].items():
        print(f"   • {table_name:25s}: {count:,} records")

    return {
        "roles": df_roles,
        "levels": df_levels,
        "locations": df_locations,
        "compensation_bands": df_bands,
        "employees": df_emp,
        "salary_records": df_salary,
        "performance_evidence": df_perf,
        "tenure": df_tenure,
        "promotions": df_promotions,
        "comparable_groups": df_groups,
        "adjustment_proposals": df_proposals,
        "disparity_flags": df_flags,
    }


def verify_reproducibility(seed: int, scale: str, base_dir: Path) -> bool:
    """Run generation twice in isolated temp folders and verify identical checksums."""
    print("\n🔬 RUNNING DETERMINISTIC REPRODUCIBILITY VERIFICATION...")
    run1_dir = base_dir / "reproducibility_run1"
    run2_dir = base_dir / "reproducibility_run2"

    run_pipeline(seed, scale, run1_dir)
    run_pipeline(seed, scale, run2_dir)

    all_match = True
    files_to_check = [
        Path("master/roles.csv"),
        Path("master/levels.csv"),
        Path("master/locations.csv"),
        Path("master/compensation_bands.csv"),
        Path("transactions/employees.csv"),
        Path("transactions/salary_records.csv"),
        Path("transactions/performance_evidence.csv"),
        Path("transactions/tenure.csv"),
        Path("transactions/promotions.csv"),
        Path("transactions/comparable_groups.csv"),
        Path("transactions/adjustment_proposals.csv"),
        Path("transactions/disparity_flags.csv"),
    ]

    print("\nComparing file checksums (MD5):")
    for rel_path in files_to_check:
        f1 = run1_dir / rel_path
        f2 = run2_dir / rel_path
        h1 = compute_md5(f1)
        h2 = compute_md5(f2)
        match = (h1 == h2)
        status = "MATCH ✅" if match else "MISMATCH ❌"
        print(f"   {str(rel_path):35s} | {h1[:8]} == {h2[:8]} | {status}")
        if not match:
            all_match = False

    if all_match:
        print("\n🎉 REPRODUCIBILITY TEST PASSED: 100% Bit-for-bit identical checksums across runs!\n")
    else:
        print("\n❌ REPRODUCIBILITY TEST FAILED: Differences detected across runs.\n")

    return all_match


def main():
    parser = argparse.ArgumentParser(description="Synthetic Compensation Data Generator")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed (default: 20261022)")
    parser.add_argument("--scale", type=str, choices=["starter", "full"], default="full", help="Data volume preset")
    parser.add_argument("--output-dir", type=str, default=str(_PROJECT_ROOT / "data"), help="Target data directory")
    parser.add_argument("--reproducibility-check", action="store_true", help="Run 2x reproducibility checksum validation")

    args = parser.parse_args()
    out_dir = Path(args.output_dir)

    if args.reproducibility_check:
        success = verify_reproducibility(args.seed, "starter", out_dir.parent / "temp_repro")
        if not success:
            sys.exit(1)

    run_pipeline(args.seed, args.scale, out_dir)


if __name__ == "__main__":
    main()
