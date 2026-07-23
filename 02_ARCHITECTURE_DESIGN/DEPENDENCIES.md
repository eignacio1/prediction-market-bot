# Dependencies — Prediction Market Trading Bot

**Purpose:** Enumerate all external and internal dependencies — software libraries, data sources, infrastructure, and tooling. Required for reproducibility and supply-chain risk assessment.  
**Owner (role):** Architecture Owner (AO)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: verified the 2026-07-06 correction note against the live lock files directly (`requirements-base.txt`, `requirements-dev.txt`); versions cited in the note still match exactly. No new drift found.  
**Next review:** 2026-08-23, or on any dependency change  
**Staleness triggers:** New library added; version pinned; data source confirmed; venue API selected; infrastructure provisioned  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/  
**Downstream links:** 06_CODE_EXECUTION_REPRODUCIBILITY/ENVIRONMENTS.md, 06_CODE_EXECUTION_REPRODUCIBILITY/RUN_INSTRUCTIONS.md  
**Decision references:** ADR-0001, ADR-0002, ADR-0003 (pending — venue)  
**Confidence:** 4/10 — Dependencies are preliminary; exact versions pinned at G2; technology stack TBD

**⚠️ Corrected 2026-07-06 (GG-074 remediation) — the Confidence line above and the "TBD at G2"/"preliminary" framing throughout this document are stale.** G2 closed long ago. The stack is fully pinned and has been in production use for weeks: confirmed directly against `06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-base.txt` and `requirements-dev.txt` (Python 3.11+; `pandas==2.2.2`, `numpy==1.26.4`, `pyarrow==16.1.0`, `scikit-learn==1.4.2`, `scipy==1.13.0`, `nba_api>=1.5.0`, `jsonlines==4.0.0`, `python-dotenv==1.0.1`, `cryptography>=42.0.0`; dev-only: `pytest==8.2.0`, `pytest-cov==5.0.0`, `black==24.4.2`, `flake8==7.0.0`, `mypy==1.9.0`, `bandit==1.7.8`, `detect-secrets==1.4.0`, `pre-commit==3.7.1`). Venue is confirmed Kalshi primary (ADR-0003, 2026-05-23) with RSA-PSS signing via `cryptography` (ADR-0008, 2026-05-31). Model class is confirmed LogisticRegression + Platt scaling (ADR-0004, 2026-05-28), not the XGBoost/LightGBM placeholder below. Secrets management is `.env` + `python-dotenv` + OS env vars (NFR-05), not a "Vault tooling — TBD" product. The per-row "TBD at G2"/"TBD at G5"/"TBD at ADR-0003" cells below were not individually rewritten in this pass (would amount to a full rewrite, out of scope for a dated-correction-note remediation) — treat every such cell as superseded by the pinned values in this note and the lock files themselves, which are the source of truth per this file's own Version Lock Policy section.

---

## Dependency Governance Rules

1. **All dependencies must be pinned to exact versions** before any experiment runs (NFR-01). Floating version ranges are prohibited in production.
2. **Dependency changes require a CHANGELOG entry.** Breaking changes require an ADR.
3. **All pinned dependency files are tracked in** `06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/`.
4. **No dependency may be used without a documented justification** in this file.
5. **Security vulnerability in any dependency:** patch within 48 hours (live) / within 1 week (research).

---

## Software Dependencies (Research Phase — Preliminary)

*Technology stack finalized at G2. All versions are placeholders until stack ADR is accepted.*

### Core Language

| Dependency | Role | Phase Active | Version | Justification |
|------------|------|-------------|---------|---------------|
| Python (3.11+) | Primary language | Phase 3+ | TBD at G2 | Strong ecosystem for data science; strict typing enforcement via mypy |
| mypy | Static type checking | Phase 3+ | TBD at G2 | NFR-01 reproducibility; catches type errors before runtime |

### Data Processing

| Dependency | Role | Phase Active | Version | Justification |
|------------|------|-------------|---------|---------------|
| pandas | Tabular data manipulation | Phase 3+ | TBD at G2 | Standard; Player_Attribute_Matrix ingestion and feature derivation |
| numpy | Numerical operations | Phase 3+ | TBD at G2 | Dependency of pandas; probability calculations |
| pyarrow / polars | High-performance data ops (TBD) | Phase 3+ | TBD at G2 | Performance at scale; decision deferred to G2 stack ADR |

### Forecasting / Modeling

| Dependency | Role | Phase Active | Version | Justification |
|------------|------|-------------|---------|---------------|
| scikit-learn | Model training, calibration, Brier score | Phase 3+ | TBD at G2 | Calibration tools; calibrated probability outputs |
| scipy | Statistical functions | Phase 3+ | TBD at G2 | CI computation, distribution fitting |
| [XGBoost / LightGBM / Logistic Regression] | Model class (TBD) | Phase 3+ | TBD at G2 | Model class selected after initial experiments (ADR-0003) |

### Backtesting / Validation

| Dependency | Role | Phase Active | Version | Justification |
|------------|------|-------------|---------|---------------|
| [Custom backtesting framework] | Temporal integrity enforcement | Phase 3+ | Internal | Must enforce chronological splits; no standard library guarantees temporal safety |

