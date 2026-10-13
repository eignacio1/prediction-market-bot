# SESSION_HANDOFF — W71.3 NBA game markets: availability challenger

```
vision_pillar: DEPTH
gap_measure: D1 (NBA games: team -> team + personnel), D3
gap_delta: none — D1 team-only -> team-only (challenger earned NO); D3 +0 (no pre-registration earned). Source: 12_EXPLORATORY/20261013_nba_games_availability/results.md
```

**Status: DONE (result NO).** Branch `session/20261013T233401Z-w71-3-nba-availability`.

- Part A: 2025-26 injury coverage 33.9% -> 96.4% across the GG-620 rename (`fetch_injury_v2.py`, `coverage.json`); plan frozen in `README.md` before any fit.
- Part B: fit once. Integrity exact (fold A control Brier 0.2110515179 = frozen artifact). First run was invalid (bug: 2015 in train), disclosed, kept as `results_run1_INVALID_2015_in_train.json`, fixed, re-run; both runs NO.
- Pooled ΔBrier (98.33% CI): moneyline −0.00165 [−0.00377, +0.00056]; spread −0.00181 [−0.00389, +0.00024]; total −0.00017 [−0.00116, +0.00084]. None beat frozen. Fold-B spread alone excludes zero — reported, not acted on per the pre-set rule.
- No market comparison (no NBA Kalshi history).

**Operator decisions:** none. (No PROPOSED pre-registration.)
**Open items, not done in scope:** GG-620 status text not edited (shared log; fix is verified working for 2026, a note is due); a re-test needs 2026-27 in-season personnel data and a new dated pre-registration.
