# Box task `forward_entry_cost_read` — 20261103T053316Z_forward_entry_cost_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261103T053316Z_forward_entry_cost_read.toml`
- note: W98.2 Part B
- ran: 2026-11-03T05:35:18Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python 12_EXPLORATORY/forward_entry_cost/entry_cost.py --log logs/demo_fill_policy.jsonl --report`

```
# Forward-test entry cost (W98.2 Part B)  window=17.59d  orders=130093  with outcome=121297  dropped={'outcome_pending': 4924, 'no_cache': 3872}

| cell | orders | fills | fills/game | as entered (taker fee) | as entered (maker fee) | taken at quote | +depth holds | days to 550: now / taking |
|---|---|---|---|---|---|---|---|---|
| ALL|control | 62615 | 28569 | 116.608 | +0.0123 [-0.0197,+0.0469] n=28569 | +0.0248 [-0.0073,+0.0594] n=28569 | -0.0987 [-0.1416,-0.0520] n=3580 | -0.8351 [-0.8589,-0.8112] n=2 | 0.0 / 0.0 |
| ALL|treatment | 58682 | 6848 | 27.951 | +0.2313 [+0.1744,+0.2858] n=6848 | +0.2442 [+0.1873,+0.2988] n=6848 | -0.0992 [-0.1381,-0.0549] n=3266 | -0.5145 [-0.9346,-0.2838] n=5 | 0.0 / 0.0 |
| NBA|control | 41992 | 18623 | 202.424 | -0.0238 [-0.0642,+0.0192] n=18623 | -0.0112 [-0.0516,+0.0318] n=18623 | -0.0912 [-0.1510,-0.0269] n=1749 | -0.8351 [-0.8589,-0.8112] n=2 | 0.0 / 0.0 |
| NBA|treatment | 39907 | 3623 | 39.38 | +0.1806 [+0.1096,+0.2497] n=3623 | +0.1938 [+0.1228,+0.2629] n=3623 | -0.1148 [-0.1714,-0.0531] n=1502 | -0.5145 [-0.9346,-0.2838] n=5 | 0.0 / 0.0 |
| NFL|control | 13483 | 6778 | 169.45 | +0.0390 [-0.0262,+0.1028] n=6778 | +0.0512 [-0.0138,+0.1151] n=6778 | -0.1331 [-0.1967,-0.0584] n=1601 | n/a | 0.0 / 0.0 |
| NFL|treatment | 11669 | 2527 | 63.175 | +0.2308 [+0.1237,+0.3383] n=2527 | +0.2434 [+0.1366,+0.3508] n=2527 | -0.0985 [-0.1589,-0.0336] n=1565 | n/a | 0.0 / 0.0 |
| NHL|control | 7140 | 3168 | 28.035 | +0.1679 [+0.1168,+0.2156] n=3168 | +0.1802 [+0.1291,+0.2278] n=3168 | +0.0843 [-0.0652,+0.1968] n=230 | n/a | 0.0 / 24.5 |
| NHL|treatment | 7106 | 698 | 6.177 | +0.4966 [+0.4057,+0.5719] n=698 | +0.5086 [+0.4177,+0.5838] n=698 | +0.0134 [-0.0889,+0.1183] n=199 | n/a | 0.0 / 31.0 |

- book = shadow (the demo-order flat-stake book); paper rows record no arm and are not in this test
- P&L per contract = outcome - price - fee; fee exact (quant.money.fee_rate), taker headline, maker sensitivity
- taken-at-quote uses the archive quote at/before the decision time, excluded if older than 300s; depth unknown is counted as holding in the timeline upper bound
- an unfilled order has no as-entered P&L (zero contracts); its outcome is used only for the counterfactual

```
