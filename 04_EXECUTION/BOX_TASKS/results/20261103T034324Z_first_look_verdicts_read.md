# Box task `first_look_verdicts_read` — 20261103T034324Z_first_look_verdicts_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261103T034324Z_first_look_verdicts_read.toml`
- note: W98.2 Part A retry after deploy
- ran: 2026-11-03T03:43:43Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/first_look_verdicts_read.py --report`

```
engine file: engine_20261102T135056Z.json  generated: 2026-11-02T13:49:01Z
summary: {"cells": 49, "logging": 49, "with_outcomes": 46, "reached_look": 12}
cells with a released verdict: 12 of 49

cell | n | d-Brier vs market [95% CI] | d-Brier vs climatology [95% CI] | verdict | next look
NFL_NFL_GAME_TOTAL_T1 | 60 | -0.0161 [-0.0294, -0.0027] | +0.0024 [-0.0079, +0.0128] | RULED_OUT | first look reached
NFL_NFL_GAME_TOTAL_T2 | 60 | -0.0157 [-0.0299, -0.0011] | +0.0024 [-0.0073, +0.0131] | RULED_OUT | first look reached
NFL_NFL_GAME_TOTAL_T3 | 60 | -0.0140 [-0.0279, +0.0007] | +0.0023 [-0.0074, +0.0128] | SHADOW | first look reached
NFL_NFL_MONEYLINE_T1 | 60 | -0.0061 [-0.0343, +0.0254] | +0.0174 [-0.0150, +0.0476] | SHADOW | first look reached
NFL_NFL_MONEYLINE_T2 | 60 | -0.0070 [-0.0360, +0.0250] | +0.0174 [-0.0166, +0.0487] | SHADOW | first look reached
NFL_NFL_MONEYLINE_T3 | 60 | -0.0075 [-0.0364, +0.0239] | +0.0174 [-0.0166, +0.0487] | SHADOW | first look reached
NFL_NFL_SPREAD_T1 | 60 | -0.0076 [-0.0217, +0.0078] | +0.0049 [-0.0112, +0.0200] | SHADOW | first look reached
NFL_NFL_SPREAD_T2 | 60 | -0.0084 [-0.0232, +0.0078] | +0.0049 [-0.0113, +0.0202] | SHADOW | first look reached
NFL_NFL_SPREAD_T3 | 60 | -0.0080 [-0.0231, +0.0082] | +0.0061 [-0.0105, +0.0212] | SHADOW | first look reached
NFL_NFL_TEAM_TOTAL_T1 | 60 | -0.0071 [-0.0148, +0.0009] | +0.0023 [-0.0052, +0.0092] | SHADOW | first look reached
NFL_NFL_TEAM_TOTAL_T2 | 60 | -0.0076 [-0.0151, +0.0006] | +0.0023 [-0.0054, +0.0096] | SHADOW | first look reached
NFL_NFL_TEAM_TOTAL_T3 | 60 | -0.0070 [-0.0148, +0.0015] | +0.0030 [-0.0052, +0.0107] | SHADOW | first look reached

tally: {"RULED_OUT": 2, "SHADOW": 10}

