# Data Flows and Lineage — Prediction Market Trading Bot

**Purpose:** Document all data flows between components, transformations applied, and lineage from source to output. Required for audit, look-ahead bias prevention, and reproducibility.  
**Owner (role):** Architecture Owner (AO)  
**Last reviewed:** 2026-05-28 (T-046 — FEATURE_VERSION 1.2.0; F-032–F-038 pruned; 31 active features)  
**Next review:** After any FEATURE_VERSION bump; G4 evidence review  
**Staleness triggers:** New data source; new feature added; component interface changed; venue confirmed  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, 01_SPEC/DATA_REQUIREMENTS.md  
**Downstream links:** INTERFACES_CONTRACTS.md, 06_CODE_EXECUTION_REPRODUCIBILITY/DATA_SNAPSHOTS_INDEX.md, 08_MODEL_RISK_GOVERNANCE/DATA_PROVENANCE.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 6/10 — Research-phase flows defined; live-data flows pending venue confirmation  

---

## Data Flow Diagram (Research Phase)

```
[DS-01 Player_Attribute_Matrix]
         │
         ▼
[C1: Signal Ingestion]
  - Schema validation
  - Snapshot ID assignment ──────────────▶ [DATA_SNAPSHOTS_INDEX.md]
  - Temporal labeling (event_date)
         │
         ▼
[C2: Feature Store]
  - Feature derivation (documented below)
  - Train/test split assignment (chronological)
  - Feature version tagging
         │
         ▼
[C3: Forecasting Engine]
  - Model inference
  - Probability estimate generation
  - Null model comparison (market-implied probability)
         │
         ▼
[C6: Audit Logger] ◀──── Events from all components
  - Forecast record logged
  - Snapshot ID preserved in log
```

---

## Lineage Register — Feature Derivations (FEATURE_VERSION 1.2.0)

*Every feature used in any model must have an entry here. FEATURE_VERSION 1.2.0 — 31 active features (F-001–F-031). F-032–F-038 pruned in v1.2.0 (HYP-005 falsified). Updated 2026-05-28.*

### Rolling Mean Features (L10 window, shift(1) before rolling — TI-01 ✅)

| Feature ID | Feature Name | Source Field(s) | Transformation | Temporal Safety |
|-----------|-------------|----------------|----------------|-----------------|
| F-001 | pts_l10_mean | pts | shift(1).rolling(10, min_periods=3).mean() per player | ✅ Uses prior 10 games only |
| F-002 | reb_l10_mean | reb | shift(1).rolling(10).mean() | ✅ |
| F-003 | ast_l10_mean | ast | shift(1).rolling(10).mean() | ✅ |
| F-004 | stl_l10_mean | stl | shift(1).rolling(10).mean() | ✅ |
| F-005 | blk_l10_mean | blk | shift(1).rolling(10).mean() | ✅ |
| F-006 | tov_l10_mean | tov | shift(1).rolling(10).mean() | ✅ |
| F-007 | min_l10_mean | min | shift(1).rolling(10).mean() | ✅ |
| F-008 | fg_pct_l10_mean | fg_pct | shift(1).rolling(10).mean() | ✅ |
| F-009 | fg3_pct_l10_mean | fg3_pct | shift(1).rolling(10).mean() | ✅ |
| F-010 | ft_pct_l10_mean | ft_pct | shift(1).rolling(10).mean() | ✅ |
| F-011 | plus_minus_l10_mean | plus_minus | shift(1).rolling(10).mean() | ✅ |
| F-012 | fgm_l10_mean | fgm | shift(1).rolling(10).mean() | ✅ |
| F-013 | fga_l10_mean | fga | shift(1).rolling(10).mean() | ✅ |
| F-014 | fg3m_l10_mean | fg3m | shift(1).rolling(10).mean() | ✅ |
| F-015 | fg3a_l10_mean | fg3a | shift(1).rolling(10).mean() | ✅ |
| F-016 | ftm_l10_mean | ftm | shift(1).rolling(10).mean() | ✅ |
| F-017 | fta_l10_mean | fta | shift(1).rolling(10).mean() | ✅ |
| F-018 | pf_l10_mean | pf | shift(1).rolling(10).mean() | ✅ |

### Rolling Std Features (L10, shift(1) — TI-01 ✅)

| Feature ID | Feature Name | Source Field(s) | Transformation | Temporal Safety |
|-----------|-------------|----------------|----------------|-----------------|
| F-019 | pts_l10_std | pts | shift(1).rolling(10, min_periods=3).std(ddof=1) | ✅ |
| F-020 | reb_l10_std | reb | shift(1).rolling(10).std(ddof=1) | ✅ |
| F-021 | ast_l10_std | ast | shift(1).rolling(10).std(ddof=1) | ✅ |
| F-022 | min_l10_std | min | shift(1).rolling(10).std(ddof=1) | ✅ |
| F-023 | plus_minus_l10_std | plus_minus | shift(1).rolling(10).std(ddof=1) | ✅ |

### Efficiency Composite Features (derived from L10 rolling means — TI-01 ✅)

