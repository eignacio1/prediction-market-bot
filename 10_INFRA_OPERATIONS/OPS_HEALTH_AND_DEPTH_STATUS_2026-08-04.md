# Ops Health + Depth Time-Series Status — 2026-08-04

**Session:** T-414 (GG-154 remediation — this wave's only SSH-capable window)
**Scope:** Read-only against VPS except crontab confirmation. No `src/` changes, no new cron.
**Author window:** `session/20260804T045839Z-step4-depth-status`

---

## Task 1 — Step 4 (VPS operational health check), run verbatim

### T1 MLB cron — last 5 runs

```
  35 players in live MLB markets | 116 market/threshold pairs
  Bets placed today:  10
  17 players in live MLB markets | 52 market/threshold pairs
  Bets placed today:  0
  35 players in live MLB markets | 105 market/threshold pairs
  Bets placed today:  0
  36 players in live MLB markets | 119 market/threshold pairs
  Bets placed today:  0
  21 players in live MLB markets | 72 market/threshold pairs
  Bets placed today:  0
```

Player-matching is healthy (17–36 players/run, well above zero) — the pipeline is evaluating normally. `Bets placed today: 0` on 4 of the last 5 runs is explained below (T1-cache verdict), not a matching failure.

### T4 MLB — systemd

```
active
```

### T1 NBA — last 3 runs (off-season, 0 games expected)

```
[PIPE-03] Paper trading — 20260802
  No KXNBAPTS markets available. No games today or pre-market.
[PIPE-03] Paper trading — 20260803
  No KXNBAPTS markets available. No games today or pre-market.
[PIPE-03] Paper trading — 20260804
  No KXNBAPTS markets available. No games today or pre-market.
```

Healthy dark state, matches [NBA tabled directive](../04_EXECUTION/TODO_NEXT.md).

### Semantic oracle checks

```
SemanticFloorViolation count: 1
CONTAMINATION_HALT count (all-time): 17919
T4 staleness, recency-windowed (last 500 audit rows, failed_checks=["game_state_fresh"]): 0
```

The single `SemanticFloorViolation` hit is dated **2026-07-10** (`games_fetched=16, matched_players=0`) — historical, not current; every subsequent T1 MLB run shown above matches players normally. No live concern. `CONTAMINATION_HALT`'s large all-time count is expected (fires routinely at market close, per protocol note); the recency-windowed staleness count of 0 is the live signal and is clean.

### Dashboard OOM-restart probe

```
NRestarts=0
ActiveState=active
SubState=running
--- oom-kills, last 24h ---
0
```

Healthy baseline, no crash-loop.

**Step 4 verdict: healthy.** No new operational incidents. The two findings below come from following up on the T1/MAIN cache-staleness question the session was specifically asked to run down, not from Step 4 itself.

---

## Task 1 — T1/MAIN portfolio cache staleness verdict

**Claim under test:** `logs/.vps_portfolio_cache_mlb.json` (T1/MAIN) shows `last_updated: 2026-07-31T06:35:06.082Z` — 4 days stale — while the T4 cache (`.vps_portfolio_cache_mlb_t4.json`) is current (`2026-08-04T03:28:20.142Z`).

**Confirmed against the live VPS file directly** (not just the local cache copy): `/opt/prediction-market-bot/logs/paper_portfolio_mlb.json` itself carries `last_updated: 2026-07-31T06:35:06.082Z`, 22 open positions, 463 closed. The staleness is real VPS state, not a caching artifact.

### Root cause 1 (primary, matches the operator's hypothesis — CONFIRMED)

`kelly_fraction=0.0` for `T1_MULTI_DAY` and the other T1/T2 bands, per **ADR-0048 (2026-07-29)**, superseding ADR-0040's 0.061, following GG-135's ruin-geometry finding (DS sign-off: operator, 2026-07-29). `execution_bands.py:142`:

> `kelly_fraction=0.0, # ADR-0048 ... zeroed pending edge-conditional reactivation. Evaluations continue to log for research; only sizing is zero.`

Corroborated by the C4 edge-decision audit trail: T1 MLB placed 21/25/13/19/10 bets/day 07-25→07-29, then **exactly zero** bets/day every day 07-30→08-03 (5 consecutive days), with a new `kelly_size_zero` rejection reason first appearing 07-29 and dominating from 07-30 onward. Today's cron output above shows the same pattern continuing (`Bets placed today: 0` on 4/5 runs, with the one `10` being an earlier run before this wave). **Evaluations are not silenced — sizing is.** This alone explains why no *new* positions are written.

### Root cause 2 (secondary, previously undocumented — new finding)

The 22 positions still open **predate** the kelly zeroing (`game_date` 2026-07-01 through 2026-07-29) and are **permanently stuck**:

- All 22 are already tagged `aged_open: True` in the live portfolio file (confirmed via direct VPS query).
- `fetch_actual_hits()` — MLB Stats API regular season, MLB Stats API postseason, and ESPN boxscore fallback, all three — returns `None` for every one of them, every day, including games now 100–800+ hours old that unquestionably have final box scores available. This is not an API-outage signal; it is a standing data-resolution failure specific to these 22 (player_id, game_date) pairs.
- The GG-048 alert (`zero_resolved_with_eligible_positions`) **is** firing correctly and is logged to `audit_mlb.jsonl` every day (confirmed 08-01, 08-02, 08-03: `eligible_count: 22, resolved_count: 0`) — the machine-readable audit trail knows about this.
- However, `PaperTrader.mark_aged_open()` is idempotent and only calls `self._save()` the *first* time a position is marked aged (`paper_trader.py:963-964` early-returns on repeat calls). Since all 22 were already aged before 07-31, **every daily resolution run since has been a complete no-op at the file-write level** for the T1/T2 pool — it re-detects the same 22 stuck positions and re-logs the same alert, but never touches the portfolio file again. This — not just the absence of new bets — is why `last_updated` is frozen exactly at 07-31T06:35:06Z.
- Per `mark_aged_open()`'s own docstring: "capital remains deployed... capital is NOT credited back." **These 22 positions are holding real paper capital that cannot resolve under current logic and will not free up on its own.**

**This finding outranks Task 2 per the session's own instructions** — the cache staleness has a second, independent cause beyond the expected kelly=0 explanation, and it represents dead/stuck capital, not just an idle book. It is not registered as a governance gap yet (out of this session's scope fence to make that judgment call); flagging here for the operator to decide whether it needs a GG entry and a fix (e.g., a distinct terminal state for positions that fail all three resolution sources beyond some age ceiling, rather than indefinite `aged_open` limbo).

