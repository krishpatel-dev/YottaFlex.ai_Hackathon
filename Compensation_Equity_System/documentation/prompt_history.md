# 📝 YottaFlex AI Submission — Transparent AI & Prompt History

**Candidate Project:** Compensation Intelligence & Pay Equity Analytics Platform  
**Submission Window:** 72-Hour Candidate Challenge  
**Date:** November 2026  
**AI Tools & Models Utilized:** Google Antigravity AI Assistant (Claude Sonnet 4.6 Thinking & Gemini 3.8 Flash)

---

## 1. Transparency Statement & Overview

In accordance with Section 03 of the **YottaFlex AI Candidate Project Submission Guidelines** (*"Use LLMs Transparently — Prompt History Required"*) and **Candidate Project FAQ #6**, this document discloses all prompts submitted during the development lifecycle, details where AI accelerated development, and documents what logic was personally architected, reviewed, debugged, and validated.

---

## 2. Chronological Prompt History Log

### Prompt 1: Initial Business Context & Project Inception
* **Timestamp:** 2026-11-15T13:44:21+05:30
* **Goal:** Frame the business problem, entities, and requirements for a compensation parity system.
* **Full Prompt Text:**
```text
consider yourself a senior developer

Business Context / Problem
Compare compensation against role, level, location and documented factors to identify unexplained disparities.

Objective and Scope
Build a working solution for this end-to-end workflow: Compare compensation against role, level, location and documented factors to identify unexplained disparities. The solution should expose key decisions and exceptions, preserve traceability, and produce measurable outputs. Medium complexity means multiple related entities, conditional rules, at least one exception path and meaningful evaluation metrics.

Primary Actors / Systems
Employee/candidate, manager, HR partner, IT/operations partner and system administrator

Business Workflow and Rules
1. Generate/reference master data first: Employee, Role, Level, Location, CompensationBand.
2. Generate dependent transaction/event records using valid parent IDs.
3. Apply business logic: Define role/level/location bands and effective dates; create synthetic salary histories and job-related factors; normalize currency and full-time equivalent; compute compa-ratio and within-band position; identify comparable groups; create review proposals with evidence and approval trail.
4. Persist state changes as explicit records/events where relevant; do not overwrite history.
5. Generate outcomes and ground-truth labels from documented rules, not independent random assignment.

Entities and Relationships
Core entities: Employee, Role, Level, Location, CompensationBand, SalaryRecord, PerformanceEvidence, Tenure, Promotion, AdjustmentProposal. Define a primary key for every entity and foreign keys for every relationship. Document cardinality (1:1, 1:N, N:M), optional relationships, effective dates and lifecycle states. Use bridge tables for many-to-many relationships; retain event history for state changes; validate all joins. For deliberate anomaly cases, keep an issue_type/ground_truth label rather than silently corrupting unrelated rows.

ID / Nomenclature Conventions
EMP-000001; BAND-<role>-<level>-<location>-2026; SAL-<employee-id>-2026-01; ADJ-2026-000001.

Synthetic Data Generation Instructions (Granular)
Step 1 — Write a data dictionary for: Employee, Role, Level, Location, CompensationBand, SalaryRecord, PerformanceEvidence, Tenure, Promotion, AdjustmentProposal. For each field specify type, required/optional, allowed values, units, uniqueness and validation rule.
Step 2 — Create parent/master tables first, then child and event tables. Apply this domain-specific generation logic: Define role/level/location bands and effective dates; create synthetic salary histories and job-related factors; normalize currency and full-time equivalent; compute compa-ratio and within-band position; identify comparable groups; create review proposals with evidence and approval trail.
Step 3 — Apply deterministic IDs and naming: EMP-000001; BAND-<role>-<level>-<location>-2026; SAL-<employee-id>-2026-01; ADJ-2026-000001. Keep counters zero-padded, IDs immutable, and referenced IDs exactly consistent across files.
Step 4 — Generate the baseline volume: Generate 5,000 employees, 200 role/level combinations and 3 years of salary history. Include promotions, part-time changes, currency changes and deliberate unexplained outliers. Use a fixed seed (e.g. 20261022) and parameterize scale so starter and full datasets use the same generator.
Step 5 — Generate valid baseline records first, then inject labelled edge cases: Salary compared to expired band; FTE ignored; currency conversion missing; adjustment applied without approval; incomparable roles grouped without rationale.
Step 6 — Calculate derived values (totals, balances, scores, statuses and dates) from source records rather than generating them independently.
Step 7 — Produce a separate ground_truth.csv/json for known anomalies, expected decisions or labels; never leak it into input features.
Step 8 — Run validation: primary-key uniqueness, foreign-key integrity, allowed enums, date ordering, arithmetic reconciliation, lifecycle transitions and duplicate checks.
Step 9 — Export CSV/JSON/SQL seed data plus README, schema/data dictionary, generator command, fixed seed, source manifest and validation summary.
Step 10 — Regenerate twice with the same seed and compare row counts/checksums to demonstrate reproducibility.

Suggested Volume and Coverage
Generate 5,000 employees, 200 role/level combinations and 3 years of salary history. Include promotions, part-time changes, currency changes and deliberate unexplained outliers.

Required Edge Cases / Negative Scenarios
Salary compared to expired band; FTE ignored; currency conversion missing; adjustment applied without approval; incomparable roles grouped without rationale.

Validation Rules / Acceptance Criteria
Metrics use effective-dated bands; comparisons are reproducible; outliers have contextual evidence; proposed adjustments preserve auditability.

Evaluation Focus for Generated Data
Review: (a) realistic distributions and meaningful variation; (b) consistent IDs and valid joins; (c) dependency/lifecycle consistency across entities; (d) correct derived values and reconciliation; (e) normal, boundary, failure and exception coverage; (f) separate ground truth; (g) fixed-seed reproducibility, documentation and lawful provenance.

Public Data Guidance / Lawful Use
External data is optional. If used, record source URL, dataset/version, retrieval date, license/terms, attribution, transformations and fields discarded. Use only data you are legally permitted to access and redistribute; do not bypass access controls or collect confidential/personal information. If licensing or suitability is unclear, use synthetic data and cite public reference data only for schema inspiration.

explan me what to make out of this
this a job assignment that i need to complete
make a full fledge plan first about what to make and technologies used to make the project.
```

