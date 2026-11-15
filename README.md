# ⚖️ Compensation Intelligence & Pay Equity Analytics Platform

> **Auditable Pay Equity Benchmarking, Unexplained Disparity Detection, and Evidence-Based Salary Adjustment Governance**

---

## 📖 Executive Summary & Business Objective

This platform compares employee compensation against role family, career level, geographic business location, full-time equivalent (FTE) working hours, and documented job-related factors (performance ratings, achievements, tenure, and career promotions) to identify potentially unexplained salary disparities.

### Key Business Capabilities:
1. **Longitudinal Compensation History**: Tracks 3-year point-in-time salary progression across 5,000 employees without overwriting historical records.
2. **Deterministic Parity Normalization**: Normalizes disparate payroll currencies to base currency (INR) and part-time hours to Full-Time Equivalent (FTE).
3. **Peer Group Benchmarking**: Clustered into 589 homogeneous comparable groups (role family, level, location, tenure, employment type).
4. **Explainable Disparity Detection**: Differentiates justified compensation differences (e.g., high performance, promotions) from unexplained pay gaps and policy violations.
5. **Auditable Governance Workflow**: Generates evidence-backed salary adjustment proposals with dual-tier manager and HR Partner authorization controls.
6. **Isolated Ground Truth**: Maintains 105 labeled anomalies across 5 mandatory negative scenarios strictly isolated from analytical inputs.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   STREAMLIT INTERACTIVE DASHBOARD                      │
│   Page 1: Executive Overview · Page 2: Compensation Benchmarking        │
│   Page 3: Peer Audit · Page 4: Exception Mgmt · Page 5: Proposals      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │  In-memory & CSV Data Engine
┌───────────────────────────────────▼────────────────────────────────────┐
│                       COMPENSATION BUSINESS ENGINE                     │
│   • salary_normalization.py: Currency FX conversion, FTE scaling       │
│   • comparable_groups.py: Homogeneous clustering & statistical medians │
│   • disparity_detection.py: 5 negative exceptions & equity gap rules   │
│   • adjustment_engine.py: Lifecycle state machine & proposal audits    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │  Relational Mapping / Alembic
┌───────────────────────────────────▼────────────────────────────────────┐
│                    RELATIONAL DATABASE ARCHITECTURE                    │
│   PostgreSQL 16 / SQLAlchemy 2.0 ORM (12 Fully Normalized Tables)     │
│   roles · levels · locations · compensation_bands · employees          │
│   salary_records · performance_evidence · tenure · promotions          │
│   comparable_groups · adjustment_proposals · disparity_flags           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │  Deterministic Seeding (20261022)
┌───────────────────────────────────▼────────────────────────────────────┐
│                    SYNTHETIC DATA GENERATION ENGINE                    │
│   5,000 Employees · 8,190 Bands · 19,846 Salary Records · 75,000 Appr. │
│   100% Bit-for-bit Checksum Reproducibility Across Consecutive Runs    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ The Five Mandatory Negative Exception Scenarios

The system continuously audits and isolates five critical compliance exceptions:

| # | Exception Scenario | Detection Rule & Diagnosis | Expected Business Response |
|---|---|---|---|
| 1 | **SALARY_COMPARED_TO_EXPIRED_BAND** | `RULE_EXPIRED_COMPENSATION_BAND`: Salary effective date exceeds the benchmark band's `expiry_date`. | Halt benchmark; re-align against active current-year compensation band. |
| 2 | **FTE_IGNORED** | `RULE_PART_TIME_FTE_NORMALIZATION_MISSING`: Part-time salary compared raw without dividing by `fte_fraction`. | Re-calculate peer comparison using full-time equivalent salary (`salary / FTE`). |
| 3 | **CURRENCY_CONVERSION_MISSING** | `RULE_UNSUPPORTED_CURRENCY_EXCHANGE_RATE`: Salary denominated in an unmapped foreign currency (e.g. `XYZ`). | Freeze comparison; mandate approved treasury exchange rate mapping. |
| 4 | **ADJUSTMENT_WITHOUT_APPROVAL** | `RULE_ADJUSTMENT_LIFECYCLE_GOVERNANCE`: Proposal set to `IMPLEMENTED` while HR Partner approval is missing. | Flag unauthorized payroll change; require formal HR retrospective sign-off. |
| 5 | **INCOMPARABLE_ROLES_GROUPED** | `RULE_PEER_GROUP_HOMOGENEITY`: Employees from disparate role families merged into a single peer group. | Disband merged cohort; re-cluster strictly by validated role family and level. |

