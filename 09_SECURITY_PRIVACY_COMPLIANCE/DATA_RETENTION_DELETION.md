# Data Retention and Deletion — Prediction Market Trading Bot

**Purpose:** Define how long each data category is retained, under what conditions it is deleted, and what the deletion procedure is. Required for compliance with data minimization principles and for managing storage and audit obligations.  
**Owner (role):** Risk and Compliance Owner (RCO)  
**Last reviewed:** 2026-05-22  
**Next review:** G1 (DS-01 provenance confirmed); G5 (pre-live review); update when venue confirmed (outcome data obligations)  
**Staleness triggers:** New data category added; retention period changed (requires ADR or RCO sign-off); venue TOS retention requirements confirmed  
**Upstream links:** DATA_PROVENANCE.md, DATA_FLOWS_LINEAGE.md, POLICY_REQUIREMENTS.md (POL-002)  
**Downstream links:** DATA_SNAPSHOTS_INDEX.md, PIPELINES_JOBS.md  
**Decision references:** ADR-0001  
**Confidence:** 6/10 — Framework defined; specific periods subject to venue TOS review at G3

---

## Retention Policy by Data Category

### CAT-01 — Research Input Data (DS-01)

| Field | Detail |
|-------|--------|
| Category | Player_Attribute_Matrix (DS-01) and derivatives |
| Retention | Retain for the life of the project; archive at project close |
| Rationale | Required for experiment reproducibility; immutable snapshots |
| Deletion trigger | Project close OR provenance found to be legally problematic (OQ-001) |
| Deletion procedure | Delete snapshot files; remove from DATA_SNAPSHOTS_INDEX.md; log deletion in CHANGELOG |
| Notes | Snapshots are immutable during project — no in-place modification |

---

### CAT-02 — Market Data (DS-02)

| Field | Detail |
|-------|--------|
| Category | Live and historical market data from venue API |
| Retention | Active period: retain for model training window + buffer (TBD at G3) |
| Historical snapshots | Retain indefinitely for experiment reproducibility |
| Rationale | Training data reproducibility; compliance audit trail |
| Deletion trigger | Venue TOS requires deletion; data superseded by better quality source |
| Deletion procedure | Delete source files; invalidate dependent snapshots; log in CHANGELOG |
| Notes | Venue TOS may impose deletion obligations — confirm at G3 |

---

### CAT-03 — Outcome / Resolution Data (DS-03)

| Field | Detail |
|-------|--------|
| Category | Event resolution data from venue |
| Retention | Retain for life of model version that used it + 1 year minimum |
| Rationale | Required for post-hoc drift analysis and audit |
| Deletion trigger | Model version retired AND retention period expired |
| Deletion procedure | Purge outcome store; update DATA_SNAPSHOTS_INDEX.md |
| Notes | MUST be stored separately from feature store at all times (TI-03) |

---

### CAT-04 — Audit Logs (C6 Output)

| Field | Detail |
|-------|--------|
| Category | All C6 audit log entries: forecast records, execution events, risk limit evaluations |
| Retention | **Minimum 2 years** from event date; extend to 5 years if live capital deployed |
| Rationale | Financial audit trail; model risk governance; kill switch post-mortems |
| Deletion trigger | Retention period expired; RCO sign-off on deletion |
| Deletion procedure | Bulk delete by date range; log deletion action in a meta-audit record |
| Notes | Do NOT delete audit logs in response to adverse events — that is evidence tampering |

---

### CAT-05 — Model Artifacts

| Field | Detail |
|-------|--------|
| Category | Trained model files, feature sets, calibration objects (ARTIFACT_REGISTRY.md) |
| Retention | Retain active model version indefinitely; retain superseded versions for 1 year after supersession |
| Rationale | Reproducibility; ability to roll back to prior version |
| Deletion trigger | 1 year post-supersession AND no open investigations or incidents |
| Deletion procedure | Remove from artifact store; update ARTIFACT_REGISTRY.md status to ARCHIVED; log in CHANGELOG |

---

### CAT-06 — Secrets and Credentials

| Field | Detail |
|-------|--------|
| Category | API keys, passwords, tokens |
| Retention | Retain in vault only while active; rotate per SECRETS_HANDLING.md schedule |
| Deletion trigger | Credential rotated (previous version deleted immediately) OR credential revoked |
| Deletion procedure | Revoke at source; purge from vault; confirm no residual references in logs |
| Notes | Compromised credentials: revoke immediately; treat as incident; log to RID_LOG.md |

---

### CAT-07 — Experiment Logs and Notebooks

| Field | Detail |
|-------|--------|
| Category | EXPERIMENT_LOG/ entries; research notebooks (exploratory only) |
| Retention | Experiment logs: retain for life of project |
| Notebooks | Retain for 90 days after experiment closed; then archive or delete |
| Rationale | Notebooks are scratch space (NOTEBOOKS_POLICY.md); experiment logs are governance artifacts |
| Deletion trigger | Notebook: 90 days post-experiment closure |
| Deletion procedure | Delete notebook file; confirm experiment log entry is complete before deletion |

---

### CAT-08 — Status Reports and Operational Documents

| Field | Detail |
|-------|--------|
| Category | STATUS_REPORTS/, CHANGELOG, ADRs, runbooks |
| Retention | Retain for life of project; archive at project close |
| ADRs | Immutable — never deleted; archived only |
| Rationale | Governance audit trail; context for future decisions |
| Deletion trigger | Project close (archive, not delete) |

---

## Deletion Procedure

Any deletion of production data (CAT-01 through CAT-06) requires:

1. **Written justification** — log to CHANGELOG with category, volume, trigger, and RCO sign-off
2. **Dependency check** — confirm no active experiment, live model, or audit investigation depends on the data
3. **Snapshot invalidation** — if a snapshot is deleted, mark as INVALIDATED in DATA_SNAPSHOTS_INDEX.md
4. **Confirmation** — verify deletion completed (hash check or directory listing)

**Exception: Audit logs (CAT-04)** — deletion requires DS sign-off in addition to RCO; never delete during an active investigation.

---

## Retention Summary Table

| Category | Min Retention | Max Retention | Gate Review |
|----------|--------------|---------------|------------|
| CAT-01 Research Input | Project life | Archive at close | G1 |
| CAT-02 Market Data | Training window + buffer | Project life | G3 |
| CAT-03 Outcome Data | Model life + 1yr | Project life | G3 |
| CAT-04 Audit Logs | 2yr (5yr if live) | Indefinite | G5 |
| CAT-05 Model Artifacts | 1yr post-supersession | Indefinite | G5 |
| CAT-06 Secrets | Active only | Rotate immediately | Ongoing |
| CAT-07 Notebooks | 90 days post-close | Project life | Ongoing |
| CAT-08 Governance Docs | Project life | Archive | Project close |
