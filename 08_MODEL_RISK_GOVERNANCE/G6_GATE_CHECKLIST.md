# G6 Gate Checklist — Release to Live Capital

**Purpose:** Mechanical, per-criterion evidence checklist for the G6 promotion decision.  
**Gate:** G6 Release (live capital authorization)  
**Formal approval required:** APR-0008 (final validation report) + APR-0009 (live capital authorization)  
**Evidence standard:** APR-0017 (2026-06-01) as amended by APR-0019 (2026-06-09)  
**Last reviewed:** 2026-06-15 SESSION 63 (baseline RATIFIED at true figure — see ratification block at end)  
**Owner:** DS — Earl Ignacio  

**Sequential rule:** Tier 0 must pass before any other tier evidence counts. Failure in any tier halts G6 regardless of results in subsequent tiers.

---

## How to Use This Checklist

For each criterion: read the pass condition, locate the evidence artifact, measure the current value, mark PASS / FAIL / PENDING. Do not mark PASS without sourcing the artifact. Do not defer a measurement because the value is probably fine.

At G6 evaluation time: every row must be PASS before APR-0008 is drafted.

---

## Pre-Checklist Invariants

Before evaluating any tier criterion, confirm these hold:

| # | Invariant | Source | Status |
|---|-----------|--------|--------|
| I-1 | P&L figures use **Σpnl over `closed_positions`** (the ledger), NOT the stored scalar and NOT equity−initial | **GG-034 (2026-06-13/14):** the stored `total_realized_pnl` scalar was desynced (−$8.46) from the ledger (−$251.21) by cross-process clobbering. The T-174 fix makes `total_realized_pnl` ledger-derived (Σ `pnl`+`exit_pnl`); the live scalar now reconciles to the ledger (−$248.90 == −$248.90 post-G5-resolve). Still, **any G6 figure must be sourced from the closed-position ledger / `data/nba_finals_clean_dataset.csv`, never a stored scalar.** Also (S46 reset-equity nuance) equity−initial overstates by $142.46 — do not use it. | ⚠️ APPLY — ledger-derived only (GG-034) |
| I-2 | Tier 2 eligible bets exclude injury-contaminated positions | APR-0019 Mod 3: bets where model inputs were incomplete at prediction time (KI-011). Currently 6 documented ineligible T1 bets (EXP-018). Each ineligible bet must have documented KI-NNN basis; outcome-based exclusion prohibited. | RULE ACTIVE |
| I-3 | T1 and T4 Tier 2 evaluated **independently** — no cross-bucket pooling | APR-0019 Mod 2: T1 uses Poisson CDF, T4 uses live Bayesian GameStateModel — different model classes, different error distributions. | RULE ACTIVE |
| I-4 | G6 closure requires **all active buckets** to pass Tier 2 | APR-0019: T1 and T4 both currently active. Partial promotion not permitted. | RULE ACTIVE |
| I-5 | YES/NO direction P&L tracked separately | APR-0019 Mod 4: structural asymmetry found (EXP-018). Not a current gate, but must be reported in APR-0008. DS may exclude NO bets from T1 T2-B with documented basis and sign-off. | MONITOR |

---

## Tier 0 — Commercial Preconditions

*Must be satisfied before any paper bets count as G6 evidence.*

| ID | Criterion | Pass Condition | Evidence Artifact | Current Status |
|----|-----------|----------------|-------------------|----------------|
| **T0-A** | EXP-017 Part B: positive EV vs. real Kalshi prices | `run_exp017.py --kalshi-prices kalshi_prices.csv` → positive EV estimate with 90% CI lower bound > 0 on **structurally adequate sample** (ADR-0024: ≥500 unique markets + ≥15 distinct opponents, OR ≥2 sports each with n ≥150). Same model version hash as VPS deployed model. | EXP-017 Part B results. ADR-0024 defines adequate sample. | 🔴 **OPEN — BLOCKING** — scope shifted to MLB 2026 + NBA 26-27 regular season per ADR-0024. Last measurements: G2 EV=+$0.1042/bet (n=33, DIRECTIONAL_POSITIVE, insufficient power); G4 EV=−$0.0361/bet (n=96, DIRECTIONAL_NEGATIVE, insufficient power). Both inconclusive at Finals scale. GG-004 OPEN. |
| **T0-B** | Price discovery uses production API in paper mode | `_price_discovery_url()` returns `_KALSHI_LIVE_BASE_URL` regardless of BOT_ENV. Regression = CI failure. | `test_unauthenticated_get_uses_production_url_in_paper_mode` in test_kalshi_client.py | ✅ **COMPLETE** — T-114, 2026-06-01 |

