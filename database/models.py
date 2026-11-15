"""
database/models.py
==================
SQLAlchemy 2.0 ORM models for the Compensation Intelligence & Pay Equity Analytics Platform.

All 12 entities are defined here using the declarative style.
Engine and session factory are configured from the DATABASE_URL environment variable.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from dotenv import load_dotenv
from sqlalchemy import (
    DECIMAL,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

load_dotenv()

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql://hr_admin:password@localhost:5432/compensation_equity",
)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Project-wide SQLAlchemy declarative base."""
    pass


# ---------------------------------------------------------------------------
# 1. Role
# ---------------------------------------------------------------------------

class Role(Base):
    """
    Represents a job role within the organisation.

    PK format: ROLE-001
    """

    __tablename__ = "roles"

    role_id: str = Column(String(20), primary_key=True, comment="PK — e.g. ROLE-001")
    role_name: str = Column(String(100), nullable=False, unique=True, comment="Human-readable role title")
    role_family: str = Column(String(50), nullable=False, comment="Functional family — Engineering, Product, …")
    is_comparable_across_roles: bool = Column(
        Boolean, nullable=False, default=False,
        comment="True when this role can be compared across the entire family"
    )

    # Relationships
    compensation_bands: List["CompensationBand"] = relationship("CompensationBand", back_populates="role")
    employees: List["Employee"] = relationship("Employee", back_populates="role")
    comparable_groups: List["ComparableGroup"] = relationship("ComparableGroup", back_populates="role")
    promotions_from: List["Promotion"] = relationship(
        "Promotion", foreign_keys="Promotion.from_role_id", back_populates="from_role"
    )
    promotions_to: List["Promotion"] = relationship(
        "Promotion", foreign_keys="Promotion.to_role_id", back_populates="to_role"
    )

    def __repr__(self) -> str:
        return f"<Role id={self.role_id!r} name={self.role_name!r} family={self.role_family!r}>"


# ---------------------------------------------------------------------------
# 2. Level
# ---------------------------------------------------------------------------

class Level(Base):
    """
    Career level / band (IC and Manager tracks).

    PK format: LVL-001
    Level codes: L1–L6 (IC), M1–M4 (Manager)
    """

    __tablename__ = "levels"

    level_id: str = Column(String(20), primary_key=True, comment="PK — e.g. LVL-001")
    level_code: str = Column(String(10), nullable=False, unique=True, comment="Short code — L1…L6, M1…M4")
    level_name: str = Column(String(50), nullable=False, comment="Descriptive name — Junior, Senior, Director …")
    track: str = Column(String(10), nullable=False, comment="IC or MANAGER")
    rank_order: int = Column(Integer, nullable=False, comment="Numeric sort key for seniority comparisons")

    # Relationships
    compensation_bands: List["CompensationBand"] = relationship("CompensationBand", back_populates="level")
    employees: List["Employee"] = relationship("Employee", back_populates="level")
    comparable_groups: List["ComparableGroup"] = relationship("ComparableGroup", back_populates="level")
    promotions_from: List["Promotion"] = relationship(
        "Promotion", foreign_keys="Promotion.from_level_id", back_populates="from_level"
    )
    promotions_to: List["Promotion"] = relationship(
        "Promotion", foreign_keys="Promotion.to_level_id", back_populates="to_level"
    )

    def __repr__(self) -> str:
        return f"<Level id={self.level_id!r} code={self.level_code!r} track={self.track!r}>"


# ---------------------------------------------------------------------------
# 3. Location
# ---------------------------------------------------------------------------

