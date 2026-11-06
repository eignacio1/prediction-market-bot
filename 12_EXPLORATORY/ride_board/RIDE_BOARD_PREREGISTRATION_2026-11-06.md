# Ride / fade board — pre-registration (W105.4, B-053)

Status: **PART 1 FROZEN** at the commit that adds this file, before any trade P&L was computed. Part 2 (cells, judged n, forward looks, decision words, modal outcome) is appended by a later commit after Part A is run; Part 1 is not edited afterwards.
Purpose (Hard Rule 12): BREADTH — ride / fade cells with a measured, cost-net, out-of-sample status in NBA / NHL / NFL, 1 (NFL, calibration only) -> N. Demo only, kelly_fraction 0, no order path touched.

## Part 1 — the measurement rules (frozen)

Data: `exp_output/PRICE_ARCHIVE/prices_*.jsonl` (quote snapshots, ~20 min cadence), all 22 in-season-or-recent series that 103.2 measured. Cluster = `event_ticker` (one game).

1. **Event** = exactly the 103.2 definition: a one-step `yes_mid` move (gap <= 30 min) with |move| > k*sigma, k = **3**, price before in [0.05, 0.95], 60-minute refractory per market. No other k is a result (k = 2 / 4 may be shown, labelled sensitivity).
2. **Split by game, in time.** Games of a family ordered by their first snapshot; earlier **70% = fit**, later **30% = held out**. sigma_f (RMS of all step moves) is computed on the **fit games only** and applied unchanged to the held-out games. Direction (fade or follow) and any selection are chosen on fit only.
3. **Trade.** Observed at the event snapshot (the move is known only at that snapshot's quote). **FADE** = take the side against the move; **FOLLOW** = the side with it. Entry at the quote shown at that snapshot, crossing the spread: YES bought at `yes_ask`; NO bought at `1 - yes_bid`. A snapshot without a valid two-sided quote (0 < bid < ask < 1) is not tradable and drops out (counted).
4. **Exit** (primary): at ~60 minutes (tolerance +/-10 min, no interpolation), selling at the bid of the held side (YES at `yes_bid`; NO at `1 - yes_ask`), paying taker fee again. An event without a valid quote at 60 min drops out of that exit only.
   **Exit** (secondary): hold to the settlement proxy (last snapshot <= 0.03 or >= 0.97 gives y = 0 / 1; undecided markets excluded, never guessed); one entry fee.
5. **Fee: exact** — `quant.money.fee(series, price, 1, "taker", phase)` per contract, each leg (entry, and exit when sold), phase "live" if the snapshot's UTC date is the ticker date or the day after, else "prelive" (conservative: live multiplier is >= prelive). Rounded-up centicent as the schedule defines.
6. **Net P&L per contract** = exit proceeds (or settlement payoff) - entry price - fees. Reported per family and trade rule as the game-clustered bootstrap mean (`quant.inference.cluster_bootstrap`, 2,000 draws, 95% percentile interval) with n events, n games; fit and held-out side by side.
7. **Tight-book subset** reported separately: entry `half_spread` <= 0.01. (103.2: KXMLBHIT's effect was bid-ask bounce.)
8. **Status rule** (the router's rule, unchanged): a cell (family x trade rule) is **HELD_OUT** only if (a) fit net mean > 0, (b) held-out net mean > 0 with 95% interval lower bound > 0, (c) >= 15 held-out games. Otherwise **IN_SAMPLE** (a cell is written only if fit net mean > 0 for some rule). The router fires only for HELD_OUT / FORWARD_PASSED. The Holm-adjusted p over all (family x rule) held-out tests is reported beside each status; a HELD_OUT cell that fails Holm is labelled so in RESULT.md.
9. **Multiplicity honesty.** 22 families x 2 rules x 2 exits x 2 book views are examined; the primary table is **60-min exit, all-books, both rules**; everything else is secondary and unadjusted.
10. **Power** (for Part 2): judged n in held-out-equivalent games = (z_{0.95}+z_{0.80})^2 * sd_game^2 / effect^2 using the fit effect and the per-game sd of net P&L, via `quant.inference`.
11. This block reads the archive only. It places no order and changes no model, runner, ledger or frozen file. Not conflicting with EXP-042 (price-bucket calibration cells, no move trigger) or EXP-043 (ladder cells): different triggers, different families of rule; no EXP-042/043 cell is edited.

## Part 2 — cells, judged n, looks, decision words, modal outcome (appended after Part A; Part 1 above is unedited)

Part A was run once with the Part 1 rules (`analyze.py` -> `results.json`, 22 families, 28 primary held-out tests with >= 15 held-out games). Nothing in Part 1 was changed after seeing it.

**Status under rule 8, read against rule 9 (primary table = 60-min exit, all books).** No primary cell has a positive held-out lower bound; every Holm-adjusted p is ~1.0. **Zero cells are HELD_OUT.** Only KXMLBTOTAL FADE (all books, 60-min) has fit net > 0 on the primary view, so it is the only cell rule 8 lets us write from the primary table. NBA, NHL, NFL: no primary cell has fit net > 0, so **no cell is written for them** (the 103.2 FADE signals on KXNFLTEAMTOTAL / KXNHLTOTAL are gross of spread and fee and do not survive them: fit net -0.09 / -0.37 per contract).

**Secondary candidates (unadjusted; disclosed, not promoted).** 160 held-out tests were examined; 4 satisfy rule 8's three conditions on a secondary view. At a one-sided 2.5% the expected number of false passes among 160 is 4. These 4 are therefore chance-level as a group and are written as **IN_SAMPLE forward candidates**, never HELD_OUT.

| # | Family | Rule | View | Fit net | Held net [95% CI lo] | Held games | Judged n (event-bearing games) |
|---|---|---|---|---|---|---|---|
| 1 | KXMLBTEAMTOTAL | FADE | tight, 60-min | +0.062 | +0.062 [+0.004] | 49 | 263 |
| 2 | KXMLBTEAMTOTAL | FOLLOW | tight, settle | +0.072 | +0.075 [+0.014] | 101 | 410 |
| 3 | KXMLBTOTAL | FOLLOW | tight, settle | +0.057 | +0.085 [+0.028] | 95 | 266 |
| 4 | KXMLBHIT | FOLLOW | tight, settle | +0.203 | +0.080 [+0.015] | 19 | 118 |
| 5 | KXMLBTOTAL | FADE | all, 60-min (primary) | +0.022 | +0.036 [-0.008] | 74 | 740 |

**Judged n** = games with >= 1 qualifying event needed for 80% power, one-sided alpha 0.05, to detect half the observed held-out net (winner's-curse shrink), using the per-game SD implied by the held-out clustered interval: n = ((1.645 + 0.842) * SD / (net/2))^2.

**Forward rows** = archive snapshots after this file's commit, same rules, sigma frozen at the fit-games value. MLB has no regular games until ~2027-03-25. **Looks:** one scored look per cell, when its judged n is reached (earliest estimated mid-2027 for cell 4, later for the rest; the date is a consequence of accrual, not chosen). Interim reports of n only, no verdict, on 2027-06-01 and 2027-07-15.

**Decision words.** FORWARD_PASSED iff forward net > 0, clustered 95% lower bound > 0 at judged n, same trade rule. FAILED iff the point estimate <= 0 at judged n. Anything else at judged n: INCONCLUSIVE, no router use. Below judged n: no verdict. Holm across the 5 cells is reported beside each.

**Modal outcome (stated in advance).** Most likely (~70%) all five end FAILED or INCONCLUSIVE: the group-level pass count equals chance. If one passes, it will most likely be cell 4 or 1 and carry a smaller net than the held-out figure.

**Non-conflict.** EXP-042 tests price-bucket calibration cells (W89.2) and EXP-043 tests the ladder trigger; neither uses a move-trigger, and neither is a frozen test of these cells. Same archive, different hypotheses. No frozen test is edited.

**Guardrails.** Demo, kelly_fraction 0, router rows are inert until 105.5 wires a MOVE lookup and the status is HELD_OUT / FORWARD_PASSED.