| Feature ID | Feature Name | Source Field(s) | Transformation | Temporal Safety |
|-----------|-------------|----------------|----------------|-----------------|
| F-024 | ts_pct_l10_mean | pts_l10_mean, fga_l10_mean, fta_l10_mean | pts / (2 × (fga + 0.44 × fta)) | ✅ Derived from prior-game rolling means |
| F-025 | usage_proxy_l10_mean | fgm_l10_mean, ftm_l10_mean, tov_l10_mean, min_l10_mean | (fgm + 0.44×ftm + tov) / max(min, 1) | ✅ |
| F-026 | ast_tov_l10_mean | ast_l10_mean, tov_l10_mean | ast / max(tov, ε) | ✅ |

### Regime / Streak Flags (expanding window on rolling means — TI-01 ✅)

| Feature ID | Feature Name | Source Field(s) | Transformation | Temporal Safety |
|-----------|-------------|----------------|----------------|-----------------|
| F-027 | pts_hot_flag | pts_l10_mean, pts_l10_std | 1 if pts_l10_mean > expanding_mean(pts_l10_mean) + expanding_std(pts_l10_mean) | ✅ Uses prior-game rolling mean series only |
| F-028 | pts_cold_flag | pts_l10_mean, pts_l10_std | 1 if pts_l10_mean < expanding_mean − expanding_std | ✅ |

### Season Context Features (TI-01 ✅)

| Feature ID | Feature Name | Source Field(s) | Transformation | Temporal Safety |
|-----------|-------------|----------------|----------------|-----------------|
| F-029 | games_played_prior | game_date, season, season_type | cumcount() per (player, season, season_type) — 0-indexed count of prior games in season | ✅ Count of games before current |
| F-030 | pts_season_mean | pts | pts.shift(1).expanding(min_periods=1).mean() | ✅ Expanding mean of prior games only |
| F-031 | min_season_mean | min | min.shift(1).expanding(min_periods=1).mean() | ✅ |

### Schedule / Load Context Features — v1.1.0 ⚠️ PRUNED in v1.2.0

*Pruned 2026-05-28 (T-046). HYP-005 falsified: Δ Brier = +0.0002 vs v1.0.0 (threshold 0.005). Not active in FEATURE_VERSION 1.2.0.*

| Feature ID | Feature Name | Source Field(s) | Transformation | Status |
|-----------|-------------|----------------|----------------|--------|
| F-032 | season_type_is_playoffs | season_type | 1 if season_type == "Playoffs" else 0 | ❌ PRUNED v1.2.0 |
| F-033 | days_since_last_game | game_date | game_date.diff().dt.days per player | ❌ PRUNED v1.2.0 |
| F-034 | b2b_flag | days_since_last_game | 1 if days_since_last_game == 1 | ❌ PRUNED v1.2.0 |
| F-035 | load_games_l7d | game_date | Count of prior games where game_date ∈ (current − 7d, current) exclusive | ❌ PRUNED v1.2.0 |

### ERI v0 — Emotional Relay Index Features — v1.1.0 ⚠️ PRUNED in v1.2.0

*Pruned 2026-05-28 (T-046). HYP-005 falsified: no meaningful incremental signal over rolling box-score baseline. Not active in FEATURE_VERSION 1.2.0.*

| Feature ID | Feature Name | Source Field(s) | Transformation | Status |
|-----------|-------------|----------------|----------------|--------|
| F-036 | eri_prev_hot | pts_hot_flag | pts_hot_flag.shift(1) — was prior game a hot performance? | ❌ PRUNED v1.2.0 |
| F-037 | eri_prev_cold | pts_cold_flag | pts_cold_flag.shift(1) — was prior game a cold performance? | ❌ PRUNED v1.2.0 |
| F-038 | eri_consec_cold_games | pts_cold_flag | Consecutive cold game streak ending before current game (running count from shifted cold_flag) | ❌ PRUNED v1.2.0 |

### Market Price Feature (Phase 6+)

| Feature ID | Feature Name | Source Field(s) | Source (DS) | Transformation | Temporal Safety |
|-----------|-------------|----------------|------------|----------------|-----------------|
| F-099 | market_implied_prob | market bid/ask | DS-02 | mid_price = (bid + ask) / 2 | ✅ Price snapshot must be ≥1 min before event start |

*F-099 not active in Phase 3 — placeholder value 0.50 used for all backtesting.*

---

### Qualitative Features — F-100+ (Phase 6+ / Pending DS-01 Operationalization)

Qualitative features are loaded by `c2_feature_store/qualitative_store.py` via the `QualitativeSignalStore` module. They are joined to the feature DataFrame by `player_id` with an `effective_from` date guard (QTI-01). See `08_MODEL_RISK_GOVERNANCE/QUALITATIVE_SIGNALS.md` for full governance.

**Temporal safety:** Enforced by `effective_from` join guard, not by rolling window. Rows before `effective_from` receive NaN — not an error.

#### DS-01 PAM — PRF Archetype Features (F-100–F-149)

