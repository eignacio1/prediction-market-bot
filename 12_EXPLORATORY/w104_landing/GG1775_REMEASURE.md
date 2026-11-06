# GG-1775 re-measure (W104.3, 2026-11-06) - shadow fill win rate vs fill price

Source: box `exp_output/FORWARD_TEST/demo_fill_forward_cache.json` (built 2026-11-05 11:43Z) joined to `logs/demo_fill_policy.jsonl` (shadow_order, ok, with order_id). Read-only; throwaway scripts run over ssh, not committed (docs-only rule, fence test).

**Epoch split (GG1771_EPOCH 2026-11-06T01:03:42Z):** post-epoch fills in the cache: **n = 0** (the cache and policy log stop at 2026-11-05 11:43Z, before the epoch). All 38,598 settled fills are pre-epoch. The post-epoch half of the check cannot be made yet; it needs the next forward-report run.

**Reproduced (cache as stored):** NHL 4,309 fills win 0.717 at mean price 0.481 (+0.236, game-clustered 95% [+0.183, +0.289], 305 games); NFL 9,775 win 0.457 at 0.342 (+0.115 [+0.050, +0.178], 176 games); NBA 24,429 win 0.430 at 0.408 (+0.023 [-0.012, +0.060], 543 games); MLB 85 win 0.400 at 0.422.

**Cause found - scoring, not selection.** Every filled cache entry has `side = "yes"` (38,719 of 38,719), but the policy log's intended side is NO for 17,312 of them (YES 21,302; 105 unlabeled). The cache was written by the pre-#431 `order_price_side`: a NO buy comes back as `action=sell, side=yes`, was stored as YES, and `won = (result == "yes")` scored it backwards. Settled entries are never re-read (`lookup_fill` returns a settled hit), so the stale scoring persists in the cache.

**Rescored with the policy log's intended side (won_true = cache won for YES, its negation for NO):**

| sport | YES-only n, win, price, gap | NO n, win, price (price field as stored) | all, rescored gap |
|---|---|---|---|
| NHL | 570, 0.451, 0.466, -0.015 | 3,739, 0.242, 0.483 | -0.211 |
| NFL | 4,921, 0.271, 0.318, -0.047 | 4,854, 0.355, 0.366 | -0.029 |
| NBA | 15,790, 0.308, 0.380, -0.073 | 8,639, 0.346, 0.457 | -0.086 |
| MLB | 63, 0.238, 0.320, -0.082 | 22, 0.136, 0.712 | -0.210 |

The "above the price" gap is gone; pre-epoch fills win BELOW their price in every sport. The YES-only column is the clean one (the NO price field was written by the pre-fix mirror pricing, GG-1771, so the NO columns are indicative only). A below-price result is the adverse-selection direction (resting orders fill when the market moves against them) and is consistent with the fills being non-edge; it is not a P&L claim.

**Consequence.** `12_EXPLORATORY/quant_w103_tails/RESULT.md` shadow tail/breach numbers (NHL, NFL especially) were optimistic for the same reason and must be recomputed on rescored fills. ADR-0072 verdicts are unaffected: since #435 they score only post-epoch rows, which were cached by the fixed code.

**Not done:** (1) post-epoch re-measure (n = 0 now); (2) rewriting the stale cache entries (would mean ~38k order re-reads on the demo API for rows already excluded from verdicts) - not done, registered as GG-1810; (3) price field for pre-epoch NO rows not repaired.
