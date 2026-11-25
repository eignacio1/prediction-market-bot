# EXP-NFLPLAYLEVEL-001 — result: NFL play-level crosses as tree splits

**Last reviewed:** 2026-11-24 (W128.3). Source: `run_playlevel.py` -> `results.json`; `make_result.py` -> this file. PREREG.md committed first (7e4ceee).
**Proxy prices** (board_v2 anchored to consensus, earlier seasons only), not tradable quotes. Half-spread at archive medians; mean-cost net in results.json.

## Headline
- 118 cross x market x leaf x band x arm rows; **74 judged** on 2025 (>= 40 games); 44 not judged for n.
- Fit-routed rows (shrunk 90% lower bound > 0 on fit seasons): **0**. BH family: **0**. Arms earned: **0**. Every judged leaf routed to ride / no bet.
- Raw 2025 net > 0 in 14 of 74 judged rows; none with a 90% interval above 0. Best: x1_personnel_shell TT hi_lo wing FADE net +0.075 (interval -0.013 to +0.162, n 67 games).
- 2026 REG to date (descriptive, personnel / coverage **carried** from 2025, no participation feed): 48 rows reach n >= 40 games; no BH, never pooled with 2025.
- Verdict: **ride / no bet in every judged leaf. Hypothesis closed (EXP-NFLPLAYLEVEL-001, parked for R&D).** No cell, market or arm closes.

## Cut points fixed on the fit seasons (offense median, defense median)

- x1_personnel_shell: 0.6476 / 0.3896
- x2_motion_man: 0.4262 / 0.4074
- x3_success_shell: 0.0751 / 0.3896

Fit seasons {"x1_personnel_shell": [2020, 2024], "x2_motion_man": [2023, 2024], "x3_success_shell": [2020, 2024]}. Judge: 2025 REG. Look 2: 2026 REG to date (descriptive, carried personnel/coverage).

## Per cross x market x leaf x band x arm

