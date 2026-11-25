# W128.5 TRIAGE — Muse QUEUE families: SCRIPT / MUSE / ALREADY

Last reviewed: 2026-11-25. Source: `eignacio1` archive QUEUE.md read via `gh api` (read only; Muse not contacted). Chunk ids below are the QUEUE's own.
Box evidence: `04_EXECUTION/BOX_TASKS/results/20261125T062104Z_data_offload_probe.md` (reach + one capped sample run per family, from the box).
Rule held throughout: a site that refuses the server (401/403/429, challenge page) is MUSE. No bypass, no sign-in, no header spoofing.

## SCRIPT (built in `scripts/data_offload.py`, built not run)

| Family | URL pattern | Terms / rate | Size per season (gz) | Box sample | QUEUE chunks covered |
|---|---|---|---|---|---|
| MoneyPuck season summaries (teams, skaters, goalies, lines) | `moneypuck.com/moneypuck/playerData/seasonSummary/<yr>/regular/<kind>.csv` | Free, non-commercial, **must credit MoneyPuck.com**; 1 req per 3 s | lines 1.6 MB, skaters 3.5 MB, teams 0.1 MB, goalies 0.09 MB (raw) | OK, 16 files, 5.6 MB, 31 s, RSS 26 MB | C-922..C-1101, C-3516..C-4347 |
| MoneyPuck team game-by-game | `moneypuck.com/moneypuck/playerData/teamGameByGame/<yr>/regular/<TEAM>.csv` | same | ~0.1 MB per team-season | in the same sample | C-1378..C-1751, C-2138 |
| NHL officials | `api-web.nhle.com/v1/gamecenter/<id>/right-rail` + schedule | Public API; domain Content-Signal ai-train=no (we do not train AI); 0.5-1 s pauses | ~4.4 KB per game | OK, 24 games, 5 KB, RSS 27 MB | C-3399..C-3515 |
| NHL goalie game logs | `api.nhle.com/stats/rest/en/...` (goalie game rows) | same | ~45 KB per 100 rows | OK, 25 req, 23 KB, RSS 26 MB | C-4348..C-4763 |
| Baseball Savant CSV boards (12) | `baseballsavant.mlb.com/leaderboard/...&csv=true` | Public CSV export; 1 req per 3 s | <1 MB per board-year | OK, 25 req, 369 KB, 72 s, RSS 26 MB | exit velo/barrels C-5020..C-5031, C-5608..C-5619; expected C-5620..C-5643; percentile C-5644..C-5667; pitch tempo C-5668..C-5691; run value C-5692..C-5715; pitch arsenals C-5752..C-5763; pop time C-5764..C-5775; sprint speed C-5776..C-5787; 90ft running C-5788..C-5799 |
| MLB boxscore (batting orders) | `statsapi.mlb.com/api/v1/schedule` + `/game/<pk>/boxscore` | Public API | ~2 MB cap per night | **FAILED on the box: HTTP 406**, still 406 after the Accept fix (Mac fine). Classified MUSE | C-5128..C-5487 (stay with Muse) |

## MUSE (the server cannot, or should not)

| Family | Why | Evidence |
|---|---|---|
| NBA stats tables: team/player traditional, advanced, four factors, shot dashboards, tracking, play types, hustle, lineups, league matchups, quarter splits (C-001..C-1377 less NHL, C-1228..C-1347, C-1752..C-3398) | stats.nba.com and cdn.nba.com refuse the box | 403, 403 (box probe) |
| NFL team/QB splits (C-201..C-275 region and C-2136..C-2137; source site unverified, PFR itself refuses) | refuses the box | pfr 403 |
| NFL offensive personnel / tendencies (C-4764..C-5019) | needs judgment; nflverse overlap NOT settled here (ALREADY check open, see below) | — |
| NHL closing lines (kofsports, C-1806..C-1837) | reachable (200, first 4 KB read, no challenge); content not examined, so not built | 200 |
| MLB umpire scorecards (C-5032..C-5127) | reachable (200, first 4 KB read, no challenge); data format not examined, so not built | 200 |
| Savant splits batters/pitchers, top performers, park factors, batted-ball profile (C-5560..C-5607, C-5716..C-5751) | not built this block (different URL shapes); candidates for a second pass | — |
| NHL team powerplay / penalty kill (C-1102..C-1125) | NHL API has it; not built this block, candidate for a second pass | — |
| MLB batting/pitching splits (C-5488..C-5559) | not built this block | — |

## ALREADY
Open: NFL personnel vs nflverse. Not verified this block; left MUSE until the window checks overlap with the existing event store.

## Not covered by this triage
R1-R11 / B1-B3 / daily-snapshot labels were not in the QUEUE.md table I read (it lists tables, not those labels). Classification above is by QUEUE table. Map the labels in the Monday message.