class Location(Base):
    """
    Physical office location with currency and geo cost-of-living multiplier.

    PK format: LOC-001
    """

    __tablename__ = "locations"

    location_id: str = Column(String(20), primary_key=True, comment="PK — e.g. LOC-001")
    city: str = Column(String(100), nullable=False)
    state: Optional[str] = Column(String(100), nullable=True)
    country: str = Column(String(100), nullable=False)
    currency_code: str = Column(String(3), nullable=False, comment="ISO 4217 currency code")
    geo_multiplier: Decimal = Column(
        DECIMAL(4, 3), nullable=False, default=1.0,
        comment="Cost-of-living multiplier relative to Bengaluru (base = 1.0)"
    )
    timezone: str = Column(String(50), nullable=False, comment="IANA timezone string")

    # Relationships
    compensation_bands: List["CompensationBand"] = relationship("CompensationBand", back_populates="location")
    employees: List["Employee"] = relationship("Employee", back_populates="location")
    comparable_groups: List["ComparableGroup"] = relationship("ComparableGroup", back_populates="location")

    def __repr__(self) -> str:
        return f"<Location id={self.location_id!r} city={self.city!r} currency={self.currency_code!r}>"


# ---------------------------------------------------------------------------
# 4. CompensationBand
# ---------------------------------------------------------------------------

class CompensationBand(Base):
    """
    Approved salary band for a Role × Level × Location combination in a given fiscal year.

    PK format: BAND-SWE-L3-BLR-2026
    """

    __tablename__ = "compensation_bands"
    __table_args__ = (
        Index("ix_band_role_level_loc_year", "role_id", "level_id", "location_id", "fiscal_year"),
        Index("ix_band_active", "is_active"),
    )

    band_id: str = Column(String(50), primary_key=True, comment="PK — e.g. BAND-SWE-L3-BLR-2026")
    role_id: str = Column(String(20), ForeignKey("roles.role_id"), nullable=False)
    level_id: str = Column(String(20), ForeignKey("levels.level_id"), nullable=False)
    location_id: str = Column(String(20), ForeignKey("locations.location_id"), nullable=False)
    band_min: Decimal = Column(DECIMAL(14, 2), nullable=False, comment="Minimum of the salary band")
    band_mid: Decimal = Column(DECIMAL(14, 2), nullable=False, comment="Midpoint / target salary")
    band_max: Decimal = Column(DECIMAL(14, 2), nullable=False, comment="Maximum of the salary band")
    currency_code: str = Column(String(3), nullable=False, comment="ISO 4217 — matches location currency")
    fiscal_year: int = Column(Integer, nullable=False, comment="Fiscal year the band applies to")
    effective_date: date = Column(Date, nullable=False)
    expiry_date: Optional[date] = Column(Date, nullable=True)
    is_active: bool = Column(Boolean, nullable=False, default=True)

    # Relationships
    role: "Role" = relationship("Role", back_populates="compensation_bands")
    level: "Level" = relationship("Level", back_populates="compensation_bands")
    location: "Location" = relationship("Location", back_populates="compensation_bands")
    salary_records: List["SalaryRecord"] = relationship("SalaryRecord", back_populates="band")

    def __repr__(self) -> str:
        return (
            f"<CompensationBand id={self.band_id!r} fy={self.fiscal_year} "
            f"min={self.band_min} max={self.band_max} active={self.is_active}>"
        )


# ---------------------------------------------------------------------------
# 5. Employee
# ---------------------------------------------------------------------------

