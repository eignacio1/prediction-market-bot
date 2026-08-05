# Operator Console

> **GENERATED FILE — do not hand-patch.** Produced by `scripts/generate_operator_console.py` from `GOVERNANCE_GAP_LOG.md`'s live entries on every governance scan. Regenerated 46 open/in-progress entries into three sections, ranked by **blocks operator**, not severity. To change what appears here, fix the entry in GOVERNANCE_GAP_LOG.md or the classification regex in the generator script — never this file directly.

---

## 1. Decisions blocked on Earl (11)

Nothing else in this project moves on these until the operator decides. Detected via explicit operator/Earl/sign-off/awaiting-direction language already present in the entry's own text.

- **[GG-056]** NBA Main Pool Dormant at 24.9% Drawdown; No Reactivation Plan Before October Resume — `PLAN ACCEPTED` · severity `MEDIUM`
- **[GG-098]** MLB T1 Aggregate EV Metrics Are Cited as Milestones While Still Variance-Dominated (Small-n Subset Structure Masked; Aggregate Sign-Flipped n=151→169) — `OPEN` · severity `MEDIUM`
- **[GG-153]** T1's clean cohort is permanently frozen at clean_n=0 by the interaction of ADR-0048's zeroing and the epoch-10 ALL_BANDS reset; cannot self-heal under the current regime — `OPEN` · severity `MEDIUM`
- **[GG-040]** T4 Real-Time Data Sources: Required Feeds Not in Current C1 Architecture — `OPEN` · severity `UNSPECIFIED`
- **[GG-045]** Maximum Effective Bankroll Constrained by Kalshi Market Depth: Capital Ceiling Unanalyzed — `OPEN` · severity `UNSPECIFIED`
- **[GG-046]** T4 Commercial Validation: Independent Alpha Hypothesis Untested and Unregistered — `OPEN` · severity `UNSPECIFIED`
- **[GG-066]** MLB C1 Has No Real-Time/Sub-Poll-Interval Event Feed (Blocks Event-Driven T4 Sub-Bands) — `OPEN` · severity `UNSPECIFIED`
- **[GG-105]** T4M-PROJ (ACTIVE, highest-volume band) shows a statistically significant, tercile-monotonic ANTI-PREDICTIVE relationship between its own computed edge and realized win rate, on clean data (Workstream B / T-322/T-323/T-324 discovery) — `OPEN` · severity `UNSPECIFIED`
- **[GG-121]** 2026-07-11 T1 MLB `SemanticFloorViolation` (games_fetched=16, matched_players=0) surfaced by GG-049's own heartbeat but never logged — `WATCH ITEM` · severity `UNSPECIFIED`
- **[GG-124]** All four active MLB bands simultaneously clean_n=0/UNDERPOWERED, monitoring-coverage blackout from rapid-fire epoch boundaries — `OPEN` · severity `UNSPECIFIED`
- **[GG-125]** C7 `SystemMonitor`'s Brier/ECE drift-alarm ladder is never invoked from any production pipeline, for either sport — `OPEN` · severity `UNSPECIFIED`

---

## 2. What is actually broken (20)

Something is silently wrong right now — a HALT, an undetected blind spot, a contradiction between claim and code, or HIGH/CRITICAL severity.

