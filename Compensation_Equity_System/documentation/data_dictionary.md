# 📚 Compensation Intelligence & Pay Equity Analytics Platform — Data Dictionary

This document serves as the comprehensive, authoritative schema and business domain data dictionary for all 12 relational entities in the Compensation Intelligence System.

---

## 1. `roles` (Master Table)
Job roles, titles, and functional families within the enterprise.

| Column | Type | Nullable | Domain / Enum | Description | Validation Rule | Example Value |
|---|---|---|---|---|---|---|
| `role_id` | VARCHAR(20) | No | `ROLE-[0-9]{3}` | Primary Key identifier | Immutable, unique | `ROLE-001` |
| `role_code` | VARCHAR(10) | No | Text code | Abbreviated role code | Unique | `SWE` |
| `role_name` | VARCHAR(100) | No | Text | Full job title | Unique | `Software Engineer` |
| `role_family` | VARCHAR(50) | No | Engineering, Product, Design, Data & Analytics, Finance, HR, Operations, Leadership | Functional job family | Must match supported families | `Engineering` |
| `is_comparable_within_family` | BOOLEAN | No | TRUE / FALSE | Whether peers in this family can be compared across roles | Must be boolean | `TRUE` |

---

## 2. `levels` (Master Table)
Career hierarchy, seniority bands, and progression ranks across IC and Management tracks.

| Column | Type | Nullable | Domain / Enum | Description | Validation Rule | Example Value |
|---|---|---|---|---|---|---|
| `level_id` | VARCHAR(20) | No | `LVL-[0-9]{3}` | Primary Key identifier | Immutable, unique | `LVL-002` |
| `level_code` | VARCHAR(10) | No | L1–L6, M1–M4 | Standardized level code | Unique | `L2` |
| `level_name` | VARCHAR(50) | No | Text | Descriptive career stage | Required | `Mid` |
| `track` | VARCHAR(20) | No | `IC`, `MANAGER` | Career progression track | Restricted enum | `IC` |
| `rank_order` | INTEGER | No | 1 to 10 | Monotonic seniority rank | Positive integer | `2` |

---

## 3. `locations` (Master Table)
Geographic business sites, applicable currencies, and cost-of-living geo-multipliers.

| Column | Type | Nullable | Domain / Enum | Description | Validation Rule | Example Value |
|---|---|---|---|---|---|---|
| `location_id` | VARCHAR(20) | No | `LOC-[0-9]{3}` | Primary Key identifier | Immutable, unique | `LOC-001` |
| `location_code` | VARCHAR(10) | No | IATA/City code | Three-letter city code | Unique | `BLR` |
| `city` | VARCHAR(50) | No | Text | Municipal city name | Required | `Bengaluru` |
| `state` | VARCHAR(50) | Yes | Text | State or province | Optional | `Karnataka` |
| `country` | VARCHAR(50) | No | Text | Country name | Required | `India` |
| `currency_code` | VARCHAR(3) | No | INR, USD, GBP, SGD, AED | Official local payroll currency | ISO 4217 code | `INR` |
| `geo_multiplier` | DECIMAL(4,3) | No | 0.70 to 3.50 | Cost of living benchmark multiplier vs Bengaluru (1.0) | > 0.0 | `1.000` |
| `timezone` | VARCHAR(50) | No | IANA TZ | Standard timezone string | Valid IANA | `Asia/Kolkata` |

---

## 4. `compensation_bands` (Master Table)
Effective-dated annual salary ranges mapped to role, level, location, and fiscal year.

| Column | Type | Nullable | Domain / Enum | Description | Validation Rule | Example Value |
|---|---|---|---|---|---|---|
| `band_id` | VARCHAR(60) | No | `BAND-<ROLE>-<LVL>-<LOC>-<YEAR>` | Primary Key identifier | Immutable, unique | `BAND-SWE-L2-BLR-2026` |
| `role_id` | VARCHAR(20) | No | FK → `roles.role_id` | Target role | Referential integrity | `ROLE-001` |
| `level_id` | VARCHAR(20) | No | FK → `levels.level_id` | Target seniority level | Referential integrity | `LVL-002` |
| `location_id` | VARCHAR(20) | No | FK → `locations.location_id` | Target location | Referential integrity | `LOC-001` |
| `currency_code` | VARCHAR(3) | No | ISO 4217 | Currency of band figures | Matches location | `INR` |
| `band_min` | DECIMAL(14,2) | No | Currency amount | Band minimum entry salary | `band_min < band_mid` | `700000.00` |
| `band_mid` | DECIMAL(14,2) | No | Currency amount | Band market midpoint benchmark | `band_min < band_mid < band_max` | `1000000.00` |
| `band_max` | DECIMAL(14,2) | No | Currency amount | Band upper limit salary | `band_max > band_mid` | `1300000.00` |
| `fiscal_year` | INTEGER | No | 2024, 2025, 2026 | Fiscal planning year | 4-digit year | `2026` |
| `effective_date` | DATE | No | YYYY-MM-DD | Start of band validity | `effective_date < expiry_date` | `2026-01-01` |
| `expiry_date` | DATE | Yes | YYYY-MM-DD | Expiration date of band | Nullable for active | `2026-12-31` |
| `is_active` | BOOLEAN | No | TRUE / FALSE | Whether band is currently active | Required | `TRUE` |