---

## Task 2 — Depth time-series status and re-check date

### Correction to task premise

The price archiver has run since 2026-08-01, but **depth sampling specifically (`--depth-sample-per-family`) did not exist until T-412 (2026-08-04T00:46:22Z)** — confirmed via `deploy/cron.conf`'s own T-412 comment and the script default (`--depth-sample-per-family`, `default=0`). Before that timestamp the flag was absent from cron entirely, not merely defaulted off with the old unbalanced sampler — so **there is no pre-fix depth data to separate from post-fix data.** GG-155's unbalanced-sampler concern (family misattribution) does not apply to any observation currently on disk; `--depth-sample-per-family` and `_balanced_sample()` (the fix) shipped in the same commit. All 168 rows collected so far are post-fix by construction.

### Observations to date (as of 2026-08-04T05:00:01Z, 14 archiver runs)

| Family | Total rows | Usable rows |
|---|---|---|
| GAME_TOTAL | 28 | 26 |
| GAME_WINNER | 28 | 28 |
| PARTIAL_GAME_WINNER | 28 | 28 |
| PLAYER_PROP | 28 | 28 |
| RUN_LINE | 28 | 26 |
| TEAM_TOTAL | 28 | 28 |

All 6 families exactly balanced at 28 rows (14 runs × 2 samples/family/run) — the round-robin fix is working as designed; no family is being starved the way GG-155 described.

### Accrual rate and projected crossing date

- Cadence: `*/20` during UTC hours 22–23 and 0–5 (8 active hours/day) → 24 runs/day at steady state, 2 samples/family/run → **48 observations/family/day** at steady state.
- Day 1 (2026-08-04) is partial — sampling started mid-window at 00:46Z, giving ~22 runs for the day (matches `cron.conf`'s own "~21 runs/day" design estimate).
- 200 observations/family requires 100 runs. Cumulative: Day1 ≈22, Day2≈46, Day3≈70, Day4≈94, Day5≈118 → **the 100-run / 200-observation threshold is crossed during Day 5, i.e. 2026-08-08**, roughly in that day's 00:00–05:00 UTC window.

### Re-check date

**2026-08-09.** By this date every family should be comfortably past 200 post-fix observations with a day's margin past the projected 08-08 crossing. Re-run this table on or after that date before treating the Phase 1 hold as satisfied — do not treat this document's projection as the clearance itself.

---

*Findings here are new as of this session; no governance gap has been registered for the Task 1 stuck-position finding — that decision is left to the operator per this session's scope fence.*
