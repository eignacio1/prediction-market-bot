# W98.1 Part C: v3 availability and lineups, indexed (rank vs history, matchup cross)

EXPLORATORY, not a verdict. Code: `study_partc_w98.py` (known-answer tests: `tests/test_w98_1_nba_index_factors.py`). Numbers: `study_partc_w98_out.json`, `study_partc_w98_out_vs_v3all.json`, `study_partc_w98_out_rows.csv.gz`.

## What was built (all known before tip)
- **Rank vs history:** a team's expected-missing share and lineup-net as a percentile among *prior seasons'* team-games at the same point in the season (position within season +-5%, at least 30 comparison rows, else missing). Home minus away and home plus away. Seasons with no prior history get no rank.
- **Matchup cross:** whose missing share meets which opponent: `h_exp_missing x a_lineup_net` and `a_exp_missing x h_lineup_net`, difference and sum.

## Test
Protocol of `study_v3.py` unchanged (test 2025 and 2026, rolling origin, v2 refit on identical games, paired, game-clustered bootstrap). Each variant is v3's four factors plus the new ones, scored against v3_all (the frozen factor set) on the same games. Baseline reproduces W96.1 (v3_all minus v2_core, ALL, 2025: -0.00252; 2026: -0.00374).

Pooled Brier delta vs v3_all (negative = better), 95% CI:

| family | +rank | +cross | +rank+cross |
|---|---|---|---|
| ml | +0.00007 [-0.00008, 0.00021] | +0.00044 [-0.00013, 0.00099] | +0.00047 [-0.00010, 0.00105] |
| spread | +0.00003 [-0.00008, 0.00015] | +0.00021 [-0.00023, 0.00064] | +0.00023 [-0.00022, 0.00067] |
| team_total | +0.00018 [-0.00019, 0.00053] | +0.00007 [-0.00010, 0.00024] | +0.00026 [-0.00016, 0.00063] |
| total | +0.00044 [-0.00022, 0.00102] | +0.00005 [-0.00007, 0.00018] | +0.00053 [-0.00015, 0.00112] |
| ALL | +0.00020 [-0.00012, 0.00049] | +0.00012 [-0.00008, 0.00032] | +0.00032 [-0.00007, 0.00069] |

## Verdict
**Neither index part changes v3's held-out Brier.** Every interval includes zero and every point estimate leans slightly worse. v3 is unchanged; nothing is added to the frozen set. Rank and cross are carried as index parts (written, measured, no lift), not as pricing inputs. Not claimed: that the effects do not exist at finer grain (two test seasons, a single crude cross, injury reports only from 2022-23).

When it applies: pre-tip pricing of spread and team-total lines where an injury report exists (v3's own scope); the new parts add nothing there.

## Five parts, now complete for both factors
| part | availability | lineups |
|---|---|---|
| split | home-away and home+away expected missing share | home-away and home+away rotation-weighted net |
| rank vs history | percentile at the same season point, prior seasons: built, no lift | same |
| matchup cross | missing share x opponent lineup-net: built, no lift | same |
| market map | spread and team total move; moneyline and total do not | same |
| application | held-out Brier gain over v2 (W96.1); no forward arm until v3 is installed | same |

## Stage per factor (ADR-0075)
Availability: interpreted (tested path to a price, measured). Lineups: interpreted. Applied only once forward rows log (v3 install pending). The count of factors with all five parts: 0 -> 2.