---

## 5. `employees` (Master Table)
Employee core master profile, demographic attributes, organizational hierarchy, and employment status.

| Column | Type | Nullable | Domain / Enum | Description | Validation Rule | Example Value |
|---|---|---|---|---|---|---|
| `employee_id` | VARCHAR(12) | No | `EMP-[0-9]{6}` | Primary Key identifier | Immutable, zero-padded | `EMP-000001` |
| `full_name` | VARCHAR(100) | No | Text | Legal employee name | Required | `Rahul Sharma` |
| `gender` | VARCHAR(10) | No | `M`, `F`, `NB` | Gender classification | Valid enum | `M` |
| `role_id` | VARCHAR(20) | No | FK → `roles.role_id` | Current assigned role | Referential integrity | `ROLE-001` |
| `level_id` | VARCHAR(20) | No | FK → `levels.level_id` | Current seniority level | Referential integrity | `LVL-002` |
| `location_id` | VARCHAR(20) | No | FK → `locations.location_id` | Work location | Referential integrity | `LOC-001` |
| `hire_date` | DATE | No | YYYY-MM-DD | Date joined organization | <= Current Date | `2022-03-15` |
| `employment_type`| VARCHAR(20) | No | `FULL_TIME`, `PART_TIME` | Hours commitment | Valid enum | `FULL_TIME` |
| `fte_fraction` | DECIMAL(3,2) | No | 0.10 to 1.00 | Full-time equivalent decimal | `0.0 < FTE <= 1.0` | `1.00` |
| `status` | VARCHAR(20) | No | `ACTIVE`, `INACTIVE`, `ON_LEAVE` | Employment state | Valid enum | `ACTIVE` |
| `manager_id` | VARCHAR(12) | Yes | FK → `employees.employee_id` | Reports-to manager | Self-referential FK | `EMP-000210` |
| `created_at` | TIMESTAMP | No | ISO 8601 | Record creation timestamp | Auto-generated | `2026-10-22T00:00:00` |

---

## 6. `salary_records` (Transaction Table)
Longitudinal, effective-dated compensation records preserving point-in-time salary snapshots. Never overwritten.

| Column | Type | Nullable | Domain / Enum | Description | Validation Rule | Example Value |
|---|---|---|---|---|---|---|
| `salary_id` | VARCHAR(30) | No | `SAL-<EMP>-<YEAR>-<SEQ>` | Primary Key identifier | Immutable, unique | `SAL-000001-2026-01` |
| `employee_id` | VARCHAR(12) | No | FK → `employees.employee_id` | Target employee | Referential integrity | `EMP-000001` |
| `band_id` | VARCHAR(60) | No | FK → `compensation_bands.band_id` | Benchmark band applied | Referential integrity | `BAND-SWE-L2-BLR-2026` |
| `annual_salary` | DECIMAL(14,2) | No | Currency amount | Raw annual salary in local currency | > 0.0 | `800000.00` |
| `currency_code` | VARCHAR(3) | No | ISO 4217 | Salary currency | Matches location | `INR` |
| `annual_salary_normalized` | DECIMAL(14,2) | No | INR amount | Salary converted to base currency (INR) | Normalized via FX | `800000.00` |
| `annual_salary_fte` | DECIMAL(14,2) | No | INR amount | Normalized salary adjusted for FTE | `salary_norm / FTE` | `800000.00` |
| `effective_date` | DATE | No | YYYY-MM-DD | Start of salary change | `>= hire_date` | `2026-04-01` |
| `end_date` | DATE | Yes | YYYY-MM-DD | End of validity (chained) | Nullable if current | `None` |
| `change_reason` | VARCHAR(30) | No | `HIRE`, `PROMOTION`, `MERIT`, `ADJUSTMENT`, `CORRECTION` | Action trigger | Valid enum | `MERIT` |
| `source` | VARCHAR(20) | No | `SYSTEM`, `MANUAL` | Ingestion origin | Valid enum | `SYSTEM` |
| `compa_ratio` | DECIMAL(6,2) | No | Percentage | Ratio against band midpoint | `fte_salary / band_mid * 100` | `80.00` |
| `created_at` | TIMESTAMP | No | ISO 8601 | Record creation timestamp | Auto-generated | `2026-10-22T00:00:00` |

