---
task_id: B-095 / W117.1 (PARKED by operator mid-block, 2026-11-18 02:55Z)
vision_pillar: EXECUTION (E1/E2/E3 after real costs)
gap_measure: spread_logged on arm orders
gap_delta: 0 of 486 -> unmeasured. New-order logging merged but no new order placed since; backfill count not yet read on the box.
pattern_sweep: spread/depth read paths (kalshi_client.get_market_book -> demo_fill_policy meta -> arm_orders.submit_context -> placement.join); only caller of get_market_book is demo_fill_policy.
surface_delta: 0 live components (read-time module + read script fields only)
directive_conflicts: not checked - OPERATOR_DIRECTIVES.md was not read before building. Read it first next session.
---
# W117.1 parked handoff

## Merged (#512, CI green on head 67ef666)
- A2: arm orders log yes_bid/ask, spread, own-touch depth at submit. Verified by tests only; no live row yet.
- A2 backfill: `placement/archive_book.py`, read-time from `exp_output/PRICE_ARCHIVE` (30 min max age). Log never edited. Wired into `scripts/arm_orders_read.py` (`spread_coverage`). Fill count for the 486 NOT yet measured; archive coverage of spread/total tickers on the box is unverified.
- A3: NFL per-leaf -> NO BET, reason "hypothesis closed (EXP-W110.5 NFL per-leaf, parked for R&D)". Tested.
- B tooling: `model.option_net_clustered` (strict real-spread cross, game-clustered CIs, n games + n orders); output under `join.cross_clustered` in arm_orders_read.

## NOT done
1. A1: PR adding `ARM_BOOK_CAPS=raised` to `deploy/demo_fill.env`; merge on green; deploy readback; t4-mlb restart decision; `arm_orders_read` skips before -> after. Before: day cap RIDE 5,039 / FADE 2,040 / MOMENTUM 2,046 (02:38Z).
2. Box `arm_orders_read` on new code (push request docs-only) -> coverage, FADE crossed verdict (plain either way), why FADE rests and rarely fills (6 of 111).
3. Part C: `config/placement_policy.json` frozen + pre-registration (judged n, how a look is read), min n 30 per cell, else rest_touch; then `ARM_PLACEMENT_POLICY=on` PR + readback.
4. No new GG or window error logged. Box healthcheck was UNHEALTHY (1 fault, 02:35Z, nhl_event_store_install refused) - Hard Rule 14 applies before surface grows.
