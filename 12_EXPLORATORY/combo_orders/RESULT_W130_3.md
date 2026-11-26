# W130.3 Part A — combo RFQ demo ledger settled and read

Last reviewed: 2026-11-26. Source: box ledger `exp_output/COMBO_RFQ_DEMO/COMBO_RFQ_DEMO.jsonl` via BOX_TASKS `20261126T0204Z_combo_rfq_demo_read`;
settlement from the public Kalshi market API. Both fills are post-epoch (2026-11-06T01:03:42Z), so NO-side prices are not mirror-priced.

| # | Combo | Legs | Side bought @ price | Engine P(yes) | Quote (buy YES / buy NO) | Settled | Gross P&L (1 contract) |
|---|---|---|---|---|---|---|---|
| 1 | same-game NBA | 4 | NO @ 0.55 | 0.349 | 0.45 / 0.55 | NO | +0.45 |
| 2 | same-game NBA | 7 | YES @ 0.45 | 0.605 | 0.45 / 0.55 | NO | −0.45 |

Two further combos from the same runs are still unsettled; re-read at the next box read before any count is quoted.

**What this says, and does not say**
- n = 2 settled fills. No score is read below judged n (PREREG.md). The table is descriptive, not a verdict.
- **Quote rate is not measurable from this ledger.** 12 RFQs were sent over the runs, only 3 records survive; 3 of 3 recorded RFQs were quoted, in 3.9–9.1 s.
- **The demo maker quoted a fixed 0.45 / 0.55 regardless of the legs.** A 4-leg and a 7-leg combo got the same quote. Demo quotes therefore say nothing
  about what a production maker charges; they test the plumbing and our engine's probability on fills, not the production cost of a combo.
- **Defect found:** `accept_side` had no edge threshold. It took the larger (fair − price) gap even when negative, and sent a one-sided YES with
  negative edge (HTTP 400). Fill 2 shows the same shape: engine 0.605 vs 0.45 is a +0.155 edge by the engine on a 7-leg combo, the largest
  extrapolation in the sample. Fixed in this block: accepts require engine edge ≥ fee + 0.03, with skip reasons counted.
- Same-player cross-stat combos (flagged by the combo shadow) and teammate-points combos (joint.py has the wrong sign for teammate PTS×PTS, W110.4/W113.3)
  are now excluded from orders, not only from scoring.
