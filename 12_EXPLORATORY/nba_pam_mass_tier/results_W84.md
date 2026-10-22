# W84.2 — NBA PAM mass tier (layer 3): results

Purpose: DEPTH, D5(b) NBA — PAM player-role factors aggregated, then interpreted (stability). Operator, 2026-10-21: "I'm sure it makes sense why I'm letting Muse architect its database off of the NBA PAM archetype". Stage reached: **aggregated** (all scored factors, 3 seasons) and **interpreted** (split-half and year-over-year stability). **Applied: none.** Part B cross: **not run, n = 0** (see below).

Source of the signals: the NBA event store (`exp_output/NBA_EVENTS/raw/`, regular season, minutes > 0; 1,230 games per season). Thresholds are taxonomy v4, applied as written (`qualitative_data/pam/nba/taxonomy.json`, not edited). Qualifier: ≥15 GP and ≥10 mpg at season end; ≥10 prior GP for the point-in-time table. Statuses: MET (all clauses scored and met), MET_PARTIAL (every scored clause met, at least one clause unscorable from free data), NOT_MET, UNSCORED (no clause scorable). Nothing is proxied.

Premise correction: the prompt's `data/raw/nba/players_2026.json` is the legacy gitignored store; the current store is the NBA event store above. The store has no height, age, years in league, screen assists, charges, catch-and-shoot, contested rebounds or deflections — those clauses are unscored (GG-1061).

## Part A — assignment

Player-seasons assigned: 2024 → 572, 2025 → 569, 2026 → 582 (qualified 410 / 422 / 420). Prior state: 0. Point-in-time 2026: 26,648 player-game rows, 19,499 qualified (`qualitative_data/pam/nba/mass_tier_pit_2026.csv`, strictly-before-game cumulative; test `tests/test_nba_pam_mass_tier.py`). Per-player-season factors, modifiers and signal values: `qualitative_data/pam/nba/mass_tier_season_end.jsonl`. Counts per factor per season: `mass_tier_counts.json`.

Qualified 2026 counts (MET / MET_PARTIAL / NOT_MET / UNSCORED, n=420):

| id | MET | MET_PARTIAL | NOT_MET | UNSCORED |
|---|---|---|---|---|
| PRF-1 | 0 | 23 | 397 | 0 |
| PRF-2 | 0 | 49 | 371 | 0 |
| PRF-3 | 0 | 163 | 257 | 0 |
| PRF-4 | 0 | 199 | 221 | 0 |
| PRF-5 | 79 | 0 | 341 | 0 |
| PRF-6 | 0 | 5 | 133 | 282 |
| PRF-7 | 112 | 65 | 208 | 35 |
| PRF-8 | 0 | 27 | 46 | 347 |
| PRF-9 | 0 | 44 | 376 | 0 |
| PRF-10 | 0 | 0 | 0 | 420 |
| PRF-11 | 0 | 0 | 0 | 420 |
| PRF-12 | 0 | 62 | 358 | 0 |
| PRF-13 | 55 | 0 | 343 | 22 |
| PRF-14 | 0 | 46 | 253 | 121 |
| PRF-15 | 0 | 101 | 319 | 0 |
| M-1 | 0 | 0 | 0 | 420 |
| M-2 | 50 | 0 | 370 | 0 |
| M-3 | 28 | 0 | 392 | 0 |
| M-4 | 0 | 8 | 412 | 0 |
| M-5 | 8 | 0 | 412 | 0 |
| M-6 | 0 | 59 | 361 | 0 |
| M-7 | 0 | 0 | 0 | 420 |
| M-8 | 0 | 0 | 0 | 420 |
| M-9 | 0 | 0 | 0 | 420 |
| M-10 | 0 | 0 | 0 | 420 |
| M-11 | 0 | 0 | 0 | 420 |
| M-12 | 0 | 0 | 0 | 420 |
| M-13 | 0 | 53 | 367 | 0 |
| M-14 | 0 | 28 | 392 | 0 |
| M-15 | 0 | 0 | 0 | 420 |
| M-16 | 0 | 0 | 0 | 420 |
| M-17 | 65 | 0 | 355 | 0 |
| M-18 | 0 | 94 | 326 | 0 |
| M-19 | 0 | 0 | 0 | 420 |
| M-20 | 0 | 0 | 0 | 420 |
| M-21 | 0 | 0 | 0 | 420 |
| M-22 | 0 | 0 | 0 | 420 |
| M-23 | 0 | 0 | 0 | 420 |
| M-24 | 0 | 108 | 312 | 0 |
| M-25 | 0 | 0 | 0 | 420 |
| M-26 | 0 | 0 | 0 | 420 |
| M-27 | 0 | 0 | 0 | 420 |
| M-28 | 0 | 0 | 0 | 420 |
| M-29 | 51 | 0 | 369 | 0 |
| M-30 | 0 | 0 | 0 | 420 |
| M-31 | 0 | 0 | 0 | 420 |
| M-32 | 0 | 0 | 0 | 420 |

