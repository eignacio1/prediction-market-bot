# Segmented Pool Architecture — Market-Type Expansion (Phases 1 & 3)

**Status:** DRAFT — design note, no code, no live change. Requires an ADR before implementation.
**Date:** 2026-07-30
**Scope:** the seams that must change to support team-level MLB markets (moneyline / run line / totals) as independently-measured pools, without contaminating the player-prop measurement.
**Precondition:** Phase 0 survey (`MARKET_UNIVERSE_SURVEY_SPEC.md`) complete. Nothing here starts first.

---

## 1. The problem this solves

Two things are true and they pull against each other. Operator directive 2026-07-30 is that the three core market families must exist as testable capability — absent the capability there is no option to test it, and "these markets are efficient" is a prior, not a finding (GG-037 tested NBA Finals *player props*, not MLB game markets). Against that: the props book is 3–4 weeks from its first clean verdict, and every shared-seam defect to date has reset `clean_n` to zero across everything.

**The design goal is therefore not "add markets." It is: add markets such that a defect in one family cannot reset another family's measurement.** Segmentation is the whole deliverable.

---

## 2. Blast radius, measured against source (HEAD=00201fe)

| Component | Verdict | Evidence |
|---|---|---|
| C1 `c1_signal_ingestion` | **Mostly built** | `MLBTeamStatsStore` exposes `get_opp_runs_scored()` / `get_opp_runs_allowed()`, rolling, TI-01 temporally guarded, cache-serializable, built from `MLBIngestionClient.fetch_completed_games()`. `MLBPitcherStatsStore` gives ERA/K9/BB9 L5. These are the inputs a team scoring-rate model needs. |
| C2 `c2_feature_store` | **New** | `mlb_features.py` emits batter-game rows; `MLB_FEATURE_CSV_CONTRACT` is batter/pitcher shaped. Needs a team-game matrix + its own `SourceContract`. |
| C3 `c3_forecasting` | **Extend, not author** | `scoring_distribution.py` (NB/Poisson) already states its purpose as *"one λ estimate → P(X≥n) for ANY n… multiplies addressable markets without new data or retraining"* — built under T-076/EXP-013, currently an ADR-0004 experimental supplement, never promoted. `game_state_model.py` is structurally already a totals model. |
| C4 `risk.py` | **No market-shape change required** | `evaluate_forecast()` reads eight record fields — `forecast_id`, `p_estimate`, `edge`, `gross_edge`, `recommended_direction`, `market_implied_prob`, `vig`, `kelly_fraction`. **Correction (2026-07-31 audit): the first draft of this row listed only five and stated "no change required." Both were wrong** — the field list was incomplete, and ADR-0050 subsequently added a `fixed_stake_usd` parameter (`risk.py:361/456/715`). The *conclusion* survives: every one of the eight is market-type-neutral, no player fields, so no market-shape change is required. **But it is the contamination seam — see § 3.** |
| C5 `paper_trader.py` | **Hard seam** | `open_position()` (L380) requires `player_name: str`, `player_id: int`, `kalshi_threshold: int`, and carries the per-band vig cascade (branches at L460/462/464, verified 2026-07-31 — the first draft cited L462-468) already flagged as a cross-band contamination risk. |
| C5 `venue_adapter.py` | **Repair first** | The protocol's own abstract method is `fetch_player_points_markets()`. The layer designed for extensibility hardcodes one market type. |
| C5 `kalshi_client.py` | **Repair** | One series constant (`SERIES_MLB_PLAYER_HITS`), one player-shaped fetch, `_parse_market()` → `PlayerMarket`. |
| C5 `market_mapper.py` | **Build** | Contains `normalize_player_name`, `market_key`, `group_by_key` — a name matcher. The market-type registry CLAUDE.md claims lives here does not exist. |
| C5 `portfolio_schema.py` | **No change** | `REQUIRED_TOP_LEVEL_FIELDS` is market-agnostic. A new pool file needs no schema change. |
| C6 audit | Trivial | 1 player-shaped reference. |
| C7 monitoring | Small | `monitor.py` 1 ref; `semantic_contracts.py` 13 — oracles are prop-shaped, need family analogues. |
| C8 dashboard | Small | 2 refs. |
| Registries | **Extend** | `run_band_monitor.py` hardcodes `BOOK_BANDS = ("T1","T2","T3")` with T4M-PROJ special-cased; `run_power_calc.py` mirrors it; `execution_bands.BAND_CONFIGS` and `logic_epoch.bands_affected` need entries. |
| Tests | **53 of 83 files** reference player/threshold shape | Not all require change; that is the surface. |

