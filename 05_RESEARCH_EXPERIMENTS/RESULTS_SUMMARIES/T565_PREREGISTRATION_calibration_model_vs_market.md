# T-565 Pre-Registration — T4M-PROJ Model-vs-Market Calibration Reproduction

**Status:** PRE-REGISTERED, IMMUTABLE from the moment this file is pushed to origin/main.
**Session:** T-565, worktree `session/20260922T235038Z-calibration-model-vs-market`.
**Written:** 2026-09-22, BEFORE any analysis script has been run, BEFORE the live VPS
portfolio has been pulled. This file records only what was already read at write time:
the CLAIM figures supplied in the task, and ADR-0046's text (read in full, quoted below
where load-bearing). No Brier/ECE/paired-diff/P&L figure has been computed by this
session as of this file's first commit.

**Standing DO NOT (from task):** once pushed, the criteria below may not be relabelled
after seeing results. If a criterion turns out to be poorly chosen, that is reported as
a limitation in Deliverable 5, not silently patched here.

---

## 1. What the CLAIM is

A Cowork strategic window computed the following on 2026-09-22 from the LOCAL mirror
`logs/.vps_portfolio_cache_mlb_t4.json` (last_updated 2026-09-21T01:57:35Z):

| figure | claimed value |
|---|---|
| clean_n | 765 |
| closed positions (mirror) | 2994 |
| logic_epoch | 12 |
| game window | 2026-07-31 to 2026-08-13 |
| Brier | 0.2191 |
| ECE | 0.0519 |
| observed base rate | 0.4026 |
| mean model_p | 0.3976 |
| skill vs climatology | +0.089 |
| market Brier (same 765 events) | 0.1890 |
| paired diff (model − market), bet-level | +0.0301, se 0.0053, t=5.66 |
| paired diff, day-clustered (11 game-days) | +0.0593, se 0.0207, t=2.87 |
| cohort P&L | +$39.73 total, +$0.052/bet, win rate 40.5% |

This is a claim from a local, possibly-stale mirror. It is not yet evidence.

## 2. Outcome/price construction (as specified by the task, used verbatim in D2–D4)

- `y = 1 if actual_hits >= kalshi_threshold else 0`
- `p = model_p` (raw, not directionally flipped for NO-side rows)
- market price = `mid_price_at_entry`, YES-side convention, cross-checked against
  `entry_price_paid` on a NO row for sign consistency
- clean filter: `prediction_market_bot.logic_epoch.is_clean_for_band(logic_epoch, "T4M-PROJ")`
- Brier/ECE: `c7_monitoring.monitor._compute_brier` / `_compute_ece`, 10 equal-width bins

## 3. What counts as REPRODUCED vs NOT REPRODUCED (Deliverable 2)

Two figure classes, two tolerances:

**Count/identity figures** (clean_n, closed-position count, logic_epoch value, game-day
span in calendar dates) — must match **exactly**. Any delta is NOT REPRODUCED for that
figure, and the delta itself is reported (this is also how a stale-mirror finding gets
surfaced — see §5).

**Continuous metrics** (Brier, ECE, base rate, mean model_p, skill, market Brier, paired
diff, se, t, day-clustered diff/se/t, P&L total/per-bet, win rate) — REPRODUCED if the
recomputed value **rounds to the same figure at the precision the claim itself used**
(4 decimals for Brier/ECE/base-rate/mean-p/paired-diff/se, 3 for skill, 2 for t-stats and
day-clustered diff/se, 2 for P&L dollars, 1 decimal-point for win-rate percent). Anything
outside that rounding band is NOT REPRODUCED, and the signed delta is reported alongside
the recomputed value — no figure is reported as a bare pass/fail without its number.

A figure computed from a *different* live n than the claimed 765 (see §5) is evaluated
against the claim only as a directional/sign check, not a numeric-tolerance check —
if n differs, exact numeric reproduction is not the right question and D2 says so
explicitly rather than forcing a tolerance comparison across mismatched samples.

If any figure is NOT REPRODUCED, Deliverable 2 stops there and reports what was
obtained; Deliverable 4 does not run this session (per task instruction).

## 4. Materiality threshold for model-minus-market Brier difference

A model-vs-market paired Brier difference is treated as **material** only if **both**:

1. Statistically significant at the **day-clustered** level (not bet-level) —
   `|t| >= 2.0` against the day-clustered se, using game-day as the clustering unit
   (below). Bet-level significance alone is not sufficient: bets within a game-day
   share the same underlying game state and are not independent draws, so the
   bet-level se understates true uncertainty. This is the conservative, decision-
   relevant test.