**Tier 0 verdict: BLOCKED — T0-A not met. G6 evaluation cannot proceed until EXP-017 CONFIRMED_POSITIVE on ADR-0024 adequate sample.**

---

## Statistical Floor (APR-0019 per-bucket)

*Minimum sample for Tier 2 trend analyses to be statistically valid. Meeting the floor is necessary but not sufficient.*

| Bucket | Floor | Derivation | Current Count | Status |
|--------|-------|------------|---------------|--------|
| T1 eligible bets | ≥ 66 resolved | T2-A calibration power formula at α=0.10, power=0.80, δ=15pp, p̂=0.60 (APR-0017/0019) | 82 resolved as of Finals G3 (2026-06-08). Subtract 6 ineligible injury-contaminated → **76 eligible**. | ✅ **MET** — 76 > 66 |
| T4 eligible bets | ≥ 50 resolved | T2-A at α=0.05, power=0.80, δ=20pp, p̂=0.514 (APR-0019) | ~1,115 G3 bets + subsequent games | ✅ **MET** (trivially) |
| Game nights | ≥ 5 | Slope regression df ≥ 3 (APR-0017). NBA Finals series must last ≥5 games. | G5 is Finals Game 5; series ongoing. G6 adds 5th game night if it resolves. | 🟡 **PENDING** — meets floor if Finals series is ≥5 games (≥5 game nights of paper data) |

**Binding G6 constraints (not bet count):**
1. GG-004 resolved — EXP-017 Part B CONFIRMED_POSITIVE on ADR-0024 adequate sample
2. ≥5 game nights — needed for slope regression df ≥ 3

---

## Tier 1 — Execution Integrity

*The machine works reliably. Sequential: evaluate only after Tier 0 passes.*

| ID | Criterion | Pass Condition | Evidence Artifact | Current Status |
|----|-----------|----------------|-------------------|----------------|
| **T1-A** | Pipeline execution error rate ≤ 5% | (1) Cumulative error rate ≤ 5% over paper period (≤1 error per 20 scheduled sessions). (2) Slope of per-game-night error rate ≤ 0 (non-increasing). | C6 JSONL events with severity `ERROR` during PIPE-03 session_ids; VPS cron logs for missed windows. | 🔴 **NOT MET** — G5 peak-window: 9/29 = 31% failures at 22:00 UTC (GG-014). Cause: server-side Kalshi congestion, not bot's own rate pressure. T-164 effective off-peak (0/12 at 01:30 UTC) but does not reduce peak failures. **Confirmation deferred to 2026-27 Season Day 1 cron batch (Oct 2026) per DARK_PERIOD_PLAN.md.** |
| **T1-B** | Idempotency — zero duplicate client_order_ids | Zero duplicate `client_order_id` values across all PIPE-03 sessions. No position has `duplicate=True` without `duplicate_of` annotation confirming it is a known twin, not a live double-fire. | C6 JSONL idempotency log entries; `paper_portfolio.json` open_positions; `duplicate_of` annotations. | 🟡 **SUBSTANTIALLY MET** — per-ticker `_open_tickers` guard shipped S53 (d6283b1); blocks exact failed-transient→late-window mechanism. 9 G5 twins annotated `duplicate_of` (pre-guard, GG-028 → RESOLVED). T-166 run-level game_date guard (defense-in-depth) ships this session. Full confirmation requires zero-duplicate measurement over paper period from C6. |
| **T1-C** | Resolution fidelity ≥ 85% | (1) Cumulative resolution rate ≥ 85% over paper period. (2) Slope of per-game-night rate ≥ 0 (non-decreasing). | `paper_portfolio.json` `closed_positions`; `resolution_source` field; `resolved_at` timestamps. | 🟡 **PENDING MEASUREMENT** — **158/158 positions resolved (100%) after the GG-036 G5 settlement (2026-06-16).** Zero open positions remain. Rate has not been formally measured against an eligible-resolution denominator with the slope criterion. Measure: count positions with `resolution_source: "nba_api"` / total eligible. |
| **T1-D** | Audit completeness — zero-tolerance | For every PIPE-03 session: C6 `approve` + `reject` count = total C4 evaluations. No position in `paper_portfolio.json` without corresponding C6 `approve` event with matching `client_order_id`. | C6 JSONL `approve` and `reject` events cross-referenced against `paper_portfolio.json` and C4 evaluation count per session. | 🟡 **PENDING MEASUREMENT** — completeness has not been formally audited across all paper sessions. Requires C6 JSONL cross-reference script. |

