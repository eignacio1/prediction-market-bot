# PREREG — NBA depth splits from the archive (W118.2, EXP-NBADEPTH-001)

**Last reviewed:** 2026-11-18. **Frozen before any outcome (`y`) or net figure is read for any split below.**
Only schemas, row counts, seasons and timestamps were read to write this (Part A inventory). Changing anything below after the
first scored row is a new pre-registration, not an edit.

Binds to: DOCTRINE (a factor is applied when it is a tested split scored per leaf per arm, net after costs, held out);
ADR-0075 (splits enter the router as layer-3 splits); ADR-0077. "Does not beat the market" is a routing result, never a stop.

## 1. Inventory (Part A.1) — archive pinned at `bafaeef4de9596fd7a69941b36ca16a34af2f344` (`eignacio1/sports-intel-archive`, read-only)

All NBA archive files were extracted 2026-10-21 .. 2026-11-09 (`asof` / `source_time`). A full-season value for a COMPLETED season
(`season` 2025 = 2025-26 and earlier) was therefore knowable before every 2026-27 row (first shadow row 2026-10-20 is a
rounding case: guard below). A 2026-27 archive value is NOT point-in-time for rows before its `source_time`. Rule used by every split:
**only prior-completed-season archive values, or snapshots with `status_at_utc <= row ts_utc`.**

| Family (path under `L3-split/nba`) | Holds | Seasons | Subject / join key | PIT status |
|---|---|---|---|---|
| `advanced-*`, `clutch-*`, `hustle-*`, `defense-dashboard-*` | player season leaderboards (usage, TS%, ratings, hustle, defence) | 2023-24..2025-26 (+2026-27 advanced) | player + team abbr | prior season PIT-safe; 2026-27 not |
| `matchups-<season>-<TEAM>` | player-vs-player matchup minutes/points (80,043 rows) | 2023-24..2025-26 | player, team abbr | prior season PIT-safe |
| `lineups-onoff-*` | unit and player on/off | 2023-24..2025-26 | unit / player | prior season PIT-safe |
| `r025-team-advanced-season` | team off/def/net rating, **pace** (360 rows) | 2023..2025 | team abbr | PIT-safe (prior) |
| `r025-team-four-factors-season` | team four factors (720 rows) | 2023..2025 | team abbr | PIT-safe (prior) |
| `referees-*` | crew-level: games worked, PF/g, FTA/g, total points/g | 2023-24..2025-26 | referee name | prior season PIT-safe |
| `splits/C-xxx` (720 files, 3.7 GB) | team and player splits: home/road, clutch, quarter, month, conference/division, **team shooting by zone**, **opponent shot dashboards (shot clock, closest defender, touch time, dribbles, shot type)**, tracking | 2020..2025 (most 2022..2025) | team name / abbr | prior season PIT-safe |
| `L3-snapshots/nba/lineups-<date>` | per game: projected / confirmed starters, `away_status` / `home_status`, `status_at_utc`, `confirmed_at_utc`, out list, day-to-day list, late scratches | daily 2026-11-10 .. 11-17 only | `game_id` = `AWAY@HOME-YYYY-MM-DD` | PIT per row by `status_at_utc` |
| `L3-snapshots/nba/refs-<date>` | assigned crew per game | 2026-11-10 .. 11-17 | `game_id` | PIT per row by snapshot time |

Join keys to our rows: `event_ticker` → (away, home abbreviations, game date) → archive `team` abbr / `game_id`. Join coverage is
STATED IN THE RESULTS FILE per split (rows joined / rows total), never assumed. Coverage gaps already seen: several zone and
opponent-dashboard split files carry 20–27 of 30 teams (partial); snapshot tables begin 2026-11-10 while shadow rows begin 2026-10-20.
Rows with no join get leaf `unknown`, and `unknown` is never scored (same rule as `score_leaves.py`).

## 2. The five splits (Part A.2)

Leaves are categorical, from terciles of the two teams' PRIOR-season values (same edges as `nba_engine.filters`: `LOW,HIGH=1/3,2/3`;
side edge `SIDE_EDGE=1/3`). Names are `<class>@total` (high/mid/low) or `<class>@side` (home_edge/away_edge/neutral).