---

## 7. `performance_evidence` (Transaction Table)
Semi-annual appraisal ratings, performance labels, and qualitative documented achievements.

| Column | Type | Nullable | Domain / Enum | Description | Validation Rule | Example Value |
|---|---|---|---|---|---|---|
| `perf_id` | VARCHAR(30) | No | `PERF-<EMP>-<CYCLE>` | Primary Key identifier | Immutable, unique | `PERF-000001-2025-Q4` |
| `employee_id` | VARCHAR(12) | No | FK → `employees.employee_id` | Assessed employee | Referential integrity | `EMP-000001` |
| `review_period` | VARCHAR(20) | No | `YYYY-Q[1-4]` | Appraisal review cycle | Cycle format | `2025-Q4` |
| `rating` | DECIMAL(3,2) | No | 1.00 to 5.00 | Quantitative appraisal score | `1.0 <= rating <= 5.0` | `4.20` |
| `rating_label` | VARCHAR(20) | No | `EXCEEDS`, `MEETS`, `BELOW`, `PIP` | Qualitative grade | Valid enum | `MEETS` |
| `documented_factors` | TEXT | No | JSON array of strings | Documented achievements/factors | Valid JSON | `["Exceeded revenue OKRs"]` |
| `reviewer_id` | VARCHAR(12) | Yes | FK → `employees.employee_id` | Reviewing manager | Referential integrity | `EMP-000210` |
| `review_date` | DATE | No | YYYY-MM-DD | Evaluation sign-off date | `>= hire_date` | `2025-12-15` |
| `is_active` | BOOLEAN | No | TRUE / FALSE | Active appraisal record | Required | `TRUE` |

---

## 8. `tenure` (Transaction / Snapshot Table)
Continuous service duration, months in current role, and tenure bucket classification.

| Column | Type | Nullable | Domain / Enum | Description | Validation Rule | Example Value |
|---|---|---|---|---|---|---|
| `tenure_id` | VARCHAR(30) | No | `TEN-<EMP>` | Primary Key identifier | Immutable, unique | `TEN-000001` |
| `employee_id` | VARCHAR(12) | No | FK → `employees.employee_id` | Target employee | Unique 1:1 constraint | `EMP-000001` |
| `months_in_company` | INTEGER | No | >= 0 | Total service duration in months | Derived from `hire_date` | `36` |
| `months_in_current_role` | INTEGER | No | >= 0 | Service duration in current level/role | Derived from last promo | `18` |
| `tenure_band` | VARCHAR(20) | No | `0-12M`, `1-3YR`, `3-5YR`, `5PLUS_YR` | Tenure grouping bucket | Valid enum | `1-3YR` |
| `last_calculated_at`| DATE | No | YYYY-MM-DD | Metric computation snapshot | Required | `2026-10-22` |

---

## 9. `promotions` (Transaction Table)
Career progression events recording level/role changes, salary increases, and approval audit.

| Column | Type | Nullable | Domain / Enum | Description | Validation Rule | Example Value |
|---|---|---|---|---|---|---|
| `promo_id` | VARCHAR(30) | No | `PROMO-<EMP>-<YEAR>-<MO>` | Primary Key identifier | Immutable, unique | `PROMO-000001-2025-07` |
| `employee_id` | VARCHAR(12) | No | FK → `employees.employee_id` | Promoted employee | Referential integrity | `EMP-000001` |
| `from_level_id` | VARCHAR(20) | No | FK → `levels.level_id` | Prior level | Referential integrity | `LVL-001` |
| `to_level_id` | VARCHAR(20) | No | FK → `levels.level_id` | Promoted level | `to_rank > from_rank` | `LVL-002` |
| `from_role_id` | VARCHAR(20) | No | FK → `roles.role_id` | Prior role | Referential integrity | `ROLE-001` |
| `to_role_id` | VARCHAR(20) | No | FK → `roles.role_id` | Promoted role | Referential integrity | `ROLE-001` |
| `effective_date` | DATE | No | YYYY-MM-DD | Promotion effective date | `>= hire_date` | `2025-07-01` |
| `approved_by` | VARCHAR(12) | Yes | FK → `employees.employee_id` | Authorizing leader | Referential integrity | `EMP-000210` |
| `promo_type` | VARCHAR(20) | No | `LEVEL_UP`, `ROLE_CHANGE`, `LATERAL` | Promotion category | Valid enum | `LEVEL_UP` |
| `salary_adjustment_pct`| DECIMAL(5,2)| No | Percentage (e.g. 15.00) | Promotional pay raise % | >= 0.0 | `15.00` |

