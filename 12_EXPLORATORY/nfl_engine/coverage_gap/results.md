# W82.3 results — 2026 coverage / pressure gap, bot-side

Part A (recompute + Muse grade): `part_a.py`, `results/part_a_verdict.json`. Part B (stability, cross, application): `part_b.py`, `results/part_b_verdict.json`.
The CSVs are gitignored and regenerable (`python3 part_a.py <muse_arch_dir>`; `python3 part_b.py <ws_dir> <frozen_dir>`); only the verdict JSONs are committed.
Muse archive pinned at 4e939f523a4a98e49ee67f3f45a05cee67bfd6fb (read-only).

## Part A — recompute and Muse grade
- Bot recompute from nflverse participation + FTN: man/zone, MOF closed/open, 5+ rusher blitz, pressure, time to throw. Fill is 0% for coverage in 2016–17, ~0.89 in 2018–22, ≥0.996 from 2023.
- Muse prior-season (2023–25) coverage, blitz, pressure, MOF, personnel and team time-to-throw values are null (96 of 96 each). Those classes stay REPORTED: a null is not a pass.
- QB time to throw is the only prior-season class with values: 62 matched QB-seasons, r = 0.962, mean diff −0.161 s (bot lower). Pre-stated tolerance (r ≥ 0.90 and mean |diff| ≤ 0.05 s) → **FAILED on level**; the shape agrees and the offset is constant (slope 0.998), consistent with a definition difference (NGS clock vs the participation field).
- Muse 2026 QB-side splits are null/blocked (192 rows). League man rate swings .41/.48/.31 over 2023/24/25: a source-vintage swing, flagged to Muse.

## Part B — stability (is the rank a trait?)
Split-half (defense games 1–6 vs 7+), team-season bootstrap 95% CI; year-to-year with league-level season shift removed.
| metric | window | split-half r [CI] | n | year-to-year r |
|---|---|---|---|---|
| man share | 2018–25 | 0.79 [0.74, 0.84] | 256 | 0.53 |
| man share | 2023–25 | 0.78 [0.70, 0.85] | 96 | 0.46 |
| pressure rate | 2018–25 | 0.31 [0.20, 0.42] | 256 | 0.32 |
| pressure rate | 2023–25 | 0.38 [0.20, 0.54] | 96 | 0.47 |
| 5+ rusher rate | 2018–25 | 0.64 [0.57, 0.71] | 256 | 0.55 |
| 5+ rusher rate | 2023–25 | 0.57 [0.42, 0.70] | 96 | 0.62 |
All three pass the pre-stated gate (CI lower bound > 0): TRAIT. Man share and blitz rate are strong traits at six games; pressure rate is a weaker trait (r ≈ 0.3–0.4).

## Part B — cross and application (frozen model untouched)
Held-out QB-games per the frozen model's split (gameday ≥ 2024-01-01; includes 33 Week-18 games of the 2023 season): n = 1,060 QB-games, 559 games, 2023-season rows 33. Frozen passyds_strike_v1 sha256 1053c843… verified before use.
d_man = defense man-share deviation × QB (EPA vs man − vs zone) deviation; d_press = defense pressure deviation × QB (pressured − clean EPA) deviation. Point-in-time, 3-season look-back, fixed pseudo-counts K_DEF 300 / K_QB 150 (stated before computing).
| cross | sd(d) | slope on frozen-model residual (yards per sd of d) | 95% CI (game-cluster bootstrap) |
|---|---|---|---|
| d_man | 0.0046 | −2.6 | [−7.2, +1.5] |
| d_press | 0.0021 | −0.3 | [−4.1, +3.7] |
Neither is supported; CIs span zero and are small against a QB-game residual sd of roughly 80 yards. **No measurable gain beyond the frozen model; the design can rule out effects larger than about 4–7 yards per sd, not smaller ones.**

## Market map and application to price
KXNFLPASSYDS (T1 pre-game strike ladder) is the family a passing-yards shift would move; other consumers are KXNFLTEAMTOTAL, KXNFLSPREAD and KXNFLTOTAL via team passing. No market prices were joined here: the test is against the frozen model residual, not against a Kalshi price, so the stage is **interpreted**, not applied.

## Stage by factor
- Defensive man/zone tendency × QB response: aggregated → interpreted (trait confirmed; no gain vs frozen model).
- Pressure/blitz tendency × QB response: aggregated → interpreted (same).
- Muse's coverage/pressure facts: REPORTED, ungradeable (null priors).
