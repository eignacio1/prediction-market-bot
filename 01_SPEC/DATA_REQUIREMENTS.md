# Data Requirements — Prediction Market Trading Bot

**Purpose:** Define all data sources, quality thresholds, lineage expectations, retention constraints, and access requirements.  
**Owner (role):** Research Lead (RL) / Architecture Owner (AO)  
**Last reviewed:** 2026-05-21  
**Next review:** G1 Spec Gate; then on any new data source addition  
**Staleness triggers:** New data source approved; venue confirmed (adds market data feed); Player_Attribute_Matrix schema changes; retention policy change; external data contract change  
**Upstream links:** SCOPE_IN_OUT.md, REQUIREMENTS.md (FR-01)  
**Downstream links:** 02_ARCHITECTURE_DESIGN/DATA_FLOWS_LINEAGE.md, 06_CODE_EXECUTION_REPRODUCIBILITY/DATA_SNAPSHOTS_INDEX.md, 08_MODEL_RISK_GOVERNANCE/DATA_PROVENANCE.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 6/10 — Sources partially known (Player_Attribute_Matrix confirmed); market data feed and external sources pending venue confirmation  

---

## Data Source Inventory

### DS-01 — Player_Attribute_Matrix (Research Input)

| Field | Detail |
|-------|--------|
| Source name | Player_Attribute_Matrix_v4.docx (legacy artifact from prior iteration) |
| Source type | Structured attribute data — player and market-relevant attributes |
| Access path | 05_RESEARCH_EXPERIMENTS/ (staged as research input; not canonical spec) |
| Current version | v4 (filename-referenced) |
| Format | .docx → requires extraction/parsing to tabular format before use |
| Temporal coverage | TBD upon extraction |
| Refresh cadence | Static historical artifact; future versions require ADR to incorporate |
| Access control | Internal only; no external API required |
| Quality notes | Provenance from prior iteration; must be independently validated before any signal from it is used in production |
| Retention | Retain indefinitely as research reference; superseded versions archived with rationale |
| **Canonical status** | **Research input only. NOT canonical spec. Earns production status through G4 validation evidence.** |

### DS-02 — Market Data Feed (Pending)

| Field | Detail |
|-------|--------|
| Source name | TBD — contingent on ADR-0003 (venue selection) |
| Source type | Real-time and historical prediction market prices, volumes, order book snapshots |
| Access path | Venue API (credentials via ACC-0002; requires G5 minimum) |
| Format | Venue-specific (JSON/REST expected; WebSocket for real-time) |
| Temporal coverage | Historical: TBD by venue; Real-time: Phase 6+ |
| Refresh cadence | Real-time (Phase 6+); batch historical pulls (Phase 3) |
| Access control | Requires API credentials (ACC-0002); no credentials before G5 |
| Quality notes | Bid-ask spread must be recorded (not just mid-price); vig/take rate must be tracked |
| Retention | Raw snapshots retained per DATA_RETENTION_DELETION.md; historical data pinned at Snapshot IDs |
| **Canonical status** | **Pending venue confirmation** |

### DS-03 — Outcome/Resolution Data (Pending)

| Field | Detail |
|-------|--------|
| Source name | TBD — venue settlement records or authoritative external source |
| Source type | Ground truth outcomes for settled prediction market events |
| Access path | Venue settlement API or manual collection |
| Format | TBD |
| Temporal coverage | Historical: needed for backtesting; Real-time: Phase 6+ |
| Quality notes | Critical for calibration evaluation; must be authoritative (not self-reported); settlement edge cases must be documented |
| Retention | Permanent retention as ground truth for validation |
| **Canonical status** | **Pending** |

---

## Minimum Data Quality Thresholds

| Data Source | Quality Dimension | Threshold | Enforcement |
|------------|------------------|-----------|-------------|
| All sources | Completeness | ≥95% of required fields non-null | Schema validation at ingestion (FR-01) |
| All sources | Timeliness | Data labeled with source timestamp; lag quantified | Timestamp field required in all schemas |
| Player_Attribute_Matrix | Parseable | 100% of records extractable to tabular format | Extraction script with error report |
| Market data | Price validity | All prices ∈ (0, 1) exclusive (prediction market contracts) | Schema constraint |
| Market data | Volume | Non-negative; zero-volume markets flagged but not rejected | Warning log |
| Outcome data | Completeness | 100% of settled markets have confirmed outcome | Alert on gap; do not use unsettled outcomes in training |

---

## Lineage Expectations

1. **Every dataset used in an experiment must have a Snapshot ID** registered in DATA_SNAPSHOTS_INDEX.md before the experiment runs. No Snapshot ID = experiment is invalid.
2. **Every feature derived from raw data must document the transformation** in DATA_FLOWS_LINEAGE.md with: input field → transformation logic → output feature name.
3. **No raw data file may be modified after snapshotting.** Corrections require a new snapshot with a new ID and a note in DATA_SNAPSHOTS_INDEX.md.
4. **Player_Attribute_Matrix lineage:** Any feature derived from the Player_Attribute_Matrix must cite the source document version and field name in the experiment record.

---

## Retention and Deletion Constraints

| Data Class | Retention Period | Deletion Method | Exceptions |
|-----------|-----------------|----------------|-----------|
| Research snapshots (historical) | Indefinite (pinned) | Manual with DS approval; requires CHANGELOG entry | None — immutable after snapshot |
| Live market data (raw feed) | 24 months rolling | Automated purge; Snapshot IDs retained as references | Snapshots used in validated experiments are exempt from purge |
| Decision log (forecast + order records) | Indefinite for audit trail | Requires RCO approval for any deletion | None expected |
| API credentials / secrets | Rotate per SECRETS_HANDLING.md; delete on expiry | Vault deletion | None |

---

## Access Constraints

| Data Source | Who May Access | Approval Required | Audit |
|------------|---------------|------------------|-------|
| Player_Attribute_Matrix | RL, MO/V, DS | None (internal) | Directory header version control |
| Market data feed | AO, RL, OO | ACC-0002 (RCO approval) | API access log |
| Outcome data | RL, EO, MO/V | ACC-0002 or equivalent | API access log |
| Secrets / credentials | OO, RCO | Vault access log | Vault audit trail |
