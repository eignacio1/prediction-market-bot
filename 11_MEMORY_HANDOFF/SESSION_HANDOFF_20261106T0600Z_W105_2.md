<!-- session-meta
task_id: W105.2-B-052
tier: STANDARD
timestamp: 2026-11-06T06:10:00Z
commit: 52638e3
one_line_summary: W105.2 B-052: order-context fields logged (PR #440), GG-1793/1794/1810 resolved, placement study merged (PR #443).
gg_touched: GG-1793, GG-1794, GG-1810
adr_touched: none
plan_deliverable_moved: no
vision_pillar: EXECUTION
gap_measure: E3
gap_delta: order fields logged on new orders 0 -> 6 (code merged, first real row not yet seen); E3 counterfactual per rule done, pre-epoch YES-only n=65,217 orders (result.json @ 263f7d4+#443)
pattern_sweep: wire-side intended-side defect swept in scripts/demo_fill_forward_report.py (fixed #440); other order-GET readers NOT exhaustively swept - open item
surface_delta: 0
-->

# SESSION_HANDOFF 2026-11-06 — W105.2 (B-052) order data + counterfactual placement

```
vision_pillar: EXECUTION
gap_measure: E3 (win rate / markout on fills vs non-fills; adverse selection)
gap_delta: order fields logged on new orders 0 -> 6 (code merged; first real row NOT yet observed). E3 counterfactual per rule: done on pre-epoch YES-only n=65,217 orders / 17,135 fills / 1,800 games; post-epoch n=0.
surface_delta: +0 running components (fields added to existing order log; no order/price/placement change). Red signals: not re-measured this block.
pattern_sweep: wire-side/intended-side defect (GG-1770 pattern) swept in scripts/demo_fill_forward_report.py (fixed, #440). Other readers of order GET side were NOT exhaustively swept in this session -> open item below.
```

## Tickets
- GG-1794 fields: RESOLVED in code (#440, merged, CI green). Unverified: (a) real Kalshi market payload may not carry yes_bid_size/yes_ask_size (then those two are None); (b) box HEAD = 263f7d49 but newest box shadow_order (2026-11-05T10:23Z) predates the merge, so zero post-merge rows exist yet.
- GG-1793: RESOLVED (#440). GG-1810: RESOLVED (#440); derived file produced from a COPY of the cache (17,312 filled intended-NO entries re-scored); NOT placed on the box.
- Part B tools `quant/placement.py` + 8 tests + runner + RESULT.md: PR #443 (CI was still pending at handoff time; merge only on a green run you read).
- Found+fixed in-session: bucket_markout clobbered price edges with CI keys (now price_lo/price_hi, tested).

## Findings (descriptive; no prereg, so hypotheses not verdicts) — see 12_EXPLORATORY/quant_w105_orders/RESULT.md
- 1-min markout worsens monotonically with price: -0.5c (<0.20) to -4.1c (>=0.80). Slope, not step (change-point 0.51, CI 0.29-0.79).
- No rule makes fills positive. Cap >=0.50: per fill -1.23c -> -0.73c, net/order -0.26c -> -0.16c; settle P&L unchanged within noise.
- Post lower (treatment vs control): net/order +0.44c (CI +0.29,+0.61), fill rate -28.8 pts.
- Not testable: cancel-after-t (cache times are collector-observed), distance-from-mid/depth (never logged until #440).

## For the operator
- Recommend (not applied): pre-register "do not rest >= 0.50 on held side" as a shadow arm. Needs post-#440 rows plus post-epoch NO fills.
- Box install task: none needed (fields ride the existing runner). Service restart on next deploy picks up #440; confirm with deploy_truth_read.
- Open: GG archive move for 1793/1794/1810 (status set to RESOLVED in place); ACTIVE_QUEUE row 105.2 update; post-merge row check.

## POST-MERGE ADDENDUM (supersedes any "CI pending / queue row open" text above)
- PR #440 and #443 both MERGED (#443 on green run 42171050764). ACTIVE_QUEUE row 105.2 DONE (52638e3).
- GG-1793/1794/1810 set RESOLVED in place; archive move NOT done (operator sign-off per retire_resolved_gaps).
- Open: confirm a real post-merge shadow_order row carries the new fields (none yet; box newest row predates merge); verify book size fields vs live payload; wider sweep of order-side readers; rescored cache not on box.
- Recommended (not applied): pre-register "do not rest >=0.50 on held side" as a shadow arm.
