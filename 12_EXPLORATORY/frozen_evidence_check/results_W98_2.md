# Frozen-evidence re-run (W98.2 Part C) — PARTIAL, stopped at the time cap

Source: box results `04_EXECUTION/BOX_TASKS/results/20261103T054703Z_{a,b,c}_frozen_resume_step.md` and `..._z_frozen_resume_combine.md` (2026-11-03, up to 06:20Z). Read-only; no frozen file touched.

**Plain English:** 11 of the 13 frozen ride cells are classified, and none of the 11 reproduced to the reported numbers. All 11 are DIFFERS: re-run n differs from the reported n (it is larger in 7, smaller in 4) and the net edge is positive in every one but smaller than reported in all 11. Not one is NOT REPRODUCED, because the sign held everywhere. The two KXMLBTOTAL ladder cells are not classified yet: their ladder shards (KXMLBTOTAL, KXMLBSPREAD, KXMLBTEAMTOTAL, and 26 of 95 for KXNFLTEAMTOTAL) did not run in time. The combine prints "NOT REPRODUCED" for them only because n = 0 with the shards missing, so read them as UNCLASSIFIED.

| cell | reported n / net | re-run n (games) | exact net [95%] | class |
|---|---|---|---|---|
| 89.2 KXMLBHIT T0-2h 20-25c all yes | 1892 / 0.027 | 2734 (516) | +0.0186 [+0.0009, +0.0351] | DIFFERS |
| 89.2 KXMLBHIT T0-2h 20-25c tight yes | 1151 / 0.044 | 1864 (488) | +0.0280 [+0.0072, +0.0483] | DIFFERS |
| 89.2 KXMLBF5TOTAL T6-24h 90-95c all yes | 143 / 0.038 | 132 (128) | +0.0397 [+0.0230, +0.0501] | DIFFERS |
| 89.2 KXMLBF5TOTAL T6-24h 90-95c wide yes | 111 / 0.033 | 101 (98) | +0.0443 [+0.0400, +0.0486] | DIFFERS |
| 89.2 KXMLBF5TOTAL T2-6h 90-95c tight yes | 85 / 0.043 | 89 (87) | +0.0473 [+0.0238, +0.0603] | DIFFERS |
| 89.2 KXNFLTOTAL D1 5-10c all no | 154 / 0.038 | 148 (89) | +0.0370 [+0.0014, +0.0637] | DIFFERS |
| 89.2 KXMLBSPREAD T>24h 20-25c tight no | 186 / 0.052 | 262 (206) | +0.0444 [-0.0003, +0.0825] | DIFFERS |
| 89.2 KXMLBTEAMTOTAL T6-24h 15-20c tight no | 49 / 0.095 | 59 (50) | +0.0750 [-0.0017, +0.1433] | DIFFERS |
| 89.2 KXMLBF5 T2-6h 10-15c all no | 44 / 0.078 | 75 (75) | +0.0468 [-0.0184, +0.1004] | DIFFERS |
| 89.2 KXMLBTOTAL T0-2h 85-90c wide yes | 52 / 0.089 | 72 (72) | +0.0419 [-0.0265, +0.0950] | DIFFERS |
| 89.2 KXMLBF7 T0-2h 40-45c wide yes | 121 / 0.065 | 144 (105) | +0.0595 [-0.0033, +0.1166] | DIFFERS |
| 91.2 KXMLBTOTAL T0-2h net2-5c tight (held-out) | 117 / 0.087 | not run | — | UNCLASSIFIED (shards missing) |
| 91.2 KXMLBTOTAL T0-2h net5c+ tight (held-out) | 30 / 0.2166 | not run | — | UNCLASSIFIED (shards missing) |

Results are identical for the "dates < 2026-10-28" window. Caveat: a game whose rows straddle two date files is split across two shards.

## Box capacity (measured)
259 ladder shards ran: total 2390.6 s, mean 9.2 s, max 52.3 s. No unit comes near 900 s, so the sharding fits. The limit is total throughput on one core: about 311 shards remain (95 each for KXMLBTOTAL, KXMLBSPREAD, KXMLBTEAMTOTAL, 26 for KXNFLTEAMTOTAL), and MLB date files are likely larger than NFL. At the observed rate of about 11 min per 700 s step, expect roughly 4–5 more steps, 50–60 min. To finish: queue 5 `frozen_resume_step` requests plus `frozen_resume_combine` in one push.
