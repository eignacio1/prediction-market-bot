# W130.4 — PIT NBA production profiles and archetype mixtures: what was built and what it shows

**Code:** `pam/nba_pit_profile.py` (profiles), `pam/nba_pit_archetype.py` (mixture), `scripts/pam_pit_archetype_build.py`, `analyze.py`.
**Fit:** training seasons 2022-2025 only (1,609 player-seasons, ≥1,500 possessions); mixture assigned to **2026** at 7 monthly snapshots
(2025-11-01 .. 2026-05-01), games strictly before each date, ≥800 possessions. **2,413 records, 469 players** in `qualitative_data/pam_pit/nba/records.jsonl`
(tier mass, classifier model/"mass", confidence filled, `extra.profile` holds the production profile; the deep-tier file is untouched).

**Known-answer check:** pbp-derived OREB/DREB equal the box score for 97.2% of 2026 player-games (mean abs diff 0.03 per game).
**Not derivable:** contested rebounds (no contest flag), height (opponent size = PRF-9 anchor flag), PRF-10 and PRF-13 (no tracking). They get weight 0.

## Agreement with the 100 deep-tier records (hindsight, descriptive only; no label touched the fit)
92 of 100 records matched a 2026 player. Top-1 agreement 34.8%; deep top archetype present in the PIT mixture 71.7%; mean weight overlap 0.41.
Rows deep top, columns PIT top (record counts; two records per player):
```
deep\PIT  PRF-1 PRF-11 PRF-12 PRF-15 PRF-2 PRF-4 PRF-5 PRF-6 PRF-7 PRF-9
PRF-1       24
PRF-11             2                          2     2
PRF-2       32                                       2     2     2
PRF-3                         2      2                                  2
PRF-6                    4
PRF-7                                                                   2
PRF-8                    2
PRF-9                    2                                        2     6
```
Reading: the 26+44 stars PRF-1/PRF-2 split mostly into PIT PRF-1 (PIT has no way to see the human "non-helio" line); bigs land PRF-9/12/7 as expected.
Weakness named: PRF-4 is over-assigned (100 of 420 players' top) because three-point share dominates its score; scores are fixed a priori and were not tuned to the deep tier.

## Zubac vs Wembanyama (2026, games before 2026-07-01)
| | Zubac | Wembanyama |
|---|---|---|
| DREB / 100 poss | 11.96 | 14.70 |
| OREB / 100 poss | 5.47 | 3.30 |
| OREB share of own team's misses on floor | 11.0% | 6.5% |
| DREB share of opponent misses on floor | 22.2% | 25.3% |
| offensive share of his rebounds | 31% | 18% |
| blocks / 100 poss | 1.37 | 5.08 |
| opponent rim rate while on floor | 26.8% | 25.4% |
| usage / 100 poss | 21.5 | 35.7 |
| rim share of own FGA / three share | 58% / 0% | 38% / 32% |
| **archetype mixture** | **PRF-12 .51, PRF-7 .49** | **PRF-9 1.00** |
Ten rebounds for Zubac come with a third from the offensive glass, at the rim, from a low-usage big; for Wembanyama they come from the defensive glass
beside five blocks and a 36-usage load. Same raw count, different producers.

## Look-ahead tests (`tests/test_pam_pit_archetype.py`)
Game on the as-of day excluded; a poisoned future game does not change an earlier profile (frame-equal); known-answer rates; mixture sums to 1 and
never gives weight to PRF-10/13; fit depends only on the frame passed; store `as_of` returns only the snapshot in force; PAM5 arm keeps S's probability.