class Employee(Base):
    """
    Core employee record.

    PK format: EMP-000001
    Self-referential FK on manager_id allows org-hierarchy traversal.
    """

    __tablename__ = "employees"
    __table_args__ = (
        Index("ix_emp_role_level", "role_id", "level_id"),
        Index("ix_emp_location", "location_id"),
        Index("ix_emp_status", "status"),
        Index("ix_emp_manager", "manager_id"),
    )

    employee_id: str = Column(String(20), primary_key=True, comment="PK — e.g. EMP-000001")
    full_name: str = Column(String(200), nullable=False)
    gender: str = Column(String(5), nullable=False, comment="M | F | NB")
    role_id: str = Column(String(20), ForeignKey("roles.role_id"), nullable=False)
    level_id: str = Column(String(20), ForeignKey("levels.level_id"), nullable=False)
    location_id: str = Column(String(20), ForeignKey("locations.location_id"), nullable=False)
    hire_date: date = Column(Date, nullable=False)
    employment_type: str = Column(String(20), nullable=False, comment="FULL_TIME | PART_TIME")
    fte_fraction: Decimal = Column(
        DECIMAL(3, 2), nullable=False, default=Decimal("1.00"),
        comment="FTE fraction — 1.00 for full-time; 0.50 for half-time"
    )
    status: str = Column(String(20), nullable=False, default="ACTIVE", comment="ACTIVE | INACTIVE | ON_LEAVE")
    manager_id: Optional[str] = Column(
        String(20), ForeignKey("employees.employee_id"), nullable=True,
        comment="Self-referential FK to direct manager"
    )
    created_at: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    role: "Role" = relationship("Role", back_populates="employees")
    level: "Level" = relationship("Level", back_populates="employees")
    location: "Location" = relationship("Location", back_populates="employees")
    manager: Optional["Employee"] = relationship("Employee", remote_side="Employee.employee_id", back_populates="direct_reports")
    direct_reports: List["Employee"] = relationship("Employee", back_populates="manager")
    salary_records: List["SalaryRecord"] = relationship("SalaryRecord", back_populates="employee")
    performance_records: List["PerformanceEvidence"] = relationship(
        "PerformanceEvidence", foreign_keys="PerformanceEvidence.employee_id", back_populates="employee"
    )
    reviews_given: List["PerformanceEvidence"] = relationship(
        "PerformanceEvidence", foreign_keys="PerformanceEvidence.reviewer_id", back_populates="reviewer"
    )
    tenure: Optional["Tenure"] = relationship("Tenure", back_populates="employee", uselist=False)
    promotions: List["Promotion"] = relationship(
        "Promotion", foreign_keys="Promotion.employee_id", back_populates="employee"
    )
    promotions_approved: List["Promotion"] = relationship(
        "Promotion", foreign_keys="Promotion.approved_by", back_populates="approver"
    )
    adjustment_proposals: List["AdjustmentProposal"] = relationship(
        "AdjustmentProposal", foreign_keys="AdjustmentProposal.employee_id", back_populates="employee"
    )
    managed_proposals: List["AdjustmentProposal"] = relationship(
        "AdjustmentProposal", foreign_keys="AdjustmentProposal.manager_id", back_populates="manager"
    )
    hr_proposals: List["AdjustmentProposal"] = relationship(
        "AdjustmentProposal", foreign_keys="AdjustmentProposal.hr_partner_id", back_populates="hr_partner"
    )
    disparity_flags: List["DisparityFlag"] = relationship("DisparityFlag", back_populates="employee")

    def __repr__(self) -> str:
        return f"<Employee id={self.employee_id!r} name={self.full_name!r} status={self.status!r}>"


# ---------------------------------------------------------------------------
# 6. SalaryRecord
# ---------------------------------------------------------------------------

