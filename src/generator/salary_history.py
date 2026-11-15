"""
salary_history.py — Core synthetic-data generation functions:
  generate_employees, generate_salary_records, generate_performance_evidence,
  generate_tenure, generate_promotions, generate_comparable_groups,
  generate_adjustment_proposals, generate_disparity_flags
"""

from __future__ import annotations

import json
import math
import random
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from faker import Faker

try:
    from .config import (
        FISCAL_YEARS, REFERENCE_DATE,
        FX_TO_INR, LOCATIONS, INDIAN_LOCATION_CODES, INTL_LOCATION_CODES,
        ROLES, ROLE_FAMILY_WEIGHTS, ROLE_FAMILY_MULTIPLIERS,
        LEVELS, LEVEL_DISTRIBUTION,
        GENDER_DISTRIBUTION, EMPLOYMENT_TYPE_DISTRIBUTION,
        PART_TIME_FTE_RANGE, INDIA_EMP_FRACTION,
        HIRE_DATE_START, HIRE_DATE_END,
        PERF_RATING_MEAN, PERF_RATING_STD, PERF_RATING_MIN, PERF_RATING_MAX,
        PERF_QUARTERS,
        MERIT_RANGE, PROMOTION_FRACTION, PROMO_MIN_MONTHS, PROMO_SALARY_ADJ_RANGE,
        COMPARABLE_GROUP_MIN_SIZE, COMPA_RATIO_THRESHOLD,
        ANOMALY_FTE_IGNORED_COUNT,
    )
except ImportError:
    from config import (
        FISCAL_YEARS, REFERENCE_DATE,
        FX_TO_INR, LOCATIONS, INDIAN_LOCATION_CODES, INTL_LOCATION_CODES,
        ROLES, ROLE_FAMILY_WEIGHTS, ROLE_FAMILY_MULTIPLIERS,
        LEVELS, LEVEL_DISTRIBUTION,
        GENDER_DISTRIBUTION, EMPLOYMENT_TYPE_DISTRIBUTION,
        PART_TIME_FTE_RANGE, INDIA_EMP_FRACTION,
        HIRE_DATE_START, HIRE_DATE_END,
        PERF_RATING_MEAN, PERF_RATING_STD, PERF_RATING_MIN, PERF_RATING_MAX,
        PERF_QUARTERS,
        MERIT_RANGE, PROMOTION_FRACTION, PROMO_MIN_MONTHS, PROMO_SALARY_ADJ_RANGE,
        COMPARABLE_GROUP_MIN_SIZE, COMPA_RATIO_THRESHOLD,
        ANOMALY_FTE_IGNORED_COUNT,
    )

_REF_DATE = date.fromisoformat(REFERENCE_DATE)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _weighted_choice(choices: list, weights: list[float], rng) -> object:
    """Pick a single element from choices using provided weights."""
    total = sum(weights)
    normed = [w / total for w in weights]
    cum = []
    s = 0.0
    for w in normed:
        s += w
        cum.append(s)
    r = rng.uniform(0, 1)
    for c, threshold in zip(choices, cum):
        if r <= threshold:
            return c
    return choices[-1]


def _random_date_between(start_str: str, end_str: str, rng) -> date:
    start = date.fromisoformat(start_str)
    end   = date.fromisoformat(end_str)
    delta = (end - start).days
    return start + timedelta(days=int(rng.randint(0, delta)))


def _months_between(d1: date, d2: date) -> int:
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


def _tenure_band(months: int) -> str:
    if months < 12:
        return "0-12M"
    elif months < 36:
        return "1-3YR"
    elif months < 60:
        return "3-5YR"
    else:
        return "5PLUS_YR"


def _rating_label(rating: float) -> str:
    if rating >= 4.5:
        return "EXCEEDS"
    elif rating >= 3.0:
        return "MEETS"
    elif rating >= 2.0:
        return "BELOW"
    else:
        return "PIP"


# ---------------------------------------------------------------------------
# Step 5 — Employees
# ---------------------------------------------------------------------------

