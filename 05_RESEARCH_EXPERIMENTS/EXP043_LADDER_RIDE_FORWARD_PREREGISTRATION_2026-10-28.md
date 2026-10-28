# EXP-043 — Ladder ride: forward pre-registration

**Status:** FROZEN at the commit that adds this file (hash is that commit's SHA; recorded in its commit message and in `12_EXPLORATORY/fees_exact/results_W92_2.md`). Written before any archive row dated after the freeze was read. Not edited after the freeze; a change is a superseding EXP.
**Pillar / measure:** PROOF — ride hypotheses pre-registered for a forward look 11 (EXP-042) -> 11 + this. Two HELD_OUT cells carried forward; one pooled ladder hypothesis added.
**Scope guard:** scoring only. No order, stake, gate, model, runner or registry cell. Reads the price archive and Kalshi public market data.
**Block:** W92.2 Part B. Source of the cells and the trigger: `12_EXPLORATORY/ride_ladder/` (W91.2), `ride_cells.toml` (PR #360).

## H-A — the two HELD_OUT cells, forward

| Cell | Gap bin | Out-of-sample net (k007) | 95% interval | games | cluster SD | judged n (full effect) | judged n (half effect) |
|---|---|---|---|---|---|---|---|
| KXMLBTOTAL T0-2h tight | net2-5c | +0.0870 | [0.0336, 0.1424] | 117 | 0.295 | 71 games | 284 games |
| KXMLBTOTAL T0-2h tight | net5c+ | +0.2166 | [0.0951, 0.3411] | 30 | 0.340 | 16 games | 61 games |

Judged n = ((z_a + z_b) · sigma_c / delta)^2, one-sided alpha 0.05 (z 1.645), power 0.80 (z 0.842), delta = measured net, sigma_c = SE · sqrt(games) with SE = (net − lo)/1.96. **The half-effect column is the n for a PASS call**: the cells were chosen on the best of 36, so the measured size is inflated (winner's curse); the net5c+ point estimate in particular is not an expected size.
**Scoring:** forward rows only (archive snapshots after the freeze), the trigger exactly as in 91.2 (`trigger(rec)`, `gapbin(e)`), book tight (half spread <= 0.01), one snapshot per ladder per clock hour, game-clustered. Fee: the **exact** fee from `quant/money.py::fee` (MLB prelive multiplier 0.5), not k007; the trigger set is recomputed under that fee and a bin is assigned by the exact-fee gap. A k007 re-score is reported beside it.
**Pass rule (per cell):** game-clustered 95% lower bound > 0 at the half-effect judged n **and** BH q = 0.10 across the two cells plus H-B **and** positive sign. Otherwise FAIL (n reached) or UNDECIDED (n not reached) — never PASS on a point estimate.
**Earliest look:** MLB accrues nothing between the end of the World Series (~2026-11-01) and opening day (~2027-03-25). At roughly 12-15 games/day with T0-2h ladders, net2-5c half-effect n (284) is reachable about **2027-05-15**, net5c+ (61) about **2027-04-30**. **No H-A look can fall this winter.**

## H-B — the pooled ladder trigger

**Hypothesis:** across sports and families, when a ladder of >= 4 strikes (leave-one-out normal fit, `quant/ladder_loo.py`) prices a strike better than the quote by more than the cost (spread + exact fee), taking that side at the quote has positive net P&L per bet. 91.2's definition exactly, no re-tuning, no cell selection.
**Measured effect (91.2, MLB, whole sample):** 108,279 triggers over 2,191 games, net +0.007 [−0.002, 0.017]; first half −0.006, second half +0.013 [−0.000, 0.026]. This is **not** a significant effect; the hypothesis is that it is real and small.
**Judged n:** sigma_c = 0.227 (from the whole-sample interval over 2,191 games). Using delta = 0.013 (second half, the better-estimated regime): **1,884 games at full effect, 7,535 at half effect** (alpha 0.05 one-sided, power 0.80). At the whole-sample delta 0.007 the full-effect n is 5,831 games. The PASS call uses the half-effect n.
**Scoring population:** NFL rows now (ladder families as the archive carries them); NBA and NHL rows **from the date 92.1's archive lines are installed** (not before; their date is the first row in the archive, read from the archive, not assumed). MLB rows from the season opening are scored as a separate stratum and pooled. Exact fee from `fee()`.
**Pass rule:** game-clustered 95% lower bound of net per bet > 0, pooled, at the half-effect judged n (7,535 games), and the sign positive in at least two of the sport strata with >= 100 games. Fewer games than n: UNDECIDED.
**Earliest look:** NFL gives ~14 games a week (~150 more this season); NBA and NHL from install add very roughly 250 games a month each if their ladders are well covered, which is unverified. **Judged n is not reachable before 2027 on any of those**; the reachable date is the 2026-27 regular-season end for the winter sports plus the MLB 2027 season, i.e. **summer 2027** for a PASS call. A **descriptive checkpoint** (sign and interval, no verdict, no status change) is set for **2027-01-31**.

## Modal outcome, stated before the data
H-A: most likely FAIL or UNDECIDED. Cells chosen as the best of 36 on a time split of one archive regress toward zero; the expected out-of-sample size is a fraction of the measured one and the half-effect n is large. H-B: most likely a net near zero, interval including zero, UNDECIDED at the checkpoint; a small positive pooled net is plausible only if the 91.2 second-half sign holds under the exact fee, which is more favourable than k007 for MLB.

## Statuses
HELD_OUT stays until a verdict. PASS moves a cell to FORWARD_PASSED (a separate toml edit through a PR); FAIL moves it to FAILED. Nothing here is wired to orders.

## Out of scope
Any change to the trigger, bins, fee model or book rule after the freeze; wiring `ride.decide()` to LADDER cells (it keys on price bucket and maps a non-"yes" side to RIDE-NO; `side = "by_trigger"` is not consumable until `ride.py` handles it — registered, not fixed here).
