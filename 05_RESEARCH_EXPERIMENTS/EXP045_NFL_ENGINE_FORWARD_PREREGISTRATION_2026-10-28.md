# EXP-045 — NFL engine forward test on alternate strikes (pre-registration)

**Frozen:** 2026-10-29T03:00:00Z (rows scored are those with `run_ts` at or after this instant). **Committed before the freeze instant.**
**Pillar / measure:** PROOF (P1/P3: NFL engine look 0 → 1, dated). Standing authorization 2026-10-08 (new pre-registration).
**Status:** frozen; nothing here is wired to an order, gate, runner or ledger. Paper/shadow only, no stake.

## Question
Does board v2 (the NFL engine's joint margin/total distribution, W93.4) price Kalshi's *alternate* strikes — alternate spreads, alternate totals, team totals — better than the quote, by enough to clear the exact taker fee plus half the spread?

## Pinned inputs
| Input | Pin |
|---|---|
| Engine | `src/prediction_market_bot/nfl_engine/board_v2.py`, merge commit `f88d455`, sha256 `6057dbec68025e4bd13f78261723e0886149b180ca940dd96ac450fe6c85e5bc`; bandwidths H_SPREAD=1.75, H_TOTAL=4.0 |
| Library | `build_library(sched, before_season=2026)` — seasons before 2026 only, never refit in-season |
| Schedule data | `schedules_20261020T001136Z.parquet`, sha256 `c57e424c641df057f459488dc8fc60946583e9dcd434bf5c4777780b2bd428a9` (kickoff times; scores replaced by public finals) |
| Scorer | `forward_test.py` + `12_EXPLORATORY/nfl_engine_forward/score_exp045.py`, tested on a frozen synthetic archive with a known answer (`tests/test_nfl_forward_test.py`) |
| Fee | `quant/money.py::fee`, exact: taker 0.07·C·P·(1−P) rounded UP to a centicent; NFL series are not at a reduced multiplier |

## Rule (frozen)
1. Each archive snapshot (~20 min cadence) is read per game. The main spread and main total are the 0.5 crossings of that snapshot's own mid-price ladders (linear), rounded to 0.25. Board v2 prices the game at those two lines.
2. Strikes scored: alternate spread and alternate total strikes **at least 3 points off the main line**, and every team-total strike. Moneyline (`KXNFLGAME`) is not scored. Kalshi convention "gt": suffix N means YES iff value > N.
3. Quote sanity: `0 < yes_bid ≤ yes_ask < 1` and `yes_ask − yes_bid ≤ 0.10`.
4. **Trigger:** buy YES at the ask if `P_engine − ask >` fee(ask); buy NO at `1 − bid` if `bid − P_engine >` fee(1 − bid). This is identical to `|P_engine − mid| > fee + half-spread`, side chosen by sign, entry at the quote.
5. **One position per market**, the first snapshot that triggers; later snapshots on that market are ignored. Only snapshots before kickoff, and only games whose kickoff is after the freeze.
6. Settlement: public final score (ESPN scoreboard GET). P&L per contract = `won − entry − fee`. Regular season only.

## Test and pass rule
Per family (spread, total, team total) the unit is the **game**; the interval is the game-clustered bootstrap (2,000 resamples, seed 20261002) of net P&L per contract; the p-value is a one-sided centred game bootstrap (4,000, seed 20261029) for mean ≤ 0. **Benjamini–Hochberg at q = 0.10 across the three families.** A family PASSES iff it is BH-rejected **and** its net lower bound is > 0. No family passing is the expected result.

## Judged n (from 93.4's measured variance)
In-sample replay of the same rule over the 86 settled 2026 games already in the archive (`replay_insample.json`): net P&L per contract — spread −0.003 [−0.039, +0.032], total +0.009 [−0.029, +0.045], team total −0.021 [−0.052, +0.008]; every interval includes 0. Game-level SD of per-game mean P&L: 0.167 / 0.169 / 0.148. For a one-sided test at α = 0.05, power 0.80, minimum effect **0.02 per contract**: judged n = **429 / 442 / 337 games** (spread / total / team total).

**Stated plainly: the 2026 regular season cannot reach judged n.** 165 games kick off after the freeze (last 2027-01-10). At n = 165 the minimum detectable effect is ≈ 0.032 per contract (0.029–0.033 across families), 1.6× the 0.02 we want to detect.

## Look date
- **Interim reads (descriptive counts only; no verdict, no p-value):** weekly, first scored at `run_ts ≥ freeze`.
- **Look 1 (the scored look): 2027-01-12**, after the final regular-season games (2027-01-10) are settled. It is **UNDERPOWERED by construction** (MDE ≈ 0.032, not 0.02) and is labelled so in its result.
- **Reading of Look 1:** a PASS stands (lower bound > 0 does not need judged n). A non-pass reads **NOT DISTINGUISHABLE at MDE ≈ 0.032** — not "no edge". To reach judged n the pre-registration continues unchanged into the 2027 regular season (a second scored look when ≥ 337 games per family have settled, pooled across seasons with the 2027 library refit only at a season boundary, announced in writing before it happens). Playoffs are excluded.

## Modal outcome (stated before any new row)
**NOT DISTINGUISHABLE at Look 1, ~85%.** Reasons: the engine matched Kalshi's ladders in-sample (every interval includes 0, W93.4), alternate NFL strikes are the most-attended board on the venue, and 165 games is below judged n. A family PASS: ~5%. A family significantly negative (fee drag from a systematic bias): ~10% — team totals sit closest to that in the replay (−0.021).

## How EXP-045 differs from EXP-041 (frozen, read only)
EXP-041 tests an F8-adjusted **anchored price function** (`anchored_price.py`, weights ML 1.0 / spread 0.4 / total 0.0 / team total 0.2) against the market anchor with a pooled **Brier** score at T1/T2/T3, game-clustered, n ≈ 500 games, first look ~Jan 2028. EXP-045 uses board v2's pricing of the **ladder shape around the market's own main line** — no anchor adjustment and no F8 — and tests **triggered trades by net-of-exact-fee P&L**, not Brier, on **alternate strikes only** (the main lines are the market's own, so they cannot be mispriced by construction). It is scored from the price archive with no runner and nothing wired, on a 2026-season forward clock. A pass in one says nothing about the other.

## Not done by this pre-registration
No order, position, stake, kelly_fraction, runner, cron line, registry cell or gate is created or changed. A pass would be a *finding that licenses a separate pre-registered shadow arm*, not an activation.
