# First-look REPORT - synthetic rehearsal

> **SYNTHETIC - rehearsal of the report format on generated data. No cell below is a real cell, no number is a finding, nothing here releases a look.**

NHL synthetic cell uses bootstrap B=400 for runtime (the pre-registration is B=10,000).

Sign convention: `delta_brier_vs_X = Brier(X) - Brier(model)`; positive = model better.
Scoring unit: first ledger row per (market_ticker, band); inference: game-cluster bootstrap.

| cell | status | n (games scored) | delta-Brier vs market (95% CI) | delta-Brier vs climatology (95% CI) | verdict |
|---|---|---:|---|---|---|
| SYN_NFL_model_worse | JUDGED | 60 | -0.1733  95% CI [-0.2800, -0.0667] | -0.1733  95% CI [-0.2800, -0.0667] ⚠ model worse than climatology | **RULED_OUT** |
| SYN_NFL_no_edge | JUDGED | 60 | -0.0031  95% CI [-0.0077, +0.0023] | -0.0031  95% CI [-0.0077, +0.0023] ⚠ model worse than climatology | **SHADOW** |
| SYN_NFL_real_edge | JUDGED | 60 | +0.0475  95% CI [+0.0175, +0.0775] | +0.0733  95% CI [+0.0333, +0.1133] | **CANDIDATE-PENDING-CAPACITY** |
| SYN_MLB_no_edge | JUDGED | 150 | +0.0000  95% CI [+0.0000, +0.0000] | unavailable (no climatology field on this sport's settled rows) | **SHADOW** |
| SYN_NHL_no_edge | JUDGED | 2500 | +0.0000  95% CI [+0.0000, +0.0000] | unavailable (no climatology field on this sport's settled rows) | **SHADOW-continue** |
| SYN_NFL_59_games | SEALED (59 of 60) | 59 | - | - | none (not at a look) |

### SYN_NFL_model_worse
- verdict **RULED_OUT** - rule: delta vs market < 0 with the CI upper bound < 0
- E_net per contract (entry, expected): k007 +0.3725, kmult +0.3813
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `a3d81b3863a2cd43...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### SYN_NFL_no_edge
- verdict **SHADOW** - rule: CI spans zero
- E_net per contract (entry, expected): k007 -0.0075, kmult +0.0013
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `a3d81b3863a2cd43...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### SYN_NFL_real_edge
- verdict **CANDIDATE-PENDING-CAPACITY** - rule: delta vs market CI lower bound > 0 and E_net > 0 under both fees
- E_net per contract (entry, expected): k007 +0.1228, kmult +0.1314
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 60, 60 games, digest `a3d81b3863a2cd43...`, frozen=False
- pre-registration: EXP-037 NFL pre-registration (2026-10-02): first look judged n=60 settled games per cell, second look 150; no scoring before judged n; models frozen

### SYN_MLB_no_edge
- verdict **SHADOW** - rule: CI spans zero
- E_net per contract (entry, expected): k007 -0.0275, kmult -0.0187
- bootstrap: B=2000, seed=20261002, unit=game-cluster
- release: look 150, 150 games, digest `2cbe8362ace24698...`, frozen=False
- pre-registration: EXP-037 MLB pre-registration (2026-10-02): 2026 postseason rows never scored (head-start, counted only); judged looks use 2027 regular season only, n=150 then 600

### SYN_NHL_no_edge
- verdict **SHADOW-continue** - rule: everything else
- E_net per contract (entry, expected): k007 -0.0275, kmult -0.0187
- bootstrap: B=400, seed=20261002, unit=game-mean
- release: look 2500, 2500 games, digest `30524859f017e7c7...`, frozen=False
- pre-registration: EXP-036 NHL pre-registration (2026-10-02): judged n=2,500 settled games per cell; below that figures are PRELIMINARY only; T3 sealed while GG-401 is open

