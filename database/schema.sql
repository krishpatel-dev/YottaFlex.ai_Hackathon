-- ============================================================
-- Compensation Intelligence & Pay Equity Analytics Platform
-- Full DDL Schema — PostgreSQL 15+
-- Tables ordered by dependency (no FK forward references)
-- ============================================================

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- fuzzy name searches

-- ============================================================
-- 1. roles
-- ============================================================
CREATE TABLE IF NOT EXISTS roles (
    role_id                     VARCHAR(20)     PRIMARY KEY,
    role_name                   VARCHAR(100)    NOT NULL UNIQUE,
    role_family                 VARCHAR(50)     NOT NULL,
    is_comparable_across_roles  BOOLEAN         NOT NULL DEFAULT FALSE,

    CONSTRAINT chk_role_id_format CHECK (role_id ~ '^ROLE-\d{3}$')
);

COMMENT ON TABLE  roles                             IS 'Catalogue of job roles in the organisation.';
COMMENT ON COLUMN roles.role_id                     IS 'PK in ROLE-NNN format, e.g. ROLE-001';
COMMENT ON COLUMN roles.role_name                   IS 'Human-readable job title';
COMMENT ON COLUMN roles.role_family                 IS 'Functional family: Engineering, Product, Design, …';
COMMENT ON COLUMN roles.is_comparable_across_roles  IS 'TRUE → role participates in cross-role equity comparisons within the same family';

CREATE INDEX IF NOT EXISTS ix_roles_family ON roles (role_family);


-- ============================================================
-- 2. levels
-- ============================================================
CREATE TABLE IF NOT EXISTS levels (
    level_id    VARCHAR(20)     PRIMARY KEY,
    level_code  VARCHAR(10)     NOT NULL UNIQUE,
    level_name  VARCHAR(50)     NOT NULL,
    track       VARCHAR(10)     NOT NULL,
    rank_order  INTEGER         NOT NULL,

    CONSTRAINT chk_level_id_format  CHECK (level_id   ~ '^LVL-\d{3}$'),
    CONSTRAINT chk_level_code       CHECK (level_code ~ '^[LM][1-6]$'),
    CONSTRAINT chk_level_track      CHECK (track IN ('IC', 'MANAGER')),
    CONSTRAINT chk_rank_order       CHECK (rank_order BETWEEN 1 AND 20)
);

COMMENT ON TABLE  levels            IS 'Career levels: IC (L1–L6) and Manager (M1–M4) tracks.';
COMMENT ON COLUMN levels.level_id   IS 'PK in LVL-NNN format, e.g. LVL-003';
COMMENT ON COLUMN levels.level_code IS 'Short code used in band IDs: L1…L6, M1…M4';
COMMENT ON COLUMN levels.track      IS 'IC or MANAGER';
COMMENT ON COLUMN levels.rank_order IS 'Numeric seniority order — higher is more senior';

CREATE INDEX IF NOT EXISTS ix_levels_track ON levels (track);


-- ============================================================
-- 3. locations
-- ============================================================
CREATE TABLE IF NOT EXISTS locations (
    location_id     VARCHAR(20)     PRIMARY KEY,
    city            VARCHAR(100)    NOT NULL,
    state           VARCHAR(100),
    country         VARCHAR(100)    NOT NULL,
    currency_code   VARCHAR(3)      NOT NULL,
    geo_multiplier  DECIMAL(4,3)    NOT NULL DEFAULT 1.000,
    timezone        VARCHAR(50)     NOT NULL,

    CONSTRAINT chk_location_id_format   CHECK (location_id   ~ '^LOC-\d{3}$'),
    CONSTRAINT chk_currency_code_len    CHECK (LENGTH(currency_code) = 3),
    CONSTRAINT chk_geo_multiplier_range CHECK (geo_multiplier BETWEEN 0.100 AND 10.000)
);