- **[GG-154]** Session-start protocol cannot verify CLAUDE.md's architectural claims against live source, and Step 4 silently no-ops without SSH access — `OPEN` · severity `MEDIUM`
- **[GG-159]** PROJECT_ASSESSMENT_2026-07-30's T4M-PROJ headline reconstruction didn't match the code it claimed to match — verified figure is n=388/+9.65%, not n=344/+10.99% — `OPEN` · severity `MEDIUM`
- **[GG-161]** 22 stuck T1/T2 aged_open positions: OPS_HEALTH_AND_DEPTH_STATUS_2026-08-04.md's "not an API-outage signal" claim is contradicted by direct evidence; retries genuinely happen daily but a cron-window-correlated 406 failure mode was never surfaced — `OPEN` · severity `MEDIUM`
- **[GG-162]** GG-NNN numbers picked mid-session have no atomic reservation, unlike T-/ADR- ranges claimed at session start; two concurrent sessions independently registered GG-159 on 2026-08-04 — `OPEN` · severity `LOW`
- **[GG-004]** EV Validation Benchmark Was Never the Commercial Question — `OPEN` · severity `UNSPECIFIED`
- **[GG-020]** Kalshi Taker Fee Rate (0.07) Never Verified Against Actual Transaction Receipts — `ACCEPTED UNCERTAINTY` · severity `UNSPECIFIED`
- **[GG-038]** T4 Kill Switch SLA: 60s NFR-03 Is 12× Too Slow for Continuous T4 Evaluation — `OPEN` · severity `UNSPECIFIED`
- **[GG-060]** Silent Success Indistinguishability: Zero Bets from "No Edge" Looks Identical to Zero Bets from Pipeline Failure — `IN PROGRESS` · severity `UNSPECIFIED`
- **[GG-072]** T1 MLB (PIPE-05) HALTed by the Same GG-068 Bug On the Same Day, But Was Never Cross-Checked or Recovered — 2026-07-02 Betting Day Permanently Lost — `OPEN` · severity `UNSPECIFIED`
- **[GG-078]** T4 MLB's Real ~341-Bet/Day Cadence Means Kill-Switch Fate Is Decided Within ~15 Days Regardless of True Edge Sign; Long-Horizon Projections for T4 Are Not Meaningful at Any Stake Cap — `OPEN` · severity `UNSPECIFIED`
- **[GG-091]** `mypy --strict` Full-Tree Baseline: 365 Pre-Existing Errors in 57 Files, Not Yet Remediated — `PARTIAL RESOLVE` · severity `UNSPECIFIED`
- **[GG-137]** A1's holdout-Brier-optimal K=400 shrinkage candidate gives only ~7% weight to actual player data; may trade calibration for discrimination — `OPEN` · severity `UNSPECIFIED`
- **[GG-140]** GG-105 remediation exhausted the entire class of monotonic-transform recalibration candidates without a structural check ruling that class out first (temperature scaling, LR+Platt refit, isotonic — all tested serially, all failed the same way) — `OPEN` · severity `UNSPECIFIED`
- **[GG-143]** T4 MLB live engine goes silently blind to all in-progress games after any process restart that lands after 00:00 UTC; GG-058 fixed the in-loop rollover but left the cold-start path unprotected — `OPEN` · severity `UNSPECIFIED`
- **[GG-145]** `park_factor_hits` is hardcoded 1.0 across all 20,943 rows of the historical C2 feature matrix; second, independent instance of GG-141's failure shape, found live by GG-141's own preventive fix — `OPEN` · severity `UNSPECIFIED`
- **[GG-146]** 8 pre-existing test failures in `test_exp015_t3_simulation.py`, traced to ADR-0048's `T1_MULTI_DAY.kelly_fraction=0.0` propagating into `run_exp015.py`'s Monte Carlo simulation as a division-by-zero; first surfaced by a full-suite run on an unrelated branch — `OPEN` · severity `UNSPECIFIED`
- **[GG-151]** `merge=union` does not guarantee dedup: identical content reaching both merge sides via different commit paths can be duplicated, not deduplicated — `OPEN` · severity `UNSPECIFIED`
- **[GG-156]** No forward price archive existed for any MLB market family before 2026-08-01; Phase 2's market-comparison gate had no input source and the same absence limits GG-142 counterfactual analysis — `OPEN` · severity `UNSPECIFIED`
- **[GG-157]** `paper_trader.py` has zero orderbook/depth/fill validation; every paper fill (including the live epoch-12 flat-$1 cohort) is assumed at mid, and GG-155/T-411 shows that assumption sits against a quantity that swings 10-100x intraday — `OPEN` · severity `UNSPECIFIED`
- **[GG-160]** Four `file:line` citations across three Phase 0/1 docs had drifted from source with nothing catching it; no mechanism exists that resolves a doc's code citations against current source — `OPEN` · severity `UNSPECIFIED`

