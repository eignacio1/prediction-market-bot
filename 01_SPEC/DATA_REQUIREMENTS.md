# Data Requirements — Prediction Market Trading Bot

**Purpose:** Define all data sources, quality thresholds, lineage expectations, retention constraints, and access requirements.  
**Owner (role):** Research Lead (RL) / Architecture Owner (AO)  
**Last reviewed:** 2026-07-02 (documentation-remediation pass — DS-02/DS-03 below had sat marked "Pending" since 2026-05-21 despite venue confirmation (ADR-0003, 2026-05-23) and months of live resolution data since)  
**Next review:** On any new data source addition (staleness trigger below fired at least twice since last review — MLB C1 source, ESPN as primary outcome source — without being acted on; treat this document as under-reviewed relative to its own trigger list)  
**Staleness triggers:** New data source approved; venue confirmed (adds market data feed); Player_Attribute_Matrix schema changes; retention policy change; external data contract change  
**Upstream links:** SCOPE_IN_OUT.md, REQUIREMENTS.md (FR-01)  
**Downstream links:** 02_ARCHITECTURE_DESIGN/DATA_FLOWS_LINEAGE.md, 06_CODE_EXECUTION_REPRODUCIBILITY/DATA_SNAPSHOTS_INDEX.md, 08_MODEL_RISK_GOVERNANCE/DATA_PROVENANCE.md  
**Decision references:** ADR-0001, ADR-0002, ADR-0003 (venue selection — resolves DS-02 below)  
**Confidence:** 6/10 — DS-02/DS-03 status updated below based on MEMORY_BANK narrative and governance-log cross-references (ADR-0003 venue confirmation, `kalshi_client.py` in active use, MLB Stats API/ESPN/`nba_api` cited as resolution sources across multiple GG entries — e.g. GG-063, GG-069), **not** a fresh field-level schema audit of the actual source files performed in this pass. Treat the field-level detail rows below as still needing verification against current code if precision matters for a specific decision.  

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

### DS-02 — Market Data Feed (RESOLVED — Kalshi confirmed, live in production)

| Field | Detail |
|-------|--------|
| Source name | **Kalshi** — confirmed primary venue per ADR-0003 (2026-05-23); `kalshi_client.py` in active use for both order submission and price polling |
| Source type | Real-time and historical prediction market prices, volumes, order book snapshots |
| Access path | Kalshi REST API (RSA-PSS signed requests, ADR-0008); DEMO environment for paper trading (`BOT_ENV=paper`), live URL reserved for post-G6 |
| Format | REST/JSON. Order endpoint migrated v1→v2 (`/portfolio/events/orders`) per ADR-0038 (SESSION 108) after Kalshi deprecated v1 platform-wide — a real breaking change this document did not anticipate when it said "Venue-specific, JSON/REST expected" |
| Temporal coverage | Real-time polling active (T4 bands: 45s cycle); historical price history not separately warehoused beyond what's captured in per-cycle logs |
| Refresh cadence | Real-time — T1/T2/T3 poll once per scheduled cron run; T4/T4M poll every 45-90s continuously during live games |
| Access control | API credentials provisioned (ACC-0002) and in active use, vault/env-var protocol (NFR-05) | 
| Quality notes | Fee-adjusted edge gate implemented (ADR-0016); fee rate (0.07 vs possible 0.06 for sports markets) not fully confirmed against real receipts — GG-020 OPEN, paper-trading-only means no live receipts exist yet |
| Retention | Per-cycle price data logged to JSONL (e.g. `t4_mlb_cycle_log.jsonl`); Data Snapshot Discipline applied when frozen for backtesting (DATA_SNAPSHOTS_INDEX.md) |
| **Canonical status** | **RESOLVED and live.** *(Corrected 2026-07-02 — this row said "Pending venue confirmation" for over a month after ADR-0003 confirmed Kalshi.)* |

### DS-03 — Outcome/Resolution Data (RESOLVED — sport-specific, live in production)

| Field | Detail |
|-------|--------|
| Source name | **NBA:** `nba_api` / ESPN NBA scoreboard. **MLB:** MLB Stats API (`gameLog` endpoint) + ESPN MLB scoreboard (used for game-status/FINAL confirmation). |
| Source type | Ground truth outcomes for settled prediction market events (player stat thresholds) |
| Access path | Public stats APIs, not venue settlement records — the original design assumed venue settlement would be the ground truth source; production instead resolves independently against the underlying sport's official stats and compares to the market's threshold |
| Format | JSON (`nba_api`, MLB Stats API), HTML/JSON (ESPN) |
| Temporal coverage | Historical (backtesting) and real-time (Phase 6+, live) |
| Quality notes | **Known defect, not yet fixed:** `fetch_actual_hits`/`_fetch_mlb_hits` (`run_resolve_mlb.py`) has no FINAL-game-status gate — it can resolve against in-progress hit totals rather than confirmed-final ones (GG-069, registered SESSION 111, partially addressed via T-221 but cross-check current status in GOVERNANCE_GAP_LOG.md before trusting any MLB resolution pulled without an explicit STATUS_FINAL check). This directly affects data quality for this source and should not be treated as fully resolved just because the source itself is identified. |
| Retention | Resolved outcomes written to paper portfolio + resolution logs; permanent retention as ground truth |
| **Canonical status** | **RESOLVED (source identified, live) with an open data-quality defect (GG-069).** *(Corrected 2026-07-02 — this row said "Pending" and didn't anticipate that ground truth would come from independent stats APIs rather than venue settlement.)* |

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