COMMENT ON TABLE  locations                 IS 'Office locations with currency and cost-of-living index.';
COMMENT ON COLUMN locations.location_id     IS 'PK in LOC-NNN format, e.g. LOC-001';
COMMENT ON COLUMN locations.geo_multiplier  IS 'Cost-of-living multiplier; 1.000 = Bengaluru baseline';
COMMENT ON COLUMN locations.currency_code   IS 'ISO 4217 three-letter code';


-- ============================================================
-- 4. compensation_bands
-- ============================================================
CREATE TABLE IF NOT EXISTS compensation_bands (
    band_id         VARCHAR(50)     PRIMARY KEY,
    role_id         VARCHAR(20)     NOT NULL REFERENCES roles(role_id),
    level_id        VARCHAR(20)     NOT NULL REFERENCES levels(level_id),
    location_id     VARCHAR(20)     NOT NULL REFERENCES locations(location_id),
    band_min        DECIMAL(14,2)   NOT NULL,
    band_mid        DECIMAL(14,2)   NOT NULL,
    band_max        DECIMAL(14,2)   NOT NULL,
    currency_code   VARCHAR(3)      NOT NULL,
    fiscal_year     INTEGER         NOT NULL,
    effective_date  DATE            NOT NULL,
    expiry_date     DATE,
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_band_min_mid_max     CHECK (band_min <= band_mid AND band_mid <= band_max),
    CONSTRAINT chk_band_min_positive    CHECK (band_min > 0),
    CONSTRAINT chk_band_fiscal_year     CHECK (fiscal_year BETWEEN 2020 AND 2050),
    CONSTRAINT chk_band_expiry_after    CHECK (expiry_date IS NULL OR expiry_date > effective_date)
);

COMMENT ON TABLE  compensation_bands                IS 'Approved salary bands per Role × Level × Location × FY.';
COMMENT ON COLUMN compensation_bands.band_id        IS 'PK — e.g. BAND-SWE-L3-BLR-2026';
COMMENT ON COLUMN compensation_bands.band_mid       IS 'Target / market midpoint salary';
COMMENT ON COLUMN compensation_bands.expiry_date    IS 'NULL = still valid; set when superseded by a newer band';
COMMENT ON COLUMN compensation_bands.is_active      IS 'Quick filter; set to FALSE instead of hard-deleting rows';

CREATE INDEX IF NOT EXISTS ix_band_role_level_loc_year ON compensation_bands (role_id, level_id, location_id, fiscal_year);
CREATE INDEX IF NOT EXISTS ix_band_active              ON compensation_bands (is_active);
CREATE INDEX IF NOT EXISTS ix_band_fiscal_year         ON compensation_bands (fiscal_year);


-- ============================================================
-- 5. employees
-- ============================================================
CREATE TABLE IF NOT EXISTS employees (
    employee_id      VARCHAR(20)     PRIMARY KEY,
    full_name        VARCHAR(200)    NOT NULL,
    gender           VARCHAR(5)      NOT NULL,
    role_id          VARCHAR(20)     NOT NULL REFERENCES roles(role_id),
    level_id         VARCHAR(20)     NOT NULL REFERENCES levels(level_id),
    location_id      VARCHAR(20)     NOT NULL REFERENCES locations(location_id),
    hire_date        DATE            NOT NULL,
    employment_type  VARCHAR(20)     NOT NULL,
    fte_fraction     DECIMAL(3,2)    NOT NULL DEFAULT 1.00,
    status           VARCHAR(20)     NOT NULL DEFAULT 'ACTIVE',
    manager_id       VARCHAR(20)     REFERENCES employees(employee_id),
    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_emp_id_format        CHECK (employee_id  ~ '^EMP-\d{6}$'),
    CONSTRAINT chk_emp_gender           CHECK (gender       IN ('M', 'F', 'NB')),
    CONSTRAINT chk_emp_employment_type  CHECK (employment_type IN ('FULL_TIME', 'PART_TIME')),
    CONSTRAINT chk_emp_fte_fraction     CHECK (fte_fraction BETWEEN 0.10 AND 1.00),
    CONSTRAINT chk_emp_status           CHECK (status IN ('ACTIVE', 'INACTIVE', 'ON_LEAVE')),
    CONSTRAINT chk_emp_no_self_manager  CHECK (manager_id IS NULL OR manager_id <> employee_id)
);

