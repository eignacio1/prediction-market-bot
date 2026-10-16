# NBA engine — first factor read (W79.3)

**Date:** 2026-10-16 · **Pillar:** DEPTH · **Measures:** D4, D5(b) NBA · **Decisions logged:** false (DECISION_LOG row appended at close)
Script `scripts/nba_factors_first_read.py`, results `factors_first_read.json`. Universe: 2016-2025 regular seasons, 10,421 games, `eligible_games` rule; 2026-27 untouched. Features built point-in-time (contract: G' usable iff `tip_latest(G')+4h <= tip_earliest(G)`), cross-checked on 300 sampled games.

## Rules fixed before results
- **Trait:** lower CI bound of split-half r (first vs second half of season, cluster bootstrap over team-seasons) >= 0.30.
- **Moves:** out-of-sample MSE gain CI (paired bootstrap, 1000 reps) excludes 0; train 2016-2020, test 2021-2025; baseline is the team's season-to-date rating.

## Factor 1 — possession pace and efficiency (N2)
Poss = FGA + 0.44 FTA - ORB + TOV; pace = poss*240/min; ortg/drtg per 100 poss. Rolling, season-to-date and last 10, MIN_GAMES 10.
| metric | split-half r | 95% CI | trait |
|---|---|---|---|
| pace | 0.80 | 0.75-0.83 | yes |
| ortg | 0.75 | 0.70-0.79 | yes |
| drtg | 0.71 | 0.65-0.75 | yes |
| net | 0.74 | 0.68-0.79 | yes |

Moves: pace+efficiency vs game **total**, MSE gain 11.2 (CI 8.4-14.2) → moves. Recent efficiency deviation vs **margin**, gain 0.99 (CI 0.34-1.63) → moves, small (coef 0.156 per net-rating point, CI 0.11-0.20). **Stage: interpreted.**

## Factor 2 — rest (N3)
b2b, three-in-four, days since last game, games in last 7.
- Trait: b2b rate r = -0.09 (CI -0.19-0.02), three-in-four r = -0.04 → **not a team trait**; it is schedule, not a team property.
- Moves margin: gain 1.88 (CI 0.96-2.86) → moves. Back-to-back differential coef **-2.30 points** (CI -2.96 to -1.61); odd seasons -2.58, even -2.24 (stable). Last-7 load -0.39 (CI -0.82 to -0.02).
- Moves total: gain 0.12 (CI -0.70-1.02) → does **not** move.
**Stage: interpreted.**

## Caveats
- Not "applied": no comparison against a market price; edge is untested. Rest's b2b effect is probably already in lines.
- The pace/efficiency total gain is a decomposition and may partly reflect league-wide drift in pace/scoring across 2016-2025; not isolated.
- Regular season only; playoffs excluded. 2026 label not read. No opponent adjustment of ratings. Travel distance skipped (GG-913).
- Multiple looks: four moves tests, no correction; the margin-efficiency gain is the weakest.

## D4 / D5(b) lines (NBA)
- **D4:** none → event-level data layer with a point-in-time contract, on main (#278) and on the box (hash-verified), 2015-16..2025-26 + 2026-27 schedule. Source: `DATA_LAYER.md`, manifest 2026-10-16T06:01:34Z.
- **D1 (NBA):** factor classes mapped to free sources 0 → 13 (`FACTOR_TAXONOMY.md`; 5 gaps GG-910..914).
- **D5(b) (NBA):** two factor classes aggregated → interpreted (pace/efficiency, rest); applied: 0.

## Drafted, NOT added: RUNTIME_REGISTRY entry for Wave 80 (weekly store rebuild)
```toml
[[component]]
id = "nba-event-store-rebuild"
kind = "cron"
schedule = "weekly, Mon 08:00 UTC; injuries snapshot DAILY (history is not recoverable)"
purpose = "Rebuild exp_output/NBA_EVENTS from free sportsdataverse releases; refresh store_file_hashes.json"
pillar = "DEPTH"
writes = ["exp_output/NBA_EVENTS/", "event_store_manifest.json"]
alarm = "manifest build_as_of older than 8 days, or nba_store_verify verify nonzero"
```
Field names follow nothing verified; Wave 80 must adapt to `runtime_registry.py add`.