2. `|paired diff| >= 0.01` absolute Brier points — roughly 5% of the ADR-0046 baseline
   magnitude (0.2190) and the CLAIM's own market Brier (0.1890), chosen as a threshold
   large enough that it would not plausibly be sampling noise or floating-point/binning
   artifact at n≈765.

Both bet-level and day-clustered results are reported regardless; only the day-clustered
test governs the materiality verdict.

## 5. Significance test and clustering unit

- **Bet-level paired test:** one-sample t-test on the per-bet difference
  `d_i = (model_p_i − y_i)^2 − (market_price_i − y_i)^2` against 0, df = n_clean − 1.
- **Day-clustered test:** compute the mean of `d_i` within each game-day (the calendar
  date the game resolved on), producing one mean-diff observation per game-day, then run
  a one-sample t-test on those day-means against 0, df = (number of game-days − 1). This
  matches the claimed pattern of se=0.0207/t=2.87 on "11 game-days" — a day-level mean
  test, not a cluster-robust bet-level SE correction — and is the test actually run.
- **Clustering unit for Deliverable 4's extension table:** game-day, identically defined,
  per cell.

## 6. Comparability checklist for ADR-0046 (Deliverable 3) — read, not yet verdicted

ADR-0046 (read in full before writing this file) states its own derivation explicitly.
Quoting the load-bearing text: its n=261 baseline used

- **`raw_n`, not `clean_n`** — ADR-0046 §"Why raw_n, not clean_n" argues the epoch
  boundaries (GG-087/077/113/119/123) gate the approval/sizing write path, not `model_p`
  itself, so restricting to clean_n was judged unnecessary for a calibration baseline.
  This is a *different filter* than this task's specified `is_clean_for_band(...,
  "T4M-PROJ")` clean-epoch filter.
- **Directional `p_estimate`**: `model_p` for YES bets, `1 − model_p` for NO bets, with
  `outcome = 1` iff WIN. This task's construction uses raw `model_p` against
  `y = actual_hits >= kalshi_threshold` directly, with no YES/NO directional flip
  described. These are not guaranteed to be the same quantity per-row.
- **Scope**: `threshold ∈ {1, 2}` across MLB generally, filtered on `duplicate_of`
  exclusion and `outcome ∈ {WIN, LOSS}` — **not scoped to the T4M-PROJ band
  specifically**, and not scoped to logic_epoch 12 (ADR-0046 predates epoch 12; it was
  derived 2026-07-16, this task's window is 2026-07-31 to 2026-08-13, entirely after
  ADR-0046's derivation date).
- **ECE binning**: 10 equal-width bins on `[0,1]` — this one dimension matches.

Pre-registered comparability rule: the Brier/ECE-vs-ADR-0046-baseline comparison is
**comparable only if** clean filter, directional convention, and band/threshold scope
all match. Based on the text above, at least the clean-filter and band-scope dimensions
already look mismatched before any data is pulled — Deliverable 3 verifies this against
the live data and states the verdict explicitly, but this file commits in advance to
reporting non-comparability plainly if confirmed, rather than adjusting the comparison
to make it fit post hoc. The model-vs-market comparison (Brier(model) vs Brier(market)
on the *same* 765-ish rows) does not reference ADR-0046 at all and is unaffected by
whatever this verdict turns out to be.

## 7. Deliverable 4 — MIN_N for per-cell extension table

`MIN_N = 30`, matching the existing precedent in this codebase (ADR-0046 cites the
GG-044 "≥30 resolved MLB paper bets" precondition as its own bar for a usable sample).
Cells with `30 <= clean_n < 100` are included but flagged low-power in the table (wide
se, day-clustered df likely single digits); cells below 30 are omitted and listed by
name only, not computed.

## 8. rejected_positions cohort (Deliverable 4)

Pre-registered framing: a same-sign paired diff (model beats market, or market beats
model, matching direction) on `rejected_positions` versus the approved-T4M-PROJ result
is evidence the approved-cohort result is not purely a selection artifact of which bets
the risk engine chose to approve. It is **not** a true holdout (rejected bets were not
randomly withheld; they were filtered by a different rule — the risk gate — which may
correlate with edge in unknown ways) and does not establish out-of-sample generalization
in the ordinary sense. This limitation is restated in Deliverable 5 regardless of the
sign found.

---

*No figure below this line exists yet. Everything above was written and committed before
Deliverable 2's data pull.*
