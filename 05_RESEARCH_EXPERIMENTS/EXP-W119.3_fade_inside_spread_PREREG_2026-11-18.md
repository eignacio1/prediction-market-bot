# EXP-W119.3 FADE rests inside the spread - pre-registration (frozen 2026-11-19T01:08:53Z, before any order at this option)
**Last reviewed:** 2026-11-18. Demo only, kelly_fraction 0. Ships under the 2026-11-17 placement approval (ARM_PLACEMENT_POLICY=on, frozen table);
this adds ONE option to that frozen table. Amends nothing in EXP-W117.1 (its fit and its cross rule stand).

**Why.** FADE backs the side the market is leaving; resting at its own best bid it filled 6 of 111 orders (W117.1; mechanism from code, price vs touch
at submit not tabulated). Crossing the spread paid +0.166 [-0.016, +0.348] per order on 105 orders / 20 games - not clear of zero, and it pays the spread.
Resting inside the spread is the cheaper way to ask whether a better price fills more without paying all of it.

**Option (policy.price_for, rest_inside).** Spread in ticks (0.01): under 2 -> no inside price, the order stays rest_touch ("inside_not_room").
2 ticks or more -> the mid, snapped to the tick toward our own touch (YES buys round down, NO buys round up), so it never crosses; on a
2-tick spread that is one tick inside. Cancel at 60 s, the same rule as every arm order (book_anchor_cancel).

**Assignment.** Table cell FADE: best rest_inside, share 0.5, forward_test true. Per order, sha256(row id) decides: inside for half, rest_touch for the
other half as the CONCURRENT control (reason "control:FADE"). Outcome-blind and deterministic. RIDE and MOMENTUM stay rest_touch (W117.1: no cell cleared).
The table cell is an assignment to a pre-registered test, not a fit; "supported" in it means "run this test".

**GG-1943 fixed first.** placement.model counts a record as evidence for rest_touch / rest_inside only if its cancel_rule is cancel_60s (every record
joined from the arm log; a record that says otherwise, e.g. the never-cancelled ADR-0072 control, is excluded and never pooled). Test:
test_gg1943_never_cancelled_control_is_not_rest_inside_evidence.

**Measures, per option (rest_touch vs rest_inside), FADE, post-epoch only, orders with a logged spread:**
fill rate (Wilson 95%); adverse-selection term (E(won - price | filled) minus E(won - price | not filled), price-adjusted); net per order placed after
exact maker fees (game-clustered 95% interval); the fill-rate difference and the net difference, game-clustered.
**Judged n:** 100 resolved orders AND >= 20 games PER OPTION. No look is read below it; before that the per-option counts are reported as counts only.
**Reading a look.** Net difference (inside - touch) interval wholly above 0 -> rest_inside becomes FADE's option for the next frozen table (share 1.0).
Includes 0 -> unchanged, keep splitting. Wholly below 0 -> the hypothesis "resting inside helps FADE" is closed (EXP-W119.3, parked for R&D); FADE stays
rest_touch; no arm closes. Re-fit of any other cell: a new dated table and a new line here, on orders whose spread was LOGGED at submit, never archive-backfilled.