---

## Tier 2 — Model Performance Trends (T1 Bucket)

*T1 evidence only. Slope-primary — trends over game nights, not endpoints.*

| ID | Criterion | Pass Condition | Evidence Artifact | Current Status |
|----|-----------|----------------|-------------------|----------------|
| **T2-A (T1)** | Calibration deviation ≤ 15pp, slope ≤ 0 | (1) Cumulative calibration deviation ≤ 15pp over paper period (6× TEST ECE of 0.0247). (2) Slope of per-game-night deviation ≤ 0. | `paper_portfolio.json` closed T1 positions; per-game-night \|realized win rate − mean predicted prob\|. | 🔴 **MEASURED — FAILED on raw model (GG-037, 2026-06-16).** Directional deviation = \|0.601 − 0.799\| = **19.8pp > 15pp** on the 158-bet book (calibration collapse: pure-Poisson overconfidence ignoring NBA over-dispersion). **ADR-0027** adds a temperature-scaling layer (NBA T=2.05) reducing deviation to ~6pp (OOS G5: 0.731 vs 0.537). Mechanism fixed going forward; the **historical book was traded uncalibrated** so this criterion is not retroactively met. Re-measure on regular-season data with calibration active. |
| **T2-B (T1)** | Rolling EV > 0, slope ≥ 0 | (1) Rolling per-bet EV at paper period close > 0. (2) Slope of rolling EV over game nights ≥ 0 (not deteriorating). Apply eligible-bet filter (ineligible = injury-contaminated). YES/NO direction P&L reported separately. | EXP-018 methodology; `paper_portfolio.json` T1 `pnl` fields (eligible subset). | 🟡 **DIRECTIONAL — NOT YET CONFIRMED** — EXP-018 (n=60 eligible, injury-filtered): EV = +$0.0202/bet (DIRECTIONAL_POSITIVE, borderline). YES: +$0.0733/bet (n=24); NO: −$0.0440/bet (n=42). Overall EV −$0.0361/bet (EXP-017B G4, n=96, includes pre-eligible-filter period). Slope and G5 data not yet incorporated. YES-only gate now active (EXP-018 Hypothesis C, S47/S56 DS ruling) — future T1 bets are YES-only, which will isolate YES EV going forward. |
| **T2-C (T1)** | Brier ≤ 0.265, slope ≤ 0 | (1) Rolling Brier ≤ 0.265 (L1 drift threshold) at paper period close. (2) Slope of rolling Brier over game nights ≤ 0. | `paper_portfolio.json` T1 eligible positions; per-game-night Brier calculation. TEST baseline: 0.2480 (ADR-0004). | 🟡 **MEASURED (GG-037, 2026-06-16) — Brier passes, but masks the failure.** Directional Brier on the 158-bet book = **0.2308 (≤ 0.265, technically PASS)**; calibration layer (ADR-0027) improves it to 0.2054. **However** Brier-pass coexists with a 19.8pp calibration deviation (T2-A FAIL) and an **anti-predictive edge** (T2-B/T2-D): Brier alone does not detect that the edge signal is inverted. Slope not yet computed. Do not read this PASS as model health — see T2-D. |
| **T2-D (T1)** | P&L slope > 0 | Slope of cumulative T1 P&L curve over game nights > 0 (linear regression on [game_night_index, cumulative_P&L]). | `paper_portfolio.json` T1 `pnl` fields, per game night. | 🔴 **NOT CURRENTLY MET** — **True ledger realized P&L = −$248.90 (full 158-bet book, G5 resolved 2026-06-16; GG-034/GG-036).** Per-Finals-game ledger: G2 +$75.67, G3 −$198.84, G4 −$128.04, G5 +$2.31 → cumulative slope strongly NEGATIVE (G3/G4 dominate; G5 break-even). Clean-subset (contamination excluded) is −$212.25. GG-004 (adverse Finals window, insufficient power for commercial conclusions). Re-evaluate via EXP-017 on adequate sample. Source: `data/nba_finals_clean_dataset.csv`. |