### Logging / Audit

| Dependency | Role | Phase Active | Version | Justification |
|------------|------|-------------|---------|---------------|
| Python standard `logging` | Structured log emission | Phase 3+ | stdlib | Avoid third-party dependency for core logging; JSON formatter added |
| `jsonlines` | JSON Lines file writer | Phase 3+ | TBD at G2 | Append-only structured log format per NFR-02 |

### Secrets Management

| Dependency | Role | Phase Active | Version | Justification |
|------------|------|-------------|---------|---------------|
| [Vault tooling — TBD] | Credential storage | Phase 5+ | TBD at G5 | NFR-05: zero hardcoded secrets; implementation selected at G5 |

### Venue API Client (Phase 6+)

| Dependency | Role | Phase Active | Version | Justification |
|------------|------|-------------|---------|---------------|
| [Venue SDK / requests] | Order submission and market data | Phase 6+ | TBD at ADR-0003 | Depends on venue selection (Kalshi / Polymarket); confirmed at ADR-0003 |

### Development Tooling

| Dependency | Role | Phase Active | Version | Justification |
|------------|------|-------------|---------|---------------|
| pytest | Unit and integration testing | Phase 3+ | TBD at G2 | Standard Python testing framework |
| black | Code formatting | Phase 3+ | TBD at G2 | Consistent style; reduces review noise |
| pre-commit | Hook runner | Phase 3+ | TBD at G2 | Enforce lint, format, secrets scan before commit |
| bandit | Security linting | Phase 5+ | TBD at G5 | Detect hardcoded secrets and common security anti-patterns |

---

## Data Source Dependencies

| ID | Source | Type | Phase | Status | Owner |
|----|--------|------|-------|--------|-------|
| DS-01 | Player Attribute Matrix v4 | Static file (XLSX) | Phase 1+ (staged); Phase 3+ (active) | Available — not yet validated | RL |
| DS-02 | Market Data Feed | API (venue TBD) | Phase 6+ | Pending ADR-0003 | AO |
| DS-03 | Outcome / Resolution Data | API (venue TBD) | Phase 3+ (historical); Phase 6+ (live) | Pending ADR-0003 | AO |

**⚠️ Corrected 2026-07-06 (GG-074 remediation) — all three status cells above are stale.** ADR-0003 (venue selection, Kalshi primary) was accepted 2026-05-23; DS-02 (live Kalshi market data feed, KXNBAPTS/KXMLBHIT series) and DS-03 (ESPN/MLB Stats API outcome resolution) have both been live in production for weeks, not "Pending." DS-01 (Player Attribute Matrix / F-100+ qualitative features) has a confirmed positive signal since EXP-007 and has been live in the C2 feature store since — "not yet validated" no longer describes it, though see the DS-01 note immediately below for the original scope caveat (research-input status, independent schema validation) which is a separate, narrower point that may still hold.

**DS-01 note:** Player_Attribute_Matrix is a research input only. Requires independent schema validation before use in any experiment. Not a canonical data source until validation is complete and documented.

---

## Infrastructure Dependencies

| Dependency | Role | Phase | Status |
|------------|------|-------|--------|
| Local filesystem | Data snapshots, logs, model artifacts | All phases | Active |
| [Version control — TBD] | Code and artifact versioning | Phase 3+ | TBD at G2 |
| [Cloud compute — TBD] | Model training at scale | Phase 5+ | TBD at G5 |
| [Monitoring stack — TBD] | C7 metric collection and alerting | Phase 5+ | TBD at G5 |
| [Secrets vault — TBD] | Credential management | Phase 5+ | TBD at G5 |

---

## Dependency Risk Register

| Dependency | Risk | Likelihood | Impact | Mitigation |
|------------|------|------------|--------|------------|
| Venue API (DS-02/DS-03) | API deprecation or schema change | MED | HIGH | Monitor API changelogs; versioned interfaces (IF-C1-C2) absorb changes |
| Player_Attribute_Matrix (DS-01) | Provenance unclear; schema may change | MED | MED | Treat as research input only; validate before use; pin snapshot before any experiment |
| ML library (scikit-learn etc.) | Breaking change in minor version | LOW | MED | Pin exact versions; lock in DEPENDENCY_LOCKS/; test suite catches regressions |
| Venue SDK | Unmaintained or deprecated | LOW | HIGH | Select venue with stable API history (ADR-0003 evaluation criteria) |
| Python version | EOL or breaking change | LOW | MED | Pin Python version; containerize at G5 |

---

## Version Lock Policy

Per NFR-01 (Reproducibility):

- **Before any experiment:** all dependencies must be pinned and recorded in `06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements.txt` (Python) or equivalent
- **Lock file format:** `package==X.Y.Z` (exact pin); no `>=`, `~=`, or range specifiers
- **Lock file must be committed** to version control alongside any experiment record that references it
- **Experiment records** must cite the dependency lock version (or lock file hash) under the Reproducibility section

*Lock files created at Phase 3 entry. Updated only with deliberate version bumps documented in CHANGELOG.*