Rows with no scorable clause in any season (PRF-10, PRF-11, M-1, M-7…M-12, M-15, M-16, M-19, M-20, and others in the table above): registered as GG-1060. No row is a free-data MET for a full archetype where a clause is missing: the missing-clause archetypes (PRF-1…4, 8, 9, 12, 14, 15) can only reach MET_PARTIAL.

### Muse grade (games-played recompute)

Muse's play-type and tracking records carry a games-played value; the bot recomputed it from the store (play-type: per team stint; tracking: season total). 21,249 records graded, 67 names unmatched, exact 15,153, within ±1 17,525. Rule: VERIFIED if exact ≥ 99% for the family-season cell, else FAILED with the difference.

| family | season | n | exact | exact rate | mean diff (Muse − store) | verdict |
|---|---|---|---|---|---|---|
| play-type PPP | 2024 | 2266 | 1813 | 0.8001 | -0.159 (range -2…1) | FAILED |
| play-type PPP | 2025 | 2461 | 2439 | 0.9911 | +0.008 (range -1…1) | VERIFIED |
| play-type PPP | 2026 | 2467 | 380 | 0.1540 | -2.289 (range -5…1) | FAILED |
| play-type frequency | 2024 | 2266 | 1813 | 0.8001 | -0.159 (range -2…1) | FAILED |
| play-type frequency | 2025 | 2461 | 2439 | 0.9911 | +0.008 (range -1…1) | VERIFIED |
| play-type frequency | 2026 | 2467 | 380 | 0.1540 | -2.289 (range -5…1) | FAILED |
| tracking: drives | 2024 | 570 | 373 | 0.6544 | -0.372 (range -3…2) | FAILED |
| tracking: drives | 2025 | 566 | 524 | 0.9258 | -0.101 (range -5…0) | FAILED |
| tracking: drives | 2026 | 579 | 575 | 0.9931 | -0.003 (range -1…1) | VERIFIED |
| tracking: potential | 2024 | 570 | 373 | 0.6544 | -0.372 (range -3…2) | FAILED |
| tracking: potential | 2025 | 567 | 525 | 0.9259 | -0.101 (range -5…0) | FAILED |
| tracking: potential | 2026 | 579 | 575 | 0.9931 | -0.003 (range -1…1) | VERIFIED |
| tracking: time | 2024 | 570 | 373 | 0.6544 | -0.372 (range -3…2) | FAILED |
| tracking: time | 2025 | 566 | 524 | 0.9258 | -0.101 (range -5…0) | FAILED |
| tracking: time | 2026 | 579 | 575 | 0.9931 | -0.003 (range -1…1) | VERIFIED |
| tracking: touches | 2024 | 570 | 373 | 0.6544 | -0.372 (range -3…2) | FAILED |
| tracking: touches | 2025 | 566 | 524 | 0.9258 | -0.101 (range -5…0) | FAILED |
| tracking: touches | 2026 | 579 | 575 | 0.9931 | -0.003 (range -1…1) | VERIFIED |

Likely cause of the 2026 play-type miss (stated as likely, not proven): Muse's 2026 play-type snapshot predates the season's end, so its GP runs 1–5 below the full-season store. The 2024 miss is small (play-type within ±1 in 2,265 of 2,266). Only games-played was graded; the play-type frequencies and PPP values themselves were not recomputed (GG-1031: no play-type labels in the store). Entry appended to `TO_MUSE.md`; GG-1063.

## Part B — interpretation

### 1. Stability

Split-half = odd versus even games within a season (≥8 games and ≥10 mpg in each half); year over year = season-end flags for players qualified in both seasons. Cohen's kappa and retention (share of half-A MET that stay MET). Muse-snapshot or team-relative factors (PRF-6, 7, 13, M-17) have no split-half. Full table: `results/stability.csv`.

