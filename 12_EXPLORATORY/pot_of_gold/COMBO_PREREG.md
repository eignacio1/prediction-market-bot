# COMBO arm pre-registration — NBA same-game combos (W126.4 Part C, EXP-COMBO-001)

**Last reviewed:** 2026-11-25. Committed **before any combo row exists and before any combo outcome is read**. Measures: B4 (parlay family
logging, 0 -> 1 when activated), D3 (challenger pre-registered). Ties to D-09 ("beating buddy off his phone placing parlays, that's the
first step") and backlog B-024. Mechanics: `MECHANICS.md`. Pricer: `src/prediction_market_bot/nba_engine/combo_price.py`. Writer:
`scripts/nba_combo_shadow.py` (PM_COMBO_SHADOW, default off). Registry cells NBA_SAME_GAME_COMBO stay NOT_IMPLEMENTED until the writer runs.

## What a row is
One row per (combo market, hourly run) with the game tipping in 0-180 min: engine P(all legs) from the same draws (`engine_p`), the
product-of-legs P (`p_product_of_legs`), `lift`, `mc_se`, `resolved`, legs priced / unpriced with reasons, flags, the quote showing
(`yes_bid` / `yes_ask` / sizes, or none), the default-fee cost at the ask (`fee_at_ask_default`, multiplier **unverified**), and
`minutes_to_tip`. Settlement is read later from the market's `result`. Unquoted combos are logged at a 5% hash sample to measure how
often a price exists at all (it is rare: MECHANICS.md).

## Scored rows (frozen filter)
`engine_p` not null (every leg priced) · `resolved` · `mc_se <= 0.01` · no flags (so no same-player cross-stat) · an ask or bid showing.
One row per combo per window: the row nearest **T-120 min** (window 105-135) and the row nearest **T-30 min** (window 20-40).

## Arms and the net after costs (per contract, $1 payout)
- **fade_yes:** buy YES at the ask when `engine_p >= ask + fee + 0.03`. Net = 1[result yes] - ask - fee.
- **fade_no:** buy NO at 1 - bid when `engine_p <= bid - fee - 0.03` (needs a standing bid >= 0.01). Net = 1[result no] - (1 - bid) - fee.
- **ride:** buy YES at the ask whenever one shows, no model. Net as fade_yes. This is the market's own price taken as it stands (the
  baseline each leaf's fade must beat).
- **no_bet:** 0.
Costs: fee at the default taker multiplier, rounded up to the centi-cent; if the combo multiplier is found different, every row is
re-scored with it and both are reported. No fill is assumed beyond the shown size; fills are NOT measured by this shadow (execution
evidence needs demo orders, a separate step).

## Leaves (fixed grid, no tuning)
legs {2-3, 4-6, 7+} x has a team leg (ml / spread / total / team total) {yes, no} x window {T-120, T-30}. 12 leaves. A leaf's arm is
the one with the best held-out net after costs; "does not beat the market" is a routing result (that leaf rides or no-bets), not a stop.

## Judged n (variance-derived)
Per-contract net sd is about sqrt(p(1-p)) ~ 0.4 at p ~ 0.2. To separate a mean net of +0.05 from 0 at 95%: n = (1.96 x 0.4 / 0.05)^2 ~ 246,
so **judged n = 250 scored rows per leaf, from at least 40 distinct games** (combos in a game share outcomes; the interval is cluster-robust
by game, and the game count, not the row count, is what the look reports). Held out: the first 40% of game-days by date are a
description-only window; the verdict uses the remaining 60%. No score is read below judged n. The first look is the pre-registered modal
outcome: **most leaves are under n for months** because an ask shows on ~1% of NBA same-game combos (547/61,000 open combos, MECHANICS.md);
so the look that arrives first is the quote-availability one: share of games with >= 1 two-sided priced combo at T-120 and T-30.

## Words
A losing leaf is "routed to ride / no bet in this leaf". A failed look is "hypothesis closed (EXP-COMBO-001, parked for R&D)"; no cell, market
or arm closes.

## Activation proposal (2026-11-25, awaiting the operator)
Install the cron line in `deploy/cron.nba_combo_shadow` (registry entry `cron|41 * * * *|scripts/nba_combo_shadow.py`, now `paused`) via the
named box task `nba_combo_shadow_install` (not yet in the allowlist; adding it is a separate approved step). **Surface check (Hard Rule 14):**
adds 1 hourly cron (surface +1 live component when installed), reads public Kalshi list pages (about 62 requests of 1,000 per run, ~1-2 min) plus
the existing ESPN stores; memory ~ the props runner's (4,000 draws per game, games inside a 3 h window only); writes one jsonl under
`exp_output/COMBO_SHADOW/` (~1-3 MB per game-day). It must not be installed while the health signals are red; the window checks the scan's
SURFACE BUDGET first. No order, no sizing, Kelly 0, $0.