COMMENT ON TABLE  employees                 IS 'Core employee roster.';
COMMENT ON COLUMN employees.employee_id     IS 'PK in EMP-NNNNNN format, e.g. EMP-000001';
COMMENT ON COLUMN employees.fte_fraction    IS '1.00 = full-time; 0.50 = half-time part-time';
COMMENT ON COLUMN employees.manager_id      IS 'Self-referential FK — direct reporting manager';

CREATE INDEX IF NOT EXISTS ix_emp_role_level ON employees (role_id, level_id);
CREATE INDEX IF NOT EXISTS ix_emp_location   ON employees (location_id);
CREATE INDEX IF NOT EXISTS ix_emp_status     ON employees (status);
CREATE INDEX IF NOT EXISTS ix_emp_manager    ON employees (manager_id);


-- ============================================================
-- 6. salary_records
-- ============================================================
CREATE TABLE IF NOT EXISTS salary_records (
    salary_id                   VARCHAR(40)     PRIMARY KEY,
    employee_id                 VARCHAR(20)     NOT NULL REFERENCES employees(employee_id),
    band_id                     VARCHAR(50)     NOT NULL REFERENCES compensation_bands(band_id),
    annual_salary               DECIMAL(14,2)   NOT NULL,
    currency_code               VARCHAR(3)      NOT NULL,
    annual_salary_normalized    DECIMAL(14,2)   NOT NULL,
    annual_salary_fte           DECIMAL(14,2)   NOT NULL,
    effective_date              DATE            NOT NULL,
    end_date                    DATE,
    change_reason               VARCHAR(20)     NOT NULL,
    source                      VARCHAR(10)     NOT NULL DEFAULT 'SYSTEM',
    created_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_sal_annual_positive      CHECK (annual_salary > 0),
    CONSTRAINT chk_sal_normalized_positive  CHECK (annual_salary_normalized > 0),
    CONSTRAINT chk_sal_fte_positive         CHECK (annual_salary_fte > 0),
    CONSTRAINT chk_sal_change_reason        CHECK (change_reason IN ('HIRE','PROMOTION','MERIT','ADJUSTMENT','CORRECTION')),
    CONSTRAINT chk_sal_source               CHECK (source IN ('SYSTEM','MANUAL')),
    CONSTRAINT chk_sal_end_after_effective  CHECK (end_date IS NULL OR end_date > effective_date)
);

COMMENT ON TABLE  salary_records                            IS 'Point-in-time salary history. NULL end_date = current record.';
COMMENT ON COLUMN salary_records.annual_salary_normalized   IS 'Salary converted to INR for cross-location comparisons';
COMMENT ON COLUMN salary_records.annual_salary_fte          IS 'FTE-normalised salary (annual_salary / fte_fraction)';

CREATE INDEX IF NOT EXISTS ix_sal_employee  ON salary_records (employee_id);
CREATE INDEX IF NOT EXISTS ix_sal_effective ON salary_records (effective_date);
CREATE INDEX IF NOT EXISTS ix_sal_active    ON salary_records (end_date);


-- ============================================================
-- 7. performance_evidence
-- ============================================================
CREATE TABLE IF NOT EXISTS performance_evidence (
    perf_id             VARCHAR(40)     PRIMARY KEY,
    employee_id         VARCHAR(20)     NOT NULL REFERENCES employees(employee_id),
    review_period       VARCHAR(20)     NOT NULL,
    rating              DECIMAL(3,1)    NOT NULL,
    rating_label        VARCHAR(10)     NOT NULL,
    documented_factors  TEXT,
    reviewer_id         VARCHAR(20)     NOT NULL REFERENCES employees(employee_id),
    review_date         DATE            NOT NULL,
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_perf_rating_range    CHECK (rating BETWEEN 1.0 AND 5.0),
    CONSTRAINT chk_perf_rating_label    CHECK (rating_label IN ('EXCEEDS','MEETS','BELOW','PIP')),
    CONSTRAINT chk_perf_no_self_review  CHECK (reviewer_id <> employee_id)
);

