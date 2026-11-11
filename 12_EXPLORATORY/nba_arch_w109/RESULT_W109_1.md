# W109.1 Part C -- NBA applied path (factor -> filter -> tree -> price), moneyline KXNBAGAME

Script: `applied_path.py`; output `applied_path_out.json` (+ per-game rows csv.gz). Test season 2025-26, held out (K on 2024-25; v2 params fit on 2022-23..2024-25 in-coverage seasons; Platt on training predictions only). Market = mid of last hourly Kalshi candle ending <= tip-1h, flipped to home side. Historical quotes only: no demo fills, no data-epoch mix (GG-1771/1784 not engaged).

## Result: NULL (market better)
n=397 games scored (of 1,130 test games with factors; Kalshi game-market history starts 2026-02, so the rest have no quote -- not dropped for outcome disagreement; 226 Kalshi events fall outside the regular-season frame: 2026-27 and playoffs).
| | Brier |
|---|---|
| Kalshi mid (tip-1h) | 0.1529 |
| Tree T3 (1h, ratings + lineup) | 0.1745 |
| Tree T1 (20h, ratings only) | 0.1775 |

Paired Brier diff, game-cluster bootstrap: T3 - market **+0.0215 [+0.0117, +0.0312]** (market better); T1 - market +0.0246 [+0.0142, +0.0347]; T3 - T1 -0.0031 [-0.0124, +0.0065] (lineup adds nothing resolvable).
Gate (lineup shift >= train p90, 5.43 pts): n=52, T3-market +0.012 [-0.006, +0.030] -- below judged n, not scored as a result.
Net, flat 1 contract at the quote, before fees: all-games T3 bets at edge>2c: 339 bets, -0.042/contract [-0.082, +0.001]; >5c: -0.046 [-0.090, -0.002]. Gated T1: ~0 with intervals spanning zero (n<=50). No positive cell.

## Reading
Consistent with W88.3 (-0.015) and the efficiency-gradient prior: the NBA moneyline at tip-1h is already well priced, and the tree is worse in Brier and loses net. The architecture is built and runs end to end; it does not yet find edge on ml. Limits: lineup factors exist 2023+ only; 2025-26 quotes cover Feb-Apr 2026 only; one family (ml); hourly candles, mid quote.
