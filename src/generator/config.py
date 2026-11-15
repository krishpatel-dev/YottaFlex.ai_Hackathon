"""
src/generator/config.py
=======================
Master configuration for the synthetic data generator.

All seed data (roles, levels, locations, band ranges, FX rates, generation parameters) lives here.
Import this module wherever you need reference data.
"""

from __future__ import annotations
import os
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Global seed for reproducibility
# ---------------------------------------------------------------------------
SEED: int = int(os.environ.get("SEED", 20261022))

REFERENCE_DATE: str = "2026-10-22"
FISCAL_YEARS: List[int] = [2024, 2025, 2026]

HIRE_DATE_START: str = "2021-01-01"
HIRE_DATE_END: str = "2024-12-31"

# ---------------------------------------------------------------------------
# Roles (20 entries)
# ---------------------------------------------------------------------------
ROLES: List[Dict] = [
    # Engineering family
    {
        "role_id": "ROLE-001",
        "role_code": "SWE",
        "code": "SWE",
        "role_name": "Software Engineer",
        "name": "Software Engineer",
        "role_family": "Engineering",
        "family": "Engineering",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    {
        "role_id": "ROLE-002",
        "role_code": "SSE",
        "code": "SSE",
        "role_name": "Senior Software Engineer",
        "name": "Senior Software Engineer",
        "role_family": "Engineering",
        "family": "Engineering",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    {
        "role_id": "ROLE-003",
        "role_code": "STE",
        "code": "STE",
        "role_name": "Staff Engineer",
        "name": "Staff Engineer",
        "role_family": "Engineering",
        "family": "Engineering",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    {
        "role_id": "ROLE-004",
        "role_code": "DE",
        "code": "DE",
        "role_name": "Data Engineer",
        "name": "Data Engineer",
        "role_family": "Engineering",
        "family": "Engineering",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    {
        "role_id": "ROLE-005",
        "role_code": "DOE",
        "code": "DOE",
        "role_name": "DevOps Engineer",
        "name": "DevOps Engineer",
        "role_family": "Engineering",
        "family": "Engineering",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    {
        "role_id": "ROLE-006",
        "role_code": "QAE",
        "code": "QAE",
        "role_name": "QA Engineer",
        "name": "QA Engineer",
        "role_family": "Engineering",
        "family": "Engineering",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    # Product family (NOT comparable across Engineering)
    {
        "role_id": "ROLE-007",
        "role_code": "PM",
        "code": "PM",
        "role_name": "Product Manager",
        "name": "Product Manager",
        "role_family": "Product",
        "family": "Product",
        "is_comparable_across_roles": False,
        "is_comparable_within_family": True,
        "comparable": False,
    },
    {
        "role_id": "ROLE-008",
        "role_code": "SPM",
        "code": "SPM",
        "role_name": "Senior Product Manager",
        "name": "Senior Product Manager",
        "role_family": "Product",
        "family": "Product",
        "is_comparable_across_roles": False,
        "is_comparable_within_family": True,
        "comparable": False,
    },
    # Design family
    {
        "role_id": "ROLE-009",
        "role_code": "UXD",
        "code": "UXD",
        "role_name": "UX Designer",
        "name": "UX Designer",
        "role_family": "Design",
        "family": "Design",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    {
        "role_id": "ROLE-010",
        "role_code": "SUXD",
        "code": "SUXD",
        "role_name": "Senior UX Designer",
        "name": "Senior UX Designer",
        "role_family": "Design",
        "family": "Design",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    # Data & Analytics family
    {
        "role_id": "ROLE-011",
        "role_code": "DA",
        "code": "DA",
        "role_name": "Data Analyst",
        "name": "Data Analyst",
        "role_family": "Data & Analytics",
        "family": "Data & Analytics",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    {
        "role_id": "ROLE-012",
        "role_code": "DS",
        "code": "DS",
        "role_name": "Data Scientist",
        "name": "Data Scientist",
        "role_family": "Data & Analytics",
        "family": "Data & Analytics",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    {
        "role_id": "ROLE-013",
        "role_code": "BA",
        "code": "BA",
        "role_name": "Business Analyst",
        "name": "Business Analyst",
        "role_family": "Data & Analytics",
        "family": "Data & Analytics",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    # Finance family
    {
        "role_id": "ROLE-014",
        "role_code": "FA",
        "code": "FA",
        "role_name": "Finance Analyst",
        "name": "Finance Analyst",
        "role_family": "Finance",
        "family": "Finance",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    {
        "role_id": "ROLE-015",
        "role_code": "FM",
        "code": "FM",
        "role_name": "Finance Manager",
        "name": "Finance Manager",
        "role_family": "Finance",
        "family": "Finance",
        "is_comparable_across_roles": False,
        "is_comparable_within_family": True,
        "comparable": False,
    },
    # HR family
    {
        "role_id": "ROLE-016",
        "role_code": "HBP",
        "code": "HBP",
        "role_name": "HR Business Partner",
        "name": "HR Business Partner",
        "role_family": "HR",
        "family": "HR",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    {
        "role_id": "ROLE-017",
        "role_code": "TAS",
        "code": "TAS",
        "role_name": "Talent Acquisition Specialist",
        "name": "Talent Acquisition Specialist",
        "role_family": "HR",
        "family": "HR",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    # Operations family
    {
        "role_id": "ROLE-018",
        "role_code": "OM",
        "code": "OM",
        "role_name": "Operations Manager",
        "name": "Operations Manager",
        "role_family": "Operations",
        "family": "Operations",
        "is_comparable_across_roles": False,
        "is_comparable_within_family": True,
        "comparable": False,
    },
    {
        "role_id": "ROLE-019",
        "role_code": "PGM",
        "code": "PGM",
        "role_name": "Program Manager",
        "name": "Program Manager",
        "role_family": "Operations",
        "family": "Operations",
        "is_comparable_across_roles": True,
        "is_comparable_within_family": True,
        "comparable": True,
    },
    # Leadership / Manager track
    {
        "role_id": "ROLE-020",
        "role_code": "EM",
        "code": "EM",
        "role_name": "Engineering Manager",
        "name": "Engineering Manager",
        "role_family": "Leadership",
        "family": "Leadership",
        "is_comparable_across_roles": False,
        "is_comparable_within_family": False,
        "comparable": False,
    },
    {
        "role_id": "ROLE-021",
        "role_code": "DOE2",
        "code": "DOE2",
        "role_name": "Director of Engineering",
        "name": "Director of Engineering",
        "role_family": "Leadership",
        "family": "Leadership",
        "is_comparable_across_roles": False,
        "is_comparable_within_family": False,
        "comparable": False,
    },
]

# ---------------------------------------------------------------------------
# Levels (10 entries)
# ---------------------------------------------------------------------------
LEVELS: List[Dict] = [
    # IC track
    {"level_id": "LVL-001", "level_code": "L1", "code": "L1", "level_name": "Junior",        "name": "Junior",        "track": "IC",      "rank_order": 1, "rank": 1},
    {"level_id": "LVL-002", "level_code": "L2", "code": "L2", "level_name": "Mid",           "name": "Mid",           "track": "IC",      "rank_order": 2, "rank": 2},
    {"level_id": "LVL-003", "level_code": "L3", "code": "L3", "level_name": "Senior",        "name": "Senior",        "track": "IC",      "rank_order": 3, "rank": 3},
    {"level_id": "LVL-004", "level_code": "L4", "code": "L4", "level_name": "Lead / Staff",  "name": "Lead / Staff",  "track": "IC",      "rank_order": 4, "rank": 4},
    {"level_id": "LVL-005", "level_code": "L5", "code": "L5", "level_name": "Principal",     "name": "Principal",     "track": "IC",      "rank_order": 5, "rank": 5},
    {"level_id": "LVL-006", "level_code": "L6", "code": "L6", "level_name": "Distinguished", "name": "Distinguished", "track": "IC",      "rank_order": 6, "rank": 6},
    # Manager track
    {"level_id": "LVL-007", "level_code": "M1", "code": "M1", "level_name": "Manager",       "name": "Manager",       "track": "MANAGER", "rank_order": 7, "rank": 7},
    {"level_id": "LVL-008", "level_code": "M2", "code": "M2", "level_name": "Senior Manager","name": "Senior Manager","track": "MANAGER", "rank_order": 8, "rank": 8},
    {"level_id": "LVL-009", "level_code": "M3", "code": "M3", "level_name": "Director",      "name": "Director",      "track": "MANAGER", "rank_order": 9, "rank": 9},
    {"level_id": "LVL-010", "level_code": "M4", "code": "M4", "level_name": "VP",            "name": "VP",            "track": "MANAGER", "rank_order": 10, "rank": 10},
]

# ---------------------------------------------------------------------------
# Locations (13 entries)
# ---------------------------------------------------------------------------
LOCATIONS: List[Dict] = [
    # India
    {"location_id": "LOC-001", "location_code": "BLR", "code": "BLR", "city": "Bengaluru",  "state": "Karnataka",      "country": "India",     "currency_code": "INR", "currency": "INR", "geo_multiplier": 1.00, "geo": 1.00, "timezone": "Asia/Kolkata"},
    {"location_id": "LOC-002", "location_code": "MUM", "code": "MUM", "city": "Mumbai",     "state": "Maharashtra",    "country": "India",     "currency_code": "INR", "currency": "INR", "geo_multiplier": 1.15, "geo": 1.15, "timezone": "Asia/Kolkata"},
    {"location_id": "LOC-003", "location_code": "HYD", "code": "HYD", "city": "Hyderabad",  "state": "Telangana",      "country": "India",     "currency_code": "INR", "currency": "INR", "geo_multiplier": 0.95, "geo": 0.95, "timezone": "Asia/Kolkata"},
    {"location_id": "LOC-004", "location_code": "PUN", "code": "PUN", "city": "Pune",       "state": "Maharashtra",    "country": "India",     "currency_code": "INR", "currency": "INR", "geo_multiplier": 0.90, "geo": 0.90, "timezone": "Asia/Kolkata"},
    {"location_id": "LOC-005", "location_code": "CHN", "code": "CHN", "city": "Chennai",    "state": "Tamil Nadu",     "country": "India",     "currency_code": "INR", "currency": "INR", "geo_multiplier": 0.92, "geo": 0.92, "timezone": "Asia/Kolkata"},
    {"location_id": "LOC-006", "location_code": "DEL", "code": "DEL", "city": "Delhi",      "state": "Delhi",          "country": "India",     "currency_code": "INR", "currency": "INR", "geo_multiplier": 1.10, "geo": 1.10, "timezone": "Asia/Kolkata"},
    {"location_id": "LOC-007", "location_code": "KOL", "code": "KOL", "city": "Kolkata",    "state": "West Bengal",    "country": "India",     "currency_code": "INR", "currency": "INR", "geo_multiplier": 0.85, "geo": 0.85, "timezone": "Asia/Kolkata"},
    {"location_id": "LOC-008", "location_code": "AMD", "code": "AMD", "city": "Ahmedabad",  "state": "Gujarat",        "country": "India",     "currency_code": "INR", "currency": "INR", "geo_multiplier": 0.80, "geo": 0.80, "timezone": "Asia/Kolkata"},
    {"location_id": "LOC-009", "location_code": "NOI", "code": "NOI", "city": "Noida",      "state": "Uttar Pradesh",  "country": "India",     "currency_code": "INR", "currency": "INR", "geo_multiplier": 1.05, "geo": 1.05, "timezone": "Asia/Kolkata"},
    {"location_id": "LOC-010", "location_code": "GGN", "code": "GGN", "city": "Gurugram",   "state": "Haryana",        "country": "India",     "currency_code": "INR", "currency": "INR", "geo_multiplier": 1.08, "geo": 1.08, "timezone": "Asia/Kolkata"},
    # International
    {"location_id": "LOC-011", "location_code": "SGP", "code": "SGP", "city": "Singapore",  "state": "Singapore",      "country": "Singapore", "currency_code": "SGD", "currency": "SGD", "geo_multiplier": 2.10, "geo": 2.10, "timezone": "Asia/Singapore"},
    {"location_id": "LOC-012", "location_code": "LDN", "code": "LDN", "city": "London",     "state": "England",        "country": "UK",        "currency_code": "GBP", "currency": "GBP", "geo_multiplier": 3.20, "geo": 3.20, "timezone": "Europe/London"},
    {"location_id": "LOC-013", "location_code": "DXB", "code": "DXB", "city": "Dubai",      "state": "Dubai",          "country": "UAE",       "currency_code": "USD", "currency": "USD", "geo_multiplier": 2.50, "geo": 2.50, "timezone": "Asia/Dubai"},
]

INDIAN_LOCATION_CODES: List[str] = ["BLR", "MUM", "HYD", "PUN", "CHN", "DEL", "KOL", "AMD", "NOI", "GGN"]
INTL_LOCATION_CODES: List[str] = ["SGP", "LDN", "DXB"]

# ---------------------------------------------------------------------------
# FX rates → INR (reference date: 2026-10-22)
# ---------------------------------------------------------------------------
FX_TO_INR: Dict[str, float] = {
    "INR": 1.0,
    "USD": 83.5,
    "GBP": 105.2,
    "EUR": 90.1,
    "SGD": 62.3,
    "AED": 22.73,
}

# ---------------------------------------------------------------------------
# Base salary band ranges in INR (Bengaluru baseline, geo=1.0)
# (band_min, band_mid, band_max)
# ---------------------------------------------------------------------------
BAND_BASE_RANGES: Dict[str, Tuple[int, int, int]] = {
    "L1": (400_000,    600_000,   800_000),
    "L2": (700_000,  1_000_000, 1_300_000),
    "L3": (1_200_000, 1_600_000, 2_000_000),
    "L4": (1_800_000, 2_400_000, 3_000_000),
    "L5": (2_800_000, 3_600_000, 4_500_000),
    "L6": (4_000_000, 5_500_000, 7_000_000),
    "M1": (1_600_000, 2_200_000, 2_800_000),
    "M2": (2_600_000, 3_400_000, 4_200_000),
    "M3": (3_800_000, 5_000_000, 6_200_000),
    "M4": (5_500_000, 7_500_000, 10_000_000),
}
BAND_RANGES_INR = BAND_BASE_RANGES
BAND_ANNUAL_INCREASE: float = 0.03

# ---------------------------------------------------------------------------
# Role family multipliers & weights
# ---------------------------------------------------------------------------
ROLE_FAMILY_MULTIPLIERS: Dict[str, float] = {
    "Engineering": 1.00,
    "Product": 0.95,
    "Design": 0.88,
    "Data & Analytics": 0.92,
    "Finance": 0.90,
    "HR": 0.85,
    "Operations": 0.88,
    "Leadership": 1.05,
}

ROLE_FAMILY_WEIGHTS: Dict[str, float] = {
    "Engineering": 0.40,
    "Product": 0.10,
    "Data & Analytics": 0.15,
    "Design": 0.08,
    "Finance": 0.08,
    "HR": 0.07,
    "Operations": 0.07,
    "Leadership": 0.05,
}

LEVEL_DISTRIBUTION: Dict[str, float] = {
    "L1": 0.15,
    "L2": 0.25,
    "L3": 0.25,
    "L4": 0.15,
    "L5": 0.08,
    "L6": 0.03,
    "M1": 0.05,
    "M2": 0.02,
    "M3": 0.01,
    "M4": 0.01,
}

GENDER_DISTRIBUTION: Dict[str, float] = {
    "M": 0.60,
    "F": 0.35,
    "NB": 0.05,
}

EMPLOYMENT_TYPE_DISTRIBUTION: Dict[str, float] = {
    "FULL_TIME": 0.90,
    "PART_TIME": 0.10,
}

PART_TIME_FTE_RANGE: Tuple[float, float] = (0.50, 0.80)
INDIA_EMP_FRACTION: float = 0.80

PERF_RATING_MEAN: float = 3.2
PERF_RATING_STD: float = 0.75
PERF_RATING_MIN: float = 1.0
PERF_RATING_MAX: float = 5.0
PERF_QUARTERS: List[str] = ["2024-Q2", "2024-Q4", "2025-Q2", "2025-Q4", "2026-Q2"]

MERIT_RANGE: Tuple[float, float] = (0.05, 0.12)
PROMOTION_FRACTION: float = 0.15
PROMO_MIN_MONTHS: int = 18
PROMO_SALARY_ADJ_RANGE: Tuple[float, float] = (0.10, 0.20)

COMPARABLE_GROUP_MIN_SIZE: int = 3
COMPA_RATIO_THRESHOLD: float = 0.85

# ---------------------------------------------------------------------------
# Anomaly injection counts (for Starter scale, scaled up for Full scale)
# ---------------------------------------------------------------------------
ANOMALY_EXPIRED_BAND_INJECT_COUNT: int = 15
ANOMALY_FTE_IGNORED_COUNT: int = 30
ANOMALY_CURRENCY_MISSING_COUNT: int = 20
ANOMALY_UNAPPROVED_ADJUSTMENT_COUNT: int = 25
ANOMALY_INCOMPARABLE_GROUP_COUNT: int = 15

# ---------------------------------------------------------------------------
# Data generation scale presets
# ---------------------------------------------------------------------------
SCALE_CONFIGS: Dict[str, Dict] = {
    "starter": {"num_employees": 500,  "years_history": 3},
    "full":    {"num_employees": 5000, "years_history": 3},
}
SCALE_PRESETS = SCALE_CONFIGS

TENURE_BANDS: List[str] = ["0-12M", "1-3YR", "3-5YR", "5PLUS_YR"]


def get_tenure_band(months: int) -> str:
    """Classify total months of service into the standard tenure band."""
    if months <= 12:
        return "0-12M"
    elif months <= 36:
        return "1-3YR"
    elif months <= 60:
        return "3-5YR"
    else:
        return "5PLUS_YR"


def normalize_to_inr(amount: float, currency: str) -> float:
    """Convert amount from currency to INR using reference FX rates."""
    rate = FX_TO_INR.get(currency, 1.0)
    return round(amount * rate, 2)