COMMENT ON TABLE  performance_evidence              IS 'Performance review records; supports 360 and manager reviews.';
COMMENT ON COLUMN performance_evidence.rating       IS 'Numeric rating 1.0 (lowest) to 5.0 (highest)';
COMMENT ON COLUMN performance_evidence.is_active    IS 'FALSE if superseded by a correction review';

CREATE INDEX IF NOT EXISTS ix_perf_employee ON performance_evidence (employee_id);
CREATE INDEX IF NOT EXISTS ix_perf_period   ON performance_evidence (review_period);
CREATE INDEX IF NOT EXISTS ix_perf_active   ON performance_evidence (is_active);


-- ============================================================
-- 8. tenure
-- ============================================================
CREATE TABLE IF NOT EXISTS tenure (
    tenure_id               VARCHAR(40)     PRIMARY KEY,
    employee_id             VARCHAR(20)     NOT NULL UNIQUE REFERENCES employees(employee_id),
    months_in_company       INTEGER         NOT NULL,
    months_in_current_role  INTEGER         NOT NULL,
    tenure_band             VARCHAR(15)     NOT NULL,
    last_calculated_at      DATE            NOT NULL,

    CONSTRAINT chk_tenure_months_company    CHECK (months_in_company >= 0),
    CONSTRAINT chk_tenure_months_role       CHECK (months_in_current_role >= 0),
    CONSTRAINT chk_tenure_role_lte_company  CHECK (months_in_current_role <= months_in_company),
    CONSTRAINT chk_tenure_band              CHECK (tenure_band IN ('0-12M','1-3YR','3-5YR','5PLUS_YR'))
);

COMMENT ON TABLE  tenure                        IS 'Pre-computed tenure snapshot; one row per employee, updated nightly.';
COMMENT ON COLUMN tenure.tenure_band            IS '0-12M | 1-3YR | 3-5YR | 5PLUS_YR';
COMMENT ON COLUMN tenure.last_calculated_at     IS 'Date of most recent recalculation';


-- ============================================================
-- 9. promotions
-- ============================================================
CREATE TABLE IF NOT EXISTS promotions (
    promo_id                VARCHAR(40)     PRIMARY KEY,
    employee_id             VARCHAR(20)     NOT NULL REFERENCES employees(employee_id),
    from_level_id           VARCHAR(20)     NOT NULL REFERENCES levels(level_id),
    to_level_id             VARCHAR(20)     NOT NULL REFERENCES levels(level_id),
    from_role_id            VARCHAR(20)     NOT NULL REFERENCES roles(role_id),
    to_role_id              VARCHAR(20)     NOT NULL REFERENCES roles(role_id),
    effective_date          DATE            NOT NULL,
    approved_by             VARCHAR(20)     NOT NULL REFERENCES employees(employee_id),
    promo_type              VARCHAR(15)     NOT NULL,
    salary_adjustment_pct   DECIMAL(5,2)    NOT NULL,

    CONSTRAINT chk_promo_type               CHECK (promo_type IN ('LEVEL_UP','ROLE_CHANGE','LATERAL')),
    CONSTRAINT chk_promo_salary_pct_range   CHECK (salary_adjustment_pct BETWEEN -50.00 AND 200.00),
    CONSTRAINT chk_promo_no_self_approval   CHECK (approved_by <> employee_id)
);

COMMENT ON TABLE  promotions                        IS 'Promotion events: level changes, role changes, and lateral moves.';
COMMENT ON COLUMN promotions.salary_adjustment_pct  IS 'Percentage salary delta applied at promotion (can be 0 for laterals)';