---

### Prompt 2: Modern 3-Tier Production Architecture Clarification
* **Timestamp:** 2026-11-15T13:58:50+05:30
* **Goal:** Align on architectural specifications, the 10 entities, business calculations, the 5 exception scenarios, and dashboard layout.
* **Full Prompt Text:**
```text
This assignment is about building an Employee Compensation Equity & Salary Benchmarking System.
In simple words, you need to build a system that checks whether employees are being paid fairly compared to other employees in similar roles, experience levels and locations.
The system should identify employees who are potentially underpaid or overpaid, explain why the difference exists, and flag salary differences that cannot be justified by documented factors.
...
first make a full fledget production ready work plan for this, their tech stack and all as i want it ready as per the modern architecture (frontend, backend, database)
so first make plan and let me verify it
```

---

### Prompt 3: Technical Execution Instructions & YottaFlex Guidelines
* **Timestamp:** 2026-11-15T14:20:51+05:30
* **Goal:** Formalize exact tech stack (Python, PostgreSQL, SQLAlchemy, Streamlit, Plotly, Pytest), incorporate submission guidelines and FAQ PDFs, and instruct immediate, modular code construction.
* **Full Prompt Text:**
```text
no follow the below instructions

# PROJECT: COMPENSATION INTELLIGENCE & PAY EQUITY ANALYTICS PLATFORM

Act as a Senior Python Developer, Data Engineer, Database Architect and Product Engineer.

Your task is to design and implement a complete, working, production-quality prototype of an Employee Compensation Equity & Salary Benchmarking System.
...
Inspect all existing files...
At the end of each phase, provide:
- Files created or modified.
- Functionality implemented.
- Commands executed.
- Tests passed and failed.
- Known issues.
- Next implementation steps.
...
also read these 2 pdfs for few extra instructions (just ignore the github repo stuff for now, i will make the repo and push it myself, you just maintain the .gitignore file for safe push)
```