---

## Tier 2 — Model Performance Trends (T4 Bucket)

*T4 evidence only — independent evaluation required (APR-0019).*

| ID | Criterion | Pass Condition | Evidence Artifact | Current Status |
|----|-----------|----------------|-------------------|----------------|
| **T2-A (T4)** | Calibration deviation ≤ 20pp, slope ≤ 0 | (1) Cumulative calibration deviation ≤ 20pp (conservative: no validated ECE baseline for T4 live Bayesian model). (2) Slope ≤ 0. | C6 T4 JSONL events; `paper_portfolio.json` T4 positions; T4 model predictions vs resolved outcomes. | 🟡 **PENDING** — T4 win rate G3: 51.4% (n=1,115). No formal per-game-night calibration analysis run. Dark period work required. |
| **T2-B (T4)** | Rolling EV > 0, slope ≥ 0 | (1) Rolling T4 EV > 0. (2) Slope ≥ 0. T4 flat-sizing; EV = P&L / total amount wagered. | T4 pool: $478.41 remaining (initial $500). T4 `pnl` fields in C6 or T4-specific portfolio file. | 🟡 **PENDING MEASUREMENT** — T4 pool tracking: $478.41 / $500 initial = −$21.59 net. Formal per-game-night EV not calculated. |
| **T2-C (T4)** | Brier ≤ 0.265, slope ≤ 0 | Rolling T4 Brier ≤ 0.265 at period close. Slope ≤ 0. | T4 resolved positions, predicted prob vs outcome. | 🟡 **PENDING MEASUREMENT** |
| **T2-D (T4)** | P&L slope > 0 | Slope of cumulative T4 P&L curve > 0. | T4 pool P&L per game night. | 🟡 **PENDING MEASUREMENT** |

---

## Tier 3 — Risk Control Validation

*The guardrails are operative.*