| Feature ID | Feature Name | Source | Transformation | Temporal Safety |
|-----------|-------------|--------|----------------|-----------------|
| F-100 | prf_primary | DS-01 PAM QS snapshot | Integer 1–15; player's primary PRF archetype | ✅ effective_from guard (QTI-01) |
| F-101 | prf_secondary | DS-01 PAM QS snapshot | Integer 0–15; secondary archetype (0=none) | ✅ effective_from guard |
| F-102 | prf_hybrid_weight | DS-01 PAM QS snapshot | Float 0–1; weight of primary in hybrid notation; NaN for pure archetype | ✅ effective_from guard |
| F-103–F-149 | (reserved) | DS-01 PAM | Reserved for future PRF-derived composite features | — |

#### DS-01 PAM — Modifier Features (F-150–F-181)

| Feature ID | Feature Name | Source | Transformation | Temporal Safety |
|-----------|-------------|--------|----------------|-----------------|
| F-150 | mod_01 | DS-01 PAM QS snapshot | Binary 0/1; Modifier 1 (name per DS-01 document) | ✅ effective_from guard |
| F-151 | mod_02 | DS-01 PAM QS snapshot | Binary 0/1; Modifier 2 | ✅ effective_from guard |
| F-152–F-181 | mod_03 … mod_32 | DS-01 PAM QS snapshot | Binary 0/1; Modifiers 3–32 | ✅ effective_from guard |
| F-182–F-199 | (reserved) | DS-01 PAM | Reserved for future modifier-derived features | — |

#### Reserved Ranges for Future Qualitative Sources

| Range | Reserved For | Source |
|-------|-------------|--------|
| F-200–F-249 | DS-04 (future source 1) | TBD |
| F-250–F-299 | DS-05 (future source 2) | TBD |
| F-300–F-399 | Cross-source composites | Multiple qualitative sources |

**Status:** All F-100+ features are PENDING. `QualitativeSignalStore` is implemented as a stub. Features will be NaN for all rows until DS-01 QS snapshot is populated and registered.

---

*Active features F-001–F-031 confirmed TI-01 compliant (automated tests in test_c2_features.py). F-032–F-038 were TI-01 compliant but pruned in v1.2.0 (HYP-005 falsified). Source for all quantitative features: DS-02 via nba_api (C1 NBAIngestionClient). Qualitative features F-100+: source DS-01 PAM + future sources via QualitativeSignalStore; governed by QUALITATIVE_SIGNALS.md.*

---

## Temporal Integrity Rules

These rules exist to prevent look-ahead bias — the primary data contamination risk.

| Rule | Description | Enforcement |
|------|-------------|-------------|
| TI-01 | All quantitative features must be computable using only data available at or before T_forecast | Temporal safety column in lineage register; automated check in backtesting framework |
| TI-02 | Training window must end before validation/test window begins (chronological split only; no random shuffling) | EXPERIMENTS must specify exact date splits; overlap check automated |
| TI-03 | Outcome data (T_resolution) must never appear in training data | Outcome field excluded from feature store; ingested separately after event resolution |
| TI-04 | Market prices used as features must be from a defined look-back window (e.g., ≥1 min pre-event), not from post-event | Feature definition must specify exact time offset |
| QTI-01 | Qualitative features must only be joined to game rows where game_date ≥ classification.effective_from | Enforced in QualitativeSignalStore.enrich_features() effective_from guard |
| QTI-02 | Classification effective_from must not predate the seasons used as classification basis | Documented in QS snapshot classification_basis field; enforced by operator discipline |
| QTI-03 | Historical backdating requires explicit evidence and second review | backdated + backdating_rationale fields in QS snapshot schema; see QUALITATIVE_SIGNALS.md §3 |
| QTI-04 | QS snapshots are immutable once registered | QS-ID registry in QUALITATIVE_REGISTRY.md; no silent modification after registration |

---

## Snapshot Discipline

Every dataset that enters the pipeline must be registered as a Snapshot before use:

1. **Assign Snapshot ID** — format: `SNAP-YYYY-MM-DD-NNN` (NNN = sequence for that date)
2. **Register in DATA_SNAPSHOTS_INDEX.md** — all required fields
3. **Reference in experiment record** — every EXPERIMENT_LOG entry must cite all Snapshot IDs used
4. **Immutability** — once registered, a snapshot is never modified. Corrections create a new snapshot with a lineage note.

---

## Live Data Flow (Phase 6+ — Design, Not Yet Active)

```
[Venue API] ──▶ [C1: Signal Ingestion]
                  - Real-time market data
                  - Price, volume, order book snapshots
                  - Outcome resolution events
                       │
                       ▼
                [C2: Feature Store]
                  - Rolling feature computation
                  - No training-window data accessible
                       │
                       ▼
                [C3: Forecasting Engine]
                  - Live inference only (model frozen)
                  - No retraining in production
                       │
                       ▼
                [C4: Risk Engine]
                  - Kelly sizing
                  - Hard limit checks
                       │
                       ▼
                [C5: Execution Engine]
                  - Order submission (Phase 8)
                       │
                       ▼
                [Venue API] ──▶ [C6: Audit Logger]
```

*Live data flow design frozen at G2; wired at G5.*