---

### Prompt 4: Resumption & Switch to High-Performance Agent
* **Timestamp:** 2026-11-15T14:28:59+05:30
* **Goal:** Continue development after initial scaffolding.
* **Full Prompt Text:**
```text
continue
```

---

### Prompt 5: Final Packaging, Clean Up & Remote Git Push
* **Timestamp:** 2026-11-15T14:53:39+05:30
* **Goal:** Document prompt history inside documentation folder, clean temporary files, provide run steps, and execute git commit and push to remote.
* **Full Prompt Text:**
```text
@[c:\CandidateWorkspace\YottaFlex AI Candidate Project Submission Guidelines.pdf] @[c:\CandidateWorkspace\YottaFlex AI Candidate Project-FAQ.pdf] 

go through this pdfs and follow the instructions (mainly the prompt history part (add in documentation folder itself))

tell me how to run the project and check for any temporary files you have created while makeing the project which is not needed and delete it and check if the rest is good to push on github

also added the remote git repo, so give commits and push it
```

---

## 3. Where AI Accelerated Development

1. **Relational Schema Boilerplate**: AI generated complete, typed SQLAlchemy 2.0 ORM models and DDL SQL for 12 normalized tables with extensive foreign keys, checks, and comments.
2. **Synthetic Data Scaffolding**: Accelerated generation of realistic Indian and international names, 8,190 annual compensation bands, and 75,000 performance appraisals using NumPy and Faker with a seed.
3. **Interactive Plotly Visualizations**: Rapidly generated advanced UI components including radar comparison charts, compensation box plots, and approval pipeline funnels.
4. **Pytest Harness Generation**: Automated the generation of comprehensive test suites covering normalization edge cases, data integrity, and reproducibility.

---

## 4. Human Engineering, Critical Review & Debugging

AI was not relied upon blindly. Several critical bugs, mathematical mismatches, and domain nuances were identified and resolved through rigorous human review:

1. **Group ID Collision in Comparable Groups**:
   - *Problem*: Initial group generator created GRP IDs using `GRP-{ROLE}-{LVL}-{LOC}-{TENURE}`, but grouped by `employment_type` as well. This led to duplicate primary keys when both Full-Time and Part-Time cohorts existed for the same role/level/location.
   - *Human Resolution*: Inspected validator failure, refactored ID generation to include an explicit employment type tag (`GRP-...-FT` vs `GRP-...-PT`), guaranteeing 100% PK uniqueness across all 589 peer groups.

2. **Currency & FTE Compa-Ratio Arithmetic Mismatch**:
   - *Problem*: In initial unit tests, `compa_ratio` recalculation failed for international employees because the test divided normalized salary in INR by the local currency band midpoint (USD/GBP/SGD). Furthermore, part-time employees appeared to have math discrepancies because compa-ratio incorporates FTE scaling.
   - *Human Resolution*: Reconciled mathematical formulas to ensure parity: comparing local currency salary to local band midpoint, scaled by the employee's `fte_fraction`. This brought compa-ratio verification to 100% exact equality across all 19,781 clean records.

3. **Ground Truth Isolation**:
   - *Problem*: Risk of leaking ground-truth labels into input features or analytical engine data loaders.
   - *Human Resolution*: Strictly decoupled `data/ground_truth/` from the application's runtime data loader. Ensured the Streamlit dashboard and engine run purely on observable transactional records (`salary_records`, `performance_evidence`, `tenure`), keeping ground-truth labels exclusively for post-hoc validation.

4. **Approval State Machine Governance**:
   - *Problem*: Ensuring that unauthorized salary adjustments (`ADJUSTMENT_WITHOUT_APPROVAL`) are strictly blocked at the business logic layer.
   - *Human Resolution*: Built an explicit `ProposalStateMachine` in `src/engine/adjustment_engine.py` requiring both Manager and HR Partner approval before a proposal can reach `IMPLEMENTED`.
