# W52.D — Can EXP-036's T3 run know the confirmed starting goalie in time? (GG-401)

**Session:** Wave 52 CC executor (cloud), T-657, 2026-10-03. **Probe script:** branch `w52/nhl-goalie-probe` @ `3e31e95b`
(`scripts/nhl_goalie_source_probe.py` + offline tests; one-shot, read-only, no loop). No NHL score read or computed;
`nhl_pregame.py` / `nhl_shadow_eval.py` and every pre-registered parameter untouched.

## D1 — what T3 needs
- **Promise** (`EXP036_NHL_PREGAME_SHADOW_PREREGISTRATION_2026-10-02.md` line 42): "Goalie: projected starter at
  T1/T2, **confirmed starter at T3 when the source shows it**; flagged per row."
- **Interface** (`nhl_pregame.py` ~222-255): `StarterProvider = Callable[[game_id, as_of_utc], Optional[(home_goalie, away_goalie)]]`.
  `feature_row()` sets `confirmed=True` if either is returned. Nothing passes a provider today, so every band uses
  the projected starter (last start). That is GG-401.
- **Run times** (from the tracked `deploy/cron.nhl_shadow`; `deploy/cron.nhl_shadow.draft` is fully commented out. The live
  crontab is VPS-PENDING): T3 runs `*/10` at 17:00-23:50 and 00:00-02:50 UTC. `nhl_shadow_eval.py` `BANDS["T3"] = (0.25, 1.0)` h,
  so a game gets T3 rows from ~60 to ~15 min before puck drop. The last T3 row is written 15-25 min before start.
- **Requirement:** both teams' starting goalie IDs, marked confirmed (not projected), queryable at `as_of_utc`
  **no later than ~15 min before puck drop** (to cover every T3 row, by ~60 min before).

## D2 — sources probed
| Source | Names starter? | Confirmed vs projected? | When it appears | Terms | Result from this session |
|---|---|---|---|---|---|
| api-web.nhle.com `/v1/schedule/{date}` | — | — | — | official, public | **refused by egress proxy** (`CONNECT tunnel failed, response 403`) |
| api-web.nhle.com `/v1/gamecenter/{id}/boxscore` — `playerByGameStats.<side>.goalies[].starter` | yes (`starter: true`) | the flag means "started"; repo uses it **post-game only** (`nhl_ingest.py:128-130`) | **unknown pre-game** — the question | official, public | refused by proxy |
| api-web.nhle.com `/v1/gamecenter/{id}/landing` | unknown | unknown | unknown | official, public | refused by proxy |
| dailyfaceoff.com starting goalies (unofficial) | — | — | — | not checked (unofficial; terms must be read before any use) | refused by proxy |

No other public feed was probed. The only verified fact here comes from the repo itself: the official boxscore carries a
per-goalie `starter` flag, and this project has only ever read it after the game.

## D3 — Verdict: **(c) cannot tell**
Every candidate source is unreachable from this cloud session, and the repo has no timestamped pre-game capture of the
`starter` flag. **The measurement that decides it** is a terminal session on the VPS (which reaches api-web.nhle.com,
per `nhl_ingest.py`'s docstring) running
`python3 scripts/nhl_goalie_source_probe.py --date <slate date>` from branch `w52/nhl-goalie-probe` by hand three
times on one slate, at about 60, 30 and 15 minutes before the first puck drop. Then, per game, record the earliest
probe that shows `boxscore_starters` / `landing_starters` for both sides.
- Starter flag present for both sides at ≥15 min before start in k of n games → verdict **(a)**. Scope a
  `StarterProvider` reading that field as one ~30-min block. It must cap `as_of_utc` (information cutoff) and flag rows
  confirmed only when the flag is present.
- Flag appears only at or after puck drop → verdict **(b)**. Operator choice: move T3 later (it cannot move past start),
  or amend the pre-registration, line 42, to: *"Goalie: projected starter (last start) at every band, T3 included; no
  confirmed-starter source is available before puck drop. Rows are flagged `confirmed=False`."* (exact wording for the
  amendment, which is the operator's call).
Until one of those happens, GG-401 stands: **no NHL T3 score may be read.**