---

## ⚡ Quickstart & Installation

### 1. Prerequisites
- **Python**: 3.11+
- **Git**
- Optional: PostgreSQL 15+ (for database persistence mode; Streamlit runs directly against generated relational CSVs with zero setup).

### 2. Environment Setup
```bash
# Clone the repository and enter directory
cd c:\CandidateWorkspace

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Generate the Dataset
Execute the deterministic data generator using fixed seed `20261022`:
```bash
# Generate the full production dataset (5,000 employees, 3-year history)
python -m src.generator.generate --seed 20261022 --scale full

# Or generate starter dataset (500 employees for rapid testing)
python -m src.generator.generate --seed 20261022 --scale starter
```

### 4. Run the Automated Test Suite
Execute the full pytest suite (covering normalization, disparity detection, integrity, and reproducibility):
```bash
# Run all tests directly
python -m pytest tests/ -v
```

### 5. Launch the Streamlit Analytics Platform
```bash
python -m streamlit run dashboard/app.py
```
Open your browser at `http://localhost:8501`.

---

## 🖥️ Interactive Dashboard Walkthrough

### 📊 Page 1: Executive Overview
- Organization-wide headcount, average compa-ratio (100.0% market midpoint target), and band penetration counts.
- Salary distribution histograms with median overlays.
- Compa-ratio distribution across underpaid (<80%), target (80%–120%), and premium (>120%) corridors.
- Real-time exception audit feed showing the latest compliance flags.

### 📈 Page 2: Compensation Analysis
- Multi-dimensional filtering by Role Family, Career Level (L1–L6, M1–M4), Business Location (13 cities), and Employment Type.
- Salary progression by level with min/mid/max band overlay.
- Out-of-band exception table identifying all employees outside the 80%–120% corridor.

### 👥 Page 3: Side-by-Side Employee Comparison
- Select 2 to 4 employees for side-by-side equity auditing.
- Multi-dimensional radar chart comparing Compa-Ratio, Performance, Band Penetration, and Tenure.
- Automated Comparability & Justification Engine: tests whether pay deltas are justified by documented performance ratings (e.g. >=4.5), promotion histories, or longer service tenure.

### 🚨 Page 4: Disparity & Exception Management
- Comprehensive inventory of all 6 exception categories.
- Filter by Severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and Investigation State (`OPEN`, `UNDER_REVIEW`, `RESOLVED`, `DISMISSED`).
- Deep-dive inspection modal displaying full JSON evidence payload.
- Investigation workflow allowing auditors to record notes and advance resolution states.

### 📑 Page 5: Salary Adjustment Proposals
- Governance pipeline funnel tracking proposals from generation to implementation.
- Dual-tier approval workflow enforcing managerial and HR Partner sign-offs.
- Role-based authorization actions (`MANAGER`, `HR_PARTNER`, `ADMIN`) with audit logging.

---

## 📊 Relational Database Schema (12 Entities)

Full schema documentation and column-level definitions are available in [`documentation/data_dictionary.md`](documentation/data_dictionary.md).

```
1.  roles:               Job family classifications and cross-role comparability flags
2.  levels:              Career progression levels (IC: L1–L6, Manager: M1–M4)
3.  locations:           10 Indian cities + 3 International sites with FX and geo-multipliers
4.  compensation_bands:  Effective-dated min/mid/max salary ranges by fiscal year (2024–2026)
5.  employees:           Master profiles, demographic distributions, and reporting hierarchy
6.  salary_records:      Historical point-in-time salary snapshots with currency & FTE
7.  performance_evidence: Semi-annual appraisal ratings (1.0–5.0) and documented achievements
8.  tenure:              Total company service and role tenure bucket classifications
9.  promotions:          Career progression events, salary adjustment %, and approvals
10. comparable_groups:   Homogeneous clusters sharing role family, level, location, and tenure
11. adjustment_proposals: Recommended salary adjustments with approval lifecycle tracking
12. disparity_flags:     Auditable equity exceptions with detection rules and root causes
```

---

## 🔬 Deterministic Reproducibility

Every dataset generation execution is strictly deterministic:
```bash
python src/generator/generate.py --seed 20261022 --scale starter --reproducibility-check
```
Both test runs produce **100% bit-for-bit identical MD5 file checksums** across all generated CSV tables.
See [`documentation/validation_summary.md`](documentation/validation_summary.md) for the full MD5 verification table.
