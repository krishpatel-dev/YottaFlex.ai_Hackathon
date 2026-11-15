# ⚖️ Compensation Intelligence & Pay Equity Analytics Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.40+-FF4B4B.svg)](https://streamlit.io/)
[![Tests Passing](https://img.shields.io/badge/tests-52%20passed-brightgreen.svg)](tests/)
[![Code Style](https://img.shields.io/badge/architecture-deterministic%20%26%20explainable-purple.svg)]()

> **Enterprise-grade compensation intelligence, auditable pay equity benchmarking, explainable disparity detection, and dual-approval governance platform built with Python, Streamlit, and SQLAlchemy.**

---

## 📖 Executive Summary & Business Problem

Pay equity is not merely a legal requirement—it is a critical driver of employee trust, retention, and organizational integrity. In modern global enterprises, compensation decision-making is often complicated by:
1. Multi-currency payrolls and fluctuating exchange rates.
2. Full-time vs. part-time (FTE) discrepancies leading to erroneous peer comparisons.
3. Rapidly evolving market benchmark bands that leave legacy salaries evaluated against expired structures.
4. Unclear, opaque compensation adjustments implemented without documented justification or dual-level sign-off.
5. Inappropriate peer groupings that compare non-comparable roles or job families.

This platform provides an **end-to-end, deterministic, and auditable analytics solution** that evaluates point-in-time salaries against current market bands, groups employees into statistically sound peer cohorts, differentiates justified compensation deltas (performance, tenure, promotions) from unexplained pay gaps, and enforces a strict governance approval workflow for all proposed salary adjustments.

---

## ✨ Key Capabilities & Highlights

* **Deterministic, Explainable Logic**: 100% rule-based and auditable; avoids non-deterministic "black-box" machine learning models for compensation decisions.
* **Modern Executive UI/UX**: Designed using high-fidelity Dribbble design principles with dark-slate sidebar navigation, crisp white main container cards, glassmorphic metric panels, and interactive Plotly telemetry.
* **Native Multipage Navigation**: Zero-flicker routing using Streamlit's official `st.navigation()` API with dedicated `0_System_Overview.py` entrypoint.
* **Dual-Approval Governance**: State machine requiring explicit Manager and HR Partner sign-offs before salary adjustments can reach `IMPLEMENTED`.
* **52 Automated Tests (100% Pass Rate)**: Comprehensive pytest test suite covering normalization edge cases, state machine transitions, peer group statistics, disparity detectors, and reporting serialization.
* **Isolated Ground Truth Benchmarking**: 105 systematically injected anomaly records across 5 mandatory negative scenarios, isolated from analytical inputs to ensure unbiased evaluation.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   STREAMLIT INTERACTIVE DASHBOARD                      │
│   Page 0: System Overview & Telemetry · Page 1: Executive Overview      │
│   Page 2: Compensation Analysis · Page 3: Side-by-Side Peer Audit       │
│   Page 4: Disparity & Exceptions · Page 5: Adjustment Proposals        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │  In-Memory Caching & Analytical Engine
┌───────────────────────────────────▼────────────────────────────────────┐
│                       COMPENSATION BUSINESS ENGINE                     │
│   • salary_normalization.py: FX conversion (INR base) & FTE scaling   │
│   • comparable_groups.py: Cohort clustering & statistical medians      │
│   • disparity_detection.py: 6 disparity & exception detection rules    │
│   • adjustment_engine.py: Dual-approval state machine & audit trails  │
│   • compensation.py: Single & batch employee analysis orchestrator    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │  Relational ORM & Data Access
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

## 🛡️ Six Disparity & Compliance Exception Scenarios

The platform continuously audits organizational compensation records across six critical scenarios:

| # | Exception Scenario | Detection Rule & Diagnosis | Expected Business Resolution |
|---|---|---|---|
| 1 | **SALARY_COMPARED_TO_EXPIRED_BAND** | `RULE_EXPIRED_COMPENSATION_BAND`: Salary effective date is evaluated against a band where `expiry_date < effective_date`. | Halt benchmark comparison; re-align against active current-year compensation band. |
| 2 | **FTE_IGNORED** | `RULE_PART_TIME_FTE_NORMALIZATION_MISSING`: Part-time salary compared raw without dividing by `fte_fraction`. | Re-calculate peer comparison using FTE-normalized salary (`salary / FTE`). |
| 3 | **CURRENCY_CONVERSION_MISSING** | `RULE_UNSUPPORTED_CURRENCY_EXCHANGE_RATE`: Salary denominated in an unmapped foreign currency (e.g., `XYZ`). | Freeze comparison; mandate approved treasury exchange rate mapping. |
| 4 | **ADJUSTMENT_WITHOUT_APPROVAL** | `RULE_ADJUSTMENT_LIFECYCLE_GOVERNANCE`: Proposal set to `IMPLEMENTED` while HR Partner approval is missing. | Flag unauthorized payroll change; require formal HR retrospective sign-off. |
| 5 | **INCOMPARABLE_ROLES_GROUPED** | `RULE_PEER_GROUP_HOMOGENEITY`: Employees from disparate role families merged into a single peer group. | Disband merged cohort; re-cluster strictly by validated role family and level. |
| 6 | **UNEXPLAINED_DISPARITY** | `RULE_UNEXPLAINED_PEER_DISPARITY`: Salary deviates by >20% from peer median without supporting performance ratings or recent promotions. | Generate candidate for equity remediation review; route to management. |

---

## 📂 Repository Directory Structure

```text
C:\CandidateWorkspace\
├── .github/
│   └── workflows/
│       └── ci.yml                     # Automated GitHub Actions CI workflow
├── .streamlit/
│   └── config.toml                    # Streamlit theme configuration (custom scoped CSS)
├── dashboard/
│   ├── app.py                         # Native st.navigation router entrypoint
│   ├── data_loader.py                 # Resilient transactional data loading & caching
│   ├── components/
│   │   ├── cards.py                   # Executive KPI cards & metric badge formatters
│   │   ├── charts.py                  # Plotly charts (histograms, boxplots, radar, bars)
│   │   ├── filters.py                 # Sidebar filtering controls
│   │   └── styles.py                  # Centralized CSS & HTML sanitization utilities
│   └── pages/
│       ├── 0_System_Overview.py       # Macro system telemetry, benchmarks & safeguards
│       ├── 1_Executive_Overview.py    # Executive pay parity corridor & distribution
│       ├── 2_Compensation_Analysis.py # Granular role, level, and location benchmarks
│       ├── 3_Employee_Comparison.py   # Multi-employee side-by-side radar & equity audit
│       ├── 4_Disparity_Management.py  # Exception inventory, root cause & investigation
│       └── 5_Adjustment_Proposals.py  # Dual-approval governance review & decision console
├── data/
│   ├── master/                        # Master dimension tables (roles, levels, bands, etc.)
│   ├── transactions/                  # Generated transactional tables (employees, salary, etc.)
│   └── ground_truth/                  # Isolated ground truth anomaly verification dataset
├── documentation/
│   ├── data_dictionary.md             # Complete 12-table column-level schema definitions
│   ├── methodology.md                 # Statistical formulas and equity calculation rules
│   ├── prompt_history.md              # Complete prompt log & human engineering decisions
│   └── validation_summary.md          # Checksums, MD5 verification, and audit reports
├── src/
│   ├── engine/
│   │   ├── adjustment_engine.py       # Governance state machine & salary recommendations
│   │   ├── comparable_groups.py       # Peer cohort clustering & statistical metrics
│   │   ├── compensation.py            # Comprehensive compensation analysis orchestrator
│   │   ├── disparity_detection.py     # 6 disparity & exception detection algorithms
│   │   └── salary_normalization.py    # FX conversion (INR) & FTE scaling logic
│   ├── generator/
│   │   └── generate.py                # Deterministic synthetic data generator
│   ├── models/
│   │   ├── base.py                    # SQLAlchemy declarative base
│   │   ├── entities.py                # 12 relational ORM entity classes
│   │   └── validation.py              # Schema validation and integrity rules
│   └── services/
│       └── reporting.py               # Executive briefing & JSON export services
├── tests/
│   ├── conftest.py                    # Pytest fixtures & environment setup
│   ├── test_adjustment_engine.py      # 20 tests: state machine, governance, recommendations
│   ├── test_comparable_groups.py      # 6 tests: clustering, peer discovery, stats
│   ├── test_compensation_engine.py    # 4 tests: single employee, comparison, batch analysis
│   ├── test_disparity_detection.py    # 7 tests: all 6 disparity scenarios + ground truth
│   ├── test_normalization.py          # 7 tests: currency conversion, FTE, compa-ratio
│   ├── test_reporting.py              # 2 tests: executive briefing & JSON export
│   └── test_validation.py             # 6 tests: data integrity, monotonic bands, checksums
├── requirements.txt                   # Production dependencies
└── README.md                          # Platform documentation
```

---

## ⚡ Getting Started & Quickstart Guide

### 1. Prerequisites
* **Python**: `3.11` to `3.14`
* **Git**: Installed and on system PATH

### 2. Clone and Setup Environment
```bash
# Clone the repository
git clone https://github.com/krishpatel-dev/YottaFlex.ai_Hackathon.git
cd YottaFlex.ai_Hackathon

# Create and activate a virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (cmd):
.\venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Generate or Verify Synthetic Data
The repository includes pre-generated, validated datasets in `data/`. If you wish to regenerate the dataset from scratch:
```bash
# Regenerate full dataset (5,000 employees, 19,846 salary records)
python -m src.generator.generate --seed 20261022 --scale full

# Check bit-for-bit MD5 checksum reproducibility
python -m src.generator.generate --seed 20261022 --scale starter --reproducibility-check
```

### 4. Run the Full Test Suite
Execute all 52 unit and integration tests:
```bash
python -m pytest tests/ -v
```

Output:
```text
======================= 52 passed in 185.49s (0:03:05) ========================
```

### 5. Launch the Streamlit Analytics Dashboard
Run the platform with Streamlit:
```bash
python -m streamlit run dashboard/app.py
```
Open your browser at **`http://localhost:8501`**.

---

## 🧪 Comprehensive Test Coverage (52/52 Passing)

The test suite covers the complete functional footprint across 8 dedicated test modules:

| Test File | Count | Focus Areas |
| :--- | :---: | :--- |
| `tests/test_adjustment_engine.py` | **20** | • State machine valid transitions (`OPEN` → `PENDING_MANAGER` → `PENDING_HR` → `IMPLEMENTED`)<br>• Rejection of unauthorized roles (non-managers / non-HR)<br>• Terminal state immutability (`WITHDRAWN`, `REJECTED`, `IMPLEMENTED`)<br>• Dual-approval governance gate enforcement<br>• Audit trail event recording and per-proposal filtering<br>• Recommended adjustment calculation (minimum adjustments, high-performer midpoint targets, peer-median anchoring, ceiling protection) |
| `tests/test_comparable_groups.py` | **6** | • `build_comparable_groups`: Dynamic cohort clustering respecting `min_group_size`<br>• Resilient empty-dataset handling<br>• `find_comparable_peers`: Target peer group isolation & metadata lookup<br>• Missing/unknown employee fallback<br>• `validate_group_comparability`: Detection of incomparable role family cross-contamination<br>• `compute_group_statistics`: Computation of median, mean, P25, P75, min, and max salaries |
| `tests/test_reporting.py` | **2** | • `generate_executive_briefing`: Macro headcount, compa-ratio distribution, disparity exceptions, and proposal pipeline metrics<br>• `export_summary_json`: Validation of formatted JSON serialization |
| `tests/test_disparity_detection.py` | **7** | • **Scenario 1**: `SALARY_COMPARED_TO_EXPIRED_BAND`<br>• **Scenario 2**: `FTE_IGNORED`<br>• **Scenario 3**: `CURRENCY_CONVERSION_MISSING`<br>• **Scenario 4**: `ADJUSTMENT_WITHOUT_APPROVAL`<br>• **Scenario 5**: `INCOMPARABLE_ROLES_GROUPED`<br>• **Scenario 6**: `UNEXPLAINED_DISPARITY` (statistical peer pay gap detection with performance/promotion explanatory validation)<br>• Ground truth anomaly class isolation verification |
| `tests/test_compensation_engine.py` | **4** | • Single employee compensation analysis<br>• Multi-employee side-by-side comparison<br>• Executive summary KPI metrics<br>• `analyze_all`: Batch employee analysis across cohorts |
| `tests/test_normalization.py` | **7** | • FX conversion (USD/GBP/EUR/SGD to INR) & unsupported currency flagging<br>• Part-time FTE salary normalization & invalid FTE boundary checks<br>• Compa-ratio arithmetic & band position calculation<br>• Active/expired compensation band status validation |
| `tests/test_validation.py` | **6** | • Comprehensive dataset schema & integrity checks<br>• Monotonic band arithmetic (`min < p25 < mid < p75 < max`)<br>• FTE bounds enforcement (`0.1 <= fte <= 1.0`)<br>• Promotion seniority advancement validation<br>• Compa-ratio mathematical verification on clean records<br>• Deterministic reproducibility checksums |

---

## 🎨 UI/UX Design System & Theme Architecture

The user interface follows modern SaaS design standards inspired by leading enterprise Dribbble references:

1. **Native Multipage Router (`st.navigation`)**: Eliminates the white background flash and page title flicker during navigation transitions.
2. **Container-Scoped Form Theming**:
   - **Sidebar**: High-contrast dark slate (`#1E293B`) background, `#0B0F19` input elements, and pure white (`#FFFFFF`) text.
   - **Main Content**: Clean white (`#FFFFFF`) card containers, dark navy typography (`#0F172A`), and subtle border styling (`#E2E8F0`).
3. **Streamlit 1.62+ Standard Compatibility**: All layout components use `width="stretch"` instead of deprecated `use_container_width=True`.
4. **Clean HTML Sanitization**: Built-in regex-based HTML sanitizer (`render_html`) prevents Markdown indentation parser errors from escaping styled HTML into literal code blocks.
5. **Executive Visual Components**:
   - **Glass-Card KPI Displays**: Gradient top indicators, bold primary numbers, and contextual percentage badges.
   - **Parity Corridor Progress Bars**: Visual bar metrics dividing workforce into below-band (<80%), target corridor (80%–120%), and premium (>120%).
   - **Side-by-Side Radar Comparisons**: Plotly polar radar charts contrasting peer compa-ratios, performance ratings, and tenure metrics.
   - **Executive Dossier Cards**: Replace raw JSON dumps with structured, readable key-value dossiers and appraisal event pills.

---

## 📄 Documentation Reference

* **[documentation/data_dictionary.md](documentation/data_dictionary.md)**: Full schema documentation for all 12 relational database tables, data types, nullability, and foreign key relationships.
* **[documentation/methodology.md](documentation/methodology.md)**: Mathematical formulations for FTE normalization, FX conversions, compa-ratio calculations, and peer grouping algorithms.
* **[documentation/prompt_history.md](documentation/prompt_history.md)**: Comprehensive prompt log detailing all user prompts, AI acceleration points, and 13 critical human engineering debugging decisions.
* **[documentation/validation_summary.md](documentation/validation_summary.md)**: Data integrity audit logs, MD5 bit-for-bit reproducibility checksum tables, and validation suite outputs.

---

## ⚖️ Governance & Ethical Compliance Statement

This system adheres to strict ethical and governance principles:
* **No Black-Box Machine Learning**: Compensation adjustments and parity evaluations are calculated using deterministic, transparent, and auditable rules.
* **Dual-Approval Governance Gate**: Salary adjustments cannot be executed without both direct Manager and HR Business Partner approval.
* **Non-Discriminatory Parity Benchmarking**: Peer groups are established strictly on job-relevant parameters (role family, career level, geography, tenure, employment type).
* **Audit Trail Immutability**: All state transitions, approvals, rejections, and comments are permanently recorded in the adjustment proposal audit ledger.

---

## 👥 Authors & Acknowledgments

* **Platform Developed for**: YottaFlex AI Candidate Project & Pay Equity Evaluation.
* **Lead Engineer**: Krish Patel ([krishpatel-dev](https://github.com/krishpatel-dev))
* **Repository**: [YottaFlex.ai_Hackathon](https://github.com/krishpatel-dev/YottaFlex.ai_Hackathon)
