# EXP-039 addendum — frozen artifact record (2026-10-11)

Separate file; the pre-registration (`EXP039_NBA_PLAYER_POINTS_SHADOW_PREREGISTRATION_2026-10-09.md`) is unedited. Nothing here changes a decision rule, look, seed or unit.

| Item | Value |
|---|---|
| Artifact | `models/nba_player_points_v1.json` (force-added; `models/` is gitignored, as for the other frozen artifacts) |
| File sha256 | `20d7d16ac821ff9d11985420fdb92ddbd33fcd1fdf5cef7ed74bcb47a68f2438` |
| Embedded canonical sha256 (verified at every load) | `9eae0460fafa243bd44233e836b934342687faa5a2e15f64d100767188819bfc` |
| Features | 10 quantitative, 0 qualitative (`pts10, pts30, min10, fga10, pts_season, gp_prior, home, rest, b2b, opp_def10`) |
| Training seasons | 2023, 2024 (ending year = 2022-23, 2023-24); n = 45,857 player-games |
| Calibration season | 2025 (2024-25); n = 25,233; NB dispersion r = 2.810 (MLE), Platt a = 1.1287, b = 0.3495 on the logit across stacked strikes 10/15/20/25 |
| Held-out (reported only, never used for a choice) | 2026 (2025-26); n = 25,556 player-games, 1,231 games |
| Mean model | ridge-linear, λ = 100, mean floor 0.5; one NB per player-game, every strike read off it |
| Trained | once; never refit |

Split, λ and structure are exactly as §2 states. No stop condition found: the data allows the pre-registered design.

## Disclosures
- Only four seasons of box scores were pulled (2022-23 … 2025-26), so two seasons train the model, one calibrates.
- The box-score population is every player who appears; the live board is stars-only. The `pts10>=15` subset is the closer proxy and is reported separately.
- Shipped fit = train + calibrate (as D1); held-out is reporting only.

## Held-out (climatology-relative; no market comparison until live rows)
| subset:strike | n | Brier model | Brier climatology | mean p | observed |
|---|---|---|---|---|---|
| all:10 | 25556 | 0.1634 | 0.2500 | 0.478 | 0.494 |
| all:15 | 25556 | 0.1338 | 0.2088 | 0.289 | 0.297 |
| all:20 | 25556 | 0.0914 | 0.1363 | 0.174 | 0.163 |
| all:25 | 25556 | 0.0548 | 0.0743 | 0.105 | 0.081 |
| pts10≥15:10 | 6272 | 0.0952 | 0.2547 | 0.842 | 0.889 |
| pts10≥15:15 | 6272 | 0.1848 | 0.3728 | 0.665 | 0.714 |
| pts10≥15:20 | 6272 | 0.2127 | 0.3442 | 0.484 | 0.483 |
| pts10≥15:25 | 6272 | 0.1701 | 0.2325 | 0.333 | 0.275 |

Known miss: on the star-like subset the model under-predicts strike 10/15 (−4.7/−4.9 pts) and over-predicts strike 25 (+5.8 pts). Reported, not fixed (frozen).