**S1 `pace_prod@total` — pace and efficiency shift.** Mean of the two teams' 2025-26 `pace (NBA.com teams advanced)` percentile.
Cells: NBA GAME_TOTAL, TEAM_TOTAL, bands T1–T3. Arm it would change: FADE vs RIDE (and NO_BET) on totals in high / low pace leaves.
Companion `net_rating@side`: home minus away 2025-26 net-rating goodness (higher better) → cells SPREAD, MONEYLINE; arm RIDE vs FADE.

**S2 `shotzone_matchup@side` and `@total` — opponent's defence against this team's shot profile.** For each team: share of its
shots from three-point + restricted area (team shooting by zone, 2025-26, all-games table) versus the opponent's allowed FG% in the
same zones (opponent shooting table). Matchup score = team's offensive zone mix dotted with the opponent's allowed-FG% percentile by
zone; side leaf from home minus away matchup score, total leaf from the mean. Cells: SPREAD, MONEYLINE, GAME_TOTAL. Arm changed:
RIDE / FADE / MOMENTUM per leaf. Coverage risk stated above.

**S3 `lineup_status@side` / `@total` — confirmed vs projected lineup.** Leaf from the latest snapshot with `status_at_utc <=
ts_utc`: `confirmed` (both sides) / `mixed` / `projected_only`, crossed with count of rotation players (>= 20 min/g in the snapshot
`*_starters_detail.min`) listed OUT. Cells: all four families. Arm changed: to NO_BET/RIDE when projected-only and a rotation player
is out; FADE allowed only on confirmed leaves. Coverage: only rows with `ts_utc >= 2026-11-10`.

**S4 `home_road_gap@side` — home/road differential.** Home-win% minus road-win% (2025-26 `Location=Home` / `Location=Road`
tables) of each team; leaf from (home team's home strength) minus (away team's road strength) percentile. Cells: SPREAD, MONEYLINE.
Arm changed: RIDE vs FADE on the home side.

**S5 `ref_crew@total` — officiating crew tendency.** Mean of the assigned crew's 2025-26 `total points per game in games worked` and
`free-throw attempts per game in games worked` percentiles (referees table), crew from the refs snapshot. Cells: GAME_TOTAL,
TEAM_TOTAL. Arm changed: FADE/RIDE on totals in high / low crew leaves. Coverage: refs snapshot dates only.

## 3. Scoring rule (Part B), frozen

Data: the box's settled NBA shadow rows (56,824 rows at export), cells KXNBAGAME / KXNBASPREAD / KXNBATOTAL / KXNBATEAMTOTAL, bands T1–T3.
Harness: `quant.retro_route` as used by `score_leaves.py` — same fit/test 70/30 game split (`split_games`, by game, never by row),
same costs, same arms (RIDE, FADE, MODEL_FADE, MOMENTUM), same `MIN_FIT_ROWS=60`, `MIN_FIT_GAMES=20`, `MIN_TEST_GAMES=10`,
`DRAFT_TEST_GAMES=15`. Per (split × leaf × cell × band): the fit window picks the best positive-net arm, the test window scores it
with a game-clustered bootstrap CI on net per contract; Benjamini–Hochberg across every test in this file (q=0.10).
**Kept** = not thin, arm != NO_BET, held-out games >= `MIN_TEST_GAMES`, held-out mean net > 0 (the `filter_splits.json` rule).
**Draft-strength** = kept AND BH reject AND lower CI > 0 AND test games >= `DRAFT_TEST_GAMES`. Nothing is called edge, and kept
does not mean wired (118.3 wires). Expectation recorded now: ~5 weeks of 2026-27 rows, so most leaves are thin and route to NO_BET.
That is a routing result for the look, not a verdict on the split. A split that keeps no leaf is logged as
"hypothesis closed (EXP-NBADEPTH-001-S<n>, parked for R&D)" in `nba_depth_v2.json`, not deleted.

## 4. Guards
No look-ahead: tested per split (a row at time t never reads an archive value with `source_time`/`status_at_utc` > t, nor any
2026-27 season value). No edits to `filter_supply.py`, `leaf_map.json` (frozen v1) or `leaf_map_v2.json`. Kelly stays 0. Free data only.
