# EXP-036 — NHL pregame shadow evaluation: PRE-REGISTRATION

**Registered:** 2026-10-02 (T-607, Wave 47 block fly-nhl-pregame). **Pushed alone, before any shadow row is scored.**
**Status of rules:** FIXED at push time. No rule below changes after any score is seen; a change requires a new, dated, superseding pre-registration.
**Scope:** SHADOW = evaluate-and-log only. No order, position, paper fill, stake or `kelly_fraction` change (ADR-0048 zero-Kelly stands).

## Operator framing (stated, not softened)
Game-market expansion is a test of **generality**. The operator (2026-10-02, "We need to start flyin") accepted that moneyline / puck line / totals sit at the most-attended, most-efficient end of the efficiency gradient, so **thinner edge is expected**. That expectation is written down here *before* scoring so a result cannot be explained afterward.

## Cells (9)
`NHL_MONEYLINE`, `NHL_PUCK_LINE`, `NHL_GAME_TOTAL` × bands T1 (12–48h pre-start), T2 (4–8h), T3 (15–60 min). Kalshi series `KXNHLGAME`, `KXNHLSPREAD` (strikes "wins by over 1.5/2.5 goals"), `KXNHLTOTAL` (`floor_strike` N.5). Total counts regulation + OT goals; a shootout adds one goal to the winner. All derived from ONE frozen goals distribution per game (coherent ladder).

## Pre-registered expectations (per cell, all 9)
| Comparison | Expected sign | Meaning |
|---|---|---|
| ΔBrier vs **climatology** (climo Brier − model Brier) | **> 0** | model has skill over base rates |
| ΔBrier vs **market mid** (market Brier − model Brier) | **≤ 0** | operator-accepted: the market is at least as good; a positive value would be a surprise |
| E_net at entry (best side, per-contract, after fee) | **≤ 0** expected | thin/negative edge is the accepted cost of generality |

Band note: T3 expected to be hardest to beat (confirmed goalies priced in); T1 the least-priced-in (goalie uncertainty) and therefore the cell where a positive ΔBrier vs market is *least implausible*, though still not expected.

## Units and primary metric
- Unit = **settled game**. Strikes on one game are highly correlated, so per cell the per-game score is the mean over that game's strikes in that cell; inference is **game-clustered** (bootstrap over games, 10,000 resamples, 95% two-sided CI; paired model-vs-market difference).
- Primary metric: ΔBrier vs market (paired, per game). Secondary: ΔBrier vs climatology; E_net at entry.
- Fees: E_net computed under **both** candidates — k=0.07, and 0.07 × series `fee_multiplier` (currently 1 for all three series, verified 2026-10-02; re-read from the series endpoint before any CANDIDATE call).
- Rows labelled by n against the judged n; any figure at n < judged n is labelled **PRELIMINARY (n=… of …)**.

## Judged n (power calculation)
One-sided α = 0.05, power 0.80, paired per-game ΔBrier. n = ((1.645 + 0.842)·σ/δ)². Assumed σ(per-game ΔBrier) = 0.04 (two near-identical forecasts differ by a few points per game; this is an assumption, stated), smallest effect worth acting on δ = 0.002 Brier. → **judged n = 2,473 settled games per cell**, rounded to **2,500**. Sensitivity: σ 0.03/0.05 → 1,391 / 3,864 at δ=0.002. A regular season is 1,312 games, so ≈ two seasons to reach judged n for a cell with full coverage; **until then every cell is SHADOW-continue by construction** unless a RULED_OUT rule fires.

## Decision rules (fixed now)
Evaluated per cell only when its pre-registration is already pushed (this file) and only on settled games with a valid row.
1. **RULED_OUT** — either: (a) n ≥ 500 games and the 95% CI of ΔBrier vs climatology has upper bound ≤ 0 (no demonstrated skill over base rate); or (b) n ≥ 2,500 and ΔBrier vs market CI upper bound < 0 AND mean E_net < 0 under both fee candidates. Requires a `reason` and `measured_date`.
2. **CANDIDATE-PENDING-CAPACITY** — n ≥ 2,500 AND ΔBrier vs market > 0 with the 95% game-clustered CI excluding zero AND mean E_net at entry > 0 under **both** fee candidates. "Pending capacity" because live book depth must be measured at decision time (CLAUDE.md, GG-155); no sizing is authorized by this status.
3. **SHADOW-continue** — everything else, including all cells below judged n.
A cell is never promoted on a favourable partial n; a negative result against an *expected* sign is reported as expected, not as failure.

## Backtest
Pre-registered retrospective on the 2025-26 season requires validated NHL market history published by 47.1 on origin/main. **None exists at push time** (checked `origin/main`, 2026-10-02: no NHL market-history artifact). Therefore the retrospective is **climatology-only** (held-out 2025-26 reliability + ΔBrier vs climatology); **no market-relative backtest is claimed.** Market-relative evidence accrues only from forward shadow rows.

## Model-side commitments
Frozen model (ADR-0004: LR + Platt or documented equivalent), trained on prior seasons only (2021-22 … 2024-25), 2025-26 held out and **not tuned on**, artifact hashed, information cutoff enforced in code (inputs timestamped after `as_of_utc` raise). Goalie: projected starter at T1/T2, confirmed starter at T3 when the source shows it; flagged per row.

## Known limitations declared in advance
Travel distance is not modelled (no venue coordinates ingested; road-streak and rest only). Kalshi moneyline/puck-line OT/SO treatment is assumed to follow the official final result (rules text silent on OT/SO; shootout winner's margin is 1, so 1.5/2.5 strikes are unaffected).


## Addendum 2026-10-08 — bootstrap seed (closes GG-511)
Authorization: operator, 2026-10-07 19:03 PT ("Yes proceed with both recommendations"), recorded in 04_EXECUTION/ACTIVE_QUEUE.md "AUTHORIZATION - PRE-REGISTRATION ADDENDA". Appended 2026-10-08 (W60.2 Part B) before any judged data exists. The text above is unchanged.

The bootstrap seed is **20261002** (B = 10,000 on per-game means, as already specified above). Intervals produced before W59.2 used B=2000 on raw strike rows and are superseded.

## Addendum 2026-10-08 — goalie amendment (W59.3 Part B verdict (b); text verbatim from W59_3_nba_nhl_readiness_results.md Part B)
Authorization: operator, 2026-10-07 19:03 PT ("Yes proceed with both recommendations"), recorded in 04_EXECUTION/ACTIVE_QUEUE.md "AUTHORIZATION - PRE-REGISTRATION ADDENDA". Appended 2026-10-08 (W60.2 Part B) before any judged data exists. The text above is unchanged.

Replaces "Goalie: projected starter at T1/T2, confirmed starter at T3 when the source shows it; flagged per row." (Model-side commitments) with:

> Goalie: projected starter (last start) at every band, T3 included; no confirmed-starter source is available before puck drop (W59.3 probe: `starter` flag absent pre-drop and throughout live play, present only once the game is final). Rows are flagged `confirmed=False`.
