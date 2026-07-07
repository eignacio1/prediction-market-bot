# MLB Build-Out Scaffold Plan (T-174 WS4)

**Status:** DRAFT — scaffold/plan only. No MLB code emits live bets until its own gate.
**Prepared:** 2026-06-14 (SESSION 63, dark-period transition)

**⚠️ Corrected 2026-07-06 (GG-074 remediation) — this entire document describes a not-yet-built future state that has since been completed and gone live.** As of this correction, MLB is the ACTIVE paper-trading pool (per CLAUDE.md and `MEMORY_BANK.md`'s Current State Snapshot): C1 MLB ingestion, C2 MLB feature store, C3 MLB forecasting model (LR + Platt per ADR-0004, as this plan anticipated), and `market_mapper` MLB registration are all live and cron/systemd-managed on the VPS. MLB T1/T2/T3/T4M-PROJ are cron-active; T4M-ARITH/T4M-FLOW are built-but-registry-BLOCKED pending their own EXP verdicts (ADR-0039). MLB has 99/30 resolved paper bets (well past the 30-bet floor) and EXP-017's MLB run has cleared ADR-0024 Tier 1 (n=151, DIRECTIONAL_POSITIVE) per CLAUDE.md's commercial-validation-gap section. **Correction to this note (same pass, caught on re-verification):** an earlier draft of this note claimed the C2 MLB feature store included "PRF-analogue qualitative features" per Section 2 below's anticipated "baseball analogue of the PRF framework" — this is **not accurate**. Direct inspection of `c2_feature_store/mlb_features.py` (541 lines, `MLB_FEATURE_VERSION = "1.0.0"`) found zero qualitative/archetype/role/PRF content — it is purely quantitative rolling-batter-stat features (`_compute_rolling_batter_features`, opposing-starter and venue lookups). `qualitative_store.py`/`qualitative_amplifier.py` also have no MLB references. The PRF-analogue qualitative layer this plan anticipated for MLB was never built — MLB's C2 is quantitative-only. Treat this as a real, current scope gap (not just doc staleness) if MLB's model relies on qualitative context the way NBA's does. This plan document is retained as a historical record of the original build sequencing (contract → C1 → C2 → C3 → market_mapper), not as a description of current status — do not read "Status: DRAFT" or any open constraint below (C-1, C-2, "operator decision" on data source, etc.) as still unresolved without checking current code/MEMORY_BANK.md first.
**Architectural invariant (CLAUDE.md):** adding a sport = new C1 + new C2 + new C3 +
register market type in `market_mapper`. **C4–C8 do not change.** If MLB needs more
than this, something is wrong — surface it before building.

---

## What WS4 delivered now (code-complete, tested)

1. **`analytics/bet_record_contract.py`** — the sport-agnostic bet-record contract.
   This is the keystone: it generalizes the NBA WS2 schema (`clean_dataset.COLUMNS`)
   into sport-neutral field names (`subject_name`, `stat_type`, `threshold`,
   `venue_ticker`, …) plus a `validate_bet_record()` validator. Proven against the
   real 158-row NBA dataset via `from_nba_row` (`test_bet_record_contract.py`).
   **MLB C2 must emit rows that pass `validate_bet_record` with `sport="MLB"`.**

2. **`market_mapper.py` sport-agnosticism verified.** Name normalization +
   `(normalized_name, threshold)` key carry no NBA-specific logic. MLB player markets
   route through it unchanged. **Two constraints to resolve before MLB activation**
   (below) — flagged, not silently assumed.

---

## Constraints surfaced (do NOT assume away)

- **C-1 `PlayerMarketKey.threshold: int`** (`market_mapper.py:44`). NBA points markets
  are integer "X+" thresholds. MLB count props (strikeouts, hits, total bases) are
  also integer "X+" on Kalshi *as currently understood* — **verify against the actual
  MLB market structure before relying on it.** If any MLB stat uses a half-point line,
  `threshold` must widen to a numeric type. (Per "verify external claims" — this is a
  market-structure fact to confirm with Kalshi data, not to assert.)
- **C-2 No `sport` dimension in `PlayerMarketKey`.** Cross-venue grouping is currently
  sport-implicit (one snapshot = one sport per run). When NBA + MLB run concurrently,
  either (a) keep runs sport-partitioned, or (b) add `sport` to `PlayerMarketKey`.
  Decision deferred to MLB activation; recorded here so it is not discovered late.

## What MLB needs (the four-part build)

### 1. C1 — MLB ingestion (`c1_ingestion/mlb/…`)
- New module mirroring the NBA C1 output schema (IF-C1-C2 contract).
- **Data source is an operator decision.** Do not fabricate an MLB stats API.
  Candidates to evaluate (operator/DS to choose + verify access/licensing):
  MLB StatsAPI, a paid feed, etc. Source selection + reliability must be sourced,
  per the project's "verify external claims" standard.
- Output: raw per-player, per-game stat lines conforming to the existing C1 schema.

### 2. C2 — MLB feature store (`c2_feature_store/mlb/…`)
- New feature set for baseball: rolling stat performance, rest/travel, park factors,
  handedness matchup, lineup/role. (Baseball analogue of the PRF framework.)
- **Output must conform to `bet_record_contract`** with `sport="MLB"` and the right
  `stat_type` values (strikeouts, hits, total_bases, …).

### 3. C3 — MLB forecasting model
- New model trained on baseball data. Same model-class policy (LR + Platt, ADR-0004)
  unless a superseding ADR is filed. Frozen-model policy applies (Hard rule #4).
- Must produce calibrated `model_p` per market; calibration validated before activation.

### 4. `market_mapper` registration
- Register MLB market types / ticker patterns. Resolve C-1 and C-2 above first.

## Gating

MLB inherits the full gate discipline. No MLB live capital — paper-trading validation,
calibration sign-off, and commercial validation (the MLB analogue of EXP-017) all apply.
This plan is the scaffold; each part lands behind its own task + tests.

## Why the contract comes first

The NBA close-out (WS3) froze the canonical NBA record. The bet-record contract makes
that record's shape the cross-sport standard, so MLB data lands in the same analysis
substrate (true-baseline P&L, drawdown, EXP-017-style commercial test) with zero rework
of C4–C8. Build order: **contract (done) → C1 data source decision → C2 features →
C3 model → market_mapper registration.**