- NFL_NFL_GAME_TOTAL_T1: rule: delta vs market < 0 with the CI upper bound < 0; E_net k007 +0.0431 kmult +0.0491; look 60, digest a76a2ea191957401, frozen=False; next-look projection {"date": null, "note": "first look reached", "method": "schedule"}
- NFL_NFL_GAME_TOTAL_T2: rule: delta vs market < 0 with the CI upper bound < 0; E_net k007 +0.0470 kmult +0.0531; look 60, digest a76a2ea191957401, frozen=False; next-look projection {"date": null, "note": "first look reached", "method": "schedule"}
- NFL_NFL_GAME_TOTAL_T3: rule: CI spans zero; E_net k007 +0.0477 kmult +0.0537; look 60, digest 38eb32b82a3700b6, frozen=False; next-look projection {"date": null, "note": "first look reached", "method": "schedule"}
- NFL_NFL_MONEYLINE_T1: rule: CI spans zero; E_net k007 +0.0751 kmult +0.0828; look 60, digest a76a2ea191957401, frozen=False; next-look projection {"date": null, "note": "first look reached", "method": "schedule"}
- NFL_NFL_MONEYLINE_T2: rule: CI spans zero; E_net k007 +0.0743 kmult +0.0820; look 60, digest a76a2ea191957401, frozen=False; next-look projection {"date": null, "note": "first look reached", "method": "schedule"}
- NFL_NFL_MONEYLINE_T3: rule: CI spans zero; E_net k007 +0.0727 kmult +0.0805; look 60, digest a76a2ea191957401, frozen=False; next-look projection {"date": null, "note": "first look reached", "method": "schedule"}
- NFL_NFL_SPREAD_T1: rule: CI spans zero; E_net k007 +0.0595 kmult +0.0655; look 60, digest a76a2ea191957401, frozen=False; next-look projection {"date": null, "note": "first look reached", "method": "schedule"}
- NFL_NFL_SPREAD_T2: rule: CI spans zero; E_net k007 +0.0593 kmult +0.0653; look 60, digest a76a2ea191957401, frozen=False; next-look projection {"date": null, "note": "first look reached", "method": "schedule"}
- NFL_NFL_SPREAD_T3: rule: CI spans zero; E_net k007 +0.0591 kmult +0.0651; look 60, digest 79136e1e150838d3, frozen=False; next-look projection {"date": null, "note": "first look reached", "method": "schedule"}
- NFL_NFL_TEAM_TOTAL_T1: rule: CI spans zero; E_net k007 +0.0339 kmult +0.0387; look 60, digest a76a2ea191957401, frozen=False; next-look projection {"date": null, "note": "first look reached", "method": "schedule"}
- NFL_NFL_TEAM_TOTAL_T2: rule: CI spans zero; E_net k007 +0.0379 kmult +0.0426; look 60, digest a76a2ea191957401, frozen=False; next-look projection {"date": null, "note": "first look reached", "method": "schedule"}
- NFL_NFL_TEAM_TOTAL_T3: rule: CI spans zero; E_net k007 +0.0398 kmult +0.0447; look 60, digest 38eb32b82a3700b6, frozen=False; next-look projection {"date": null, "note": "first look reached", "method": "schedule"}

--- FIRST_LOOK_REPORT.md
# First-look REPORT (released cells only)

Sign convention: `delta_brier_vs_X = Brier(X) - Brier(model)`; positive = model better.
Scoring unit: first ledger row per (market_ticker, band); inference: game-cluster bootstrap.

| cell | status | n (games scored) | delta-Brier vs market (95% CI) | delta-Brier vs climatology (95% CI) | verdict |
|---|---|---:|---|---|---|
| NFL_NFL_GAME_TOTAL_T1 | JUDGED | 60 | -0.0161  95% CI [-0.0294, -0.0027] | +0.0024  95% CI [-0.0079, +0.0128] | **RULED_OUT** |
| NFL_NFL_GAME_TOTAL_T2 | JUDGED | 60 | -0.0157  95% CI [-0.0299, -0.0011] | +0.0024  95% CI [-0.0073, +0.0131] | **RULED_OUT** |
| NFL_NFL_GAME_TOTAL_T3 | JUDGED | 60 | -0.0140  95% CI [-0.0279, +0.0007] | +0.0023  95% CI [-0.0074, +0.0128] | **SHADOW** |
| NFL_NFL_MONEYLINE_T1 | JUDGED | 60 | -0.0061  95% CI [-0.0343, +0.0254] | +0.0174  95% CI [-0.0150, +0.0476] | **SHADOW** |
| NFL_NFL_MONEYLINE_T2 | JUDGED | 60 | -0.0070  95% CI [-0.0360, +0.0250] | +0.0174  95% CI [-0.0166, +0.0487] | **SHADOW** |
| NFL_NFL_MONEYLINE_T3 | JUDGED | 60 | -0.0075  95% CI [-0.0364, +0.0239] | +0.0174  95% CI [-0.0166, +0.0487] | **SHADOW** |
| NFL_NFL_SPREAD_T1 | JUDGED | 60 | -0.0076  95% CI [-0.0217, +0.0078] | +0.0049  95% CI [-0.0112, +0.0200] | **SHADOW** |
| NFL_NFL_SPREAD_T2 | JUDGED | 60 | -0.0084  95% CI [-0.0232, +0.0078] | +0.0049  95% CI [-0.0113, +0.0202] | **SHADOW** |
| NFL_NFL_SPREAD_T3 | JUDGED | 60 | -0.0080  95% CI [-0.0231, +0.0082] | +0.0061  95% CI [-0.0105, +0.0212] | **SHADOW** |
| NFL_NFL_TEAM_TOTAL_T1 | JUDGED | 60 | -0.0071  95% CI [-0.0148, +0.0009] | +0.0023  95% CI [-0.0052, +0.0092] | **SHADOW** |
| NFL_NFL_TEAM_TOTAL_T2 | JUDGED | 60 | -0.0076  95% CI [-0.0151, +0.0006] | +0.0023  95% CI [-0.0054, +0.0096] | **SHADOW** |
| NFL_NFL_TEAM_TOTAL_T3 | JUDGED | 60 | -0.0070  95% CI [-0.0148, +0.0015] | +0.0030  95% CI [-0.0052, +0.0107] | **SHADOW** |

