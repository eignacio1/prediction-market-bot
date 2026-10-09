# W61.2 — Verdict readiness: results

Session claim: T-750..T-752, GG-532, GG-534..GG-535 (claimed 2026-10-09T00:21Z). Run 2026-10-09 ~00:20-00:40 UTC.

## Part A — Health, GG-401, retirement

### A1. CLAUDE.md Step 4 on the VPS (2026-10-09 00:21Z)
| Check | Result |
|---|---|
| T1 MLB last runs | Latest 6 runs: 0, 27, 15, 12, 27, 6 players matched; `Bets placed today: 0` on all (T1 kelly is 0.0 per ADR-0048; evaluations only) |
| t4-mlb | `active` |
| T4 cycle log | last row 2026-10-09T00:21:01Z, age ~0h (live postseason games in progress) |
| Dashboard | NRestarts=0, active/running, 0 oom-kills (24h) |
| NBA T1 (off-season) | `No KXNBAPTS markets available` 10-07, 10-08 (expected) |
| Oracle: SemanticFloorViolation | 1, **historical**: log line 1229 is the 2026-07-10 run (games_fetched=16, matched=0). Not current; not re-registered |
| Oracle: CONTAMINATION_HALT | 164,182 cumulative in the audit file (expected game-end `market_active=False`); recency-windowed `game_state_fresh` count (tail 500) = 0 |

### A1b. Shadow arms: newest row vs schedule
| Arm | Newest row (UTC) | Verdict |
|---|---|---|
| NFL T1/T2/T3 (4 market types each) | T1 10-08 12:05, T2 10-08 20:10, T3 10-08 23:58 (TNF) | on schedule |
| NHL T1/T2/T3 (3 types) | T1 10-08 14:00, T2 10-08 21:34, T3 10-09 00:16 | on schedule |
| NBA preseason (T1/T2/T3) | T3 mtime 10-08 22:57 | on schedule (judged NBA ledgers do not exist until regular season 10-20, by design) |
| **MLB postseason** | T3 10-08 01:43, T1 10-08 06:07, T2 10-07 21:12 | **SILENT ~23h: GG-532** |

**GG-532 (new, OPEN, MEDIUM).** Every run since logs `written: {}` and `skipped: no_kickoff` = 41 (10+6+11+14), i.e. every open market. Games cache is healthy (refreshed 2026-10-08T19:01Z). Mechanism, from code + cache (not reproduced by a run): `MLBScheduleIndex.game` requires teams AND start within 45 min of the ET time encoded in the event ticker. Open event `KXMLBGAME-26OCT081700CLECWS` encodes 17:00 ET but the cache has 20:00 ET (3h gap); the LAD/MIL events (10-11..10-15) have only placeholder rows in the cache. Whether Kalshi's postseason ticker time is a placeholder is unverified. Not fixed (Rule 11).

### A2. GG-401 — checked on stored rows
Rows written at/after the #188 deploy (2026-10-08 02:43 UTC), VPS `data/shadow/nhl/`:
| Band | n | pass (confirmed=False and starter_source non-empty) | combo |
|---|---|---|---|
| **T3** | **510** | **510 (0 fail)** | (False, projected_last_start) |
| T2 | 1200 | 1200 | same |
| T1 | 59 | 59 | same |

First T3 row 2026-10-08T22:06:04Z. **GG-401 RESOLVED** with this evidence. Premise note: the prompt called GG-401 the "T3 projected-goalie flag"; the log entry is titled "T1/T2 pregame model has no projected-starter source" and its closing condition is the W59.3 verdict-(b) amendment (projected starter at every band, confirmed=False) — which is what was checked, on all three bands.

### A3. Retirement
`scripts/retire_resolved_gaps.py --apply`: moved GG-228, GG-300, GG-401, GG-515, GG-525 (verbatim). After: headers=153 / status lines=153 (equal; includes the template fence header), uniqueness OK across live + archive, live OPEN = 130 (−GG-401, +GG-532), 0 resolved-class left in live log.
