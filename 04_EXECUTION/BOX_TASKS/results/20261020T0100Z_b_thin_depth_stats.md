# Box task `thin_depth_stats` — 20261020T0100Z_b_thin_depth_stats

- request: `04_EXECUTION/BOX_TASKS/requests/20261020T0100Z_b_thin_depth_stats.toml`
- note: W80.1 Part A: depth with post-game split
- ran: 2026-10-20T01:00:43Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python 12_EXPLORATORY/thin_markets/depth_stats.py`

```
| series | bucket | n snaps | n tickers | est-time share | median spread c | median d1 | median d2 | median d5 | P(side>=5 @2c) | P(>=10) | P(>=25) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| KXNBAGAME | in-game | 24 | 24 | 100% | 1 | 5248 | 14405 | 35870 | 100% | 100% | 100% |
| KXNBAGAME | >6h | 4 | 4 | 0% | 1 | 166460 | 267874 | 379639 | 100% | 100% | 100% |
| KXNBAPTS | >6h | 63 | 63 | 0% | 2 | 58 | 1111 | 2127 | 89% | 86% | 60% |
| KXNBAREB | >6h | 53 | 53 | 0% | 4 | 0 | 549 | 2086 | 62% | 60% | 49% |
| KXNBASPREAD | in-game | 313 | 313 | 100% | 7 | 0 | 0 | 886 | 27% | 27% | 21% |
| KXNBASPREAD | >6h | 37 | 37 | 0% | 2 | 1723 | 4975 | 11467 | 100% | 100% | 100% |
| KXNBATEAMTOTAL | >6h | 38 | 38 | 0% | 5 | 0 | 0 | 1504 | 39% | 29% | 29% |
| KXNBATOTAL | in-game | 288 | 288 | 100% | 5 | 0 | 0 | 2754 | 29% | 28% | 22% |
| KXNBATOTAL | >6h | 29 | 29 | 0% | 2 | 1011 | 1987 | 6594 | 100% | 100% | 100% |
| KXNFL1HSPREAD | in-game | 195 | 195 | 92% | 1 | 1416 | 3604 | 6861 | 77% | 75% | 73% |
| KXNFL1HTOTAL | in-game | 130 | 130 | 92% | 1 | 1701 | 3700 | 6934 | 85% | 84% | 82% |
| KXNFLFIRSTTD | in-game | 33 | 33 | 100% | 2 | 48 | 558 | 2130 | 70% | 64% | 55% |
| KXNFLGAME | in-game | 26 | 26 | 92% | 1 | 285826 | 554832 | 789567 | 96% | 96% | 96% |
| KXNFLPASSYDS | in-game | 238 | 238 | 92% | 1 | 431 | 1038 | 3362 | 73% | 71% | 68% |
| KXNFLRECYDS | in-game | 1210 | 1210 | 94% | 3 | 0 | 701 | 2370 | 53% | 53% | 52% |
| KXNFLRSHYDS | in-game | 626 | 626 | 91% | 4 | 0 | 2 | 1272 | 43% | 42% | 40% |
| KXNFLSPREAD | in-game | 156 | 156 | 84% | 1 | 9511 | 29469 | 82757 | 88% | 85% | 83% |
| KXNFLTEAMTOTAL | in-game | 139 | 139 | 85% | 3 | 0 | 3251 | 7706 | 59% | 58% | 55% |
| KXNFLTOTAL | in-game | 118 | 118 | 84% | 1 | 6838 | 22497 | 41646 | 76% | 75% | 74% |

```
