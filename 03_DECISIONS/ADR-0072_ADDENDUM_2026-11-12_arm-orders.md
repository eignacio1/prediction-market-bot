# ADR-0072 Addendum — the router's arm picks the side of the demo orders (2026-11-12)

**Status: AUTHORIZED by the operator, 2026-11-11 16:51 PT ("yes I approve").** Written by terminal W112.3 (B-083). The frozen ADR-0072 file is not edited; this is the superseding addendum for the one thing below.
Measure: D6 layer 7 (execution by arm, fills measured); E1 / E2 / E3 per arm.

## What changes
On a shadow row that carries a router decision (`row["router"]`, 111.3), the **arm** picks the side of the demo order, not the old net-edge rule (`maybe_place`: larger of `e_net_yes_k007` / `e_net_no_k007`, edge > 0):
RIDE backs the favoured side (mid >= 0.5 -> yes); FADE backs the other; MOMENTUM backs the move's side; POT OF GOLD backs the longshot branch's side; MODEL FADE backs the larger net-edge side; NO BET places nothing. For RIDE and FADE the side is re-derived from the row and a router disagreement skips. Code: `decision_trees/arm_orders.py`, behind the switch `ARM_ORDERS` (`off` default / `dry` / `on`). Rows with no router decision keep the old rule.

## What stays
- Placement rule: `book_anchor_cancel`, cancel after `DEMO_FILL_CANCEL_AFTER_S` (60 s), `DEMO_FILL_MAX_MID_GAP` (0.05). Every registered parameter, the seed (`w64-2`) and share (0.5) unchanged.
- Stakes: flat demo stake (ADR-0050 measurement stake) behind `size_for(arm, cell, context)`; Block 112.2 plugs the per-arm rule into the same signature. `kelly_fraction` 0 everywhere. DEMO money only; `demo_host_ok()` refuses any other host. No real capital (Hard Rule 2).
- Kill switch (global + shadow band, NFR-03), per-event cap and daily breaker (c4 constants), listing and cash checks, the exposure gate, and the zero-orders alarm: unchanged.
- Epoch rules (GG-1771/GG-1784): NO-side fills before 2026-11-06T01:03:42Z were mirror-priced. The per-arm report gives `pre_epoch_yes_only` and `post_epoch_all_sides` separately.

## How the two tests stay separable
- Arm orders go to their own log (`logs/arm_orders/orders.jsonl`, events `arm_order` / `arm_skip` / `arm_would_order`) with their own client-order-id namespace (`arm-orders/<row>`), not into `shadow_order` rows. The treatment-vs-control placement comparison (verdicts a/b/c) is read on `shadow_order` rows only and is unchanged.
- Every arm order is tagged: `arm`, `leaf_id`, split path (branch, tier, filters fired, reason), and `adr0072_assignment` — the treatment / control assignment the row would have had under the registered hash.
- While `ARM_ORDERS=on`, a routed row no longer produces a `shadow_order` row, so the placement test collects only on rows with no router decision. This is stated, not hidden: the placement verdict's n grows more slowly, and the per-arm report is the measurement for routed rows. `dry` leaves the old path untouched.
- `demo_fill_forward_report.py` reports `arm_orders` per arm: orders, fills, fill rate, P&L per filled contract before fees, win rate on fills vs the counterfactual win rate of unfilled orders (E3), 30-minute markout where a markout row exists for the order (the collector does not yet read arm orders: `n_markout` 0 says so).

## Turn-off
Delete the `ARM_ORDERS` line (or set `off`): the old rule resumes on the next run. The ADR-0072 turn-off conditions are unchanged.
