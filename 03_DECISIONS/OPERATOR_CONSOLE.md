# Operator Console

> **GENERATED FILE — do not hand-patch.** Produced by `scripts/generate_operator_console.py` from `GOVERNANCE_GAP_LOG.md`'s live entries on every governance scan. Regenerated 72 open/in-progress entries into three sections, ranked by **blocks operator**, not severity. To change what appears here, fix the entry in GOVERNANCE_GAP_LOG.md or the classification regex in the generator script — never this file directly.

> **Severity debt:** 30/72 live entries have no explicit severity (`UNSPECIFIED`) — sort order below is unreliable wherever it relies on severity for entries not in this backfill's scope. See GG-165.

---

## 1. Decisions blocked on Earl (4)

Nothing else in this project moves on these until the operator decides. Detected via explicit operator/Earl/sign-off/awaiting-direction language already present in the entry's own text.

- **[GG-046]** T4 Commercial Validation: Independent Alpha Hypothesis Untested and Unregistered — `OPEN` · severity `HIGH`
- **[GG-125]** C7 `SystemMonitor`'s Brier/ECE drift-alarm ladder is never invoked from any production pipeline, for either sport — `OPEN` · severity `MEDIUM`
- **[GG-153]** T1's clean cohort is permanently frozen at clean_n=0 by the interaction of ADR-0048's zeroing and the epoch-10 ALL_BANDS reset; cannot self-heal under the current regime — `OPEN` · severity `MEDIUM`
- **[GG-045]** Maximum Effective Bankroll Constrained by Kalshi Market Depth: Capital Ceiling Unanalyzed — `OPEN` · severity `LOW`

---

## 2. What is actually broken (6)

Something is silently wrong right now — a HALT, an undetected blind spot, a contradiction between claim and code, or HIGH/CRITICAL severity.

- **[GG-038]** T4 Kill Switch SLA: 60s NFR-03 Is 12× Too Slow for Continuous T4 Evaluation — `OPEN` · severity `HIGH`
- **[GG-143]** T4 MLB live engine goes silently blind to all in-progress games after any process restart that lands after 00:00 UTC; GG-058 fixed the in-loop rollover but left the cold-start path unprotected — `OPEN` · severity `HIGH`
- **[GG-060]** Silent Success Indistinguishability: Zero Bets from "No Edge" Looks Identical to Zero Bets from Pipeline Failure — `IN PROGRESS` · severity `MEDIUM`
- **[GG-091]** `mypy --strict` Full-Tree Baseline: 365 Pre-Existing Errors in 57 Files, Not Yet Remediated — `PARTIAL RESOLVE` · severity `MEDIUM`
- **[GG-154]** Session-start protocol cannot verify CLAUDE.md's architectural claims against live source, and Step 4 silently no-ops without SSH access — `OPEN` · severity `MEDIUM`
- **[GG-161]** 22 stuck T1/T2 aged_open positions: OPS_HEALTH_AND_DEPTH_STATUS_2026-08-04.md's "not an API-outage signal" claim is contradicted by direct evidence; retries genuinely happen daily but a cron-window-correlated 406 failure mode was never surfaced — `OPEN` · severity `MEDIUM`

---

## 3. What is accruing and its clock (62)

Open, tracked, not currently blocking Earl and not flagged as actively broken — but still open, and the clock (epoch resets, n* thresholds, re-check triggers) keeps running. Default bucket: absence of blocked/broken signal, not absence of importance.