---

## 3. The isolation boundary — the load-bearing decision

`risk.py::evaluate_forecast()` is shared, unconditional, and has no band gate. GG-142 lived there; epoch 10 was scoped `ALL_BANDS` (`bands_affected={"*"}`) precisely because a change there alters every band's write path. **If team-level families route through it unmodified, a defect in the shared gate still resets the props cohort along with theirs.** That is the exact failure this design exists to prevent, and it is not solved by separate ledger files.

Three options. Pick one explicitly in the ADR — do not leave it implicit.

**Option 1 — Accept coupled resets at the shared gate.** Simplest. Keeps one risk engine. Cost: any C4 correctness fix zeroes `clean_n` for every family simultaneously, exactly as on 2026-07-30. Given the observed defect-discovery rate, this plausibly means no family ever completes a 14-day window. **Not recommended.**

**Option 2 — Per-family epoch scoping at the C4 seam.** Extend `bands_affected` so a C4 change can be scoped to the families whose computation it actually alters, determined by inspecting the diff rather than defaulting to `ALL_BANDS`. Requires discipline (the `ALL_BANDS` default exists because scoping honestly is hard), but it is a measurement-layer change only, no execution risk. **Recommended — and now with two live precedents.** Epochs 11 (GG-046/ADR-0050, flat-stake reactivation) and 12 (GG-149, offsetting suppression) both landed 2026-07-31 scoped `bands_affected={"T4M-PROJ"}` while touching `risk.py`'s shared `evaluate_forecast()` signature, and neither reset MAIN's floor (T1 floor stayed at 10, T4M-PROJ moved to 12). That is exactly this option working in production, on the exact seam in question, before the first team-level family exists.

**Option 3 — Separate RiskEngine instance per family.** Full isolation, at the cost of duplicating the one component that is currently correct and market-agnostic. Divergence risk over time. Only justified if Option 2 proves unworkable.

**Whichever is chosen, the following are non-negotiable per family:** its own portfolio/ledger file · its own `clean_n` and `n*` (independent `run_power_calc.py` row) · its own band-monitor entry · its own kill switch (band-level halt must not halt other families; system-level must halt all) · its own semantic oracles.

---

## 4. Two controls that must exist before any family goes live

**4.1 — Offsetting-position suppression. STATUS: intra-book BUILT 2026-07-31 (GG-149, epoch 12); cross-book ALARM-ONLY; cross-family NOT BUILT.** The historical T4 ledger held **161 tickers with simultaneously-open YES and NO positions** (all 161 simultaneous, zero sequential — see `MARKET_UNIVERSE_SURVEY_SPEC.md` § 3): a measurement dilution at paper scale (374 of 2,015 legs, 18.6%, structurally zero information) and a wash-trade exposure at live capital on a CFTC-regulated DCM. `run_t4_mlb_live.py` now carries `_find_open_position_opposite_direction()` (intra-book skip) and `_t1_open_position_opposite_direction()` (cross-book warning). `complement_lock_scanner.py` addresses *cross-venue* complement locks and does **not** cover either case — confirmed, not assumed.

**What remains open is the part this section exists for.** Intra-book suppression keys on identical `kalshi_ticker`. Team-level families break that key: moneyline, run line, and totals on the same game are **economically correlated, not independent**, so an offsetting exposure can exist across two different tickers with no string match. The existing guard will not see it.