| ID | Criterion | Pass Condition | Evidence Artifact | Current Status |
|----|-----------|----------------|-------------------|----------------|
| **T3-A** | Per-bet cap — zero-tolerance (≤ $500) | Zero bets with `approved_size_usd` > $500.00 in any PIPE-03 session across paper period. | C6 JSONL `approve` events; `approved_size_usd` field. | 🟡 **PENDING AUDIT** — $500 cap enforced by `_HARD_LIMITS["max_single_event_exposure_usd"]` in risk.py. No violations reported. Formal C6 audit across all paper sessions required for sign-off. |
| **T3-B** | Drawdown < 15%, slope ≤ 0 | (1) Peak realized drawdown at any point during paper period < 15%. (2) Slope of per-game-night drawdown ≤ 0 at paper period close. Kill switch fires at 20% (NFR-03); 15% paper ceiling = 75% of kill switch trigger. | `paper_portfolio.json` bankroll history; per-game-night drawdown calculation. | 🔴 **FAILING (GG-034 — was falsely ✅ PASSING on the corrupted scalar).** True realized drawdown = **24.9%** (−$248.90 / $1000, full 158-bet book post-G5-resolve), or **21.2% on the clean subset** (−$212.25). Both exceed the 15% paper ceiling AND the 20% kill-switch trigger (NFR-03) — the switch never fired only because it read the desynced −$8.46 (0.8%) scalar; it is now un-blinded and reads the true figure. The prior "✅ PASSING — 0.8%" entry was the blind kill switch manifesting in the gate evidence itself. Source: `data/nba_finals_clean_dataset.csv`. |
| **T3-C** | Rejection rate [20%, 80%] | (1) Cumulative rejection rate in [20%, 80%] at paper period close. (2) \|slope\| ≤ 10pp per game night. Note: YES-only gate (PAPER_YES_ONLY) is an EXP-018 research gate, NOT a C4 rejection. T3-C measures C4 `reject` events (edge < MIN_EDGE) only. | C6 JSONL `reject` vs `approve` events per PIPE-03 session. | 🟡 **PENDING MEASUREMENT** — Rejection rate not formally calculated from C6 logs across paper period. |
| **T3-E** | Aggregate deployed capital ≤ available cash | No portfolio state where `Σ open non-isolated stake > initial + Σ closed non-isolated pnl` (free cash ≥ 0). **NEW criterion — no such invariant existed at G5.** | `paper_portfolio.json` derived `bankroll_usd`; cash-identity decomposition; C4 ADR-0026 invariant (`tests/test_c4_risk.py::TestPortfolioDeploymentInvariant`). | ✅ **PASSING (structural) — GG-035 RESOLVED 2026-06-16 via ADR-0026.** History: the G5 book DID reach an over-leverage state ($1003.38 deployed = 100.3% of initial / ~134% of $748.79 equity; corrected `bankroll_usd` −$254.59) because **no portfolio-level free-cash gate existed** — per-event + Kelly caps do not sum to a global cash constraint. **Now closed two ways:** (1) **live state** — GG-036 resolved the 41 G5 positions, `bankroll_usd` recovered to **+$751.10** (open=0, free cash positive); (2) **structural control** — C4 now enforces a two-tier free-cash invariant (8a `Σ open + size > equity` ⇒ KILL_SWITCH; 8b `> 0.60 × equity` ⇒ REJECT, per-bet), verified by `test_g5_overleverage_forensic_would_have_been_blocked` to make the $1,003.38 state unreachable. **Residual G6 obligation:** the 60% deployment threshold must be re-derived via ADR at G6 with the live bankroll (the invariant itself is permanent). Post-season audit must still rule whether the *historical* over-leveraged G5 book is admissible as G6 evidence. |

---

## Formal Gate Prerequisites

*These are administrative/governance actions required before APR-0008 can be signed. Not measurable evidence criteria — they are process gates.*

| Prerequisite | Description | Current Status | Blocker |
|-------------|-------------|----------------|---------|
| **T-117** | Two formal document readings: (1) Kalshi Participant Agreement (formal read, not informal web search); (2) KXNBAPTS contract Terms and Conditions for numerical PAL and Position Limit values | 🔴 **OPEN** — Week 1 dark period action (by 2026-06-30). Automated trading confirmed permitted; limit values not yet formally read from per-contract Terms. If limits > $500: no risk.py change. If limits < $500: add `max_position_usd_per_market` to `_HARD_LIMITS` via ADR. | Required before ADR-0005 draft |
| **GG-014** | Order failure rate ≤ 5% confirmed on adequate sample | 🔴 **OPEN — deferred** — G5 peak: 31% failures (server-side Kalshi congestion). Off-peak (01:30 UTC): 0%. T-164 partially effective. Fix path: earlier cron window or rate-limit tier escalation. Confirmation deferred to 2026-27 Season Day 1 per DARK_PERIOD_PLAN.md. | Required for T1-A criterion |
| **GG-020** | Kalshi taker fee rate verified against actual transaction receipts | 🔴 **OPEN** — Current rate: 0.07 (supported by ≥2 independent sources; one source suggests 0.06 for sports; neither confirmed by actual receipts). Paper mode: notional — LOW risk now. Pre-ADR-0005: MEDIUM risk. Must verify post-G6: place first live trade and verify receipt matches 0.07 formula. If 0.06 is correct: direction is conservative (EV understated, not overstated). T-151 owner action. | Required for ADR-0005 break-even analysis |
| **ADR-0005** | Live capital authorization — DS sign-off | 🔴 **PENDING** — Not drafted. Requires: T-117 complete, GG-014 confirmation, GG-020 receipt verified, all tier criteria met, T-148 APR signed (✅ APR-0019), break-even analysis (T-150 complete ✅ at Finals scale; needs regular-season scale). | Gate blocker |
| **GG-033 / T-171** | Untrack `logs/paper_portfolio.json` from git | 🔴 **OPEN** — Live portfolio in git breaks `git pull --ff-only` deploys. Safe dance required every deploy until resolved. T-171: untrack portfolio + GHA auto-deploy as one unit (post-G5 resolution). | Not a G6 blocker but a deploy-integrity prerequisite for live capital operation |
| **APR-0008** | Final validation report signed | 🔴 **PENDING** — Requires all tier criteria PASS, formal audit complete, APR-0017/0019 criteria documented | Final G6 gate signature |
| **APR-0009** | Live capital authorization co-signed | 🔴 **PENDING** — Countersignature required after APR-0008 | Final G6 gate signature |

