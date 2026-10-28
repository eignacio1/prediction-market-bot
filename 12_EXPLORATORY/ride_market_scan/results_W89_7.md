# W89.7 Part A results — Kalshi NBA/NHL/NFL history with true start times (PARTIAL)

Status: **PARTIAL.** Part A is done for listings, schedule join and manifest. Candles are done only for the NBA and NHL game families and partly for NFL game. Part B (89.2 hold-out scan) was NOT started.
Source: `exp_output/KALSHI_HISTORY/w89_7/<sport>/MANIFEST.json` (data git-ignored; manifests tracked). Generated 2026-10-27.

## Findings
- Kalshi `occurrence_datetime` is exactly **+3.0 h after the ESPN scheduled start** (p10 = median = p90 = 3.0 h; n = 1299 NBA, 1974 NHL, 925 NFL events). It is not the start time. Anything keyed on it is 3 h late.
- Schedule join (Kalshi event to ESPN game, ET date + team pair): NBA 9353/9356 events (3 unmatched, "LIOPOR"); NHL 8436/8436; NFL 2619/2754 (135 unmatched, all LA-prefixed codes: the Kalshi "LA" vs ESPN "LAR"/"LAC" alias is wrong — fix next). This closes GG-1252 (NFL date-only tickers) except for those 135.
- GG-1253 (MLB HHMM-as-ET) was NOT checked.
- Settled markets listed (since 2025-08-01): NBA 2025-26 and 2026-27 across game/spread/total/team-total/PTS/REB/AST/3PT; NHL same plus GOAL/PTS/AST (KXNHLSAVES returned 0; KXNHLTEAMTOTAL has no 2025-26); NFL game/spread/total/team-total/ANYTD/PASSYDS/RECYDS/REC for 2025 and 2026. No parlay/multi-leg series was found by the regex probe (not verified further).
- Hourly candles [start-30h, start]: NBA KXNBAGAME 623 markets (2025-26 505, 2026-27 118); NHL KXNHLGAME 622 (2025-26 376, 2026-27 246); NFL KXNFLGAME 269 (2025 116, 2026 153). **Nothing else has candles** (spread/total/team-total/props: 0). Sampling is outcome-independent (strike quantiles / top volume), not yet applied.

## Not done
Remaining candles (all non-game families), NFL game remainder, Part B entirely, GG registrations, ACTIVE_QUEUE row update, DECISION_LOG entry, runtime-registry entry (script is a manual tool, no cron/service).

## Stage (ADR-0075)
Aggregated only (raw prices + true start). No interpretation or application. Measure: families with usable history MLB+NFL → game-only candles for NBA, NHL (partial NFL); 89.2 hold-out 0 → 0.