class SalaryRecord(Base):
    """
    Point-in-time salary record for an employee.

    PK format: SAL-EMP000001-2026-01
    annual_salary_normalized is always stored in INR for cross-location comparisons.
    annual_salary_fte is the FTE-adjusted equivalent (annual_salary / fte_fraction).
    """

    __tablename__ = "salary_records"
    __table_args__ = (
        Index("ix_sal_employee", "employee_id"),
        Index("ix_sal_effective", "effective_date"),
        Index("ix_sal_active", "end_date"),
    )

    salary_id: str = Column(String(40), primary_key=True, comment="PK — e.g. SAL-EMP000001-2026-01")
    employee_id: str = Column(String(20), ForeignKey("employees.employee_id"), nullable=False)
    band_id: str = Column(String(50), ForeignKey("compensation_bands.band_id"), nullable=False)
    annual_salary: Decimal = Column(DECIMAL(14, 2), nullable=False, comment="Raw salary in local currency")
    currency_code: str = Column(String(3), nullable=False)
    annual_salary_normalized: Decimal = Column(
        DECIMAL(14, 2), nullable=False,
        comment="Salary converted to INR for cross-location comparisons"
    )
    annual_salary_fte: Decimal = Column(
        DECIMAL(14, 2), nullable=False,
        comment="FTE-normalised salary (annual_salary / fte_fraction)"
    )
    effective_date: date = Column(Date, nullable=False)
    end_date: Optional[date] = Column(Date, nullable=True, comment="NULL means this is the current record")
    change_reason: str = Column(
        String(20), nullable=False,
        comment="HIRE | PROMOTION | MERIT | ADJUSTMENT | CORRECTION"
    )
    source: str = Column(String(10), nullable=False, default="SYSTEM", comment="SYSTEM | MANUAL")
    created_at: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    employee: "Employee" = relationship("Employee", back_populates="salary_records")
    band: "CompensationBand" = relationship("CompensationBand", back_populates="salary_records")

    def __repr__(self) -> str:
        return (
            f"<SalaryRecord id={self.salary_id!r} emp={self.employee_id!r} "
            f"salary={self.annual_salary} {self.currency_code} eff={self.effective_date}>"
        )


# ---------------------------------------------------------------------------
# 7. PerformanceEvidence
# ---------------------------------------------------------------------------

class PerformanceEvidence(Base):
    """
    Performance review record for an employee in a given review period.

    PK format: PERF-EMP000001-2025-Q4
    reviewer_id is a self-referential FK to employees (the reviewing manager/peer).
    """

    __tablename__ = "performance_evidence"
    __table_args__ = (
        Index("ix_perf_employee", "employee_id"),
        Index("ix_perf_period", "review_period"),
        Index("ix_perf_active", "is_active"),
    )

    perf_id: str = Column(String(40), primary_key=True, comment="PK — e.g. PERF-EMP000001-2025-Q4")
    employee_id: str = Column(String(20), ForeignKey("employees.employee_id"), nullable=False)
    review_period: str = Column(String(20), nullable=False, comment="e.g. 2025-Q4 or 2025-H1")
    rating: Decimal = Column(DECIMAL(3, 1), nullable=False, comment="Numeric rating 1.0–5.0")
    rating_label: str = Column(
        String(10), nullable=False,
        comment="EXCEEDS | MEETS | BELOW | PIP"
    )
    documented_factors: Optional[str] = Column(
        Text, nullable=True,
        comment="Free-text justification / structured JSON of contributing factors"
    )
    reviewer_id: str = Column(
        String(20), ForeignKey("employees.employee_id"), nullable=False,
        comment="Employee who authored this review"
    )
    review_date: date = Column(Date, nullable=False)
    is_active: bool = Column(Boolean, nullable=False, default=True, comment="False if superseded / corrected")

    # Relationships
    employee: "Employee" = relationship(
        "Employee", foreign_keys=[employee_id], back_populates="performance_records"
    )
    reviewer: "Employee" = relationship(
        "Employee", foreign_keys=[reviewer_id], back_populates="reviews_given"
    )

    def __repr__(self) -> str:
        return (
            f"<PerformanceEvidence id={self.perf_id!r} emp={self.employee_id!r} "
            f"period={self.review_period!r} rating={self.rating} label={self.rating_label!r}>"
        )


# ---------------------------------------------------------------------------
# 8. Tenure
# ---------------------------------------------------------------------------

class Tenure(Base):
    """
    Pre-computed tenure snapshot for an employee (recalculated nightly or on demand).

    PK: tenure_id (UUID-style or generated string)
    employee_id is UNIQUE — one row per employee, updated in place.
    """

    __tablename__ = "tenure"

    tenure_id: str = Column(String(40), primary_key=True)
    employee_id: str = Column(
        String(20), ForeignKey("employees.employee_id"), nullable=False, unique=True
    )
    months_in_company: int = Column(Integer, nullable=False)
    months_in_current_role: int = Column(Integer, nullable=False)
    tenure_band: str = Column(
        String(15), nullable=False,
        comment="0-12M | 1-3YR | 3-5YR | 5PLUS_YR"
    )
    last_calculated_at: date = Column(Date, nullable=False)

    # Relationships
    employee: "Employee" = relationship("Employee", back_populates="tenure")

    def __repr__(self) -> str:
        return (
            f"<Tenure emp={self.employee_id!r} months_company={self.months_in_company} "
            f"band={self.tenure_band!r}>"
        )