| id | split-half 2026 n | kappa | retention | YoY 2025→26 kappa |
|---|---|---|---|---|
| PRF-1 | 402 | 0.856 | 0.905 | 0.542 (n=327, met 19→23) |
| PRF-2 | 402 | 0.755 | 0.766 | 0.377 (n=327, met 41→46) |
| PRF-3 | 402 | 0.757 | 0.842 | 0.32 (n=327, met 113→129) |
| PRF-4 | 402 | 0.82 | 0.906 | 0.762 (n=327, met 165→152) |
| PRF-5 | 402 | 0.706 | 0.764 | 0.621 (n=327, met 54→65) |
| PRF-6 | — | — | — | 1.0 (n=327, met 5→5) |
| PRF-7 | — | — | — | 0.312 (n=327, met 141→148) |
| PRF-8 | 402 | 0.877 | 0.905 | 0.514 (n=327, met 18→26) |
| PRF-9 | 402 | 0.677 | 0.737 | 0.795 (n=327, met 37→34) |
| PRF-12 | 402 | 0.822 | 0.885 | 0.791 (n=327, met 47→48) |
| PRF-13 | — | — | — | 0.372 (n=327, met 50→45) |
| PRF-14 | 402 | 0.806 | 0.805 | 0.48 (n=327, met 31→40) |
| PRF-15 | 402 | 0.742 | 0.783 | 0.619 (n=327, met 70→75) |
| M-2 | 402 | 0.581 | 0.667 | 0.502 (n=327, met 25→44) |
| M-3 | 402 | 0.406 | 0.419 | 0.583 (n=327, met 27→28) |
| M-4 | 402 | 0.282 | 0.273 | 0.386 (n=327, met 7→8) |
| M-5 | 402 | 0.128 | 0.125 | 0.138 (n=327, met 5→8) |
| M-6 | 402 | 0.855 | 0.86 | 0.56 (n=327, met 50→49) |
| M-13 | 402 | 0.774 | 0.86 | 0.769 (n=327, met 34→39) |
| M-14 | 402 | 0.785 | 0.759 | 0.717 (n=327, met 27→27) |
| M-17 | — | — | — | 0.497 (n=327, met 62→57) |
| M-18 | 402 | 0.458 | 0.561 | 0.52 (n=327, met 97→84) |
| M-24 | 402 | 0.6 | 0.709 | 0.597 (n=327, met 117→95) |
| M-29 | 402 | 0.243 | 0.358 | 0.274 (n=327, met 26→33) |

Reading: usage and shot-profile factors (PRF-1, 4, 8, 12, 14; M-6, M-13, M-14) are stable inside a season (kappa ≥ 0.77); year over year the ones that hold are PRF-4, 5, 9, 12, 15 and M-13, M-14 (kappa ≥ 0.6); PRF-1, 2, 3, 7, 13 drop to 0.3–0.54, meaning role changes between seasons. M-4, M-5, M-29 are unstable even within a season (kappa ≤ 0.28) — rare flags near their cutoffs. Because every threshold is a hard cutoff, kappa near the cutoff is noise-dominated; this measures the cutoff's stability, not the underlying role's.

### 2. The cross: PRF-1 versus frozen NBA player-points residuals — NOT RUN (n = 0)

The PREGAME_SHADOW NBA player-points ledgers (`NBA_NBA_PLAYER_POINTS_T1/T2/T3.jsonl`, 1,988 / 1,978 / 1,605 rows, model `nba_player_points_v1`) began ~2026-10-18; the season opened 2026-10-20; the rows carry p_yes and the market mid but no actual-points field, and the local store holds no 2026-27 games. There is no settled residual to compute. No effect, interval or price test is reported, and none is fabricated. Re-run when settled NBA rows exist (GG-1064). Also noted: `12_EXPLORATORY/CHARTER.md` rule 2 forbids exploratory code reading PREGAME_SHADOW ledgers while this block names them — the read would have been a one-off scratch extraction, disclosed; it was not needed.

Is an application worth building next? Yes for the stable subset, conditional: PRF-1 (usage engine) and PRF-4 are the candidates because their flags are stable and map directly onto points lines (usage, shot volume); build the first application once ≥ a few hundred settled player-games exist. This is a recommendation, not a finding.

## Stage per factor

Aggregated: every factor with ≥1 scorable clause (see counts). Interpreted (stability only): PRF-1, 2, 3, 4, 5, 8, 9, 12, 14, 15 and M-2, 3, 4, 5, 6, 13, 14, 18, 24, 29 (split-half); PRF-6, 7, 13, M-17 (year over year only). Applied: none. UNSCORED factors: registered gaps (GG-1060, GG-1061, GG-1062).

