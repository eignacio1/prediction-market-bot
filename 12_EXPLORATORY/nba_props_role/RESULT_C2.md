# RESULT — EXP-047-C2 (W126.2), retrospective on season 2023-24

**Last reviewed:** 2026-11-24. Run exactly as PREREG_C2.md (frozen at fc4e596). Fit: 2022-23 only (`FIT_C2.json`, frozen into the forecaster
at the commit before this was scored). Judged: 2023-24 regular season, never scored for props before. Source: `RESULT_C2.json`, `run_c2.py`.

**Verdict (pre-registered rule): SUPPORTED.** All four stats improve on EXP-047's plain average, BH-significant, none worse.
899 games, 163,894 player-ladder rows (points/rebounds/assists 43,130 each, threes 34,504); 43 of 1,230 games had no pre-tip report; 7,804 rows dropped (DNP after active) from all arms.

| Stat | lambda (fit) | log-loss diff vs EXP-047 [95% game-clustered] | vs C1 [95%] | Brier diff |
|---|---|---|---|---|
| points | 1 (C1 rule) | -0.0264 [-0.0312, -0.0216] | 0 (same rule) | -0.0079 |
| rebounds | 0.26 [0.23, 0.29] | -0.00097 [-0.00194, -0.000002] | -0.0159 [-0.0186, -0.0133] | -0.0005 |
| assists | 0.31 [0.28, 0.34] | -0.0041 [-0.0051, -0.0032] | -0.0067 [-0.0087, -0.0048] | -0.0016 |
| threes (3PA basis) | 0.27 [0.24, 0.31] | -0.0028 [-0.0037, -0.0020] | -0.0035 [-0.0053, -0.0017] | -0.0011 |

**Read plainly.**
- Points replicates C1 on a new season (-0.026 vs -0.027). Same rule, so identical by construction.
- The fitted fractions are low (about 0.26-0.31, intervals narrow): a missing player's rebounds, assists and threes are only about a quarter to a third absorbed by teammates; C1's full absorption was the error on those three stats. That is why C1 was worse and C2 is better.
- **Rebounds is thin against EXP-047**: the interval's upper edge is -0.000002 (p 0.0498), it clears BH only barely, and the V buckets are all indeterminate. The gain over C1 is solid; the gain over the plain average is not. Assists and threes are clear at every V.
- Gain grows with V (points V>=0.25: -0.066; assists -0.014; threes -0.007), as it should if the signal is the missing player.
- Open limits (PREREG_C2 section 8): pre-tip Out only, no position/role, one fit season, log-loss on a fixed ladder is calibration, not a price edge. Gross / round cost / net per arm is forward-only: no prices exist for 2023-24.

## Forward look schedule
Judged by the router per leaf on net after costs per arm (ADR-0077) once rows are logged. Logging needs the window to switch `PM_PROPS_C2` on (proposal in ACTIVE_QUEUE).
Per-leaf n and the date reached come from the router's power calendar after the first logged rows, not from this file; none is read here. Until then C2 is a candidate input, not a price.