# ---------------------------------------------------------------------------
# 9. Promotion
# ---------------------------------------------------------------------------

class Promotion(Base):
    """
    Records a promotion event: level change, role change, or lateral move.

    PK format: PROMO-EMP000001-2025-07
    """

    __tablename__ = "promotions"
    __table_args__ = (
        Index("ix_promo_employee", "employee_id"),
        Index("ix_promo_effective", "effective_date"),
    )

    promo_id: str = Column(String(40), primary_key=True, comment="PK — e.g. PROMO-EMP000001-2025-07")
    employee_id: str = Column(String(20), ForeignKey("employees.employee_id"), nullable=False)
    from_level_id: str = Column(String(20), ForeignKey("levels.level_id"), nullable=False)
    to_level_id: str = Column(String(20), ForeignKey("levels.level_id"), nullable=False)
    from_role_id: str = Column(String(20), ForeignKey("roles.role_id"), nullable=False)
    to_role_id: str = Column(String(20), ForeignKey("roles.role_id"), nullable=False)
    effective_date: date = Column(Date, nullable=False)
    approved_by: str = Column(
        String(20), ForeignKey("employees.employee_id"), nullable=False,
        comment="Manager / HR who approved the promotion"
    )
    promo_type: str = Column(
        String(15), nullable=False,
        comment="LEVEL_UP | ROLE_CHANGE | LATERAL"
    )
    salary_adjustment_pct: Decimal = Column(
        DECIMAL(5, 2), nullable=False,
        comment="Percentage salary change applied at the time of promotion"
    )

    # Relationships
    employee: "Employee" = relationship("Employee", foreign_keys=[employee_id], back_populates="promotions")
    approver: "Employee" = relationship("Employee", foreign_keys=[approved_by], back_populates="promotions_approved")
    from_level: "Level" = relationship("Level", foreign_keys=[from_level_id], back_populates="promotions_from")
    to_level: "Level" = relationship("Level", foreign_keys=[to_level_id], back_populates="promotions_to")
    from_role: "Role" = relationship("Role", foreign_keys=[from_role_id], back_populates="promotions_from")
    to_role: "Role" = relationship("Role", foreign_keys=[to_role_id], back_populates="promotions_to")

    def __repr__(self) -> str:
        return (
            f"<Promotion id={self.promo_id!r} emp={self.employee_id!r} type={self.promo_type!r} "
            f"eff={self.effective_date}>"
        )


# ---------------------------------------------------------------------------
# 10. AdjustmentProposal
# ---------------------------------------------------------------------------