The team-level families make this materially harder, not easier: moneyline, run line, and totals on the same game are **economically correlated, not independent**. A YES on the favourite plus an OVER is not an offsetting pair, but a run-line NO plus a moneyline YES on the same side substantially is. The control therefore has to reason about correlated exposure across families, not just identical-ticker collisions. Design it once, at the pool-manager level, not per-runner.

**4.2 — Feature-column health from day one.** GG-141 (four `opp_sp_*` columns 100% blank for weeks, cache poisoning) and GG-145 (`park_factor_hits` hardcoded 1.0 across 20,943 rows) are the same failure shape, found twice, both by accident. `scripts/check_feature_column_health.py` exists now. Wire it into the team-level C2 generation path **before** the first feature matrix is produced, not retrofitted after the third instance.

---

## 5. Phase plan

| Phase | Work | Live impact | Gate to exit |
|---|---|---|---|
| **0** | Market universe survey + compliance validation | None (read-only API) | Survey artifact committed; depth ≥ ~10× intended stake per family |
| **1** | Abstraction repair: market-type registry, `VenueAdapter` generalized, `open_position()` signature generalized, vig cascade extracted to per-market-type config. **No new markets.** Correct CLAUDE.md's two false claims. | None — props behavior must be **bit-identical**, verified by replaying the existing ledger through the refactored path | Replay produces byte-identical positions; full suite green |
| **2** | Team-game C2 matrix; fit `scoring_distribution` at team level; score offline against historical Kalshi prices via a D1-style what-if harness | None — offline only, no shared write path, no epoch impact | **Does the model beat historical closing prices offline?** If no, stop. No live risk spent. |
| **3** | Segmented pool infrastructure: ledgers, band configs, epoch scoping per § 3, power-calc and band-monitor enumeration, semantic oracles, § 4 controls | First point of contact with shared seams | Isolation proven — inject a synthetic C4 change and confirm it resets only the intended families' `clean_n` |
| **4** | Shadow, then flat-stake measurement, per the T4M-PROJ pattern | Live, measurement-only | Own `clean_n ≥ n*` |

**Concurrency.** Phases 1 and 2 touch different files from the live props path and can run in parallel with the T4 accrual. **Phase 3 is the first phase that must wait** — it is the first to touch shared seams, and it should land after the props verdict. Phase 1's bit-identical requirement is what makes its concurrency safe; if the replay does not reproduce exactly, Phase 1 stops and waits too.

---

## 6. Assumptions | Risks | Validation | Confidence

**Assumptions.** `scoring_distribution.py` works as documented — EXP-013's actual result has not been read and may have found it worse-calibrated than LR+Platt. `MLBTeamStatsStore`'s runs-scored/allowed series are populated in practice (GG-141 is the precedent for a store that exists, is correct, and is silently not joined). The 53/83 test-file figure is a grep on `player_id|player_name|kalshi_threshold`, an upper bound on true blast radius.

**Key risks.** Phase 1's refactor touches `open_position()` — the single shared write path for every band — and a defect there is the highest-severity outcome in this plan; the bit-identical replay gate exists specifically for that. Correlated-exposure control (§ 4.1) is genuinely harder than same-ticker suppression and could become its own project. Operator attention, not compute, is the scarce resource; running Phases 1–2 alongside the props accrual is the main thing that could compromise the verdict this plan is designed to protect.

**Validation checks.** (1) Phase 1 replay: byte-identical position records. (2) Phase 3 isolation test: synthetic C4 change resets only intended families. (3) Confirm EXP-013's actual verdict on `scoring_distribution.py` before Phase 2 assumes it. (4) Confirm `MLBTeamStatsStore` returns non-degenerate values across a full season via `check_feature_column_health.py`.

**Confidence.** Blast-radius map — High (measured against source). C1 readiness — Medium-High. C3 reusability — Medium (depends on unread EXP-013). Isolation Option 2 workability — Medium. That team-level MLB markets on Kalshi are beatable — **Unknown, and deliberately so; Phase 2's gate is what answers it.**