---

## 10. `adjustment_proposals` (Transaction Table)
Proposed salary equity remediations, recommended ranges, and multi-tier approval lifecycle states.

| Column | Type | Nullable | Domain / Enum | Description | Validation Rule | Example Value |
|---|---|---|---|---|---|---|
| `proposal_id` | VARCHAR(30) | No | `ADJ-<YEAR>-<SEQ>` | Primary Key identifier | Immutable, unique | `ADJ-2026-000001` |
| `employee_id` | VARCHAR(12) | No | FK → `employees.employee_id` | Target employee | Referential integrity | `EMP-000001` |
| `trigger_type` | VARCHAR(30) | No | `BELOW_BAND`, `DISPARITY`, `EQUITY_REVIEW` | Action trigger category | Valid enum | `BELOW_BAND` |
| `current_salary` | DECIMAL(14,2) | No | Currency amount | Current annual salary | > 0.0 | `750000.00` |
| `proposed_salary_min`| DECIMAL(14,2)| No | Currency amount | Minimum adjustment floor | `>= current_salary` | `800000.00` |
| `proposed_salary_max`| DECIMAL(14,2)| No | Currency amount | Maximum adjustment ceiling | `>= proposed_min` | `1000000.00` |
| `proposed_salary_recommended` | DECIMAL(14,2)| No | Currency amount | Targeted adjustment figure | Between min and max | `900000.00` |
| `proposed_change_pct` | DECIMAL(5,2)| No | Percentage | Proposed percentage increase | >= 0.0 | `20.00` |
| `reason_code` | VARCHAR(30) | No | Text | Business justification code | Required | `MARKET_EQUITY_ALIGNMENT`|
| `evidence_ids` | TEXT | No | JSON array of strings | Linked performance evidence IDs | Valid JSON | `["PERF-000001-2025-Q4"]`|
| `comparable_group_id` | VARCHAR(40)| Yes | FK → `comparable_groups` | Reference peer group | Nullable | `GRP-ENG-L2-BLR-1-3YR-FT`|
| `manager_id` | VARCHAR(12) | Yes | FK → `employees.employee_id` | Approving manager | Referential integrity | `EMP-000210` |
| `manager_approval` | VARCHAR(20) | No | `PENDING`, `APPROVED`, `REJECTED` | Manager sign-off status | Valid enum | `APPROVED` |
| `manager_approval_date`| DATE | Yes | YYYY-MM-DD | Manager sign-off date | Nullable | `2026-05-10` |
| `hr_partner_id` | VARCHAR(12) | Yes | FK → `employees.employee_id` | Approving HR Partner | Referential integrity | `EMP-000050` |
| `hr_approval` | VARCHAR(20) | No | `PENDING`, `APPROVED`, `REJECTED` | HR Partner sign-off status | Valid enum | `APPROVED` |
| `hr_approval_date` | DATE | Yes | YYYY-MM-DD | HR Partner sign-off date | Nullable | `2026-05-12` |
| `final_status` | VARCHAR(20) | No | `OPEN`, `PENDING_HR`, `IMPLEMENTED`, `REJECTED`, `WITHDRAWN` | Lifecycle state | Enforced by state machine | `IMPLEMENTED` |
| `created_at` | TIMESTAMP | No | ISO 8601 | Proposal generation time | Required | `2026-05-01T10:00:00` |
| `updated_at` | TIMESTAMP | No | ISO 8601 | Last state update timestamp | Required | `2026-05-12T14:30:00` |

---

## 11. `comparable_groups` (Analytical Entity)
Homogeneous peer cohorts sharing role family, level, location, tenure, and employment type.

