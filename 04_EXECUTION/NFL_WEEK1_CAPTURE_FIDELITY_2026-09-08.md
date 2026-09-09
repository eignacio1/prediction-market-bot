# NFL Week 1 Capture-Fidelity Audit — 2026-09-08

**Task:** T-528. **Deadline:** before 2026-09-09 kickoff (2026-09-10T03:20:00Z UTC, the actual opener — see Deliverable 4). **Scope:** verify capture fidelity only. Trading path, parser, `kelly_fraction`, and `--depth-sample-per-family` are explicitly out of scope for changes under this task.

## Verdict

**GO — no new capture holes found.** The one real gap this audit exists to check (price-archive coverage for Week 1) was already found and closed by a prior session (GG-245/T-521, RESOLVED 2026-09-07) with rigorous, evidence-backed verification; this audit independently re-derived Deliverables 3 and 4 from scratch (not by trusting GG-245's writeup) and reached the same conclusion by an independent path. One new, lower-severity finding is registered: NFL price-archive cron lines carry no `--depth-sample-per-family` flag at all (0, not the MLB precedent of 2), which is a **deliberate** T-521 scope decision, not an oversight — but it means zero NFL orderbook-depth history accumulates during Week 1, and that history is exactly as un-backfillable as price history once the week passes. See GG-259 (new, this session).

`deploy/cron.conf` was **not changed** by this session. No capture hole was found that the narrow additive-authorization clause covers, and depth-sample changes are explicitly out of scope for this task regardless.

---

## Deliverable 1 — Does the archiver route through the parser?

**No. Confirmed by direct read — raw payload dicts only, parser never called.**

- `scripts/archive_market_prices.py:142` — `ok, resp = client._get("/markets", params=params)`. `_get` is the raw HTTP call.
- `src/prediction_market_bot/c5_execution/kalshi_client.py:459` — `_get()` returns `True, r.json()`: unparsed JSON, straight pass-through.
- `scripts/archive_market_prices.py:119-130` (`_snapshot()`) builds the archived row directly from raw dict keys via the explicit `SNAPSHOT_FIELDS` tuple (`archive_market_prices.py:87-103`) — e.g. `market["yes_bid_dollars"]` read straight off the raw record, renamed to `yes_bid` at write time.
- `_parse_market()` is a separate method in `kalshi_client.py`; grepped across `archive_market_prices.py` in full — zero call sites. The archiver never imports or invokes it.

Parser changes (GG-252, T-526) cannot affect what has already been archived or what the archiver captures going forward. This was the one condition under which the task instructed an immediate STOP — it does not apply.

## Deliverable 2 — Per-series row counts, last 7 days

Queried live from `exp_output/PRICE_ARCHIVE/prices_2026-09-0{2..8}.jsonl` on the VPS (fresh `Counter` over `series_ticker`, this session — not carried over from any prior session's numbers).

| Date | Day | MLB total | NFL total | KXNFLGAME | KXNFLSPREAD | KXNFLTOTAL | KXNFLTEAMTOTAL |
|---|---|---:|---:|---:|---:|---:|---:|
| 2026-09-02 | Wed | 35,791 | 0 | — | — | — | — |
| 2026-09-03 | Thu | 26,552 | 0 | — | — | — | — |
| 2026-09-04 | Fri | 36,562 | 0 | — | — | — | — |
| 2026-09-05 | Sat | — | 827 (1 fire) | 64 | 404 | 304 | 55 |
| 2026-09-06 | Sun | — | 18,194 | 1,408 | 8,888 | 6,688 | 1,210 |
| 2026-09-07 | Mon | — | 8,924 | 768 | 4,848 | 3,648 | 660 |
| 2026-09-08 | Tue | — | 8,924 | 768 | 4,848 | 3,648 | 660 |

(MLB total column left blank for 09-05 onward — MLB continues unaffected per GG-245's own verification; this table isolates the NFL numbers this task is scoped to.)

All four configured series show healthy, non-zero, growing counts from first deploy (09-05) onward. Two observations worth stating explicitly rather than leaving unexplained:

- **09-05 (827 total, exactly matching live open-market counts 64+404+304+55=827):** this was the single deploy-day fire before the cron schedule was in steady state — one snapshot, one row per open market, no duplication. Expected, not a defect.
- **09-07 and 09-08 are row-for-row identical (768/4,848/3,648/660).** Both are non-Sunday off-days firing under the Mon 0-3Z and Tue 0-3Z windows respectively, each of which fires a fixed number of times (`5,25,45` across 4 hours = 12 fires). Row count = fires × open-market count per series; with the market roster unchanged between two consecutive off-nights, 12 fires × the same 64/404/304/55 markets/fire produces identical totals by construction. This is the expected shape of the fixed-window design, not an anomaly.

## Deliverable 3 — Is a 5th open KXNFL series being missed?

**No fifth full-game series exists.** Independently re-verified this session (not inherited from GG-245) by sweeping the complete `/series?category=Sports` KXNFL-filtered listing gathered live from Kalshi (~330 distinct `KXNFL*` series tickers). Excluding the four configured series (KXNFLGAME, KXNFLSPREAD, KXNFLTOTAL, KXNFLTEAMTOTAL), every remaining series falls into one of: quarter/half-line splits, player props, season awards, draft props, division/conference futures, per-team exact-win-total futures, fantasy football, or same-game-parlay/prepack combo products (`KXNFLPREPACK*`). None of these are a "standard betting mechanism" (moneyline/spread/total/team-total) full-game series in the sense the four configured series already cover.

This corroborates GG-245's own spot-check finding via a full-taxonomy sweep rather than a narrower check, and reaches the same conclusion: the four configured series are complete for this deliverable's definition of coverage.

## Deliverable 4 — Does the cron schedule cover every Week 1 kickoff?

**Yes — independently re-verified live this session.** Queried Kalshi live for all 64 open `KXNFLGAME` markets (32 events) and extracted `occurrence_datetime` (the correct kickoff field — not `close_time`/`expiration_time`, which are later settlement deadlines). Mapped every kickoff to UTC day-of-week/hour against the 5 configured cron windows:

| Cron window | Cron spec | Covers |
|---|---|---|
| Sun 17-23Z | `5,25,45 17-23 * * 0` | 09-13 20:00Z, 09-13 23:25Z, 09-20 20:00Z, 09-20 23:05Z, 09-20 23:25Z |
| Mon 0-3Z | `5,25,45 0-3 * * 1` | 09-14 03:20Z, 09-21 03:20Z |
| Tue 0-3Z | `5,25,45 0-3 * * 2` | 09-15 03:15Z, 09-22 03:15Z |
| Thu 0-3Z | `5,25,45 0-3 * * 4` | **09-10 03:20Z — the 2026 opener** (NE @ SEA, Wed-ET-origin kickoff) |
| Fri 0-3Z | `5,25,45 0-3 * * 5` | 09-11 03:35Z, 09-18 03:15Z |

**32/32 events fall inside a scheduled window. Zero coverage gaps found**, including the non-obvious opener (Thursday UTC, not the generically-assumed Friday) that GG-245 specifically added the 5th window to catch. This is a second, independent derivation of the same 32/0 result GG-245 recorded on 2026-09-07 — not a re-citation of it.

## Deliverable 5 — Is depth sampling adequate?

**Current state: NFL depth sampling is 0, not 2.** Direct re-read of `deploy/cron.conf:419-423` confirms none of the 5 NFL cron lines carry `--depth-sample-per-family` at all (the flag defaults to `0`/disabled when absent — `archive_market_prices.py:217-220`). This is documented in the cron.conf comment block (lines 405-407) as a **deliberate** choice by T-521 ("no depth sampling (kept out deliberately to minimize added volume)"), not an oversight — distinct from MLB, which runs `--depth-sample-per-family 2` on its price-archive lines.

**Is 0 adequate?** No, on the same "un-backfillable" logic that justifies this entire task. Depth is not derivable from price archives after the fact — `_sample_depth()` requires a live orderbook fetch (`/markets/{ticker}/orderbook`) at capture time; there is no way to reconstruct depth history for Week 1 once Week 1 has passed. GG-155/T-411 already established depth is highly time-varying (14x swings in 14 minutes on one series, 67x between consecutive TEAM_TOTAL reads) — a single retroactive measurement in Week 2 cannot substitute for a Week 1 time series, and CLAUDE.md's own standing instruction is that any sizing decision must consult a *live* depth measurement, which requires the history to exist.

**What's permanently lost if this stays at 0 through Week 1:** the entire opening week of NFL orderbook-depth observations across all four families (GAME 64 / SPREAD 404 / TOTAL 304 / TEAMTOTAL 55 open markets) — the exact data MLB's `--depth-sample-per-family 2` has been accumulating toward its "200+ observations/family" target since 2026-08-01. NFL would start that clock at least a week later than it needed to, with no way to backfill the delta. This matters less than price-capture urgency *today* because NFL live trading is not yet active (T4 ARITH/FLOW scaffolding just landed; T1 game-market run script is still gated on GG-255) — no sizing decision is currently blocked on missing NFL depth data. But the loss is still permanent, and the module's own design goal (a week-scale time series building toward a statistically usable sample) is set back by exactly the number of weeks this stays disabled.

**Recommendation: 2 per family**, mirroring the MLB precedent exactly. Rationale: NFL has 4 families vs. MLB's 10, so even at the same per-family sample size the added request volume is proportionally smaller (4×2=8 additional orderbook fetches per fire vs. MLB's 10×2=20); the balanced round-robin sampler (`_balanced_sample`, shared code path with MLB, the GG-155 fix) is already wired and requires no new code — enabling this is a flag change on 5 cron lines, not a build. **Not enacted under this deliverable per task instruction** — recommending only, not changing.

---

## cron.conf changes this session

**None.** No capture hole was found on Deliverable 3 or 4 that the narrow additive-authorization clause would license a change for — GG-245 already made the one change this task's mandate would have authorized. The Deliverable 5 finding is a recommendation, explicitly excluded from this task's edit authorization.

## Gaps registered this session

- **GG-259** (new) — NFL price-archive cron lines carry zero `--depth-sample-per-family` sampling; Week 1 NFL orderbook-depth history is being permanently lost while this stays disabled. Severity: MEDIUM (un-backfillable, but no live decision currently depends on it). See `GOVERNANCE_GAP_LOG.md`.

## Gaps cited, not re-registered

- **GG-245** (RESOLVED 2026-09-07, T-521) — the price-capture-coverage gap this task exists to check. Independently re-verified, not re-opened.
- **GG-252** (RESOLVED, T-526) / **GG-253** (PARTIALLY RESOLVED, T-526) — kalshi_client.py NFL parsing / NFL C1 ingestion. Out of this audit's scope; confirmed not conflated with Deliverable 1's parser-independence finding.

---

*T-528. Session worktree `session/20260908T235535Z-nfl-week1-capture-fidelity-audit`.*
