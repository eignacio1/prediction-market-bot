# T-488 / GG-157 — Realized mid-vs-book fill haircut, props + game markets

**Session:** T-488 (`session/20260826T043303Z-t488-gg157-fill-validation`)
**Scope:** MEASUREMENT ONLY. No change to `src/`, `kelly_fraction`, or the ledger.
**D1 status (checked, per task caution):** ADR-0055 is `Status: PROPOSED. Not accepted.` — no
D1-D4 decision has been made. All figures below are scoped to the **uncorrected** epoch-12
ledger (raw `game_date`, no in-place repair applied).

## Method

Depth data: `exp_output/PRICE_ARCHIVE/depth_*.jsonl`, 23 days (2026-08-04 through 2026-08-26),
6,480 rows total, produced by `scripts/archive_market_prices.py --depth-sample-per-family 2`
via `phase0_market_survey.py::_book_metrics`.

**This is a family-level, nearest-in-time join, not an exact-ticker join** (994 usable
PLAYER_PROP depth rows vs. 6,867 epoch-12 T4M-PROJ evaluations — an exact-ticker join was
already tried and found to have ~0 usable overlap, see GG-157's 2026-08-06/T-428 update). GG-157
already states that closing this gap *structurally* requires bot-side, decision-time,
ticker-targeted capture (a Phase 3/4 build, unstaffed). This measurement is a weaker proxy than
that — a statistical estimate from prevailing family-level book conditions near each position's
entry time — not a substitute for it. It is the first measurement of this kind GG-157 has
produced (the 2026-08-06 attempt found literally 0 exact-ticker matches and could not compute
anything).

Haircut model, per position, using the nearest depth observation in the same family:
- `touch_size` / `wall_size` = `top_of_book_contracts` / `within_5c_contracts` on the side the
  taker crosses (`"no"` side for a YES buy, `"yes"` side for a NO buy — Kalshi complementary
  book, `yes_ask = 100 - best_no_bid`).
- `contracts <= touch_size` → haircut = `half_spread_cents/100` (touch-only fill).
- `touch_size < contracts <= wall_size` → linear interpolation between half-spread and the 5c
  measurement wall.
- `contracts > wall_size` → haircut = $0.05, flagged `depth_exhausted` (a **floor estimate** —
  likely an *underestimate* of true cost, since no depth is measured past the 5c band).

## TASK 1 — props (KXMLBHIT / PLAYER_PROP) haircut distribution

Epoch-12 T4M-PROJ traded (non-rejected) positions: **765**. Of these, **605** were entered on or
after 2026-08-04 (depth coverage start) and are joinable; **160 predate depth coverage and
cannot be haircut-estimated at all** — excluded, not zero-filled.

| | n | mean | median | p10 | p90 | min | max |
|---|---|---|---|---|---|---|---|
| Haircut ($/contract) | 605 | $0.0101 | $0.0100 | $0.0050 | $0.0200 | $0.0050 | $0.0600 |

0/605 (0.0%) hit the `depth_exhausted` floor case — props depth was sufficient to cover every
observed position size in this sample.

## TASK 2 — before/after mean P&L/bet and n*

Resolved (CLOSED, WIN/LOSS), depth-covered subset: **n = 559**. (This is a "traded,
depth-covered, resolved" cohort defined for this measurement — not necessarily identical to
`run_power_calc.py`'s official `filter_clean()` clean_n, which applies its own epoch-floor
filters. Same n* formula reused via `run_power_calc.z_for` — alpha=0.05, power=0.95, one-sided,
sample stdev ddof=1 — for an apples-to-apples before/after comparison on this cohort.)

| | BEFORE haircut | AFTER haircut |
|---|---|---|
| mean P&L/bet | **$0.2864** | **$0.2518** (−12.1%) |
| sample stdev/bet | $1.8185 | $1.8112 |
| n* (alpha=.05, power=.95) | **437** | **560** |
| current n=559 vs n* | MEETS (559 ≥ 437) | **DOES NOT MEET (559 < 560, short by 1)** |

## TASK 3 — does the cohort's edge survive?

**Directionally, yes — mean P&L/bet stays positive ($0.2518) after the haircut.** But the
sample-adequacy margin is gone: before the haircut this cohort cleared its own n* target with
122 bets to spare (559 vs. 437); after the haircut it falls 1 bet short of its own re-derived n*
(559 vs. 560). This is not "edge disappears" — it is "edge shrinks enough that the confirmation
this cohort was resting on evaporates at the same n." The haircut was a real, measured 12%
erosion of the per-bet edge from a fill-cost source `paper_trader.py` never modeled. A ~1-bet
gap is not itself alarming (it will very likely clear on the next resolved position at current
cadence), but the finding is that this cohort's edge margin over its own confirmation bar is
*this thin* once execution cost is priced in — thinner than the raw ledger P&L implied by
construction (mid-price fills), and it should not be read as a comfortably-cleared gate on the
strength of the unadjusted number.

**Caveats on interpretation:**
- Family-level nearest-in-time join, not exact-ticker/decision-time — see Method above. This
  likely *understates* variance in the true haircut (family-level depth smooths over
  ticker-specific illiquidity spikes T-411 already measured at 14x-67x intraday).
- 160/765 traded positions (21%) are structurally uncoverable (predate depth archive) and are
  excluded, not imputed.
- 0% hit the `depth_exhausted` floor case for props, so the floor-estimate/underestimate caveat
  does not materially affect this cohort's result.
- D1 (epoch-12 ledger repair) has NOT landed — GG-170 ticker/game_date mismatches remain in this
  cohort as recorded; these figures are the uncorrected-ledger numbers, consistent with the
  task's instruction.

## TASK 4 — synthetic $1.00 ADR-0050 flat-stake haircut, game markets

No T1 game-market positions exist yet to join against (T1 game-market reopening is T-493). This
is a **fully synthetic** measurement: price a $1.00 flat stake against each depth observation's
own mid, for each family, both sides, no ledger join.

| Family (series) | n | mean | median | p10 | p90 | min | max |
|---|---|---|---|---|---|---|---|
| GAME_WINNER (KXMLBGAME) | 2160 | $0.0340 | $0.0350 | $0.0100 | $0.0550 | $0.0050 | $0.0750 |
| GAME_TOTAL (KXMLBTOTAL) | 1034 | $0.0307 | $0.0100 | $0.0050 | $0.0800 | $0.0050 | $0.4200 |
| RUN_LINE (KXMLBSPREAD) | 1000 | $0.0515 | $0.0150 | $0.0050 | $0.1500 | $0.0050 | $0.4050 |

Compare to props' $0.0101 mean / $0.0100 median. Median haircut for GAME_WINNER is **3.5x**
props' median; RUN_LINE's p90 ($0.15) is **7.5x** props' p90 ($0.02), and both GAME_TOTAL and
RUN_LINE show a max of ~$0.42 — a single fill on a thin/wide game-market book can cost 42 cents
on the dollar, an order of magnitude past anything observed in props. This matches the
directional expectation already on record in CLAUDE.md (props: median half-spread 0.0150 / mean
0.0582 / p90 0.1450 from the original phase0 sampling vs. game totals' much tighter *point
estimates* at 0.0050/0.0094/0.0150) but the archived time-series shows game-market depth is far
more volatile than that point estimate suggested — GAME_TOTAL and RUN_LINE both have a fat
right tail (max ~$0.42) that a hand-sampled point estimate would not surface. **Any T1
game-market EV case built on a flat $1.00 stake needs to net this out before it can be trusted
— a mean haircut of $0.03-$0.05/contract against markets priced near a coin flip is a
non-trivial fraction of the edge such a strategy would need.**

## What the depth sample could not cover

- 160/765 (21%) of epoch-12 traded props positions predate depth archive coverage
  (2026-08-04) — permanently uncoverable by this method, consistent with GG-157's
  2026-08-06/T-428 finding for the historical ledger generally.
- No real game-market positions exist to join against — TASK 4 is necessarily synthetic, not a
  realized-P&L measurement.
- This is a family-level proxy, not the ticker-targeted, decision-time capture GG-157 already
  states is structurally required to close the gap. This measurement narrows the gap (first
  nonzero result vs. T-428's 0-match attempt) but does not resolve it.
- Sample counts differ (994 usable PLAYER_PROP rows vs. 500-1080 per game-market series) —
  all family estimates should be read as prevailing-book proxies, not per-position ground truth.