def generate_employees(
    n_employees: int,
    df_roles: pd.DataFrame,
    df_levels: pd.DataFrame,
    df_locations: pd.DataFrame,
    rng: np.random.RandomState,
    faker_in: Faker,
    faker_en: Faker,
) -> pd.DataFrame:
    """
    Generate synthetic employee records.

    Distribution targets:
    - 80 % Indian locations, 20 % international
    - Level distribution per LEVEL_DISTRIBUTION
    - Role family distribution per ROLE_FAMILY_WEIGHTS
    - 60/35/5 gender split
    - 90/10 FULL_TIME/PART_TIME split
    """
    # Build role / level look-ups
    role_df  = df_roles.copy()
    level_df = df_levels.copy()
    loc_df   = df_locations.copy()

    # Roles grouped by family
    roles_by_family: dict[str, list] = {}
    for _, row in role_df.iterrows():
        fam = row["role_family"]
        roles_by_family.setdefault(fam, []).append(row)

    level_codes = [lv["level_code"] for lv in LEVELS]
    level_weights = [LEVEL_DISTRIBUTION.get(c, 0.01) for c in level_codes]

    gender_choices  = ["M", "F", "NB"]
    gender_weights  = [GENDER_DISTRIBUTION[g] for g in gender_choices]
    emp_type_choices = ["FULL_TIME", "PART_TIME"]
    emp_type_weights = [EMPLOYMENT_TYPE_DISTRIBUTION[t] for t in emp_type_choices]

    # Family choices & weights
    family_choices  = list(ROLE_FAMILY_WEIGHTS.keys())
    family_weights  = [ROLE_FAMILY_WEIGHTS[f] for f in family_choices]

    # Indian vs international location codes
    ind_loc_df  = loc_df[loc_df["location_code"].isin(INDIAN_LOCATION_CODES)]
    intl_loc_df = loc_df[loc_df["location_code"].isin(INTL_LOCATION_CODES)]

    rows = []
    for i in range(1, n_employees + 1):
        emp_id = f"EMP-{i:06d}"

        # --- location ---
        if rng.uniform() < INDIA_EMP_FRACTION:
            loc_row = ind_loc_df.sample(1, random_state=rng.randint(0, 2**31-1)).iloc[0]
        else:
            loc_row = intl_loc_df.sample(1, random_state=rng.randint(0, 2**31-1)).iloc[0]

        loc_code = loc_row["location_code"]
        is_indian = loc_code in INDIAN_LOCATION_CODES

        # --- name & gender ---
        gender = _weighted_choice(gender_choices, gender_weights, rng)
        if is_indian:
            full_name = faker_in.name_male() if gender == "M" else faker_in.name_female() if gender == "F" else faker_in.name()
        else:
            full_name = faker_en.name_male() if gender == "M" else faker_en.name_female() if gender == "F" else faker_en.name()

        # --- level ---
        level_code = _weighted_choice(level_codes, level_weights, rng)
        level_row  = level_df[level_df["level_code"] == level_code].iloc[0]

        # --- role family → role ---
        # Leadership roles only for M-track levels
        if level_row["track"] == "MANAGER":
            # Only manager-track roles
            mgr_families = ["Leadership", "Operations", "Finance", "HR", "Product", "Analytics", "Design", "Engineering"]
        else:
            mgr_families = [f for f in family_choices if f != "Leadership"]

        # pick family, then role within family
        attempt = 0
        while True:
            family = _weighted_choice(family_choices, family_weights, rng)
            if level_row["track"] == "MANAGER" or family != "Leadership":
                break
            attempt += 1
            if attempt > 20:
                family = "Engineering"
                break

        family_roles = roles_by_family.get(family, roles_by_family["Engineering"])
        role_row = family_roles[int(rng.randint(0, len(family_roles)))]

        # --- employment type ---
        emp_type = _weighted_choice(emp_type_choices, emp_type_weights, rng)
        fte = 1.0
        if emp_type == "PART_TIME":
            fte = round(float(rng.uniform(*PART_TIME_FTE_RANGE)), 2)

        # --- hire date ---
        hire_date = _random_date_between(HIRE_DATE_START, HIRE_DATE_END, rng)

        rows.append({
            "employee_id":    emp_id,
            "full_name":      full_name,
            "gender":         gender,
            "role_id":        role_row["role_id"],
            "role_code":      role_row["role_code"],
            "role_name":      role_row["role_name"],
            "role_family":    role_row["role_family"],
            "level_id":       level_row["level_id"],
            "level_code":     level_code,
            "location_id":    loc_row["location_id"],
            "location_code":  loc_code,
            "currency_code":  loc_row["currency_code"],
            "hire_date":      hire_date.isoformat(),
            "employment_type": emp_type,
            "fte_fraction":   fte,
            "status":         "ACTIVE",
            "manager_id":     None,
            "created_at":     "2026-10-22T00:00:00",
        })

    df_emp = pd.DataFrame(rows)

    # --- assign managers ---
    # M1+ employees can be managers for L1-L3; M2+ for L4-L5
    manager_pool_m1 = df_emp[df_emp["level_code"].isin(["M1","M2","M3","M4"])]["employee_id"].tolist()
    manager_pool_m2 = df_emp[df_emp["level_code"].isin(["M2","M3","M4"])]["employee_id"].tolist()

    # If pools are empty (small dataset), fall back to any senior employee
    if not manager_pool_m1:
        manager_pool_m1 = df_emp["employee_id"].tolist()[:max(1, len(df_emp)//10)]
    if not manager_pool_m2:
        manager_pool_m2 = manager_pool_m1

    def pick_manager(emp_id: str, level_code: str) -> Optional[str]:
        pool = manager_pool_m2 if level_code in ["L4","L5"] else manager_pool_m1
        eligible = [m for m in pool if m != emp_id]
        if not eligible:
            return None
        return eligible[int(rng.randint(0, len(eligible)))]

    for idx, row in df_emp.iterrows():
        if row["level_code"] not in ["M3","M4"]:
            df_emp.at[idx, "manager_id"] = pick_manager(row["employee_id"], row["level_code"])

    return df_emp


# ---------------------------------------------------------------------------
# Step 6 — Salary Records
# ---------------------------------------------------------------------------

def generate_salary_records(
    df_emp: pd.DataFrame,
    df_bands: pd.DataFrame,
    rng: np.random.RandomState,
    fte_ignored_emp_ids: Optional[set] = None,
) -> pd.DataFrame:
    """
    Generate salary records for all employees.

    For each employee:
    1. HIRE record effective on hire_date, salary within band for that year.
    2. Annual MERIT record for each year 2024-2026 (if hired before that year).
    3. annual_salary_normalized = salary converted to INR
    4. annual_salary_fte = normalized / fte_fraction
    5. compa_ratio = annual_salary_fte / band_mid_inr * 100

    FTE_IGNORED employees (~30 PART_TIME): store raw salary without FTE
    normalization as a deliberate error.
    """
    if fte_ignored_emp_ids is None:
        fte_ignored_emp_ids = set()

    # Build band lookup: (role_code, level_code, location_code, year) → band row
    bands_lookup: dict[tuple, pd.Series] = {}
    for _, b in df_bands.iterrows():
        key = (b["role_code"], b["level_code"], b["location_code"], int(b["fiscal_year"]))
        # prefer non-expired bands if multiple
        if key not in bands_lookup or not b["_expired_injected"]:
            bands_lookup[key] = b

    all_records: list[dict] = []
    seq_counter: dict[str, int] = {}  # emp_id → current seq

    for _, emp in df_emp.iterrows():
        emp_id    = emp["employee_id"]
        hire_date = date.fromisoformat(emp["hire_date"])
        hire_year = hire_date.year
        role_code = emp["role_code"]
        level_code = emp["level_code"]
        loc_code  = emp["location_code"]
        currency  = emp["currency_code"]
        fte       = float(emp["fte_fraction"])
        fx_rate   = FX_TO_INR.get(currency, 1.0)
        is_fte_ignored = emp_id in fte_ignored_emp_ids

        seq_counter[emp_id] = 0

        def next_sal_id() -> str:
            seq_counter[emp_id] += 1
            digits = emp_id.replace("EMP-", "")
            return f"SAL-{digits}-{year_for_id}-{seq_counter[emp_id]:02d}"

        current_salary_local = None
        prev_end_idx = None

        # HIRE record
        band_year = max(hire_year, FISCAL_YEARS[0])  # earliest band is 2024
        band_key  = (role_code, level_code, loc_code, band_year)
        band_row  = bands_lookup.get(band_key)

        if band_row is None:
            # fall back to first available year
            for fy in FISCAL_YEARS:
                band_row = bands_lookup.get((role_code, level_code, loc_code, fy))
                if band_row is not None:
                    band_year = fy
                    break

        if band_row is None:
            # skip if no band found (shouldn't happen)
            continue

        # Initial salary: uniform in [band_min, band_max] local currency
        b_min_local = float(band_row["band_min"])
        b_max_local = float(band_row["band_max"])
        b_mid_local = float(band_row["band_mid"])
        current_salary_local = rng.uniform(b_min_local, b_max_local)

        year_for_id = hire_year
        sal_id = next_sal_id()

        normalized = current_salary_local * fx_rate
        if is_fte_ignored:
            fte_salary = normalized  # deliberate error: skip FTE division
        else:
            fte_salary = normalized / fte if fte > 0 else normalized

        b_mid_inr = b_mid_local * fx_rate
        compa = round(fte_salary / b_mid_inr * 100, 4) if b_mid_inr > 0 else None

        hire_rec = {
            "salary_id":                  sal_id,
            "employee_id":                emp_id,
            "band_id":                    band_row["band_id"],
            "annual_salary":              round(current_salary_local, 2),
            "currency_code":              currency,
            "annual_salary_normalized":   round(normalized, 2),
            "annual_salary_fte":          round(fte_salary, 2),
            "effective_date":             hire_date.isoformat(),
            "end_date":                   None,
            "change_reason":              "HIRE",
            "source":                     "SYSTEM",
            "compa_ratio":                compa,
            "created_at":                 "2026-10-22T00:00:00",
            "_fte_ignored":               is_fte_ignored,
        }
        all_records.append(hire_rec)
        prev_end_idx = len(all_records) - 1

        # Annual MERIT records
        for year in FISCAL_YEARS:
            # Only for employees hired before this fiscal year
            merit_effective = date(year, 4, 1)  # April 1 merit cycle
            if hire_date >= merit_effective:
                continue

            merit_pct = rng.uniform(*MERIT_RANGE)
            current_salary_local = current_salary_local * (1 + merit_pct)

            # Look up band for this year
            band_key_yr = (role_code, level_code, loc_code, year)
            band_yr = bands_lookup.get(band_key_yr, band_row)

            b_mid_yr_inr = float(band_yr["band_mid"]) * fx_rate

            year_for_id = year
            sal_id = next_sal_id()

            normalized = current_salary_local * fx_rate
            if is_fte_ignored:
                fte_salary = normalized
            else:
                fte_salary = normalized / fte if fte > 0 else normalized

            compa = round(fte_salary / b_mid_yr_inr * 100, 4) if b_mid_yr_inr > 0 else None

            # Chain: set end_date on previous record
            prev_rec = all_records[prev_end_idx]
            prev_rec["end_date"] = (merit_effective - timedelta(days=1)).isoformat()

            merit_rec = {
                "salary_id":                  sal_id,
                "employee_id":                emp_id,
                "band_id":                    band_yr["band_id"],
                "annual_salary":              round(current_salary_local, 2),
                "currency_code":              currency,
                "annual_salary_normalized":   round(normalized, 2),
                "annual_salary_fte":          round(fte_salary, 2),
                "effective_date":             merit_effective.isoformat(),
                "end_date":                   None,
                "change_reason":              "MERIT",
                "source":                     "SYSTEM",
                "compa_ratio":                compa,
                "created_at":                 "2026-10-22T00:00:00",
                "_fte_ignored":               is_fte_ignored,
            }
            all_records.append(merit_rec)
            prev_end_idx = len(all_records) - 1

    return pd.DataFrame(all_records)


# ---------------------------------------------------------------------------
# Step 7 — Performance Evidence
# ---------------------------------------------------------------------------

def generate_performance_evidence(
    df_emp: pd.DataFrame,
    rng: np.random.RandomState,
) -> pd.DataFrame:
    """
    Generate semi-annual performance reviews (Q2, Q4) for 2024, 2025, 2026.
    Ratings are normally distributed around 3.0 (std=0.8), clipped to [1,5].
    """
    documented_pool = [
        "strong delivery record",
        "exceeded OKRs by 120%",
        "consistent high performance",
        "positive peer feedback",
        "led critical project to completion",
        "mentored two junior engineers",
        "reduced incident rate by 30%",
        "shipped key product feature ahead of schedule",
        "improved team velocity by 15%",
        "below expectations on key deliverables",
        "communication gaps identified",
        "needs improvement in technical skills",
        "placed on performance improvement plan",
        "showed significant improvement mid-year",
        "strong collaboration across teams",
    ]

    rows = []
    for _, emp in df_emp.iterrows():
        emp_id    = emp["employee_id"]
        hire_date = date.fromisoformat(emp["hire_date"])
        manager   = emp.get("manager_id", None)

        for year in FISCAL_YEARS:
            for quarter in PERF_QUARTERS:
                # Review date: end of quarter
                q_month  = 6 if quarter == "Q2" else 12
                rev_date = date(year, q_month, 30 if q_month == 6 else 31)

                # Employee must have been hired before review date
                if hire_date >= rev_date:
                    continue

                perf_id = f"PERF-{emp_id.replace('EMP-', '')}-{year}-{quarter}"
                rating  = float(np.clip(
                    rng.normal(PERF_RATING_MEAN, PERF_RATING_STD),
                    PERF_RATING_MIN, PERF_RATING_MAX
                ))
                rating  = round(rating, 1)

                # 2-4 documented factors
                n_factors = int(rng.randint(2, 5))
                factors = rng.choice(documented_pool, size=n_factors, replace=False).tolist()

                rows.append({
                    "perf_id":            perf_id,
                    "employee_id":        emp_id,
                    "review_period":      f"{year}-{quarter}",
                    "rating":             rating,
                    "rating_label":       _rating_label(rating),
                    "documented_factors": json.dumps(factors),
                    "reviewer_id":        manager,
                    "review_date":        rev_date.isoformat(),
                    "is_active":          True,
                })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 8 — Tenure
# ---------------------------------------------------------------------------

def generate_tenure(
    df_emp: pd.DataFrame,
    df_promotions: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Derive tenure metrics from hire_date to REFERENCE_DATE (2026-10-22).
    months_in_current_role comes from last promotion date if available.
    """
    rows = []
    promo_last: dict[str, date] = {}
    if df_promotions is not None and not df_promotions.empty:
        for _, pr in df_promotions.iterrows():
            eid = pr["employee_id"]
            eff = date.fromisoformat(pr["effective_date"])
            if eid not in promo_last or eff > promo_last[eid]:
                promo_last[eid] = eff

    for _, emp in df_emp.iterrows():
        emp_id    = emp["employee_id"]
        hire_date = date.fromisoformat(emp["hire_date"])
        months_total = _months_between(hire_date, _REF_DATE)

        last_promo = promo_last.get(emp_id)
        if last_promo:
            months_role = _months_between(last_promo, _REF_DATE)
        else:
            months_role = months_total

        rows.append({
            "tenure_id":            f"TEN-{emp_id.replace('EMP-', '')}",
            "employee_id":          emp_id,
            "months_in_company":    months_total,
            "months_in_current_role": months_role,
            "tenure_band":          _tenure_band(months_total),
            "last_calculated_at":   REFERENCE_DATE,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 9 — Promotions
# ---------------------------------------------------------------------------

def generate_promotions(
    df_emp: pd.DataFrame,
    df_salary: pd.DataFrame,
    df_bands: pd.DataFrame,
    df_levels: pd.DataFrame,
    rng: np.random.RandomState,
    n_employees: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Promote ~15% of eligible employees (min 18 months in level, one level up).
    Returns (df_promotions, updated_df_salary).
    """
    target_promos = max(1, int(n_employees * PROMOTION_FRACTION))

    # Level progression map (one step up)
    level_up: dict[str, str] = {
        "L1": "L2", "L2": "L3", "L3": "L4",
        "L4": "L5", "L5": "L6",
        "M1": "M2", "M2": "M3", "M3": "M4",
    }
    level_id_map = {row["level_code"]: row["level_id"] for _, row in df_levels.iterrows()}

    # Only employees with a promotable level
    promotable = df_emp[df_emp["level_code"].isin(level_up.keys())].copy()
    if promotable.empty:
        return pd.DataFrame(), df_salary

    # Filter: must have been hired >= 18 months before reference date
    cutoff = _REF_DATE - timedelta(days=PROMO_MIN_MONTHS * 30)
    promotable = promotable[
        pd.to_datetime(promotable["hire_date"]).dt.date <= cutoff
    ]

    if promotable.empty:
        return pd.DataFrame(), df_salary

    # Sample
    n_promos = min(target_promos, len(promotable))
    promoted_df = promotable.sample(n=n_promos, random_state=rng.randint(0, 2**31-1))

    # Build band lookup
    bands_lookup: dict[tuple, pd.Series] = {}
    for _, b in df_bands.iterrows():
        key = (b["role_code"], b["level_code"], b["location_code"], int(b["fiscal_year"]))
        if key not in bands_lookup or not b["_expired_injected"]:
            bands_lookup[key] = b

    promo_rows: list[dict] = []
    new_salary_rows: list[dict] = []

    # Also track existing salary seq for promo salary_id generation
    existing_sal_seqs: dict[str, int] = {}
    for _, sr in df_salary.iterrows():
        eid = sr["employee_id"]
        existing_sal_seqs[eid] = existing_sal_seqs.get(eid, 0) + 1

    for _, emp in promoted_df.iterrows():
        emp_id     = emp["employee_id"]
        from_level = emp["level_code"]
        to_level   = level_up[from_level]
        role_code  = emp["role_code"]
        loc_code   = emp["location_code"]
        currency   = emp["currency_code"]
        fte        = float(emp["fte_fraction"])
        fx_rate    = FX_TO_INR.get(currency, 1.0)

        # Promo effective date: random date in 2024/2025 (not too recent)
        promo_year  = int(rng.choice([2024, 2025]))
        promo_month = int(rng.randint(1, 13))
        promo_day   = int(rng.randint(1, 28))
        promo_date  = date(promo_year, promo_month, promo_day)

        # Must be after hire_date
        hire_date = date.fromisoformat(emp["hire_date"])
        if promo_date <= hire_date + timedelta(days=PROMO_MIN_MONTHS * 30):
            promo_date = hire_date + timedelta(days=PROMO_MIN_MONTHS * 30 + 30)
            if promo_date > _REF_DATE:
                continue

        promo_id = f"PROMO-{emp_id.replace('EMP-', '')}-{promo_date.year}-{promo_date.month:02d}"

        # Find an approver (a manager)
        manager_id = emp.get("manager_id", None)

        adj_pct = float(rng.uniform(*PROMO_SALARY_ADJ_RANGE))

        promo_rows.append({
            "promo_id":            promo_id,
            "employee_id":         emp_id,
            "from_level_id":       level_id_map.get(from_level, ""),
            "from_level_code":     from_level,
            "to_level_id":         level_id_map.get(to_level, ""),
            "to_level_code":       to_level,
            "from_role_id":        emp["role_id"],
            "to_role_id":          emp["role_id"],  # same role, level up
            "effective_date":      promo_date.isoformat(),
            "approved_by":         manager_id,
            "promo_type":          "LEVEL_UP",
            "salary_adjustment_pct": round(adj_pct * 100, 2),
        })

        # Create a new PROMOTION salary record
        # Find the latest salary record for this employee before promo_date
        emp_sal = df_salary[df_salary["employee_id"] == emp_id].copy()
        if emp_sal.empty:
            continue
        emp_sal["_eff_dt"] = pd.to_datetime(emp_sal["effective_date"])
        emp_sal = emp_sal.sort_values("_eff_dt")
        pre_promo = emp_sal[emp_sal["_eff_dt"] <= pd.Timestamp(promo_date)]
        if pre_promo.empty:
            pre_promo = emp_sal.iloc[[0]]
        last_sal = pre_promo.iloc[-1]

        new_sal_local = float(last_sal["annual_salary"]) * (1 + adj_pct)

        # Band for new level
        band_key = (role_code, to_level, loc_code, promo_date.year)
        band_yr  = bands_lookup.get(band_key)
        if band_yr is None:
            # try 2024
            band_yr = bands_lookup.get((role_code, to_level, loc_code, 2024))
        if band_yr is None:
            continue

        b_mid_inr = float(band_yr["band_mid"]) * fx_rate
        normalized = new_sal_local * fx_rate
        fte_salary = normalized / fte if fte > 0 else normalized
        compa = round(fte_salary / b_mid_inr * 100, 4) if b_mid_inr > 0 else None

        seq = existing_sal_seqs.get(emp_id, 0) + 1
        existing_sal_seqs[emp_id] = seq
        digits = emp_id.replace("EMP-", "")
        sal_id = f"SAL-{digits}-{promo_date.year}-{seq:02d}"

        new_salary_rows.append({
            "salary_id":                  sal_id,
            "employee_id":                emp_id,
            "band_id":                    band_yr["band_id"],
            "annual_salary":              round(new_sal_local, 2),
            "currency_code":              currency,
            "annual_salary_normalized":   round(normalized, 2),
            "annual_salary_fte":          round(fte_salary, 2),
            "effective_date":             promo_date.isoformat(),
            "end_date":                   None,
            "change_reason":              "PROMOTION",
            "source":                     "SYSTEM",
            "compa_ratio":                compa,
            "created_at":                 "2026-10-22T00:00:00",
            "_fte_ignored":               False,
        })

    df_promotions = pd.DataFrame(promo_rows)
    df_promo_sal  = pd.DataFrame(new_salary_rows)
    df_salary_updated = pd.concat([df_salary, df_promo_sal], ignore_index=True)

    return df_promotions, df_salary_updated


# ---------------------------------------------------------------------------
# Step 10 — Comparable Groups
# ---------------------------------------------------------------------------

def generate_comparable_groups(
    df_emp: pd.DataFrame,
    df_salary: pd.DataFrame,
    df_tenure: pd.DataFrame,
) -> pd.DataFrame:
    """
    Group employees by role_family, level_code, location_code, tenure_band,
    employment_type. Calculate group statistics.
    Groups with fewer than COMPARABLE_GROUP_MIN_SIZE employees are excluded.
    """
    # Get the latest (active) salary per employee
    latest_sal = (
        df_salary
        .sort_values("effective_date", ascending=False)
        .groupby("employee_id")
        .first()
        .reset_index()
        [["employee_id", "annual_salary_fte", "compa_ratio"]]
    )

    # Merge employee data with salary and tenure
    merged = df_emp.merge(latest_sal, on="employee_id", how="left")
    ten_cols = df_tenure[["employee_id", "tenure_band"]].copy()
    merged = merged.merge(ten_cols, on="employee_id", how="left")
    merged["tenure_band"] = merged["tenure_band"].fillna("0-12M")

    group_keys = ["role_family", "level_code", "location_code", "tenure_band", "employment_type"]
    rows: list[dict] = []
    seq = 0

    for group_vals, group_df in merged.groupby(group_keys):
        size = len(group_df)
        if size < COMPARABLE_GROUP_MIN_SIZE:
            continue

        salaries = group_df["annual_salary_fte"].dropna().values
        if len(salaries) == 0:
            continue

        seq += 1
        rf, lc, loc, tb, et = group_vals
        et_code = "FT" if et == "FULL_TIME" else "PT"

        # Compose a GRP ID (ensure full uniqueness across all grouping dimensions)
        group_id = f"GRP-{rf[:3].upper()}-{lc}-{loc}-{tb}-{et_code}"

        rows.append({
            "group_id":           group_id,
            "role_family":        rf,
            "level_code":         lc,
            "location_code":      loc,
            "tenure_band":        tb,
            "employment_type":    et,
            "group_size":         size,
            "group_median_salary": round(float(np.median(salaries)), 2),
            "group_mean_salary":   round(float(np.mean(salaries)), 2),
            "group_p25":           round(float(np.percentile(salaries, 25)), 2),
            "group_p75":           round(float(np.percentile(salaries, 75)), 2),
            "created_at":          "2026-10-22T00:00:00",
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 11 — Adjustment Proposals
# ---------------------------------------------------------------------------

def generate_adjustment_proposals(
    df_emp: pd.DataFrame,
    df_salary: pd.DataFrame,
    df_bands: pd.DataFrame,
    df_perf: pd.DataFrame,
    df_groups: pd.DataFrame,
    rng: np.random.RandomState,
    unapproved_emp_ids: Optional[set] = None,
) -> pd.DataFrame:
    """
    Generate adjustment proposals for employees with compa_ratio < 0.85.
    ~25 proposals are injected as UNAPPROVED_ADJUSTMENT anomalies.
    """
    if unapproved_emp_ids is None:
        unapproved_emp_ids = set()

    # Latest salary per employee
    latest_sal = (
        df_salary
        .sort_values("effective_date", ascending=False)
        .groupby("employee_id")
        .first()
        .reset_index()
    )
    underpaid = latest_sal[latest_sal["compa_ratio"] < (COMPA_RATIO_THRESHOLD * 100)]

    # Build band lookup
    bands_lookup: dict[tuple, pd.Series] = {}
    for _, b in df_bands.iterrows():
        key = (b["role_code"], b["level_code"], b["location_code"], int(b["fiscal_year"]))
        if key not in bands_lookup or not b["_expired_injected"]:
            bands_lookup[key] = b

    # Employee perf IDs
    perf_by_emp: dict[str, list] = {}
    for _, pr in df_perf.iterrows():
        perf_by_emp.setdefault(pr["employee_id"], []).append(pr["perf_id"])

    # Group ID by emp (best-match)
    group_by_emp: dict[str, str] = {}
    emp_grp_merge = df_emp[["employee_id", "role_family", "level_code",
                              "location_code", "employment_type"]].copy()
    for _, row in emp_grp_merge.iterrows():
        # find any matching group
        match = df_groups[
            (df_groups["role_family"] == row["role_family"]) &
            (df_groups["level_code"] == row["level_code"]) &
            (df_groups["location_code"] == row["location_code"])
        ]
        if not match.empty:
            group_by_emp[row["employee_id"]] = match.iloc[0]["group_id"]

    rows = []
    seq = 0
    # Build employee map for fast lookup
    emp_map = df_emp.set_index("employee_id")

    for _, sal in underpaid.iterrows():
        emp_id = sal["employee_id"]
        if emp_id not in emp_map.index:
            continue
        emp = emp_map.loc[emp_id]
        seq += 1
        prop_id = f"ADJ-2026-{seq:06d}"

        band_key = (emp["role_code"], emp["level_code"], emp["location_code"], 2026)
        band = bands_lookup.get(band_key)
        if band is None:
            continue

        currency = emp["currency_code"]
        fx = FX_TO_INR.get(currency, 1.0)
        b_min_inr = float(band["band_min"]) * fx
        b_mid_inr = float(band["band_mid"]) * fx

        current_sal = float(sal["annual_salary_fte"])
        disparity_pct = round((b_mid_inr - current_sal) / b_mid_inr * 100, 2)

        statuses = ["OPEN", "APPROVED", "REJECTED", "WITHDRAWN"]
        status_weights = [0.5, 0.25, 0.15, 0.10]

        is_unapproved = emp_id in unapproved_emp_ids

        if is_unapproved:
            mgr_approval   = "APPROVED"
            hr_approval    = None
            final_status   = "IMPLEMENTED"
        else:
            final_status = _weighted_choice(statuses, status_weights, rng)
            if final_status == "APPROVED":
                mgr_approval = "APPROVED"
                hr_approval  = "APPROVED"
            elif final_status == "REJECTED":
                mgr_approval = rng.choice(["APPROVED", "REJECTED"])
                hr_approval  = "REJECTED"
            elif final_status == "OPEN":
                mgr_approval = "PENDING"
                hr_approval  = None
            else:
                mgr_approval = "APPROVED"
                hr_approval  = None

        evidence_ids = perf_by_emp.get(emp_id, [])
        manager_id   = emp.get("manager_id", None)

        rows.append({
            "proposal_id":               prop_id,
            "employee_id":               emp_id,
            "trigger_type":              "LOW_COMPA_RATIO",
            "current_salary":            round(current_sal, 2),
            "proposed_salary_min":       round(b_min_inr, 2),
            "proposed_salary_recommended": round(b_mid_inr * 0.90, 2),
            "proposed_salary_max":       round(float(band["band_max"]) * fx, 2),
            "reason_code":               "BELOW_BAND_MIN",
            "evidence_ids":              json.dumps(evidence_ids),
            "disparity_pct":             disparity_pct,
            "comparable_group_id":       group_by_emp.get(emp_id, None),
            "manager_id":                manager_id,
            "manager_approval":          mgr_approval,
            "manager_approval_date":     "2026-06-01" if mgr_approval == "APPROVED" else None,
            "hr_partner_id":             None,
            "hr_approval":               hr_approval,
            "hr_approval_date":          "2026-07-01" if hr_approval == "APPROVED" else None,
            "final_status":              final_status,
            "created_at":                "2026-04-01T00:00:00",
            "updated_at":                "2026-10-01T00:00:00",
            "_unapproved_injected":      is_unapproved,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 12 — Disparity Flags
# ---------------------------------------------------------------------------

def generate_disparity_flags(
    df_emp: pd.DataFrame,
    df_salary: pd.DataFrame,
    df_groups: pd.DataFrame,
    df_perf: pd.DataFrame,
    rng: np.random.RandomState,
) -> pd.DataFrame:
    """
    Flag employees whose salary differs from group_median by >20% without
    documented high performance justification.
    Returns a DataFrame of base disparity flags (anomaly injection handled
    separately in synthetic_anomalies.py).
    """
    # Latest salary per employee
    latest_sal = (
        df_salary
        .sort_values("effective_date", ascending=False)
        .groupby("employee_id")
        .first()
        .reset_index()
        [["employee_id", "annual_salary_fte", "band_id"]]
    )

    # Latest perf per employee
    latest_perf = (
        df_perf
        .sort_values("review_date", ascending=False)
        .groupby("employee_id")
        .first()
        .reset_index()
        [["employee_id", "rating", "rating_label", "documented_factors"]]
    )

    merged = df_emp.merge(latest_sal, on="employee_id", how="left")
    merged = merged.merge(latest_perf, on="employee_id", how="left")

    group_map = df_groups.set_index(["role_family", "level_code", "location_code"])

    rows: list[dict] = []
    seq = 0

    for _, emp in merged.iterrows():
        key = (emp["role_family"], emp["level_code"], emp["location_code"])
        if key not in group_map.index:
            continue

        group = group_map.loc[key]
        # In case of multiple groups for same key, take first
        if isinstance(group, pd.DataFrame):
            group = group.iloc[0]

        emp_sal = float(emp["annual_salary_fte"]) if pd.notna(emp["annual_salary_fte"]) else 0
        g_median = float(group["group_median_salary"])
        if g_median == 0:
            continue

        diff_pct = abs(emp_sal - g_median) / g_median * 100

        if diff_pct <= 20:
            continue

        # Check for performance justification
        rating = emp.get("rating", 0.0) or 0.0
        has_justification = rating >= 4.5  # EXCEEDS = justified

        if has_justification:
            continue  # skip — performance justifies disparity

        seq += 1
        flag_id = f"FLAG-{seq:06d}"
        severity = "HIGH" if diff_pct > 40 else "MEDIUM"

        rows.append({
            "flag_id":              flag_id,
            "employee_id":          emp["employee_id"],
            "comparable_group_id":  group["group_id"],
            "issue_type":           "UNEXPLAINED_DISPARITY",
            "severity":             severity,
            "salary_difference":    round(emp_sal - g_median, 2),
            "disparity_pct":        round(diff_pct, 2),
            "detection_rule":       "SALARY_DISPARITY_GT_20PCT",
            "detection_timestamp":  "2026-10-22T00:00:00",
            "investigation_status": "OPEN",
            "resolution_notes":     None,
            "resolved_at":          None,
            "expected_response":    "Review salary against band and performance",
            "_anomaly_type":        None,
        })

    return pd.DataFrame(rows)
