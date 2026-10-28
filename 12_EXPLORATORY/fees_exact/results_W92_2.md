# W92.2 Part A — exact Kalshi fee, and what it does to the reported nets (PARTIAL)

Fee code merged: PR #357 (ac91bf6): `fee()`, `fee_rate()`, `fee_multiplier()` in `quant/money.py`, table `quant/kalshi_fees.json` (Muse R-068 cards; PDF 2026-07-07 dated, web page 2026-10-27 UNDATED). `fee_k007` untouched.

**Finding:** k007 (0.07·p(1−p)) equals the exact taker fee for NFL (M=1). For MLB it is **2× too high before the game goes live** (M=0.5 prelive, 1 live), so every MLB net reported with k007 is *understated* by 0.5·0.07·p(1−p) per contract. k007 is conservative for MLB pre-game.

## 89.2's 11 cells — ESTIMATE, not a recompute
Fee difference taken at the bucket midpoint (cell membership fixed; nothing re-selected; entries assumed prelive, as the tiers are time-to-start). Interval lower bound shifted by the same amount (the shift is a near-constant, so this is approximate). Exact per-trade recompute needs the settle caches, not done in this block.

| 89.2 cell | old net (k007) | fee diff (midpoint est.) | new net | old lo | new lo |
|---|---|---|---|---|---|
| KXMLBHIT T0-2h 20-25c all | +0.0270 | +0.0061 | +0.0331 | +0.0065 | +0.0126 |
| KXMLBHIT T0-2h 20-25c tight | +0.0440 | +0.0061 | +0.0501 | +0.0170 | +0.0231 |
| KXMLBF5TOTAL T6-24h 90-95c all | +0.0380 | +0.0024 | +0.0404 | +0.0220 | +0.0244 |
| KXMLBF5TOTAL T6-24h 90-95c wide | +0.0330 | +0.0024 | +0.0354 | +0.0110 | +0.0134 |
| KXMLBF5TOTAL T2-6h 90-95c tight | +0.0430 | +0.0024 | +0.0454 | +0.0170 | +0.0194 |
| KXNFLTOTAL D1 5-10c all | +0.0380 | +0.0000 | +0.0380 | +0.0065 | +0.0065 |
| KXMLBSPREAD T>24h 20-25c tight | +0.0520 | +0.0061 | +0.0581 | +0.0026 | +0.0087 |
| KXMLBTEAMTOTAL T6-24h 15-20c tight | +0.0950 | +0.0051 | +0.1001 | +0.0085 | +0.0136 |
| KXMLBF5 T2-6h 10-15c all | +0.0780 | +0.0038 | +0.0818 | +0.0087 | +0.0125 |
| KXMLBTOTAL T0-2h 85-90c wide | +0.0890 | +0.0038 | +0.0928 | +0.0470 | +0.0508 |
| KXMLBF7 T0-2h 40-45c wide | +0.0650 | +0.0086 | +0.0736 | +0.0006 | +0.0092 |

## Not yet done (named for the next block)
- Per-trade recompute of 89.2 / 90.3 momentum headline / 91.2 ladder whole-sample + its 2 HELD_OUT cells (the ladder trigger itself depends on the fee, so its trigger set changes too). A settle re-fetch was started (public GETs, ~2,762 events) into `12_EXPLORATORY/fees_exact/out/settle_cache.json`; it may not have completed. Distance E2: not checked.
- Frozen preregs EXP-041/042 say "k007": for MLB prelive they overstate fees 2×, direction conservative; they stay as written.
- Known table gap: series codes for NFL spread/total, NBA game/spread/total, NHL game, NCAAF spread/total are not printed on the cards, so they take maker 0 (understates their maker fee; taker is right).

**Operator line:** keep EXP-041/042 frozen on k007 (it overstates MLB pre-game fees 2×, so their verdicts are conservative); no action needed unless you want the exact fee shown beside k007 in reports.

# Part B (ride_cells.toml +2 HELD_OUT ladder cells, EXP-043) — NOT STARTED. Next block.
