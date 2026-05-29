# Interface Contracts — Prediction Market Trading Bot

**Purpose:** Define all interfaces between components. Downstream components must acknowledge changes. Decouples build parallelism from coordination failure.  
**Owner (role):** Architecture Owner (AO)  
**Status:** **CANONICAL — G2 Architecture Gate 2026-05-22** — Changes require ADR or formal Change Class A/B record  
**Last reviewed:** 2026-05-28 (IF-C6-C8 and IF-C7-C8 added; C8 Visual Dashboard registered)  
**Next review:** On staleness trigger only  
**Staleness triggers:** Schema version bump; new field added to any interface; component added/removed; venue API change  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, DATA_FLOWS_LINEAGE.md  
**Downstream links:** All components that implement these interfaces; 06_CODE_EXECUTION_REPRODUCIBILITY/PIPELINES_JOBS.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 8/10 — Interface shapes canonical at G2; venue-specific fields (IF-C5-VENUE) finalized at ADR-0003 acceptance  

---

## Interface Governance Rules

1. **Any change to a contract requires:** (a) version bump, (b) downstream acknowledgement from all consumers listed, (c) CHANGELOG entry, (d) ADR if the change is breaking.
2. **No component may consume an interface field not listed in this document.** Undocumented field usage is a shadow coupling.
3. **Backward-incompatible changes** (removing fields, changing types) require a superseding ADR and a migration plan.

---

## IF-C1-C2 — Ingestion → Feature Store

**Version:** 1.0 (DRAFT)  
**Producer:** C1 Signal Ingestion  
**Consumer:** C2 Feature Store  
**Downstream acknowledgement:** AO (self-consuming; confirmed 2026-05-21)  

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| snapshot_id | string | YES | Snapshot ID from DATA_SNAPSHOTS_INDEX.md. Format: SNAP-YYYY-MM-DD-NNN |
| event_id | string | YES | Unique identifier for the prediction market event |
| event_date | ISO 8601 datetime | YES | Scheduled event datetime (UTC). Used for temporal integrity checks. |
| source | string | YES | Source dataset identifier (e.g., "player_attribute_matrix_v4", "venue_api_v1") |
| data_version | string | YES | Schema version of the source record |
| fields | object | YES | Key-value map of raw signal fields. Field names must match lineage register in DATA_FLOWS_LINEAGE.md |
| ingestion_timestamp | ISO 8601 datetime | YES | UTC timestamp of ingestion |
| validation_status | enum: VALID, WARN, REJECTED | YES | Result of schema validation |
| validation_notes | string | NO | Human-readable notes on warnings or rejection reasons |

**Versioning policy:** Minor field additions are backward-compatible (v1.0 → v1.1). Type changes or field removals require v2.0 and an ADR.

---

## IF-C2-C3 — Feature Store → Forecasting Engine

**Version:** 1.0 (DRAFT)  
**Producer:** C2 Feature Store  
**Consumer:** C3 Forecasting Engine  
**Downstream acknowledgement:** AO (self-consuming; confirmed 2026-05-21)  

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| event_id | string | YES | Matches IF-C1-C2 |
| snapshot_id | string | YES | Inherited from C1; must flow through for audit trail |
| feature_version | string | YES | Version of the feature set (incremented when features change) |
| features | object | YES | Key-value map of engineered features. All keys must appear in DATA_FLOWS_LINEAGE.md |
| train_test_label | enum: TRAIN, VALIDATION, TEST | YES | Prevents contamination in batch mode |
| temporal_cutoff | ISO 8601 datetime | YES | Latest timestamp of data used to produce these features. Used for look-ahead audit. |

---

## IF-C3-C4 — Forecasting Engine → Risk Engine *(Phase 6+)*

**Version:** 1.0 (DRAFT)  
**Producer:** C3 Forecasting Engine  
**Consumer:** C4 Risk Engine  
**Downstream acknowledgement:** AO (confirmed 2026-05-21) — **GATED: active only after ADR-0004**  

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| event_id | string | YES | |
| snapshot_id | string | YES | |
| model_version | string | YES | Immutable after paper/live deployment |
| p_estimate | float [0,1] | YES | Forecast probability of YES outcome |
| confidence_interval | object {lower: float, upper: float} | YES | 90% CI around p_estimate |
| market_implied_prob | float [0,1] | YES | Current venue price (null model baseline for edge calculation) |
| edge | float | YES | Computed edge: p_estimate - market_implied_prob - vig |
| recommended_direction | enum: YES, NO, PASS | YES | Directional signal from forecasting engine |
| forecast_timestamp | ISO 8601 datetime | YES | UTC timestamp of forecast generation |

---

## IF-C4-C5 — Risk Engine → Execution Engine *(Phase 6+)*

