# Strategy Overview — the multi-arm router

> **Binding text: `02_ARCHITECTURE_DESIGN/DOCTRINE.md`.** Where this file disagrees with it, DOCTRINE.md wins. This file explains how the
> strategies of this project fit the doctrine; it does not restate it. State (numbers, what is running) lives in the RUNNING SITREP at
> the top of `04_EXECUTION/ACTIVE_QUEUE.md`, never here.

**Owner (role):** Director/Sponsor (DS) · **Last reviewed:** 2026-11-18 (W120.4, body rewritten to DOCTRINE.md; ADR-0077)
**Next review:** every wave close, with the Doctrine stack (RED after 14 days, `scripts/doctrine_freshness.py`)
**Upstream:** `DOCTRINE.md` · `03_DECISIONS/ADR-0077_multi-arm-routing-doctrine.md` · `03_DECISIONS/ADR-0075_betting-architecture-doctrine.md`
**Downstream:** `DECISION_ROUTING.md` (the router) · `EXECUTION_BANDS.md` (bands, live registry) · `COVERAGE_TARGET_MATRIX.md`
**History:** the previous body (strategies A–J written as separate ways to beat the market, NBA-only, confidence scores, the 2026-05
band table) is preserved verbatim at `00_ADMIN/STRATEGY_OVERVIEW_ARCHIVE_2026-11-18.md`.

---

## 1. What the strategy is

One layered decision tree per cell. For every market it picks the **arm: ride the market, fade it, momentum, pot of gold, or no bet**
(DOCTRINE §1). The layers (DOCTRINE §1, `DECISION_ROUTING.md`):

1. Market state — price, move, ladder gap, book, time to start.
2. Filters built from the depth factors — matchup, lineup / usage, rest / travel, refs, weather, PAM, qualitative.
3. A tree per cell that chooses the arm, depth set by decision horizon (ADR-0068, DOCTRINE §5).
4. Then risk / sizing (Kelly 0 until G6) and execution (fills that are not picked off, ADR-0072).

The operator's statement of the vision, verbatim (2026-11-10 21:41 PT):

> "my vision from DAY 1 was to build out the decision trees so we optimize every single route while using tried and true math scaffolding
> and betting architecture. Does a quant - that finds through rigorous testing and scaffolding that a certain betting pattern doesn't beat
> the "market" keep going? no he fucking routes it to the correct path so that loss still WINS."

Consequences that every strategy section below inherits:

- The engine's simulated probability is **one input** to the tree, never the bet by itself.
- A factor is **applied** when it is a tested split in the tree, scored per leaf: net after costs, held out, per arm. Model-vs-market
  Brier may be reported; it is never the verdict.
- `model_p > market + vig` is the **fade arm's entry rule**, nothing more.
- A test that says "this pattern does not beat the market" is a **routing result** — the leaf gets ride or no bet. It closes only that
  test: "hypothesis closed (<EXP-id>, parked for R&D)". No cell, market or arm closes (DOCTRINE §1b, operator 2026-11-11 16:51 PT).
- Words: never "no edge"; never "ruled out" for a model that lost (DOCTRINE §1b, operator 2026-11-10 21:56 PT).

## 2. Where the old strategies A–J sit

The ten strategies of the earlier document are **arms or layers of the one tree**, not stand-alone bets. Mechanics, formulas and
constraints for each are in the archive file above (headings `Strategy A` … `Strategy J`); the role each plays now:

| Old strategy | Role in the router |
|---|---|
| A — ML +EV (price discrepancy) | The **fade arm**. `model_p > market + vig` is its entry rule. |
| B — Data aggregation enhancement | Layer 2: factor inputs the filters are built from. |
| C — Complement lock arbitrage | Reference only; `arb/` is reference until APR-0010 (Hard Rule 1). Kalshi-only; no Polymarket build work (operator 10-27). |
| D — Statistical arbitrage (mean reversion) | Candidate input to entry timing at layer 1 / 3. |
| E — Line shopping | Execution-layer routing concept; Kalshi is the only venue today. |
| F — Correlated parlays | The **pot of gold arm** with its same-game correlation (DOCTRINE §6; W110.4 built the correlation). |
| G — Kelly sizing | The sizing layer. `kelly_fraction` per band in `execution_bands.py` is the live constant; Kelly is 0 on every live band until G6. |
| H — Risk envelope | The risk layer: hard limits in `risk.py`, kill switch ≤60 s (Hard Rule 6). Not an arm; never relaxed by a pillar. |
| I — Poisson / NB scoring distribution | Part of an engine's simulated probability — an input to the tree. |
| J — Momentum looping | The **momentum arm** (follow or fade price momentum; ADR-0075 component "momentum looping"). |

The earlier confidence scores (e.g. "7/10") scored each strategy as a stand-alone beat-the-market bet. They are history, not a current
estimate, and are not carried here.

## 3. Pot of gold and market classes

DOCTRINE §6: the pot of gold (big hitters, longshots, parlays) is an **arm of the same tree now, not a later phase**: "we should have the
pot of gold decision trees routed in too" (operator 11-05). Retail-priced flow (props, parlays, thin markets) comes before
institutionally priced headline lines: "beating buddy off his phone placing parlays, that's the first step" (10-16).

## 4. Bands and status

Execution bands T1–T5 (T4 with its sub-bands) are the horizon axis. The cells are keyed (MarketType, ExecutionBand) in
`src/prediction_market_bot/c5_execution/market_type_registry.py`; band specs and Kelly are in
`src/prediction_market_bot/execution_bands.py`. **The live band registry is `EXECUTION_BANDS.md` § Live Registry** and the code. The
2026-05 "Band Assignment Registry" table that used to sit in this file (strategies A–K with ACTIVE / SKELETON / BLOCKED) is stale and is
kept only in the archive; it is not a source of truth.

## 5. Guardrails (DOCTRINE §8, unchanged)

No real capital until G6 (ADR-0076); Kelly 0 on every live band; pre-registration is committed before a cell's first row; no score is
read below its judged n; installs only on the operator's named approval; demo and paper actions are plumbing.

## 6. How a strategy question is answered

Ask of the leaf, not of the strategy: *where this filter holds, does riding win, does fading win, or is it no bet — net after costs, held
out?* Work is chosen by the four pillars and the ranking in DOCTRINE §7; every block names the measure it moves.