CREATE INDEX IF NOT EXISTS ix_promo_employee  ON promotions (employee_id);
CREATE INDEX IF NOT EXISTS ix_promo_effective ON promotions (effective_date);


-- ============================================================
-- 10. comparable_groups
-- (must precede adjustment_proposals and disparity_flags)
-- ============================================================
CREATE TABLE IF NOT EXISTS comparable_groups (
    group_id              VARCHAR(40)     PRIMARY KEY,
    role_id               VARCHAR(20)     NOT NULL REFERENCES roles(role_id),
    level_id              VARCHAR(20)     NOT NULL REFERENCES levels(level_id),
    location_id           VARCHAR(20)     NOT NULL REFERENCES locations(location_id),
    tenure_band           VARCHAR(15)     NOT NULL,
    employment_type       VARCHAR(20)     NOT NULL,
    group_size            INTEGER         NOT NULL,
    group_median_salary   DECIMAL(14,2)   NOT NULL,
    group_mean_salary     DECIMAL(14,2)   NOT NULL,
    group_p25             DECIMAL(14,2)   NOT NULL,
    group_p75             DECIMAL(14,2)   NOT NULL,
    created_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_cg_group_size_positive       CHECK (group_size > 0),
    CONSTRAINT chk_cg_p25_lte_median            CHECK (group_p25 <= group_median_salary),
    CONSTRAINT chk_cg_median_lte_p75            CHECK (group_median_salary <= group_p75),
    CONSTRAINT chk_cg_tenure_band               CHECK (tenure_band IN ('0-12M','1-3YR','3-5YR','5PLUS_YR')),
    CONSTRAINT chk_cg_employment_type           CHECK (employment_type IN ('FULL_TIME','PART_TIME'))
);

COMMENT ON TABLE  comparable_groups                 IS 'Pre-computed peer groups for pay equity analysis.';
COMMENT ON COLUMN comparable_groups.group_median_salary IS 'Median annual_salary_normalized (INR) of the group';

CREATE INDEX IF NOT EXISTS ix_cg_role_level_loc ON comparable_groups (role_id, level_id, location_id);


-- ============================================================
-- 11. adjustment_proposals
-- ============================================================
CREATE TABLE IF NOT EXISTS adjustment_proposals (
    proposal_id                 VARCHAR(30)     PRIMARY KEY,
    employee_id                 VARCHAR(20)     NOT NULL REFERENCES employees(employee_id),
    trigger_type                VARCHAR(50)     NOT NULL,
    current_salary              DECIMAL(14,2)   NOT NULL,
    proposed_salary_min         DECIMAL(14,2)   NOT NULL,
    proposed_salary_max         DECIMAL(14,2)   NOT NULL,
    proposed_salary_recommended DECIMAL(14,2)   NOT NULL,
    reason_code                 VARCHAR(50)     NOT NULL,
    evidence_ids                TEXT,
    disparity_pct               DECIMAL(5,2),
    comparable_group_id         VARCHAR(40)     REFERENCES comparable_groups(group_id),
    manager_id                  VARCHAR(20)     NOT NULL REFERENCES employees(employee_id),
    manager_approval            VARCHAR(10)     NOT NULL DEFAULT 'PENDING',
    manager_approval_date       DATE,
    hr_partner_id               VARCHAR(20)     REFERENCES employees(employee_id),
    hr_approval                 VARCHAR(10)     NOT NULL DEFAULT 'PENDING',
    hr_approval_date            DATE,
    final_status                VARCHAR(15)     NOT NULL DEFAULT 'OPEN',
    created_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_adj_id_format            CHECK (proposal_id      ~ '^ADJ-\d{4}-\d{6}$'),
    CONSTRAINT chk_adj_trigger_type         CHECK (trigger_type     IN ('DISPARITY_FLAG','PROMOTION','MARKET_ADJUSTMENT','MANAGER_REQUEST','HR_INITIATIVE')),
    CONSTRAINT chk_adj_proposed_range       CHECK (proposed_salary_min <= proposed_salary_recommended AND proposed_salary_recommended <= proposed_salary_max),
    CONSTRAINT chk_adj_manager_approval     CHECK (manager_approval IN ('PENDING','APPROVED','REJECTED')),
    CONSTRAINT chk_adj_hr_approval          CHECK (hr_approval      IN ('PENDING','APPROVED','REJECTED')),
    CONSTRAINT chk_adj_final_status         CHECK (final_status     IN ('OPEN','APPROVED','REJECTED','IMPLEMENTED','WITHDRAWN'))
);