class AdjustmentProposal(Base):
    """
    Compensation adjustment workflow record — from trigger through dual-approval to implementation.

    PK format: ADJ-2026-000001
    evidence_ids stores a JSON array of perf_id / flag_id references.
    """

    __tablename__ = "adjustment_proposals"
    __table_args__ = (
        Index("ix_adj_employee", "employee_id"),
        Index("ix_adj_final_status", "final_status"),
        Index("ix_adj_manager_approval", "manager_approval"),
        Index("ix_adj_hr_approval", "hr_approval"),
    )

    proposal_id: str = Column(String(30), primary_key=True, comment="PK — e.g. ADJ-2026-000001")
    employee_id: str = Column(String(20), ForeignKey("employees.employee_id"), nullable=False)
    trigger_type: str = Column(
        String(50), nullable=False,
        comment="DISPARITY_FLAG | PROMOTION | MARKET_ADJUSTMENT | MANAGER_REQUEST | HR_INITIATIVE"
    )
    current_salary: Decimal = Column(DECIMAL(14, 2), nullable=False)
    proposed_salary_min: Decimal = Column(DECIMAL(14, 2), nullable=False)
    proposed_salary_max: Decimal = Column(DECIMAL(14, 2), nullable=False)
    proposed_salary_recommended: Decimal = Column(DECIMAL(14, 2), nullable=False)
    reason_code: str = Column(String(50), nullable=False)
    evidence_ids: Optional[str] = Column(
        Text, nullable=True,
        comment="JSON array of perf_id / flag_id references"
    )
    disparity_pct: Decimal = Column(
        DECIMAL(5, 2), nullable=True,
        comment="% gap between current salary and comparable group median"
    )
    comparable_group_id: Optional[str] = Column(
        String(40), ForeignKey("comparable_groups.group_id"), nullable=True
    )
    manager_id: str = Column(String(20), ForeignKey("employees.employee_id"), nullable=False)
    manager_approval: str = Column(String(10), nullable=False, default="PENDING", comment="PENDING | APPROVED | REJECTED")
    manager_approval_date: Optional[date] = Column(Date, nullable=True)
    hr_partner_id: Optional[str] = Column(String(20), ForeignKey("employees.employee_id"), nullable=True)
    hr_approval: str = Column(String(10), nullable=False, default="PENDING", comment="PENDING | APPROVED | REJECTED")
    hr_approval_date: Optional[date] = Column(Date, nullable=True)
    final_status: str = Column(
        String(15), nullable=False, default="OPEN",
        comment="OPEN | APPROVED | REJECTED | IMPLEMENTED | WITHDRAWN"
    )
    created_at: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: datetime = Column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    employee: "Employee" = relationship("Employee", foreign_keys=[employee_id], back_populates="adjustment_proposals")
    manager: "Employee" = relationship("Employee", foreign_keys=[manager_id], back_populates="managed_proposals")
    hr_partner: Optional["Employee"] = relationship("Employee", foreign_keys=[hr_partner_id], back_populates="hr_proposals")
    comparable_group: Optional["ComparableGroup"] = relationship("ComparableGroup", back_populates="adjustment_proposals")

    def __repr__(self) -> str:
        return (
            f"<AdjustmentProposal id={self.proposal_id!r} emp={self.employee_id!r} "
            f"status={self.final_status!r}>"
        )


# ---------------------------------------------------------------------------
# 11. ComparableGroup
# ---------------------------------------------------------------------------