---

## 3. What is accruing and its clock (15)

Open, tracked, not currently blocking Earl and not flagged as actively broken — but still open, and the clock (epoch resets, n* thresholds, re-check triggers) keeps running. Default bucket: absence of blocked/broken signal, not absence of importance.

- **[GG-007]** T4/T5 Threshold Constants (`T4_MIN_DELTA_P`, `T5_YES_CERTAINTY`, `T5_NO_CERTAINTY`) Are Uncalibrated Skeleton Values — `OPEN` · severity `LOW`
- **[GG-014]** Kalshi API HTTP 429: ~50% of Order Placements Rate-Limited in Paper Mode — `PARTIALLY RESOLVED` · severity `UNSPECIFIED`
- **[GG-027]** PAM Integration Incomplete Across Bands: T2/T3/T5 Have No Archetype Wiring; Environment Classifier Not Built — `OPEN` · severity `UNSPECIFIED`
- **[GG-037]** Calibration Collapse + Inverted Edge Realization: the Model's Edge Signal Is Anti-Predictive — `OPEN` · severity `UNSPECIFIED`
- **[GG-039]** T4 Price Cache / Staleness Check Architecture — `OPEN` · severity `UNSPECIFIED`
- **[GG-041]** KXNBAPTS Orderbook Depth Data: Finals Window Missed; ADR-0005 Limit Empirical Basis Absent — `OPEN` · severity `UNSPECIFIED`
- **[GG-064]** Kalshi DEMO Market `open_time` Lags LIVE for Same Ticker (Discovered During GG-063 Verification, Unconfirmed as Structural) — `LIKELY RESOLVED` · severity `UNSPECIFIED`
- **[GG-094]** MLB Has No Qualitative/PRF-Analogue Feature Layer Despite Being the Sole ACTIVE Pool — `OPEN` · severity `UNSPECIFIED`
- **[GG-127]** 00_ADMIN/README.md (designated nav hub, ADR-0001) went ~7 weeks with zero updates while the project moved through multiple phase transitions — `IN PROGRESS` · severity `UNSPECIFIED`
- **[GG-132]** MEMORY_BANK.md `**Last reviewed:**` narrative chain regrew unchecked 9→52 entries since T-334's 2026-07-11 fix; the 2026-07-15 ADR-0044 re-application consolidated only the sibling `## Current State Snapshot` chain, not this one — `OPEN` · severity `UNSPECIFIED`
- **[GG-133]** CHANGELOG.md has not been updated since 2026-05-30 despite ~2 months of major changes, violating its own staleness trigger — `OPEN` · severity `UNSPECIFIED`
- **[GG-134]** `mc_empirical_bootstrap.py`'s forward-risk projection has four unmodeled scope gaps not disclosed as limitations at commit time — `OPEN` · severity `UNSPECIFIED`
- **[GG-136]** No standing archival cadence exists for `04_EXECUTION/TODO_NEXT.md`'s own `## T-NNN` task sections (same class as GG-127) — `IN PROGRESS` · severity `UNSPECIFIED`
- **[GG-150]** Cross-book (T1 vs T4) opposite-direction conflicts are alarmed, not blocked; a blocking control is an unstaffed gap — `OPEN` · severity `UNSPECIFIED`
- **[GG-158]** Price archive had zero off-VPS copies for 3+ sessions despite repeated "verified"/"deployed" reports; same failure class as GG-144's unanchored grep — `OPEN` · severity `UNSPECIFIED`

---

**Full record for every entry above:** `03_DECISIONS/GOVERNANCE_GAP_LOG.md`. **Resolved/closed history:** `03_DECISIONS/GOVERNANCE_GAP_LOG_ARCHIVE.md`.