---

## T-148 / APR-0019 Status

T-148 registered (SESSION 43) for regression analysis to determine whether T1 and T4 evidence must be segregated. Analysis completed: APR-0019 accepted 2026-06-09. **T-148 is RESOLVED.** APR-0019 is operative:

- T1 floor: ≥66 eligible T1 bets ✅ MET (76 eligible as of G3)
- T4 floor: ≥50 eligible T4 bets ✅ MET (trivially)
- Per-bucket Tier 2 independence: ACTIVE
- Eligible bets definition: ACTIVE (injury-contaminated bets excluded with documented basis)

---

## S46 Equity Nuance (Applied Throughout)

At the S46 bankroll reset (2026-05-29), $142.46 of G4 stakes were still deployed. Effective post-reset equity = $1,142.46, not $1,000. Any P&L figure derived as `(current_bankroll − initial_bankroll)` overstates loss by $142.46.

**Rule:** All P&L figures in G6 evidence must use **Σpnl over the `closed_positions` ledger** (now equal to the GG-034-fixed `total_realized_pnl`, but source it from the ledger / `data/nba_finals_clean_dataset.csv`, never a stored scalar). Do not use equity−initial arithmetic. **Authoritative figure: Σpnl = −$248.90** (full 158-bet book, G5 resolved 2026-06-16; the prior −$8.46 was the corrupted scalar that GG-034 condemned — see I-1). Clean-subset (contamination labeled-out) = −$212.25.

---

## Binding G6 Constraints Summary

| Constraint | Source | Status |
|-----------|--------|--------|
| EXP-017 Part B CONFIRMED_POSITIVE on ADR-0024 adequate sample | GG-004, APR-0017 T0-A | 🔴 OPEN — primary blocker |
| T1-A: pipeline error rate ≤ 5% | APR-0017, GG-014 | 🔴 OPEN — deferred Oct 2026 |
| T-117: Kalshi document formal reads | GG-003 resolution path | 🔴 OPEN — dark period Week 1 |
| ADR-0005: DS live capital sign-off | APR-0017 | 🔴 PENDING |
| Tier 2 (T1 + T4 per-bucket): EV > 0, slope ≥ 0 | APR-0017/0019 | 🟡 NOT YET EVALUABLE — insufficient window (Finals) per ADR-0024 |
| ≥5 game nights | APR-0017 | 🟡 PENDING — depends on Finals series length |

**Bet count is not the binding constraint.** 158 resolved bets numerically exceeds the 30-bet floor from APR-0016 (now superseded) and the 66-eligible-T1-bet floor from APR-0017. The binding constraints are GG-004 (commercial validation) and ADR-0005 (formal authorization), not bet accumulation.

---

## G6 Verdict (as of 2026-06-12 SESSION 57)

**NOT READY.** Tier 0 is blocked (T0-A). No tier evaluation is operative until T0-A passes.