**Version:** 1.0 (DRAFT)  
**Producer:** C4 Risk Engine  
**Consumer:** C5 Execution Engine  
**Downstream acknowledgement:** AO (confirmed 2026-05-21) — **GATED: active only after ADR-0004**  

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| event_id | string | YES | |
| approval_status | enum: APPROVED, REJECTED, KILL_SWITCH | YES | REJECTED = do not place; KILL_SWITCH = halt all activity |
| rejection_reason | string | NO | Required if approval_status = REJECTED |
| approved_size | float | YES (if APPROVED) | Fractional Kelly position size in dollars |
| approved_direction | enum: YES, NO | YES (if APPROVED) | Must match forecasting engine recommendation |
| risk_check_timestamp | ISO 8601 datetime | YES | UTC time of risk evaluation |
| checks_passed | array[string] | YES | List of risk checks that passed (for audit trail) |

---

## IF-C5-VENUE — Execution Engine → Venue API *(Phase 8 only)*

**Version:** 1.0 (DRAFT)  
**Producer:** C5 Execution Engine  
**Consumer:** Prediction market venue (external; TBD at ADR-0003)  
**Downstream acknowledgement:** AO + RCO — **GATED: active only after ADR-0005 + G6**  

*Exact fields defined at venue confirmation (ADR-0003). Minimum required fields:*

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| event_id | string | YES | Venue's market identifier (mapped from internal event_id) |
| direction | enum: YES, NO | YES | |
| size | float | YES | Dollar amount (must equal IF-C4-C5 approved_size) |
| order_type | enum: MARKET, LIMIT | YES | |
| limit_price | float [0,1] | NO | Required if order_type = LIMIT |
| idempotency_key | string | YES | Prevents duplicate order submission on retry |

---

## IF-ALL-C6 — All Components → Audit Logger

**Version:** 1.0 (DRAFT)  
**Producer:** C1, C2, C3, C4, C5, C7  
**Consumer:** C6 Audit Logger  
**Downstream acknowledgement:** AO (confirmed 2026-05-21)  

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| log_timestamp | ISO 8601 datetime | YES | UTC timestamp of event |
| component | string | YES | e.g., "C1_ingestion", "C3_forecast", "C4_risk" |
| event_type | string | YES | e.g., "INGEST", "FORECAST", "ORDER_APPROVED", "KILL_SWITCH" |
| severity | enum: DEBUG, INFO, WARN, ERROR, CRITICAL | YES | |
| event_id | string | NO | Market event ID (if applicable) |
| snapshot_id | string | NO | (if applicable) |
| payload | object | YES | Component-specific event details |
| trace_id | string | YES | Cross-component correlation ID for a single market decision cycle |

---

## IF-DS-Q-C2 — Qualitative Data Sources → Feature Store *(Phase 6+ / Pending DS-01 operationalization)*

**Version:** 1.0 (SKELETON — 2026-05-28)  
**Producer:** Qualitative classification CSVs (`qualitative_data/<source>/<QS-ID>_classifications.csv`)  
**Consumer:** C2 Feature Store via `QualitativeSignalStore` (`c2_feature_store/qualitative_store.py`)  
**Downstream acknowledgement:** AO — **PENDING: activate when first QS snapshot is populated**

*This interface covers any qualitative data source (DS-01 PAM, DS-04+). Each source has its own schema definition in `qualitative_data/<source>/SCHEMA.md`; this contract defines the shared columns that all qualitative sources must provide for the temporal join to work.*

**Shared required columns (all qualitative sources must include these):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `player_id` | integer | YES | NBA player ID — join key to feature DataFrame |
| `effective_from` | YYYY-MM-DD | YES | Earliest game_date for which this classification applies (QTI-01) |
| `effective_until` | YYYY-MM-DD or NULL | NO | Last game_date (exclusive); NULL = currently active |
| `classification_date` | YYYY-MM-DD | YES | When this classification was made |
| `classified_by` | string | YES | Classifier identity (for audit trail) |
| `classification_basis` | string | YES | What data informed this classification (QTI-02) |
| `backdated` | boolean (0/1) | YES | Whether effective_from is set prior to classification_date |
| `backdating_rationale` | string | conditional | Required when backdated=1 |

**Source-specific feature columns:** Defined in each source's SCHEMA.md. DS-01 adds `prf_primary`, `prf_secondary`, `prf_hybrid_weight`, `mod_01`…`mod_32`.

**Join semantics:**
```
LEFT JOIN qualitative_df ON (
    feature_df.player_id == qualitative_df.player_id
    AND feature_df.game_date >= qualitative_df.effective_from
    AND (qualitative_df.effective_until IS NULL
         OR feature_df.game_date < qualitative_df.effective_until)
)
```
Non-matching rows produce NaN for all qualitative feature columns. This is correct — NaN means "unclassified for this period," not an error.

**Feature ID assignment:** All qualitative features use F-100+ range. See DATA_FLOWS_LINEAGE.md for specific ID assignments per source.

---