### NFL_NFL_GAME_TOTAL_T1
- verdict **RULED_OUT** - rule: delta vs market < 0 with the CI upper bound < 0
- E_net per contract (entry, expected): k007 +0.0431, kmult +0.0491
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `a76a2ea191957401...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### NFL_NFL_GAME_TOTAL_T2
- verdict **RULED_OUT** - rule: delta vs market < 0 with the CI upper bound < 0
- E_net per contract (entry, expected): k007 +0.0470, kmult +0.0531
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `a76a2ea191957401...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### NFL_NFL_GAME_TOTAL_T3
- verdict **SHADOW** - rule: CI spans zero
- E_net per contract (entry, expected): k007 +0.0477, kmult +0.0537
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `38eb32b82a3700b6...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### NFL_NFL_MONEYLINE_T1
- verdict **SHADOW** - rule: CI spans zero
- E_net per contract (entry, expected): k007 +0.0751, kmult +0.0828
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `a76a2ea191957401...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### NFL_NFL_MONEYLINE_T2
- verdict **SHADOW** - rule: CI spans zero
- E_net per contract (entry, expected): k007 +0.0743, kmult +0.0820
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `a76a2ea191957401...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### NFL_NFL_MONEYLINE_T3
- verdict **SHADOW** - rule: CI spans zero
- E_net per contract (entry, expected): k007 +0.0727, kmult +0.0805
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `a76a2ea191957401...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### NFL_NFL_SPREAD_T1
- verdict **SHADOW** - rule: CI spans zero
- E_net per contract (entry, expected): k007 +0.0595, kmult +0.0655
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `a76a2ea191957401...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### NFL_NFL_SPREAD_T2
- verdict **SHADOW** - rule: CI spans zero
- E_net per contract (entry, expected): k007 +0.0593, kmult +0.0653
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `a76a2ea191957401...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### NFL_NFL_SPREAD_T3
- verdict **SHADOW** - rule: CI spans zero
- E_net per contract (entry, expected): k007 +0.0591, kmult +0.0651
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `79136e1e150838d3...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### NFL_NFL_TEAM_TOTAL_T1
- verdict **SHADOW** - rule: CI spans zero
- E_net per contract (entry, expected): k007 +0.0339, kmult +0.0387
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `a76a2ea191957401...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### NFL_NFL_TEAM_TOTAL_T2
- verdict **SHADOW** - rule: CI spans zero
- E_net per contract (entry, expected): k007 +0.0379, kmult +0.0426
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `a76a2ea191957401...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### NFL_NFL_TEAM_TOTAL_T3
- verdict **SHADOW** - rule: CI spans zero
- E_net per contract (entry, expected): k007 +0.0398, kmult +0.0447
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `38eb32b82a3700b6...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen



```
