---
task_id: B-095 / W117.1 (complete)
vision_pillar: EXECUTION (E1/E2/E3 after real costs)
gap_measure: spread_logged on arm orders
gap_delta: 0 of 486 -> 454 of 486 backfilled from the price archive (32 none); 0 logged (no new order since logging merged, box read 04:52Z)
pattern_sweep: spread/depth read path kalshi_client.get_market_book -> demo_fill_policy meta -> arm_orders.submit_context -> placement.join; env pin test in test_demo_fill_policy covered both new switches
surface_delta: 0 new components; 2 approved env switches (ARM_BOOK_CAPS, ARM_PLACEMENT_POLICY)
directive_conflicts: none found (OPERATOR_DIRECTIVES.md read; no placement/caps directive)
---
# W117.1 handoff
## Merged
#512 spread/depth at submit, NFL per-leaf NO BET (reason "hypothesis closed (EXP-W110.5 NFL per-leaf, parked for R&D)", tested), archive backfill, clustered cross. #514 ARM_BOOK_CAPS=raised. #519 frozen table + prereg + ARM_PLACEMENT_POLICY=on.
## Part B (post-epoch, game-clustered, real spread, box read 20261118T045227Z)
FADE crossed +0.166 [-0.016, +0.348], 105 orders / 20 games. RIDE +0.016 [-0.057, +0.089] (253 / 22). MOMENTUM +0.052 [-0.087, +0.191] (96 / 21).
**No arm-and-option clears zero after costs.** The earlier FADE +0.183 [+0.089, +0.277] was order-level; clustering by game widens it past zero. By sport: FADE NBA +0.170 [-0.041, +0.380] (93 / 15); NFL, NHL too thin.
Why FADE rests: every arm order rests at own-side best bid (book_anchor_cancel, 60 s). FADE backs the side the market is leaving, so its bid is rarely hit: 6 of 111 filled. Mechanism from code; price-vs-touch at submit per order NOT yet tabulated.
## Part C
Table has 0 cells (rule: clustered diff interval above 0 and >= 20 games). Switch on = no-op until a re-fit. Prereg: 05_RESEARCH_EXPERIMENTS/EXP-W117.1_placement_policy_PREREG_2026-11-18.md.
## Caps and deploy
Skips before (02:38Z): day cap RIDE 5,039 / FADE 2,040 / MOMENTUM 2,046. After: NOT read; no orders since 03:45Z, so no after number exists yet. Box deploy 05:03Z, HEAD 8f8b560d. t4-mlb started 04:55Z (has caps); #519 merged 05:03Z, so the policy line loads at the next restart. Decision: no restart (empty table, no-op).
## Open
Re-read skips and spread_logged once new orders exist. Healthcheck was UNHEALTHY at 02:35Z; later healthcheck fix landed (#516), not re-verified here. Tabulate FADE price vs touch.