| Column | Type | Nullable | Domain / Enum | Description | Validation Rule | Example Value |
|---|---|---|---|---|---|---|
| `group_id` | VARCHAR(50) | No | `GRP-<FAM>-<LVL>-<LOC>-<TEN>-<ET>` | Primary Key identifier | Immutable, unique | `GRP-ENG-L2-BLR-1-3YR-FT` |
| `role_family` | VARCHAR(50) | No | Text | Common functional family | Required | `Engineering` |
| `level_code` | VARCHAR(10) | No | L1–L6, M1–M4 | Common seniority level | Required | `L2` |
| `location_code` | VARCHAR(10) | No | BLR, MUM, etc. | Common business site | Required | `BLR` |
| `tenure_band` | VARCHAR(20) | No | 0-12M, 1-3YR, etc. | Common tenure bucket | Required | `1-3YR` |
| `employment_type`| VARCHAR(20) | No | `FULL_TIME`, `PART_TIME` | Common work hours model | Required | `FULL_TIME` |
| `group_size` | INTEGER | No | >= 3 | Count of peers in group | Minimum 3 for anonymity | `15` |
| `group_median_salary` | DECIMAL(14,2) | No | INR amount | Median salary of cohort | > 0.0 | `950000.00` |
| `group_mean_salary` | DECIMAL(14,2) | No | INR amount | Mean salary of cohort | > 0.0 | `962000.00` |
| `group_p25` | DECIMAL(14,2) | No | INR amount | 25th percentile salary | <= median | `880000.00` |
| `group_p75` | DECIMAL(14,2) | No | INR amount | 75th percentile salary | >= median | `1020000.00` |
| `created_at` | TIMESTAMP | No | ISO 8601 | Cohort clustering timestamp | Required | `2026-10-22T00:00:00` |

---

## 12. `disparity_flags` (Analytical / Exception Entity)
Flagged compensation equity exceptions, detection rationales, and investigation states.

| Column | Type | Nullable | Domain / Enum | Description | Validation Rule | Example Value |
|---|---|---|---|---|---|---|
| `flag_id` | VARCHAR(30) | No | `FLAG-[0-9]{6}` | Primary Key identifier | Immutable, unique | `FLAG-000042` |
| `employee_id` | VARCHAR(12) | No | FK → `employees.employee_id` | Flagged employee | Referential integrity | `EMP-000120` |
| `comparable_group_id` | VARCHAR(50)| Yes | FK → `comparable_groups` | Comparable cohort context | Nullable | `GRP-ENG-L2-BLR-1-3YR-FT` |
| `issue_type` | VARCHAR(40) | No | `SALARY_COMPARED_TO_EXPIRED_BAND`, `FTE_IGNORED`, `CURRENCY_CONVERSION_MISSING`, `ADJUSTMENT_WITHOUT_APPROVAL`, `INCOMPARABLE_ROLES_GROUPED`, `UNEXPLAINED_DISPARITY` | Exception classification | Valid enum | `UNEXPLAINED_DISPARITY` |
| `severity` | VARCHAR(10) | No | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` | Business impact level | Valid enum | `HIGH` |
| `salary_difference` | DECIMAL(14,2)| No | Currency amount | Absolute variance from peer median | Signed decimal | `-220000.00` |
| `disparity_pct` | DECIMAL(5,2) | No | Percentage | Percentage variance from benchmark | Signed percentage | `-22.50` |
| `detection_rule` | VARCHAR(100)| No | Text | Rule identifier triggered | Required | `RULE_STATISTICAL_PEER_DISPARITY` |
| `detection_timestamp` | TIMESTAMP | No | ISO 8601 | Detection execution timestamp | Required | `2026-10-22T00:00:00` |
| `investigation_status`| VARCHAR(20) | No | `OPEN`, `UNDER_REVIEW`, `RESOLVED`, `DISMISSED` | Audit resolution stage | Valid enum | `OPEN` |
| `root_cause` | TEXT | No | Text | Plain-language diagnosis | Required | `Compensated 22.5% below median` |
| `supporting_evidence` | TEXT | No | JSON string | Machine-readable evidence | Valid JSON | `{"peer_median": 950000}` |
| `missing_evidence` | TEXT | Yes | Text | Unsubstantiated factors | Optional | `Performance justification` |
| `expected_response` | TEXT | No | Text | Prescribed remediation | Required | `Review compensation` |
| `resolution_notes` | TEXT | Yes | Text | Documented auditor findings | Optional | `Null` |
| `resolved_at` | TIMESTAMP | Yes | ISO 8601 | Timestamp of audit closure | Nullable | `Null` |
