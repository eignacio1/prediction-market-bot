# Coverage target — standard betting mechanisms × all five bands

**Status:** OPERATOR DIRECTIVE, 2026-08-12. This is the target the phase plan exists to reach. Everything in `MARKET_EXPANSION_ACTION_PLAN.md` should be read against it.
**Verified against** `origin/main` = `44e845b`. Band inventory read from `execution_bands.py`, not asserted.

---

## The directive

**Get the universe to cover the standard betting mechanisms — moneyline, spread/run line, totals (O/U), team totals — across all five execution bands.**

This is the concrete form of the vision statement in CLAUDE.md. The methodology is the asset, and an asset that only works on one market type in one band has not been shown to generalize at all. **Coverage is the evidence.**

## Where we actually are — 1 cell of ~25

The bot today places exactly one kind of bet: *will player X record ≥N hits*, series `KXMLBHIT`, band T4M-PROJ, venue Kalshi. That is a player-prop bot with a general-sounding architecture, not a prediction-market bot.

**Market types implemented: 1 of 5. Bands placing bets: 1 of 5.**

| Band | MLB status today | Notes |
|---|---|---|
| **T1** multi-day pregame | `kelly_fraction=0.0` (ADR-0048), `clean_n=0`, `raw_n=466` | Zeroed on ruin geometry (GG-135). Structurally cannot accrue. GG-153 is an unstaffed operator decision. |
| **T2** same-day | `kelly_fraction=0.0`, `raw_n=2` | Effectively never traded. |
| **T3** pre-first-pitch | `kelly_fraction=0.0`, `raw_n=0` | **Never traded at all.** |
| **T4** live in-play | T4M-PROJ live at flat $1.00 (ADR-0050); T4M-ARITH / T4M-FLOW PROVISIONAL & non-operational | The only band placing bets. |
| **T5** late-game certainty | `kelly_fraction=0.25`, `phase_active="Phase 8"` | NBA-shaped, dark, EXP-018 unrun. |

**Say this plainly rather than letting the phase plan imply otherwise:** "all five bands" means activating three bands that have essentially never traded (T2 n=2, T3 n=0, T5 n=0) on four market types that have never been implemented. That is a substantially larger scope than "add moneyline."

## The target matrix

Rows are market families confirmed to exist on Kalshi by Phase 0 (ticker-verified). Columns are the five bands.

| Market family | Ticker | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|---|
| Player prop (hits) | `KXMLBHIT` | ○ | ○ | ○ | **●** | ○ |
| Moneyline | `KXMLBGAME` | ○ | ○ | ○ | ○ | ○ |
| Run line / spread | `KXMLBSPREAD` | ○ | ○ | ○ | ○ | ○ |
| Game total (O/U) | `KXMLBTOTAL` | ○ | ○ | ○ | ○ | ○ |
| Team total | `KXMLBTEAMTOTAL` | ○ | ○ | ○ | ○ | ○ |
| *Partial-game (F3/F5/F7)* | `KXMLBF3/F5/F7` | ○ | ○ | ○ | ○ | ○ |

**●** = live · **○** = not implemented. One cell of twenty-five (thirty with partial-game).

## The matrix is not uniformly meaningful — and that is the useful part

**Do not treat this as twenty-five cells to light up.** Phase 0 produced direct evidence that liquidity is band-dependent by family, and that shape should drive build order:

- **GAME_WINNER measured deep pre-slate and thin mid-slate** — the inverse of player props. If that holds as the depth time series accumulates, **moneyline is a T1/T2/T3-shaped instrument, not a T4 one.** Building it into T4 first would be building it into its worst band.
- **Player props hold liquidity in-play** — which is why the one live cell is T4, and it is the right cell for that family.
- **GAME_TOTAL and RUN_LINE failed the depth gate 3/3 pre-slate.** Provisional, not settled, but a real signal.

**So the deliverable is not "25 cells." It is: enumerate the matrix, mark each cell plausible / implausible / unknown on liquidity and model grounds, and drive coverage against the plausible set.** A cell ruled out on measured depth is a completed cell, not a gap.

## The strategic tension nobody has adjudicated

CLAUDE.md's market-efficiency-gradient section says the strategy is designed for markets that are *not* maximally efficient — thin, low-attention, slow price discovery.

The only positive result in the project is on **player props**, which fit that description. The expansion is toward **moneyline and totals**, which are the most-attended, most-efficiently-priced markets on the board.

**Generality and edge may point in opposite directions here.** Both are real goods:
- Generality is the asset — the methodology has to transfer or there is nothing to sell.
- Edge is the score — a general framework that loses money on every market it generalizes to has proven the wrong thing.

**This needs an explicit operator decision, not a default.** The honest framing: expanding to game markets is a test of *generality*, and it should be expected to produce thinner edge than props. If it does, that is informative — not failure. But it should be predicted in advance rather than explained afterward, or the result is unfalsifiable.

## How the phases map to the matrix

| Phase | What it contributes to coverage |
|---|---|
| **0** ✅ | Enumerated the universe (12,355 series); ticker-confirmed the four target families + partial-game derivatives; measured depth per family. |
| **1** | **The rows.** Abstraction repair — market-type registry, `VenueAdapter` generalized off `fetch_player_points_markets()`, `open_position()` off player fields, vig cascade to per-market-type config. Without this the matrix cannot have more than one row. |
| **2** | **Whether the rows are worth having.** Minimal falsification first (LL-009): does the model class transfer to a team-level target at all? |
| **3** | **The columns, safely.** Segmented pools — per-family ledgers, per-family `clean_n`, per-family kill switches, cross-family correlated-exposure control. Without this a defect in one cell zeroes every other cell's measurement. |
| **4** | Activation per cell: shadow → flat-stake measurement → own `clean_n ≥ n*`. |

**The band dimension is currently unowned.** Phases 1–4 are written almost entirely in market-type terms. Nothing in the plan addresses activating T2, T3 or T5 — and three of five bands have never meaningfully traded. **That is a gap in the phase plan itself and should be registered.**

## What must be true before a cell counts as covered

Per cell, not per family, and not waived by another cell's result:

1. Depth measured live and above the gate floor at the intended stake (`0C.12` — the floor recomputes when sizing changes).
2. Its own ledger, `clean_n`, and variance-derived `n*` (APR-0024).
3. Its own band-level kill switch that does not halt other cells.
4. Its own semantic oracles.
5. Correlated-exposure control across families — moneyline, run line and totals on one game are economically correlated with **no shared ticker**, so GG-149's identical-ticker guard does not see it.
6. `clean_n ≥ n*` on its own data.

---

## Open questions for the operator

1. **Generality vs. edge** — is game-market expansion a test of generality accepted at likely-thinner edge, or is it expected to produce edge? Predicted in advance either way.
2. **Band activation order** — T2/T3 have never traded and T1 is zeroed on ruin geometry (GG-135). Does "all five bands" mean reactivating T1 (requiring GG-153's decision), or building the new families in bands that are already structurally sound?
3. **Partial-game derivatives** — Phase 0 flagged `KXMLBF3/F5/F7` as plausibly thinner and less attended, i.e. *better* fits for the efficiency gradient than full-game markets. In or out of the standard-mechanisms target?
