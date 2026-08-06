# T-421 — Decoupled Outcome-Measurement Store for T4 MLB

**Date:** 2026-08-05 | **Task:** T-421 | **Branch:** `session/20260805T054940Z-decoupled-outcome-store`

## Purpose

T4 MLB has a forecast leg (`t4_mlb_cycle_log.jsonl`, every ~45-90s evaluation) and a price leg
(`exp_output/PRICE_ARCHIVE/prices_*.jsonl`, live since 2026-08-01, GG-156). It has never had an
**outcome** leg — no cycle-log row records whether the player actually reached the bet's hit
threshold in that game. Without ground truth, no forecast in the cycle log can be scored:
calibration, Brier score, and "was the model right" are all unanswerable for the ~57,000
evaluation rows that never became a bet, which is the overwhelming majority of what the model
actually produced (T4M-PROJ's fire rate is on the order of 0.6-0.8%, see CLAUDE.md § throughput).

This is an **additive, read-only measurement path**. It does not touch the ledger
(`paper_portfolio_mlb_t4.json`), does not touch `paper_trader.py`, `risk.py`, or
`run_t4_mlb_live.py`'s write path, and does not change sizing, epoch, or any ADR. It only reads
the cycle log and `run_resolve_mlb.py`'s existing resolution helpers (imported, not edited) and
writes a new, independent, gitignored store.

## Why not `scripts/build_t4_resolved_ledger.py`

That existing script serves a narrower, non-overlapping purpose: it extracts only the positions
that were actually bet on and closed in `paper_portfolio_mlb_t4.json`. T-421's scope is the full
cycle log — every evaluation the model made, fired or not — because the measurement question is
about the model's calibration across all ~64k evaluations, not just the ~1% that became bets.

## Join key: `ticker`, not the raw `(player_id, game_date, threshold)` tuple

The task brief specified `(player_id, game_date, threshold)` as the join key but explicitly asked
that its uniqueness be verified against real data rather than assumed. It is not unique, for a
reason discovered during this task: **GG-164** — the cycle log's own `game_date` field is
stamped from UTC wall-clock date-at-write-time, not the game's true date, and is wrong on
**45,217 / 64,396 rows (70.2%)**.

Verification against the live cycle log (64,396 rows, 2,021 distinct tickers), counting distinct
tickers per candidate key (not raw row counts, which trivially collide since one ticker generates
many cycle rows over a game):

| Key | Unique keys | Keys mapping to >1 distinct ticker |
|---|---|---|
| Raw `(player_id, game_date, threshold)` | 2,132 | **194** |
| Ticker-derived `(player_id, game_date, threshold)` | 2,017 | **4** |

Deriving `game_date` from the ticker's own embedded date token instead of trusting the row's
`game_date` field collapses 194 collisions down to 4. Those remaining 4 are inspected directly and
are all genuine doubleheaders — same player, same date, two distinct tickers differentiated by the
ticker's embedded start time and `G1`/`G2` suffix, e.g.:

```
KXMLBHIT-26JUL171335TBBOSG1-TBJCAMINERO13-2   (game 1, 13:35 start)
KXMLBHIT-26JUL171910TBBOSG2-TBJCAMINERO13-2   (game 2, 19:10 start)
```

**Conclusion: `ticker` alone is the correct join key.** It is 100% regex-parseable
(`^KXMLBHIT-(\d{2})([A-Z]{3})(\d{2})(\d{4})`, format `KXMLBHIT-{YY}{MON}{DD}{HHMM}{AWAYTEAM}
{HOMETEAM}[G{n}]-{TEAM}{PLAYERCODE}-{THRESHOLD}`), uniquely encodes date+time+teams+player+
threshold, and naturally disambiguates doubleheaders where the raw tuple cannot. The store keys
on `ticker` and stores the ticker-derived `game_date` (not the raw field) as the date passed to
resolution. This also directly informs a live incident: T-416's diagnosis of 22 stuck T1/T2
positions found that most were permanently unresolvable specifically because "the player having
94-112 other splits that season" still had no split matching the *assumed* date — the same
date-mislabeling failure mode this store's ticker-derived date avoids by construction.

This finding is folded into the existing **GG-164** registration (cycle-log `game_date`
mislabeling) rather than opened as a new gap, since it is the same root cause discovered from a
second angle.

## Normalization: resolve per ticker, not per cycle-log row

64,396 cycle-log rows fold into 2,021 distinct tickers (a ticker accumulates one row per
evaluation cycle across the game, roughly 32 rows/ticker on average). The outcome for a given
ticker (did the player reach `threshold` hits in that specific game) does not change across those
32 rows — it is a property of the ticker, not the cycle. Resolving once per ticker and mapping
that result back onto every row sharing the ticker is both correct (the outcome is invariant
across cycles) and avoids ~32x redundant API calls against MLB Stats API / ESPN.

## Store schema

`logs/t4_mlb_outcome_store.jsonl` (gitignored — covered by the existing blanket `logs/` rule in
`.gitignore`, no new entry needed), one JSON object per line, keyed by `ticker`:

```json
{
  "ticker": "KXMLBHIT-26AUG011610MINSEA-SEACRALEIGH29-1",
  "player_id": 663728,
  "player_name": "Cal Raleigh",
  "threshold": 1,
  "game_date": "2026-08-01",
  "date_source": "ticker",
  "n_cycle_rows": 1,
  "has_forecast": false,
  "resolved": true,
  "actual_hits": 0.0,
  "resolution_source": "MLB_R",
  "attempt_count": 1,
  "first_attempted_at": "2026-08-06T00:01:08Z",
  "last_attempted_at": "2026-08-06T00:01:08Z",
  "attempts": [
    {"source": "MLB_R", "at": "2026-08-06T00:01:08Z", "result": 0.0, "detail": null}
  ]
}
```

Fields:
- `date_source`: `"ticker"` (the normal case) or `"raw_fallback"` if a ticker fails to
  regex-parse (none observed in the live data; the fallback exists so a future malformed ticker
  degrades gracefully instead of crashing the backfill).
- `has_forecast`: true if any cycle-log row for this ticker carried `p_t4` (i.e. was not a
  `vig_skip` row). A ticker can have both `p_t4` rows and `vig_skip` rows across its cycle
  history as the live vig crosses the skip threshold during the game — `has_forecast` is `True`
  if *any* row scored.
- `resolved` / `actual_hits` / `resolution_source`: the outcome, once found, and which of the
  three sources found it (`MLB_R`, `MLB_P`, `ESPN`).
- `attempts`: **first-class failure data (requirement 4).** Every source tried, every run, is
  recorded — including on eventual success (the winning attempt is the last entry) and on total
  failure (all three sources recorded as tried, each with its result and, when available, a
  captured-stderr `detail` string, e.g. an HTTP 403). This directly avoids reproducing T-416's
  failure mode: "T-416's 22 stuck positions exist precisely because a resolution failure had
  nowhere visible to go." Here, an unresolved ticker's exact resolution history is fully visible
  in the store itself, not silently absent.

`_fetch_mlb_hits` and `_espn_fetch_hits` are called directly (not the opaque `fetch_actual_hits()`
wrapper) specifically to capture this per-source provenance — `fetch_actual_hits()` returns only
a single `float | None` with no visibility into which source produced it or what the other two
returned, which is insufficient for first-class failure data.

## Idempotency / resumability (requirement 3)

- Tickers already `resolved: true` in the store are skipped entirely on every subsequent run — no
  re-fetch, verified by test (`test_already_resolved_ticker_is_never_refetched`).
- Unresolved tickers are retried on every run; each retry appends new entries to `attempts` (does
  not overwrite history) and refreshes `attempt_count`/`last_attempted_at`.
- The store is written atomically (temp file + `os.replace`) and checkpointed every 25 tickers
  processed, not only at the end — an interrupted backfill loses at most 25 tickers' worth of
  work, not the whole run.
- `--pull` optionally re-syncs the cycle log from the VPS first (`scp`, same pattern as
  `scripts/build_t4_resolved_ledger.py`'s `pull_vps_cache()`); otherwise the script reads the
  local cache path, allowing a daily cron-style re-run without re-fetching the whole cycle log
  from the VPS every time.

## Operational note: run locally, not on the VPS

GG-084 documented an MLB Stats API block specific to the VPS's DigitalOcean datacenter IP. This
session confirmed the primary MLB Stats API resolution path (`_fetch_mlb_hits`) returns clean
200s from the local development network, unaffected by that block. The backfill was run locally
against a pulled copy of the cycle log for this reason — running it via VPS SSH would materially
undercount resolvable tickers on the primary path.

Separately, this session extended **GG-163** (ESPN 403s any request carrying
`User-Agent: Mozilla/5.0` on `site.api.espn.com`'s scoreboard endpoint, reproduced from a network
entirely outside the VPS — not IP-specific) with a second finding: `run_resolve_mlb.py`'s own
ESPN-fallback path (`_espn_game_ids_for_date`/`_espn_fetch_hits`) uses the identical hardcoded
`_ESPN_HEADERS = {"User-Agent": "Mozilla/5.0"}` against the identical endpoint — a second,
independent consumer of the same broken UA/endpoint combination. This means the ESPN fallback
leg of resolution is expected to fail broadly regardless of where the backfill runs, until GG-163
is fixed at the header level (out of scope for T-421's hard scope fence — `run_resolve_mlb.py`
is read-only here).

## Coverage report

Full backfill run against the live cycle log (frozen snapshot pulled 2026-08-05, per the GG-163
freeze noted above):

| Metric | Count |
|---|---|
| Cycle-log rows (forecast leg, all evaluations) | 64,396 |
| Distinct tickers (unit of resolution) | 2,021 |
| Resolved | **1,943 (96.1%)** |
| Unresolved | **78 (3.9%)** |

**All 78 unresolved tickers fail for the same combined reason**, verified by inspecting every
unresolved record's `attempts` list directly rather than assuming:

1. `MLB_R` and `MLB_P` (MLB Stats API, regular season then postseason `gameType`) both return
   `None` cleanly — no exception, no captured stderr, i.e. the API responds successfully but has
   no matching game log for that `(player_id, game_date)` pair. This is not an API failure; it is
   a genuine data gap, consistent with T-416's parallel diagnosis that a subset of players have no
   stats-API split matching their *assumed* date (postponements, doubleheader date-shifts, or
   other real-world schedule irregularities the ticker's embedded date doesn't capture).
2. The `ESPN` fallback — which exists specifically to rescue MLB Stats API misses — cannot rescue
   any of these 78, because it fails independently and universally: every ESPN attempt returns
   `HTTPError: 403 Client Error: Forbidden` from `site.api.espn.com`'s scoreboard endpoint. This is
   **GG-163** (the `User-Agent: Mozilla/5.0` header `run_resolve_mlb.py` sends is blocked
   server-side, confirmed from a network outside the VPS, so it is not IP-specific and not fixable
   by where this backfill runs).

Net effect: **the true "genuinely unresolvable" rate cannot yet be measured**, because the rescue
path (ESPN) is currently 0-for-78, not because those 78 games/players lack any recoverable data.
Once GG-163 is fixed (header-level fix to `_ESPN_HEADERS` in `run_resolve_mlb.py` — out of scope
for T-421's hard scope fence, which keeps that file read-only), re-running this backfill
(idempotent — only the 78 unresolved tickers will be retried) will either resolve some fraction of
the 78 via ESPN or confirm they are genuinely unrecoverable via any of the three sources. That
re-run is the natural follow-up task, not part of T-421's scope.

96.1% first-pass coverage against real, uncurated production data — with a known, already-diagnosed
cause for the remaining gap and no silent drops (all 78 have full attempt provenance in the store)
— is the intended outcome of this store's design.

## Files

- `scripts/build_t4_outcome_store.py` — the join/backfill script.
- `tests/test_build_t4_outcome_store.py` — 19 unit tests (ticker date parsing, grouping,
  store round-trip/atomicity, resolution fallback order, idempotency), all mocked, no network
  calls.
- `logs/t4_mlb_outcome_store.jsonl` — the store (gitignored).
- `logs/.vps_t4_mlb_cycle_log_cache.jsonl` — pulled snapshot of the live cycle log used for this
  backfill (gitignored, `logs/` blanket rule).

## Cleanup

`05_RESEARCH_EXPERIMENTS/T421_HANDOFF_PARKED_2026-08-05.md`, an earlier mid-session parking
checkpoint written before GG-163/GG-164 were registered and before the join-key verification
above was done, is removed in this same change set — it described "no code written" and
"join-key uniqueness not yet checked" as open, which this document supersedes. Removing it rather
than leaving it avoids a future session reading it at face value.
