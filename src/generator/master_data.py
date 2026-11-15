"""
master_data.py — Functions to generate master/reference data:
  - Roles, Levels, Locations, CompensationBands
"""

from __future__ import annotations

import pandas as pd
from datetime import date, timedelta

try:
    from .config import (
        ROLES, LEVELS, LOCATIONS, FISCAL_YEARS,
        BAND_BASE_RANGES, BAND_ANNUAL_INCREASE,
        ROLE_FAMILY_MULTIPLIERS, FX_TO_INR,
        ANOMALY_EXPIRED_BAND_INJECT_COUNT,
    )
except ImportError:
    from config import (
        ROLES, LEVELS, LOCATIONS, FISCAL_YEARS,
        BAND_BASE_RANGES, BAND_ANNUAL_INCREASE,
        ROLE_FAMILY_MULTIPLIERS, FX_TO_INR,
        ANOMALY_EXPIRED_BAND_INJECT_COUNT,
    )


def generate_roles() -> pd.DataFrame:
    """Return a DataFrame of all roles (master data, no randomness)."""
    rows = []
    for idx, r in enumerate(ROLES, start=1):
        rows.append({
            "role_id":   f"ROLE-{idx:03d}",
            "role_code": r["code"],
            "role_name": r["name"],
            "role_family": r["family"],
            "is_comparable_within_family": r["comparable"],
        })
    return pd.DataFrame(rows)


def generate_levels() -> pd.DataFrame:
    """Return a DataFrame of all levels (master data, no randomness)."""
    rows = []
    for idx, lv in enumerate(LEVELS, start=1):
        rows.append({
            "level_id":   f"LVL-{idx:03d}",
            "level_code": lv["code"],
            "level_name": lv["name"],
            "track":      lv["track"],
            "rank_order": lv["rank"],
        })
    return pd.DataFrame(rows)


def generate_locations() -> pd.DataFrame:
    """Return a DataFrame of all locations (master data, no randomness)."""
    rows = []
    for idx, loc in enumerate(LOCATIONS, start=1):
        rows.append({
            "location_id":    f"LOC-{idx:03d}",
            "location_code":  loc["code"],
            "city":           loc["city"],
            "state":          loc["state"],
            "country":        loc["country"],
            "currency_code":  loc["currency"],
            "geo_multiplier": loc["geo"],
            "timezone":       _infer_timezone(loc["code"]),
        })
    return pd.DataFrame(rows)


def _infer_timezone(code: str) -> str:
    """Map location code to IANA timezone string."""
    _tz_map = {
        "BLR": "Asia/Kolkata",  "MUM": "Asia/Kolkata",
        "HYD": "Asia/Kolkata",  "PUN": "Asia/Kolkata",
        "CHN": "Asia/Kolkata",  "DEL": "Asia/Kolkata",
        "KOL": "Asia/Kolkata",  "AMD": "Asia/Kolkata",
        "NOI": "Asia/Kolkata",  "GGN": "Asia/Kolkata",
        "SGP": "Asia/Singapore","LDN": "Europe/London",
        "DXB": "Asia/Dubai",
    }
    return _tz_map.get(code, "UTC")


def generate_compensation_bands(
    df_roles: pd.DataFrame,
    df_levels: pd.DataFrame,
    df_locations: pd.DataFrame,
    rng,  # numpy RandomState for reproducibility
) -> pd.DataFrame:
    """
    Generate compensation bands for every role × level × location × fiscal year.

    Band values are computed as:
        base_range * geo_multiplier * role_family_multiplier
    with a 3% annual increase applied for each year after 2024.

    ~15 bands are injected with an expiry_date in the past (before the last
    day of their fiscal year) to support the EXPIRED_BAND edge-case tests.

    Returns a DataFrame of compensation bands.
    """
    rows = []

    # Build look-up dicts
    loc_by_code = {
        row["location_code"]: row
        for _, row in df_locations.iterrows()
    }
    role_by_code = {
        row["role_code"]: row
        for _, row in df_roles.iterrows()
    }

    for year in FISCAL_YEARS:
        year_factor = (1 + BAND_ANNUAL_INCREASE) ** (year - 2024)
        for _, role_row in df_roles.iterrows():
            family      = role_row["role_family"]
            fam_mult    = ROLE_FAMILY_MULTIPLIERS.get(family, 1.0)
            role_code   = role_row["role_code"]

            for _, level_row in df_levels.iterrows():
                level_code = level_row["level_code"]
                base_min, base_mid, base_max = BAND_BASE_RANGES[level_code]

                for loc_code, loc_row in loc_by_code.items():
                    geo  = loc_row["geo_multiplier"]
                    curr = loc_row["currency_code"]
                    fx   = FX_TO_INR.get(curr, 1.0)

                    # Compute band values in local currency
                    multiplier = year_factor * fam_mult * geo
                    b_min = round(base_min * multiplier / fx, 2)
                    b_mid = round(base_mid * multiplier / fx, 2)
                    b_max = round(base_max * multiplier / fx, 2)

                    band_id       = f"BAND-{role_code}-{level_code}-{loc_code}-{year}"
                    effective_dt  = date(year, 1, 1)
                    expiry_dt     = date(year, 12, 31)

                    rows.append({
                        "band_id":        band_id,
                        "role_id":        role_row["role_id"],
                        "role_code":      role_code,
                        "level_id":       level_row["level_id"],
                        "level_code":     level_code,
                        "location_id":    loc_row["location_id"],
                        "location_code":  loc_code,
                        "currency_code":  curr,
                        "band_min":       b_min,
                        "band_mid":       b_mid,
                        "band_max":       b_max,
                        "fiscal_year":    year,
                        "effective_date": effective_dt.isoformat(),
                        "expiry_date":    expiry_dt.isoformat(),
                        "is_active":      True,
                        "_expired_injected": False,
                    })

    df_bands = pd.DataFrame(rows)

    # -------------------------------------------------------------------
    # Inject ~15 expired bands (expiry_date in the past relative to
    # any salary record effective date that might reference them)
    # -------------------------------------------------------------------
    # We pick bands from fiscal_year 2024 (oldest), set expiry to 2024-06-30
    # so that if a 2025/2026 salary record ever points to them it's stale.
    target_expired = df_bands[df_bands["fiscal_year"] == 2024].sample(
        n=ANOMALY_EXPIRED_BAND_INJECT_COUNT,
        random_state=rng.randint(0, 2**31 - 1)
    ).index
    df_bands.loc[target_expired, "expiry_date"]      = "2024-06-30"
    df_bands.loc[target_expired, "is_active"]        = False
    df_bands.loc[target_expired, "_expired_injected"] = True

    return df_bands