- **[GG-170]** MLB Stats API `gameLog` date-label is transiently unstable in near-real-time; a delayed/retried resolution query can bind to `game_date+1`'s true hit total instead of `game_date`'s, root-causing the second B5 disagreement source GG-166 left unexplained — `OPEN` · severity `CRITICAL`
- **[GG-185]** 532 closed T4M-PROJ epoch-12 positions carry a ticker-vs-`game_date` mismatch despite the GG-166 guard, which should have refused every one of them, being confirmed deployed and unconditional at their `resolved_at` time — `OPEN` · severity `CRITICAL`
- **[GG-172]** `MARKET_EXPANSION_ACTION_PLAN.md` Phases 1-4 are written entirely in market-type terms and contain zero boxes addressing band activation, even though the operator's coverage directive is explicitly "all five bands" and three of five bands have essentially no trading history — `OPEN` · severity `HIGH`
- **[GG-179]** 22 data-dependent tests silently SKIP whenever their generated artifacts/secrets are absent, and CI (`.github/workflows/tests.yml`) has never once provided them — "full suite green" has been environment-dependent since T-337 with no executable check on the skip count — `RESOLVED (partial) — the 10 CSV-only tests now execute in CI via a synthetic fixture, including the MLB-G1 name-match regression gate; an executable skip-count ceiling (ADR-0052) is now enforced; the 11 secrets/combined-gated tests and 6 pre-existing model-pkl-gated tests remain unprovisioned in CI by design/scope` · severity `HIGH`
- **[GG-186]** SESSION_CLAIMS.md closure rows for T-458 and T-460 asserted "CLOSED" from local branch/commit state alone, with no check that either branch had actually reached `origin/main` — 4th occurrence of the same pattern (T-456 x2, T-458, T-460) — `RESOLVED` · severity `HIGH`
- **[GG-056]** NBA Main Pool Dormant at 24.9% Drawdown; No Reactivation Plan Before October Resume — `PLAN ACCEPTED` · severity `MEDIUM`
- **[GG-098]** MLB T1 Aggregate EV Metrics Are Cited as Milestones While Still Variance-Dominated (Small-n Subset Structure Masked; Aggregate Sign-Flipped n=151→169) — `OPEN` · severity `MEDIUM`
- **[GG-159]** PROJECT_ASSESSMENT_2026-07-30's T4M-PROJ headline reconstruction didn't match the code it claimed to match — verified figure is n=388/+9.65%, not n=344/+10.99% — `OPEN` · severity `MEDIUM`
- **[GG-163]** T4 MLB has been fully blind since 2026-08-04 23:41 UTC: ESPN game-ID discovery 403s on every poll (723/723), `systemctl is-active` shows healthy throughout, zero new cycle-log rows for 24h+ during live game nights — `RESOLVED (2026-08-07, T-429)` · severity `MEDIUM`
- **[GG-168]** Step 4's T4 cycle-log write-recency probe (GG-163/T-429) has no exemption for "daily T4 budget exhausted" — a legitimate zero-new-rows state indistinguishable from a real outage by the probe's own logic — `OPEN` · severity `MEDIUM`
- **[GG-171]** `ACTIVE_QUEUE.md`'s own T-436 task template says "Do NOT start Phase 1 even if depth clears — Phase 1 is separately blocked on T-431," but T-427's audit already scoped T-431's remaining work (outcome/pnl re-derivation) outside box 1.6's actual replay gate — the file's blocker framing appears stale against its own project's prior finding — `RESOLVED` · severity `MEDIUM`
- **[GG-174]** `PolymarketVenueAdapter._parse_market()`'s CLOB query hardcodes `"tag": "nba"` (KI-019), unconfirmed against Polymarket's real tag taxonomy, and silently returns an empty market set for any other value — `OPEN` · severity `MEDIUM`
- **[GG-180]** T-427 replay gate only ever exercised T4M-PROJ and T1 (via real ledger data); T2, T3, and the band=None fallthrough had zero replay coverage, and T2/T3 can never get real coverage since their kelly_fraction=0.0 means they never reach `open_position()`'s write path — `RESOLVED (partial) — synthetic fixture coverage added for T1/T2/T3/None at current epoch; the real-ledger T1 gap (zero T1 positions at current logic_epoch 12) remains, mitigated but not eliminated, by the synthetic fixture` · severity `MEDIUM`
- **[GG-181]** T4 MLB cycle-log 14.6h stale during live MLB game day, `systemctl is-active`/`ActiveState=active`/`NRestarts=0` healthy throughout — same GG-163-class blind spot recurring after GG-163 itself was marked RESOLVED — `RESOLVED` · severity `MEDIUM`
- **[GG-182]** Session-end token/time cost is unaddressed by Hard Rule 8's 60% trigger — second remediation attempt (T-434 fixed WHEN close-out starts, not WHAT IT COSTS); 2026-08-14 session-end consumed 53% context / ran 52m41s — `OPEN` · severity `MEDIUM`
- **[GG-188]** T-463 (team runs-scored outcome store for archived `KXMLBTOTAL` game-events, Phase 2 unblock) was claimed and never implemented, closed, or explained; Phase 2 remains blocked exactly where HYP010's Finding 5 left it — `OPEN` · severity `MEDIUM`
- **[GG-007]** T4/T5 Threshold Constants (`T4_MIN_DELTA_P`, `T5_YES_CERTAINTY`, `T5_NO_CERTAINTY`) Are Uncalibrated Skeleton Values — `OPEN` · severity `LOW`
- **[GG-162]** GG-NNN numbers picked mid-session have no atomic reservation, unlike T-/ADR- ranges claimed at session start; two concurrent sessions independently registered GG-159 on 2026-08-04 — `OPEN` · severity `LOW`
- **[GG-165]** 38/46 live gap entries carry no explicit Severity (UNSPECIFIED); full backfill deliberately deferred out of T-423's XS scope — `OPEN` · severity `LOW`
- **[GG-167]** `deploy.yml`'s dirty-tree guard only inspects tracked files; an untracked-file collision on the VPS silently blocked `git pull --ff-only` during GG-163's deploy, sibling gap shape to the already-resolved GG-130 — `OPEN` · severity `LOW`
- **[GG-169]** `claim_session.sh`'s collision check cannot distinguish "actively claimed" from "pre-reserved backlog ID awaiting staffing," blocking the exact workflow the project uses to hand off follow-on work — `RESOLVED` · severity `LOW`
- **[GG-173]** `test_t187e_mlb_resolve.py::TestFetchMlbHits::test_multiple_splits_matches_correct_date` computes its two mocked dates from the live clock at two different times (module-import time vs. test-execution time), so a CI run whose collection-to-execution window straddles UTC midnight can make both dates collide and the test fail — `RESOLVED` · severity `LOW`
- **[GG-175]** Assertion N (`ticker_player_token_consistent`) has 1 live violation in epoch 12: ticker token `NLOPE` vs. name "Nicky Lopez" — a short-token collision the matcher doesn't handle — `RESOLVED` · severity `LOW`
- **[GG-176]** `scripts/lib_chain_archive.py`'s `archive_chain()` silently no-ops whenever a nav file's `**Last reviewed` chain has exactly 1 entry, so the pointer never advances and every session sees a stale "Last reviewed" line — `RESOLVED` · severity `LOW`
- **[GG-177]** `session_end_prep.sh`'s Step 0 SESSION_CLAIMS.md lookup matches on the worktree branch's timestamp, but `claim_session.sh` stamps its row at actual claim-command time — the two are seconds-to-minutes apart, so the exact-string match fails on effectively every session even when the claim genuinely exists — `OPEN` · severity `LOW`
- **[GG-178]** `scripts/check_register_parity.py`'s `RESOLVED_PAT` regex is a bare substring search with no negation awareness, so it false-flags any ADR whose Status prose contains the literal text "NOT ACCEPTED"/"not yet ACCEPTED" as resolved — `OPEN` · severity `LOW`
- **[GG-183]** Per-cell kill-switch state (ADR-0053 §2.3/§6.3 item 4) has a store and a resolution helper but is not wired into C4/C7's live kill-switch check — `OPEN` · severity `LOW`
- **[GG-184]** `open_position()`'s `market_type` parameter defaults silently; 100% of live call sites rely on the default rather than passing it explicitly — `OPEN` · severity `LOW`
- **[GG-187]** T2's gross-edge formula is known but epoch-conditional; unsafe to backfill into assert_ledger_invariants.py's flat multiplier — `OPEN` · severity `LOW`
- **[GG-004]** EV Validation Benchmark Was Never the Commercial Question — `OPEN` · severity `UNSPECIFIED`
- **[GG-014]** Kalshi API HTTP 429: ~50% of Order Placements Rate-Limited in Paper Mode — `PARTIALLY RESOLVED` · severity `UNSPECIFIED`
- **[GG-020]** Kalshi Taker Fee Rate (0.07) Never Verified Against Actual Transaction Receipts — `ACCEPTED UNCERTAINTY` · severity `UNSPECIFIED`
- **[GG-027]** PAM Integration Incomplete Across Bands: T2/T3/T5 Have No Archetype Wiring; Environment Classifier Not Built — `OPEN` · severity `UNSPECIFIED`
- **[GG-037]** Calibration Collapse + Inverted Edge Realization: the Model's Edge Signal Is Anti-Predictive — `OPEN` · severity `UNSPECIFIED`
- **[GG-039]** T4 Price Cache / Staleness Check Architecture — `OPEN` · severity `UNSPECIFIED`
- **[GG-040]** T4 Real-Time Data Sources: Required Feeds Not in Current C1 Architecture — `OPEN` · severity `UNSPECIFIED`
- **[GG-041]** KXNBAPTS Orderbook Depth Data: Finals Window Missed; ADR-0005 Limit Empirical Basis Absent — `OPEN` · severity `UNSPECIFIED`
- **[GG-064]** Kalshi DEMO Market `open_time` Lags LIVE for Same Ticker (Discovered During GG-063 Verification, Unconfirmed as Structural) — `LIKELY RESOLVED` · severity `UNSPECIFIED`
- **[GG-066]** MLB C1 Has No Real-Time/Sub-Poll-Interval Event Feed (Blocks Event-Driven T4 Sub-Bands) — `OPEN` · severity `UNSPECIFIED`
- **[GG-072]** T1 MLB (PIPE-05) HALTed by the Same GG-068 Bug On the Same Day, But Was Never Cross-Checked or Recovered — 2026-07-02 Betting Day Permanently Lost — `OPEN` · severity `UNSPECIFIED`
- **[GG-078]** T4 MLB's Real ~341-Bet/Day Cadence Means Kill-Switch Fate Is Decided Within ~15 Days Regardless of True Edge Sign; Long-Horizon Projections for T4 Are Not Meaningful at Any Stake Cap — `OPEN` · severity `UNSPECIFIED`
- **[GG-094]** MLB Has No Qualitative/PRF-Analogue Feature Layer Despite Being the Sole ACTIVE Pool — `OPEN` · severity `UNSPECIFIED`
- **[GG-105]** T4M-PROJ (ACTIVE, highest-volume band) shows a statistically significant, tercile-monotonic ANTI-PREDICTIVE relationship between its own computed edge and realized win rate, on clean data (Workstream B / T-322/T-323/T-324 discovery) — `OPEN` · severity `UNSPECIFIED`
- **[GG-121]** 2026-07-11 T1 MLB `SemanticFloorViolation` (games_fetched=16, matched_players=0) surfaced by GG-049's own heartbeat but never logged — `WATCH ITEM` · severity `UNSPECIFIED`
- **[GG-124]** All four active MLB bands simultaneously clean_n=0/UNDERPOWERED, monitoring-coverage blackout from rapid-fire epoch boundaries — `OPEN` · severity `UNSPECIFIED`
- **[GG-127]** 00_ADMIN/README.md (designated nav hub, ADR-0001) went ~7 weeks with zero updates while the project moved through multiple phase transitions — `IN PROGRESS` · severity `UNSPECIFIED`
- **[GG-132]** MEMORY_BANK.md `**Last reviewed:**` narrative chain regrew unchecked 9→52 entries since T-334's 2026-07-11 fix; the 2026-07-15 ADR-0044 re-application consolidated only the sibling `## Current State Snapshot` chain, not this one — `OPEN` · severity `UNSPECIFIED`
- **[GG-133]** CHANGELOG.md has not been updated since 2026-05-30 despite ~2 months of major changes, violating its own staleness trigger — `OPEN` · severity `UNSPECIFIED`
- **[GG-134]** `mc_empirical_bootstrap.py`'s forward-risk projection has four unmodeled scope gaps not disclosed as limitations at commit time — `OPEN` · severity `UNSPECIFIED`
- **[GG-136]** No standing archival cadence exists for `04_EXECUTION/TODO_NEXT.md`'s own `## T-NNN` task sections (same class as GG-127) — `IN PROGRESS` · severity `UNSPECIFIED`
- **[GG-137]** A1's holdout-Brier-optimal K=400 shrinkage candidate gives only ~7% weight to actual player data; may trade calibration for discrimination — `OPEN` · severity `UNSPECIFIED`
- **[GG-140]** GG-105 remediation exhausted the entire class of monotonic-transform recalibration candidates without a structural check ruling that class out first (temperature scaling, LR+Platt refit, isotonic — all tested serially, all failed the same way) — `OPEN` · severity `UNSPECIFIED`
- **[GG-145]** `park_factor_hits` is hardcoded 1.0 across all 20,943 rows of the historical C2 feature matrix; second, independent instance of GG-141's failure shape, found live by GG-141's own preventive fix — `OPEN` · severity `UNSPECIFIED · **Assertion:** LANDED(scripts/check_feature_column_health.py) — detection assertion exists and is exactly how this gap was found; the underlying `park_factor_hits` bug itself remains unfixed (ADR-0052/T-433)`
- **[GG-146]** 8 pre-existing test failures in `test_exp015_t3_simulation.py`, traced to ADR-0048's `T1_MULTI_DAY.kelly_fraction=0.0` propagating into `run_exp015.py`'s Monte Carlo simulation as a division-by-zero; first surfaced by a full-suite run on an unrelated branch — `OPEN` · severity `UNSPECIFIED`
- **[GG-150]** Cross-book (T1 vs T4) opposite-direction conflicts are alarmed, not blocked; a blocking control is an unstaffed gap — `OPEN` · severity `UNSPECIFIED`
- **[GG-151]** `merge=union` does not guarantee dedup: identical content reaching both merge sides via different commit paths can be duplicated, not deduplicated — `OPEN` · severity `UNSPECIFIED`
- **[GG-156]** No forward price archive existed for any MLB market family before 2026-08-01; Phase 2's market-comparison gate had no input source and the same absence limits GG-142 counterfactual analysis — `OPEN` · severity `UNSPECIFIED`
- **[GG-157]** `paper_trader.py` has zero orderbook/depth/fill validation; every paper fill (including the live epoch-12 flat-$1 cohort) is assumed at mid, and GG-155/T-411 shows that assumption sits against a quantity that swings 10-100x intraday — `OPEN` · severity `UNSPECIFIED`
- **[GG-158]** Price archive had zero off-VPS copies for 3+ sessions despite repeated "verified"/"deployed" reports; same failure class as GG-144's unanchored grep — `OPEN` · severity `UNSPECIFIED`
- **[GG-160]** Four `file:line` citations across three Phase 0/1 docs had drifted from source with nothing catching it; no mechanism exists that resolves a doc's code citations against current source — `OPEN` · severity `UNSPECIFIED`
- **[GG-164]** T4 MLB cycle log's `game_date` field is wrong on 70% of all rows (45,217/64,396): stamped from UTC wall-clock "today" at write time, not the game's actual date; `(player_id, game_date, threshold)` is not a valid join key without correction, and doubleheaders break it further — `OPEN` · severity `MEDIUM · **Assertion:** PENDING(T-432, assertion A) — RESOLVED is not eligible until this lands (ADR-0052); this entry's original "Why it survived" field asserted an unverified negative ("isn't used as a resolution join key anywhere") that GG-166 directly contradicted — the motivating case for ADR-0052`
- **[GG-166]** `run_resolve_mlb.py` consumes the same corrupted `game_date` field GG-164 documented, and silently resolves T4M-PROJ positions against the wrong day's box score for ~44% of the epoch-12 clean cohort — corrupting live paper-trading WIN/LOSS/pnl, not just a future-risk join key — `OPEN — code fixed, ledger `game_date` corrected, GG-170 authority settled and 1,127/1,220 (92.4%) of the stale outcome/pnl population re-derived (T-437, 2026-08-11/12); 93 positions still outstanding pending outcome-store coverage; T4M-PROJ power-calc baseline now flips TARGET MET → NOT MET post-correction` · severity `CRITICAL · **Assertion:** PENDING(T-432, assertion A) — shared with GG-164 (same defect, write-site vs. read-site); B2's per-resolution `game_date_ticker_mismatch` refusal is a point check at resolution time, not a standing suite-level invariant, so this remains PENDING not LANDED (ADR-0052); also the concrete G6 precondition example (ADR-0052 §2.3) — Kelly sizing and the drawdown kill switch both read this same ledger`

---

**Full record for every entry above:** `03_DECISIONS/GOVERNANCE_GAP_LOG.md`. **Resolved/closed history:** `03_DECISIONS/GOVERNANCE_GAP_LOG_ARCHIVE.md`.