| cross | mkt | leaf | band | arm | fit route | fit lo | 2025 n | gross | cost | net | 90% lo | 90% hi | 2026 n | 2026 net | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| x1 | AS | away_only | mid | FADE | NO BET | -0.046 | 57 | -0.051 | +0.021 | -0.072 | -0.113 | -0.031 | 38 |  | routed to ride / no bet in this leaf |
| x1 | AS | away_only | mid | RIDE | NO BET | -0.013 | 57 | +0.051 | +0.021 | +0.030 | -0.011 | +0.071 | 38 |  | routed to ride / no bet in this leaf |
| x1 | AS | away_only | wing | FADE | NO BET | -0.046 | 22 |  |  |  |  |  | 19 |  | not judged: n below MIN_N (n=22) |
| x1 | AS | away_only | wing | RIDE | NO BET | -0.013 | 22 |  |  |  |  |  | 19 |  | not judged: n below MIN_N (n=22) |
| x1 | AS | home_only | mid | FADE | NO BET | -0.046 | 63 | +0.015 | +0.021 | -0.006 | -0.045 | +0.034 | 40 | -0.052 | routed to ride / no bet in this leaf |
| x1 | AS | home_only | mid | RIDE | NO BET | -0.013 | 63 | -0.015 | +0.021 | -0.037 | -0.076 | +0.003 | 40 | +0.010 | routed to ride / no bet in this leaf |
| x1 | AS | home_only | wing | FADE | NO BET | -0.046 | 21 |  |  |  |  |  | 15 |  | not judged: n below MIN_N (n=21) |
| x1 | AS | home_only | wing | RIDE | NO BET | -0.013 | 21 |  |  |  |  |  | 15 |  | not judged: n below MIN_N (n=21) |
| x1 | AS | neither_or_both | mid | FADE | NO BET | -0.046 | 152 | +0.019 | +0.021 | -0.002 | -0.027 | +0.023 | 85 | -0.028 | routed to ride / no bet in this leaf |
| x1 | AS | neither_or_both | mid | RIDE | NO BET | -0.013 | 152 | -0.019 | +0.021 | -0.041 | -0.065 | -0.016 | 85 | -0.014 | routed to ride / no bet in this leaf |
| x1 | AS | neither_or_both | wing | FADE | NO BET | -0.046 | 64 | +0.034 | +0.018 | +0.017 | -0.075 | +0.108 | 44 | -0.047 | routed to ride / no bet in this leaf |
| x1 | AS | neither_or_both | wing | RIDE | NO BET | -0.013 | 64 | -0.034 | +0.017 | -0.052 | -0.143 | +0.040 | 44 | +0.012 | routed to ride / no bet in this leaf |
| x1 | AT | both | mid | FADE | NO BET | -0.045 | 27 |  |  |  |  |  | 20 |  | not judged: n below MIN_N (n=27) |
| x1 | AT | both | mid | RIDE | NO BET | -0.024 | 27 |  |  |  |  |  | 20 |  | not judged: n below MIN_N (n=27) |
| x1 | AT | both | wing | FADE | NO BET |  | 0 |  |  |  |  |  | 1 |  | not judged: n below MIN_N (n=0) |
| x1 | AT | both | wing | RIDE | NO BET |  | 0 |  |  |  |  |  | 1 |  | not judged: n below MIN_N (n=0) |
| x1 | AT | none | mid | FADE | NO BET | -0.045 | 125 | -0.008 | +0.026 | -0.034 | -0.061 | -0.007 | 65 | -0.065 | routed to ride / no bet in this leaf |
| x1 | AT | none | mid | RIDE | NO BET | -0.024 | 125 | +0.008 | +0.026 | -0.018 | -0.045 | +0.009 | 65 | +0.013 | routed to ride / no bet in this leaf |
| x1 | AT | none | wing | FADE | NO BET |  | 1 |  |  |  |  |  | 1 |  | not judged: n below MIN_N (n=1) |
| x1 | AT | none | wing | RIDE | NO BET |  | 1 |  |  |  |  |  | 1 |  | not judged: n below MIN_N (n=1) |
| x1 | AT | one | mid | FADE | NO BET | -0.045 | 120 | -0.004 | +0.026 | -0.030 | -0.057 | -0.003 | 78 | -0.021 | routed to ride / no bet in this leaf |
| x1 | AT | one | mid | RIDE | NO BET | -0.024 | 120 | +0.004 | +0.026 | -0.022 | -0.049 | +0.005 | 78 | -0.031 | routed to ride / no bet in this leaf |
| x1 | AT | one | wing | FADE | NO BET |  | 0 |  |  |  |  |  | 1 |  | not judged: n below MIN_N (n=0) |
| x1 | AT | one | wing | RIDE | NO BET |  | 0 |  |  |  |  |  | 1 |  | not judged: n below MIN_N (n=0) |
| x1 | TT | hi_hi | mid | FADE | NO BET | -0.048 | 147 | +0.011 | +0.031 | -0.020 | -0.044 | +0.004 | 98 | -0.003 | routed to ride / no bet in this leaf |
| x1 | TT | hi_hi | mid | RIDE | NO BET | -0.033 | 147 | -0.011 | +0.031 | -0.042 | -0.066 | -0.017 | 98 | -0.059 | routed to ride / no bet in this leaf |
| x1 | TT | hi_hi | wing | FADE | NO BET | -0.047 | 85 | -0.013 | +0.028 | -0.041 | -0.115 | +0.033 | 50 | -0.066 | routed to ride / no bet in this leaf |
| x1 | TT | hi_hi | wing | RIDE | NO BET | -0.042 | 85 | +0.013 | +0.027 | -0.014 | -0.088 | +0.060 | 50 | +0.011 | routed to ride / no bet in this leaf |
| x1 | TT | hi_lo | mid | FADE | NO BET | -0.040 | 107 | -0.002 | +0.031 | -0.034 | -0.064 | -0.003 | 34 |  | routed to ride / no bet in this leaf |
| x1 | TT | hi_lo | mid | RIDE | NO BET | -0.040 | 107 | +0.002 | +0.031 | -0.028 | -0.059 | +0.003 | 34 |  | routed to ride / no bet in this leaf |
| x1 | TT | hi_lo | wing | FADE | NO BET | -0.049 | 67 | +0.103 | +0.028 | +0.075 | -0.013 | +0.162 | 24 |  | routed to ride / no bet in this leaf |
| x1 | TT | hi_lo | wing | RIDE | NO BET | -0.040 | 67 | -0.103 | +0.027 | -0.129 | -0.217 | -0.042 | 24 |  | routed to ride / no bet in this leaf |
| x1 | TT | lo_hi | mid | FADE | NO BET | -0.049 | 135 | -0.009 | +0.031 | -0.040 | -0.065 | -0.015 | 111 | -0.035 | routed to ride / no bet in this leaf |
| x1 | TT | lo_hi | mid | RIDE | NO BET | -0.032 | 135 | +0.009 | +0.031 | -0.022 | -0.047 | +0.003 | 111 | -0.027 | routed to ride / no bet in this leaf |
| x1 | TT | lo_hi | wing | FADE | NO BET | -0.056 | 84 | -0.047 | +0.028 | -0.076 | -0.142 | -0.009 | 74 | -0.036 | routed to ride / no bet in this leaf |
| x1 | TT | lo_hi | wing | RIDE | NO BET | -0.030 | 84 | +0.047 | +0.027 | +0.021 | -0.046 | +0.087 | 74 | -0.018 | routed to ride / no bet in this leaf |
| x1 | TT | lo_lo | mid | FADE | NO BET | -0.041 | 92 | +0.003 | +0.031 | -0.028 | -0.057 | +0.001 | 35 |  | routed to ride / no bet in this leaf |
| x1 | TT | lo_lo | mid | RIDE | NO BET | -0.040 | 92 | -0.003 | +0.031 | -0.034 | -0.063 | -0.004 | 35 |  | routed to ride / no bet in this leaf |
| x1 | TT | lo_lo | wing | FADE | NO BET | -0.048 | 49 | -0.047 | +0.028 | -0.075 | -0.163 | +0.013 | 19 |  | routed to ride / no bet in this leaf |
| x1 | TT | lo_lo | wing | RIDE | NO BET | -0.041 | 49 | +0.047 | +0.027 | +0.020 | -0.068 | +0.109 | 19 |  | routed to ride / no bet in this leaf |
| x2 | AS | away_only | mid | FADE | NO BET | -0.072 | 68 | +0.049 | +0.021 | +0.028 | -0.006 | +0.062 | 26 |  | routed to ride / no bet in this leaf |
| x2 | AS | away_only | mid | RIDE | NO BET | -0.031 | 68 | -0.049 | +0.021 | -0.070 | -0.104 | -0.036 | 26 |  | routed to ride / no bet in this leaf |
| x2 | AS | away_only | wing | FADE | NO BET | -0.070 | 27 |  |  |  |  |  | 10 |  | not judged: n below MIN_N (n=27) |
| x2 | AS | away_only | wing | RIDE | NO BET | -0.087 | 27 |  |  |  |  |  | 10 |  | not judged: n below MIN_N (n=27) |
| x2 | AS | home_only | mid | FADE | NO BET | -0.038 | 73 | +0.011 | +0.021 | -0.010 | -0.046 | +0.026 | 22 |  | routed to ride / no bet in this leaf |
| x2 | AS | home_only | mid | RIDE | NO BET | -0.062 | 73 | -0.011 | +0.021 | -0.032 | -0.068 | +0.004 | 22 |  | routed to ride / no bet in this leaf |
| x2 | AS | home_only | wing | FADE | NO BET | -0.108 | 31 |  |  |  |  |  | 13 |  | not judged: n below MIN_N (n=31) |
| x2 | AS | home_only | wing | RIDE | NO BET | -0.038 | 31 |  |  |  |  |  | 13 |  | not judged: n below MIN_N (n=31) |
| x2 | AS | neither_or_both | mid | FADE | NO BET | -0.073 | 131 | -0.024 | +0.021 | -0.045 | -0.073 | -0.017 | 115 | -0.031 | routed to ride / no bet in this leaf |
| x2 | AS | neither_or_both | mid | RIDE | NO BET | -0.005 | 131 | +0.024 | +0.021 | +0.003 | -0.025 | +0.030 | 115 | -0.012 | routed to ride / no bet in this leaf |
| x2 | AS | neither_or_both | wing | FADE | NO BET | -0.099 | 49 | -0.025 | +0.018 | -0.042 | -0.138 | +0.054 | 55 | +0.001 | routed to ride / no bet in this leaf |
| x2 | AS | neither_or_both | wing | RIDE | NO BET | -0.023 | 49 | +0.025 | +0.017 | +0.008 | -0.088 | +0.103 | 55 | -0.037 | routed to ride / no bet in this leaf |
| x2 | AT | both | mid | FADE | NO BET | -0.051 | 39 |  |  |  |  |  | 1 |  | not judged: n below MIN_N (n=39) |
| x2 | AT | both | mid | RIDE | NO BET | -0.028 | 39 |  |  |  |  |  | 1 |  | not judged: n below MIN_N (n=39) |
| x2 | AT | both | wing | FADE | NO BET |  | 1 |  |  |  |  |  | 0 |  | not judged: n below MIN_N (n=1) |
| x2 | AT | both | wing | RIDE | NO BET |  | 1 |  |  |  |  |  | 0 |  | not judged: n below MIN_N (n=1) |
| x2 | AT | none | mid | FADE | NO BET | -0.051 | 92 | +0.007 | +0.026 | -0.019 | -0.050 | +0.012 | 114 | -0.025 | routed to ride / no bet in this leaf |
| x2 | AT | none | mid | RIDE | NO BET | -0.028 | 92 | -0.007 | +0.026 | -0.033 | -0.065 | -0.002 | 114 | -0.027 | routed to ride / no bet in this leaf |
| x2 | AT | none | wing | FADE | NO BET |  | 0 |  |  |  |  |  | 3 |  | not judged: n below MIN_N (n=0) |
| x2 | AT | none | wing | RIDE | NO BET |  | 0 |  |  |  |  |  | 3 |  | not judged: n below MIN_N (n=0) |
| x2 | AT | one | mid | FADE | NO BET | -0.051 | 141 | -0.021 | +0.026 | -0.047 | -0.072 | -0.022 | 48 | -0.065 | routed to ride / no bet in this leaf |
| x2 | AT | one | mid | RIDE | NO BET | -0.028 | 141 | +0.021 | +0.026 | -0.005 | -0.031 | +0.020 | 48 | +0.012 | routed to ride / no bet in this leaf |
| x2 | AT | one | wing | FADE | NO BET |  | 0 |  |  |  |  |  | 0 |  | not judged: n below MIN_N (n=0) |
| x2 | AT | one | wing | RIDE | NO BET |  | 0 |  |  |  |  |  | 0 |  | not judged: n below MIN_N (n=0) |
| x2 | TT | hi_hi | mid | FADE | NO BET | -0.049 | 180 | +0.011 | +0.031 | -0.020 | -0.041 | +0.001 | 49 | -0.033 | routed to ride / no bet in this leaf |
| x2 | TT | hi_hi | mid | RIDE | NO BET | -0.031 | 180 | -0.011 | +0.031 | -0.042 | -0.063 | -0.021 | 49 | -0.029 | routed to ride / no bet in this leaf |
| x2 | TT | hi_hi | wing | FADE | NO BET | -0.049 | 109 | -0.001 | +0.028 | -0.029 | -0.090 | +0.032 | 31 |  | routed to ride / no bet in this leaf |
| x2 | TT | hi_hi | wing | RIDE | NO BET | -0.031 | 109 | +0.001 | +0.027 | -0.026 | -0.087 | +0.035 | 31 |  | routed to ride / no bet in this leaf |
| x2 | TT | hi_lo | mid | FADE | NO BET | -0.049 | 170 | -0.005 | +0.031 | -0.036 | -0.057 | -0.015 | 162 | -0.028 | routed to ride / no bet in this leaf |
| x2 | TT | hi_lo | mid | RIDE | NO BET | -0.031 | 170 | +0.005 | +0.031 | -0.026 | -0.047 | -0.005 | 162 | -0.033 | routed to ride / no bet in this leaf |
| x2 | TT | hi_lo | wing | FADE | NO BET | -0.049 | 103 | +0.001 | +0.028 | -0.027 | -0.089 | +0.034 | 118 | -0.023 | routed to ride / no bet in this leaf |
| x2 | TT | hi_lo | wing | RIDE | NO BET | -0.031 | 103 | -0.001 | +0.027 | -0.027 | -0.089 | +0.034 | 118 | -0.032 | routed to ride / no bet in this leaf |
| x2 | TT | lo_hi | mid | FADE | NO BET | -0.049 | 47 | -0.005 | +0.031 | -0.036 | -0.085 | +0.014 | 0 |  | routed to ride / no bet in this leaf |
| x2 | TT | lo_hi | mid | RIDE | NO BET | -0.031 | 47 | +0.005 | +0.031 | -0.026 | -0.076 | +0.023 | 0 |  | routed to ride / no bet in this leaf |
| x2 | TT | lo_hi | wing | FADE | NO BET | -0.049 | 31 |  |  |  |  |  | 0 |  | not judged: n below MIN_N (n=31) |
| x2 | TT | lo_hi | wing | RIDE | NO BET | -0.031 | 31 |  |  |  |  |  | 0 |  | not judged: n below MIN_N (n=31) |
| x2 | TT | lo_lo | mid | FADE | NO BET | -0.049 | 39 |  |  |  |  |  | 6 |  | not judged: n below MIN_N (n=39) |
| x2 | TT | lo_lo | mid | RIDE | NO BET | -0.031 | 39 |  |  |  |  |  | 6 |  | not judged: n below MIN_N (n=39) |
| x2 | TT | lo_lo | wing | FADE | NO BET | -0.049 | 28 |  |  |  |  |  | 5 |  | not judged: n below MIN_N (n=28) |
| x2 | TT | lo_lo | wing | RIDE | NO BET | -0.031 | 28 |  |  |  |  |  | 5 |  | not judged: n below MIN_N (n=28) |
| x3 | AS | away_only | mid | FADE | NO BET | -0.046 | 47 | -0.040 | +0.021 | -0.061 | -0.106 | -0.017 | 21 |  | routed to ride / no bet in this leaf |
| x3 | AS | away_only | mid | RIDE | NO BET | -0.013 | 47 | +0.040 | +0.021 | +0.019 | -0.026 | +0.063 | 21 |  | routed to ride / no bet in this leaf |
| x3 | AS | away_only | wing | FADE | NO BET | -0.046 | 26 |  |  |  |  |  | 12 |  | not judged: n below MIN_N (n=26) |
| x3 | AS | away_only | wing | RIDE | NO BET | -0.013 | 26 |  |  |  |  |  | 12 |  | not judged: n below MIN_N (n=26) |
| x3 | AS | home_only | mid | FADE | NO BET | -0.046 | 40 | -0.065 | +0.021 | -0.086 | -0.142 | -0.030 | 23 |  | routed to ride / no bet in this leaf |
| x3 | AS | home_only | mid | RIDE | NO BET | -0.013 | 40 | +0.065 | +0.021 | +0.044 | -0.012 | +0.100 | 23 |  | routed to ride / no bet in this leaf |
| x3 | AS | home_only | wing | FADE | NO BET | -0.046 | 10 |  |  |  |  |  | 8 |  | not judged: n below MIN_N (n=10) |
| x3 | AS | home_only | wing | RIDE | NO BET | -0.013 | 10 |  |  |  |  |  | 8 |  | not judged: n below MIN_N (n=10) |
| x3 | AS | neither_or_both | mid | FADE | NO BET | -0.046 | 185 | +0.030 | +0.021 | +0.009 | -0.013 | +0.030 | 119 | -0.048 | routed to ride / no bet in this leaf |
| x3 | AS | neither_or_both | mid | RIDE | NO BET | -0.013 | 185 | -0.030 | +0.021 | -0.051 | -0.072 | -0.029 | 119 | +0.006 | routed to ride / no bet in this leaf |
| x3 | AS | neither_or_both | wing | FADE | NO BET | -0.046 | 71 | -0.020 | +0.018 | -0.037 | -0.118 | +0.044 | 58 | -0.030 | routed to ride / no bet in this leaf |
| x3 | AS | neither_or_both | wing | RIDE | NO BET | -0.013 | 71 | +0.020 | +0.017 | +0.002 | -0.078 | +0.083 | 58 | -0.005 | routed to ride / no bet in this leaf |
| x3 | AT | both | mid | FADE | NO BET | -0.064 | 7 |  |  |  |  |  | 11 |  | not judged: n below MIN_N (n=7) |
| x3 | AT | both | mid | RIDE | NO BET | -0.026 | 7 |  |  |  |  |  | 11 |  | not judged: n below MIN_N (n=7) |
| x3 | AT | none | mid | FADE | NO BET | -0.049 | 178 | -0.019 | +0.026 | -0.045 | -0.069 | -0.022 | 108 | -0.041 | routed to ride / no bet in this leaf |
| x3 | AT | none | mid | RIDE | NO BET | -0.024 | 178 | +0.019 | +0.026 | -0.007 | -0.031 | +0.016 | 108 | -0.011 | routed to ride / no bet in this leaf |
| x3 | AT | none | wing | FADE | NO BET |  | 0 |  |  |  |  |  | 2 |  | not judged: n below MIN_N (n=0) |
| x3 | AT | none | wing | RIDE | NO BET |  | 0 |  |  |  |  |  | 2 |  | not judged: n below MIN_N (n=0) |
| x3 | AT | one | mid | FADE | NO BET | -0.044 | 87 | +0.015 | +0.026 | -0.011 | -0.042 | +0.019 | 44 | -0.035 | routed to ride / no bet in this leaf |
| x3 | AT | one | mid | RIDE | NO BET | -0.033 | 87 | -0.015 | +0.026 | -0.041 | -0.072 | -0.010 | 44 | -0.017 | routed to ride / no bet in this leaf |
| x3 | AT | one | wing | FADE | NO BET |  | 1 |  |  |  |  |  | 1 |  | not judged: n below MIN_N (n=1) |
| x3 | AT | one | wing | RIDE | NO BET |  | 1 |  |  |  |  |  | 1 |  | not judged: n below MIN_N (n=1) |
| x3 | TT | hi_hi | mid | FADE | NO BET | -0.042 | 94 | +0.016 | +0.031 | -0.015 | -0.048 | +0.017 | 55 | -0.013 | routed to ride / no bet in this leaf |
| x3 | TT | hi_hi | mid | RIDE | NO BET | -0.038 | 94 | -0.016 | +0.031 | -0.046 | -0.079 | -0.014 | 55 | -0.049 | routed to ride / no bet in this leaf |
| x3 | TT | hi_hi | wing | FADE | NO BET | -0.047 | 39 |  |  |  |  |  | 29 |  | not judged: n below MIN_N (n=39) |
| x3 | TT | hi_hi | wing | RIDE | NO BET | -0.039 | 39 |  |  |  |  |  | 29 |  | not judged: n below MIN_N (n=39) |
| x3 | TT | hi_lo | mid | FADE | NO BET | -0.039 | 73 | +0.007 | +0.031 | -0.024 | -0.059 | +0.010 | 14 |  | routed to ride / no bet in this leaf |
| x3 | TT | hi_lo | mid | RIDE | NO BET | -0.041 | 73 | -0.007 | +0.031 | -0.037 | -0.072 | -0.003 | 14 |  | routed to ride / no bet in this leaf |
| x3 | TT | hi_lo | wing | FADE | NO BET | -0.048 | 31 |  |  |  |  |  | 5 |  | not judged: n below MIN_N (n=31) |
| x3 | TT | hi_lo | wing | RIDE | NO BET | -0.038 | 31 |  |  |  |  |  | 5 |  | not judged: n below MIN_N (n=31) |
| x3 | TT | lo_hi | mid | FADE | NO BET | -0.052 | 167 | -0.005 | +0.031 | -0.036 | -0.056 | -0.015 | 146 | -0.022 | routed to ride / no bet in this leaf |
| x3 | TT | lo_hi | mid | RIDE | NO BET | -0.027 | 167 | +0.005 | +0.031 | -0.026 | -0.047 | -0.005 | 146 | -0.039 | routed to ride / no bet in this leaf |
| x3 | TT | lo_hi | wing | FADE | NO BET | -0.050 | 119 | -0.068 | +0.028 | -0.096 | -0.147 | -0.044 | 95 | -0.060 | routed to ride / no bet in this leaf |
| x3 | TT | lo_hi | wing | RIDE | NO BET | -0.035 | 119 | +0.068 | +0.027 | +0.041 | -0.011 | +0.092 | 95 | +0.005 | routed to ride / no bet in this leaf |
| x3 | TT | lo_lo | mid | FADE | NO BET | -0.042 | 129 | -0.004 | +0.031 | -0.035 | -0.061 | -0.008 | 51 | -0.029 | routed to ride / no bet in this leaf |
| x3 | TT | lo_lo | mid | RIDE | NO BET | -0.038 | 129 | +0.004 | +0.031 | -0.027 | -0.054 | -0.000 | 51 | -0.033 | routed to ride / no bet in this leaf |
| x3 | TT | lo_lo | wing | FADE | NO BET | -0.046 | 85 | +0.044 | +0.028 | +0.016 | -0.059 | +0.091 | 36 |  | routed to ride / no bet in this leaf |
| x3 | TT | lo_lo | wing | RIDE | NO BET | -0.041 | 85 | -0.044 | +0.027 | -0.070 | -0.145 | +0.004 | 36 |  | routed to ride / no bet in this leaf |

## Judged leaves per cross (stage evidence)

- x1_personnel_shell: 28 judged rows
- x2_motion_man: 22 judged rows
- x3_success_shell: 24 judged rows