COMMENT ON TABLE  adjustment_proposals                  IS 'Compensation adjustment workflow; dual-approval (manager + HR).';
COMMENT ON COLUMN adjustment_proposals.evidence_ids     IS 'JSON array of perf_id / flag_id references';
COMMENT ON COLUMN adjustment_proposals.disparity_pct    IS '% gap between current salary and comparable group median';

CREATE INDEX IF NOT EXISTS ix_adj_employee        ON adjustment_proposals (employee_id);
CREATE INDEX IF NOT EXISTS ix_adj_final_status    ON adjustment_proposals (final_status);
CREATE INDEX IF NOT EXISTS ix_adj_manager_approval ON adjustment_proposals (manager_approval);
CREATE INDEX IF NOT EXISTS ix_adj_hr_approval     ON adjustment_proposals (hr_approval);


-- ============================================================
-- 12. disparity_flags
-- ============================================================
CREATE TABLE IF NOT EXISTS disparity_flags (
    flag_id                 VARCHAR(40)     PRIMARY KEY,
    employee_id             VARCHAR(20)     NOT NULL REFERENCES employees(employee_id),
    comparable_group_id     VARCHAR(40)     REFERENCES comparable_groups(group_id),
    issue_type              VARCHAR(30)     NOT NULL,
    severity                VARCHAR(10)     NOT NULL,
    salary_difference       DECIMAL(14,2),
    disparity_pct           DECIMAL(5,2),
    detection_rule          TEXT            NOT NULL,
    detection_timestamp     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    investigation_status    VARCHAR(15)     NOT NULL DEFAULT 'OPEN',
    resolution_notes        TEXT,
    resolved_at             TIMESTAMPTZ,
    expected_response       TEXT,
    actual_response         TEXT,

    CONSTRAINT chk_flag_issue_type          CHECK (issue_type IN (
        'EXPIRED_BAND','FTE_IGNORED','CURRENCY_MISSING',
        'UNAPPROVED_ADJUSTMENT','INCOMPARABLE_GROUP','UNEXPLAINED_DISPARITY'
    )),
    CONSTRAINT chk_flag_severity            CHECK (severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    CONSTRAINT chk_flag_investigation_status CHECK (investigation_status IN ('OPEN','UNDER_REVIEW','RESOLVED','DISMISSED')),
    CONSTRAINT chk_flag_resolved_requires_at CHECK (
        (investigation_status IN ('RESOLVED','DISMISSED') AND resolved_at IS NOT NULL)
        OR investigation_status NOT IN ('RESOLVED','DISMISSED')
    )
);

COMMENT ON TABLE  disparity_flags                       IS 'System-raised pay equity or data quality flags.';
COMMENT ON COLUMN disparity_flags.expected_response     IS 'Ground-truth analyst response for automated evaluation';
COMMENT ON COLUMN disparity_flags.actual_response       IS 'Response captured from analyst or agent during eval run';

CREATE INDEX IF NOT EXISTS ix_flag_employee              ON disparity_flags (employee_id);
CREATE INDEX IF NOT EXISTS ix_flag_severity              ON disparity_flags (severity);
CREATE INDEX IF NOT EXISTS ix_flag_investigation_status  ON disparity_flags (investigation_status);
CREATE INDEX IF NOT EXISTS ix_flag_issue_type            ON disparity_flags (issue_type);