## IF-C6-C8 — Audit Logger → Visual Dashboard *(Phase 5+; read-only)*

**Version:** 1.0 (STUB — design only; implemented at Phase 5)  
**Producer:** C6 Audit Logger  
**Consumer:** C8 Visual Dashboard  
**Downstream acknowledgement:** AO — **GATED: active only at Phase 5+**  

*C8 reads from C6's append-only log files to surface forecast history, calibration trends, and decision audit trail. C8 is a pure consumer — it never writes to or modifies C6 state.*

| Field consumed | Source | Dashboard use |
|---------------|--------|--------------|
| log_timestamp | IF-ALL-C6 | Timeline axis for all panels |
| component | IF-ALL-C6 | Filter by component (C3 forecasts, C4 risk decisions) |
| event_type | IF-ALL-C6 | Route to appropriate panel (FORECAST → calibration chart; ORDER_APPROVED → P&L) |
| payload.p_estimate | C3 forecast events | Forecast calibration curve; rolling Brier chart |
| payload.edge | C3 forecast events | Edge distribution histogram |
| payload.recommended_direction | C3 forecast events | Direction summary |
| payload.approval_status | C4 risk events | Risk utilization panel |
| payload.approved_size | C4 risk events | Position sizing history |
| severity | IF-ALL-C6 | Alert feed (WARN/ERROR/CRITICAL events) |

---

## IF-VENUE-ADAPTER — VenueAdapter Protocol (Phase 7+)

**Version:** 1.0 (CANONICAL 2026-05-29)
**Producer:** KalshiVenueAdapter, PolymarketVenueAdapter, DFS pick'em adapters
**Consumer:** VenueRouter
**Downstream acknowledgement:** AO — Phase 7+ multi-venue activation

All venue adapters must satisfy the VenueAdapter Protocol (`c5_execution/venue_adapter.py`):

| Method / Property | Type | Description |
|-------------------|------|-------------|
| `venue_id` | str | Unique venue identifier: `"kalshi"`, `"polymarket"`, `"prizepicks"` etc. |
| `implied_prob_method` | str | `"market"` (dynamic supply/demand) or `"bookmaker"` (static line) |
| `check_connectivity()` | `(bool, dict)` | Verify API key + connectivity; call before any other method |
| `fetch_player_points_markets(sport, status)` | `(bool, DS02Snapshot)` | All open player-points markets; each PlayerMarket has `venue` field set |
| `fetch_market_detail(ticker)` | `(bool, PlayerMarket \| None)` | Single market by ticker |

**PlayerMarket.venue field:** Added 2026-05-29 (backward-compatible default `"kalshi"`). All existing code unaffected.

---

## IF-ROUTER — VenueRouter → Consumers (Phase 7+)

**Version:** 1.0 (CANONICAL 2026-05-29)
**Producer:** VenueRouter (`c5_execution/venue_router.py`)
**Consumer:** PIPE-02 (run_pregame.py), PIPE-06 (run_t3_pretip.py), ComplementLockScanner

VenueRouter is transparent to C3, C4 — consumers call it exactly as they called KalshiMarketClient.

| Method | Returns | Notes |
|--------|---------|-------|
| `fetch_all_markets(sport, status)` | `(bool, DS02Snapshot)` | Merged snapshot from all registered adapters; deduplicates by tightest vig |
| `get_best_market(player, threshold, direction)` | `(bool, PlayerMarket \| None)` | Best execution price for direction across all venues |
| `get_all_quotes(player, threshold)` | `dict[str, PlayerMarket \| None]` | One quote per venue — used by ComplementLockScanner |
| `check_all_connectivity()` | `dict[str, (bool, dict)]` | Connectivity check per venue |
| `active_venues` | `list[str]` | Currently registered venue IDs |
| `mode` | `str` | `"kalshi_only"` or `"best_price"` |

---

## IF-C7-C8 — Monitoring + Kill Switch → Visual Dashboard *(Phase 5+; read-only)*

**Version:** 1.0 (STUB — design only; implemented at Phase 5)  
**Producer:** C7 Monitoring + Kill Switch  
**Consumer:** C8 Visual Dashboard  
**Downstream acknowledgement:** AO — **GATED: active only at Phase 5+**  

*C7 emits structured metric events that C8 renders as system health indicators and alert badges. C8 receives but never acknowledges or responds to kill-switch signals — those are handled by C7 directly.*

| Field consumed | Source | Dashboard use |
|---------------|--------|--------------|
| metric_name | C7 metric stream | Route to health panel (latency, uptime, Brier drift) |
| metric_value | C7 metric stream | Gauge/chart value |
| threshold | C7 metric stream | Threshold line on charts |
| alert_level | C7 alert events | P1/P2/P3 badge in alert feed |
| alert_message | C7 alert events | Alert description |
| kill_switch_active | C7 kill-switch events | Global red banner in dashboard |
