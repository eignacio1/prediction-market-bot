# W64.1 — NFL deep challenger: QB-shrunk performance (EXPLORATORY)

Status: PART A + PART B DONE. Label: EXPLORATORY. No sizing change.

## Part A
- Step 0 (read-only): VPS checkout (e3353ad4, ancestor of main) now has `12_EXPLORATORY/NFL_FIRST_LOOK_EXPECTATIONS.md` and `NFL_TRANSLATION_MAP.md`. 63.3's UNAVAILABLE was a deploy-timing artifact; no gap registered.
- Plan frozen BEFORE fitting: `12_EXPLORATORY/20261009_nfl_qb_challenger/README.md` (M1 QB-shrunk EPA k=6, M2 EB-shrunk team rates K=2, M3 excluded: injury `date_modified` not in cache; m=8, alpha=0.00625, seed 20261009, B=2000).
- Features: `qb_features.py`; tests: `test_qb_features.py` (6 pass; K=0 reproduces the frozen builder on 2723 rows, 0 mismatches; poisoned-future and same-day rows never leak).
- Isolation tests + new tests: 24 passed.

## Part B — result (EXPLORATORY, scoped to this feature set and 2019-2025)
Rolling origin 2019-2025 (n=1852); frozen arm reproduces W61.3's 2025 Brier: 0.2185 (check passed).

| Arm | Brier | vs frozen (mean, 99.375% CI) | seasons better |
|---|---|---|---|
| frozen | 0.2260 | - | - |
| **full** (challenger) | 0.2233 | -0.0027 [-0.0050, -0.0006] | 6/7 |
| qb_only | 0.2233 | -0.0027 [-0.0050, -0.0005] | 6/7 |
| eb_only | 0.2260 | -0.00001 (CI spans 0) | 2/7 |
| full_oracle (flagged upper bound) | 0.2215 | -0.0045 | 6/7 |

- **Pre-registered rule met:** upper CI limit < 0 and 6/7 seasons better -> `full` beats the frozen model in backtest. The whole gain is mechanism 1 (QB); mechanism 2 (EB) does nothing (delta ~1e-5).
- **Caveats, stated plainly:** (1) 2025, the frozen model's held-out season, is the one season where the challenger is WORSE (+0.0038). (2) On the 182 2025 games with a Kalshi mid, Brier: mid 0.2115, frozen 0.2182, challenger 0.2221; challenger minus frozen +0.0039 (95% CI -0.0031..+0.0115); neither model beats the mid. (3) Gain is concentrated in weeks 1-4 and, via the oracle arm, in games where the starter changed; the QB-changed subset alone is not significant.
- **Effect size:** -0.0027 Brier vs frozen is a calibration improvement, not market edge. Judged live n ~984 games (~3.6 seasons).
- **Draft pre-registration:** `NFL_QB_SHRUNK_CHALLENGER_PREREGISTRATION_2026-10-09.md` (Status PROPOSED, awaiting operator).
- **Next mechanism if this is rejected or fails live:** injury-report QB-only (mechanism 3), needing a point-in-time snapshot source.
- Added after the plan froze (descriptive only): `per_game_sd` per arm in results.json, used to size n.
