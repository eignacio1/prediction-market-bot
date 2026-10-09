# W64.2 — Demo fills that don't get picked off: rule built, forward test registered (switches OFF)

**Pillar:** EXECUTION (E1/E2/E3). **Measure moved by this block: none.** Both switches are OFF, so no order, fill or stake changes. The block makes the measures movable once the operator accepts ADR-0072 and the pre-registration.

## Part A — built (PR #208)
- `c5_execution/demo_fill_policy.py`: R1 cancel-after-N (default 60 s, `DEMO_FILL_CANCEL_AFTER_S`) with a durable pending log and `sweep_overdue` for restarts; R2 limit price from the live venue book (rest at our side's best bid, never cross), skipping one-sided/crossed books, failed book reads and model-vs-book mid gaps above 0.05. Every skip and cancel is logged with its reason. One switch (`DEMO_FILL_PLACEMENT_RULE=book_anchor_cancel`; anything else is OFF), seeded hash assignment share.
- `c5_execution/shadow_flat_stake.py`: second switch (`SHADOW_FLAT_STAKE=on`, also requires the first). Called after the shadow row is persisted via an optional `on_row` observer in `pregame_shadow/runner.py`; the row is copied, never altered. Gate = the arm's logged net-of-fee (k007) edge > 0. Stake = ADR-0050 flat measurement stake. `kelly_fraction` untouched.
- Fills are classified by the existing 61.1/62.3 sidecar classifier, unchanged (it reads the ledger and the venue fills; the policy only adds a `fill_policy` field to treated positions).
- Tests: `tests/test_demo_fill_policy.py` (OFF byte-identical and no calls; ON book-anchored price for YES and NO; skips; cancel-after-N; sweep; assignment; shadow row untouched). 139 pass across new + `test_paper_trader` + `test_kalshi_client` + `test_pregame_shadow_safety`.

## Known gaps (stated, not hidden)
- **Cancel endpoint unverified.** DELETE is not permitted this session; `/portfolio/events/orders/{id}` follows the submit path's convention and has not run against the demo API. First ON day must confirm it; the pre-registration turns the policy off on >10% cancel failures.
- Treated orders that skip leave no position (same shape as a venue rejection); control orders are unchanged.
- Assignment keys on `position_id` (random per order), reproducible from the stored id.

## Part B — forward test registered
Folded into `03_DECISIONS/ADR-0072_DRAFT_demo-fills-order-placement.md` § Decision requested (Status PROPOSED). Judged n ~550 fills per arm (design effect ~4 from 63.3's clustered CI), judged on fills; underpowered if unreachable in 8 weeks.

## For the operator, plain English
Switch 1 (`DEMO_FILL_PLACEMENT_RULE`) makes the demo bot price each order off the venue's current bid instead of its own stale guess, skip markets where the book is empty on one side or disagrees with the model, and cancel an order if it has not filled within a minute; half the orders (chosen by a fixed seed) get this, half behave as today so we can compare. Switch 2 (`SHADOW_FLAT_STAKE`) additionally places a small flat demo order, about one dollar, on shadow-cell forecasts that show positive edge, under the same rule. Neither can use real money (demo venue only), neither changes `kelly_fraction` (stays 0), and neither alters a shadow forecast row. On the dashboards you would see fewer demo fills, fewer long-resting orders, and new skip and cancel counts in the policy log; fill rate should fall and win rate on fills should be the number to watch. Nothing is switched on until you say so.