Critical path:
1. **Dark period (2026-06-22 to ~2026-09):** T2/T3 production-readiness, model retrain (T-072), T-117 document reads, T-151 fee documentation
2. **MLB 2026 season (Aug–Sep):** EXP-017 commercial validation attempt (ADR-0024 path 2: ≥2 sports × n≥150)
3. **NBA 26-27 regular season (Oct 2026+):** EXP-017 primary path (n≥500, ≥15 opponents); GG-014 confirmation (Season Day 1 cron batch); all tier criteria evaluated on ≥5 game nights
4. **ADR-0005 + APR-0008 + APR-0009:** drafted and signed only after all criteria confirmed

The dark period is for making the system ready to collect G6-quality evidence quickly in October — not for accumulating evidence. The bet count clock starts running when T0-A is confirmed.

---

## G6 Baseline RE-RATIFICATION — 2026-06-16 (SESSION 64, GG-036 G5 resolved)

**Re-ratified at the full 158-bet figure** after the 41 G5 positions settled from real `nba_api` box scores (GG-036 RESOLVED — no fabrication). This supersedes the S63 117-bet ratification below.

- **Headline realized P&L: −$248.90 (−24.9% of $1,000 initial)** — 158 resolved bets, zero open. Source: `data/nba_finals_clean_dataset.csv` (SNAP-2026-06-16-001, sha256 `54bac8b2…`).
- **Clean-only realized P&L: −$212.25 (−21.2%)** — contamination labeled-out. **Story flipped vs S63:** contaminated bets now net **−$36.65** (a drag), so the clean subset is *better* than the headline but still past the 20% kill-switch line.
- **G5 net: +$2.31 (22 W / 19 L)** — the largest single exposure in the book (~$1,003) settled break-even; G3 (−$198.84) and G4 (−$128.04) remain the dominant losers.
- **The G6 positive-P&L gate is FAILING, not passing.** T2-D (slope) and T3-B (drawdown) are 🔴 on every cut. Live book reconciled: stored scalar −$248.90 == ledger −$248.90; `bankroll_usd` recovered to +$751.10, open=0.

---

## G6 Baseline Ratification — 2026-06-15 (SESSION 63) [SUPERSEDED by the 2026-06-16 re-ratification above]

**Ratified by:** Earl Ignacio (DS / operator), 2026-06-14/15, dark-period close.

The NBA Finals paper-trading track record is hereby ratified **at its true, ledger-derived figure** as the canonical G6 baseline, superseding every prior citation built on the corrupted `total_realized_pnl` scalar (GG-034):

- **Headline realized P&L: −$251.21 (−25.1% of $1,000 initial)** — 117 resolved bets. Source: `data/nba_finals_clean_dataset.csv` (SNAP-2026-06-14-001, sha256 `bf5652c3…`).
- **Clean-only realized P&L: −$302.98 (−30.3%)** — contamination labeled-out; contaminated bets netted +$51.76, so the clean subset is *worse* than the headline.
- **The G6 positive-P&L gate is FAILING, not passing.** T2-D (P&L slope) and T3-B (drawdown < 15%) are both 🔴 on the true figure. The prior "✅ PASSING / 0.8% drawdown" entries were the blind kill switch (GG-034) manifesting inside the gate evidence itself.

**Findings folded into this ratification:**
- **GG-035 (over-leverage): RESOLVED 2026-06-16 (ADR-0026).** Deployed capital reached $1003.38 = 100.3% of initial / ~134% of equity; the corruption masked it. T3-E now ✅ PASSING (structural): C4 enforces a two-tier portfolio-level free-cash invariant (8a solvency KILL / 8b 60%-of-equity REJECT), verified to make the G5 over-leverage unreachable; live `bankroll_usd` recovered to +$751.10 after GG-036. Residual: 60% threshold re-derived via ADR at G6; audit admissibility of the historical G5 book still open.
- **GG-036 (G5 unresolvable → RESOLVED 2026-06-16):** the 41 G5 positions settled from `nba_api` box scores three days post-game; baseline now reflects all 158 bets (see re-ratification above).

**What this ratification does NOT do:** it does not advance G6. Tier 0 (T0-A / EXP-017 commercial validation) remains the binding blocker; this ratification only fixes the *number of record* so the dark-period audit and all downstream evidence are computed against truth, not a lying scalar. The adverse Finals window is GG-004 (insufficient power for commercial conclusions) — a negative baseline is the honest starting point, not a project verdict.