class ComparableGroup(Base):
    """
    Pre-computed peer group for pay equity analysis.

    Groups are defined by Role × Level × Location × TenureBand × EmploymentType.
    Statistical summaries are refreshed on each data generation run.
    """

    __tablename__ = "comparable_groups"
    __table_args__ = (
        Index("ix_cg_role_level_loc", "role_id", "level_id", "location_id"),
    )

    group_id: str = Column(String(40), primary_key=True)
    role_id: str = Column(String(20), ForeignKey("roles.role_id"), nullable=False)
    level_id: str = Column(String(20), ForeignKey("levels.level_id"), nullable=False)
    location_id: str = Column(String(20), ForeignKey("locations.location_id"), nullable=False)
    tenure_band: str = Column(String(15), nullable=False)
    employment_type: str = Column(String(20), nullable=False)
    group_size: int = Column(Integer, nullable=False)
    group_median_salary: Decimal = Column(DECIMAL(14, 2), nullable=False)
    group_mean_salary: Decimal = Column(DECIMAL(14, 2), nullable=False)
    group_p25: Decimal = Column(DECIMAL(14, 2), nullable=False)
    group_p75: Decimal = Column(DECIMAL(14, 2), nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    role: "Role" = relationship("Role", back_populates="comparable_groups")
    level: "Level" = relationship("Level", back_populates="comparable_groups")
    location: "Location" = relationship("Location", back_populates="comparable_groups")
    adjustment_proposals: List["AdjustmentProposal"] = relationship(
        "AdjustmentProposal", back_populates="comparable_group"
    )
    disparity_flags: List["DisparityFlag"] = relationship("DisparityFlag", back_populates="comparable_group")

    def __repr__(self) -> str:
        return (
            f"<ComparableGroup id={self.group_id!r} role={self.role_id!r} "
            f"level={self.level_id!r} loc={self.location_id!r} n={self.group_size}>"
        )


# ---------------------------------------------------------------------------
# 12. DisparityFlag
# ---------------------------------------------------------------------------

class DisparityFlag(Base):
    """
    System-generated data quality or pay equity flag.

    Flags are raised by detection rules and require investigation.
    expected_response / actual_response support automated evaluation of analyst responses.
    """

    __tablename__ = "disparity_flags"
    __table_args__ = (
        Index("ix_flag_employee", "employee_id"),
        Index("ix_flag_severity", "severity"),
        Index("ix_flag_investigation_status", "investigation_status"),
        Index("ix_flag_issue_type", "issue_type"),
    )

    flag_id: str = Column(String(40), primary_key=True)
    employee_id: str = Column(String(20), ForeignKey("employees.employee_id"), nullable=False)
    comparable_group_id: Optional[str] = Column(
        String(40), ForeignKey("comparable_groups.group_id"), nullable=True
    )
    issue_type: str = Column(
        String(30), nullable=False,
        comment=(
            "EXPIRED_BAND | FTE_IGNORED | CURRENCY_MISSING | "
            "UNAPPROVED_ADJUSTMENT | INCOMPARABLE_GROUP | UNEXPLAINED_DISPARITY"
        )
    )
    severity: str = Column(String(10), nullable=False, comment="LOW | MEDIUM | HIGH | CRITICAL")
    salary_difference: Optional[Decimal] = Column(
        DECIMAL(14, 2), nullable=True,
        comment="Absolute INR difference from comparable group median"
    )
    disparity_pct: Optional[Decimal] = Column(
        DECIMAL(5, 2), nullable=True,
        comment="Percentage gap from comparable group median"
    )
    detection_rule: str = Column(Text, nullable=False, comment="Human-readable rule that raised this flag")
    detection_timestamp: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    investigation_status: str = Column(
        String(15), nullable=False, default="OPEN",
        comment="OPEN | UNDER_REVIEW | RESOLVED | DISMISSED"
    )
    resolution_notes: Optional[str] = Column(Text, nullable=True)
    resolved_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    expected_response: Optional[str] = Column(Text, nullable=True, comment="Ground-truth analyst response for eval")
    actual_response: Optional[str] = Column(Text, nullable=True, comment="Analyst or agent response recorded during eval")

    # Relationships
    employee: "Employee" = relationship("Employee", back_populates="disparity_flags")
    comparable_group: Optional["ComparableGroup"] = relationship("ComparableGroup", back_populates="disparity_flags")

    def __repr__(self) -> str:
        return (
            f"<DisparityFlag id={self.flag_id!r} emp={self.employee_id!r} "
            f"type={self.issue_type!r} severity={self.severity!r} status={self.investigation_status!r}>"
        )


# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------

def get_engine(database_url: str = DATABASE_URL):
    """
    Create and return a SQLAlchemy engine.

    Args:
        database_url: PostgreSQL DSN. Defaults to DATABASE_URL env var.

    Returns:
        sqlalchemy.Engine
    """
    return create_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True,
        echo=os.environ.get("LOG_LEVEL", "INFO").upper() == "DEBUG",
    )


def get_session_factory(engine=None):
    """
    Return a sessionmaker bound to *engine*.

    Args:
        engine: SQLAlchemy engine. If None, one is created from DATABASE_URL.

    Returns:
        sessionmaker factory
    """
    if engine is None:
        engine = get_engine()
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_all_tables(engine=None) -> None:
    """Create all tables in the database (idempotent — skips existing tables)."""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)
