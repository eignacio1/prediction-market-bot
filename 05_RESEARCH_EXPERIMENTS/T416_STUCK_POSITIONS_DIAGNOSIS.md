# T-416 — Diagnosis: 22 Stuck (aged_open) T1/T2 Positions

**Date:** 2026-08-05 | **Task:** T-418 | **Book:** T1/MAIN (`paper_portfolio_mlb.json`)

## Prior finding read first, per instruction

`10_INFRA_OPERATIONS/OPS_HEALTH_AND_DEPTH_STATUS_2026-08-04.md` § "Task 1 — T1/MAIN portfolio
cache staleness verdict" was read before any new investigation. It correctly establishes: all 22
positions predate ADR-0048's kelly=0 zeroing (`game_date` 2026-07-01 → 2026-07-29), are all
already tagged `aged_open: True`, GG-048's `zero_resolved_with_eligible_positions` alarm fires
correctly and daily, and capital stays deployed (`mark_aged_open()` does not credit it back).

**This diagnosis confirms that structural picture but corrects two of its specific claims,**
both with direct evidence gathered this session (SSH access to the VPS, which that document did
not have per its own Task-4 note about SSH gaps — see GG-154).

## Confirming the code path independently

`mark_aged_open()` (`paper_trader.py:935-969`) is idempotent — `pos.get("aged_open") is True` →
early-return at line 963-964 without a second `self._save()`. Confirmed directly. **But** the
prior document's conclusion that this idempotency is *why* the file never updates again is only
half right. `run_resolve_mlb.py`'s main loop (`run_resolve_mlb.py:411-433`) builds its `pending`
list purely from `game_date < today` — **it is not filtered by `aged_open` status.**
`fetch_actual_hits()` is called fresh, every position, every day, regardless of prior aging.
If it ever succeeds, `settle_position()` fires and *does* write the file (a real state change,
not a no-op). The reason `last_updated` is frozen at 2026-07-31T06:35:06Z is not "the code
stopped trying" — retries genuinely happen daily — it is that **the retries keep failing.** Why
they keep failing is the real question, and it splits into two distinct mechanisms below.

## Root cause: not one uniform "standing data-resolution failure" — two separate mechanisms

The prior document characterized this as "not an API-outage signal; a standing data-resolution
failure specific to these 22." Direct testing this session contradicts that framing for at least
part of the set:

**Mechanism 1 — genuine data absence (majority, ~9 of 10 unique players).** Querying the live
MLB Stats API `gameLog` endpoint directly (via the VPS's own venv/Python/requests version,
outside the cron window) for every stuck player's specific `game_date`: only Julio Rodríguez
(3 of 4 dates) returned a split for the requested date. Every other player/date pair — CJ
Abrams, Mike Trout, Nick Kurtz, Bobby Witt Jr., Gunnar Henderson, Ketel Marte, Steven Kwan,
José Ramírez, Christian Walker — has **no split at all** for the specific stuck date, despite
the player having 94-112 other splits that season. This is consistent with doubleheader
date-shifts, postponements, or off-days not matching the market ticker's assumed date. This part
of the prior document's framing holds: for this majority, it is a real, permanent data gap that
no amount of retrying fixes — postseason lookup and ESPN fallback were both already exhausted
per the prior document, and this session's direct API reads corroborate the regular-season leg
independently.

**Mechanism 2 — API-side 406 unreliability correlated with the cron's execution window
(minority but real, and this is new — not in the prior document).** `resolve_mlb_cron.log`
shows 8,345 "giving up" 406 failures against 3,921 successful resolutions across its history —
a ~68% failure rate on individual fetch attempts, most visible for Julio Rodríguez specifically:
even his *first* attempt of a run (full 4-try backoff, not yet circuit-breaker-throttled) failed
with 406 on every logged occasion. Yet identical requests — same player_id, same date, same
query params, same venv/Python/requests version (2.34.2) — return clean 200s with valid data
when run interactively, outside the 06:30 UTC cron window, right now. This was tested directly
against the exact venv binary cron uses (`/opt/prediction-market-bot/venv/bin/python`), ruling
out an environment/dependency mismatch as the explanation. The pattern (near-universal failure
within the batch run, reliable success outside it) points at a time-window-correlated
degradation in MLB Stats API's response to this endpoint, not a per-player defect. This directly
explains why 3 of Julio's 4 dates are recoverable *right now* by direct query but have never
once resolved via 5+ weeks of daily cron retries — the retry always lands in the same
degraded window.

**Conclusion on "one cause or 22":** two shared causes, not 22 independent ones and not one
uniform cause either. ~9 of 10 players/dates: Mechanism 1 (permanent data-absence — not
recoverable without a terminal state or a different resolution source). Julio Rodríguez's 3 of
4: Mechanism 2 (API-window unreliability — plausibly recoverable if resolution is ever attempted
outside the 06:30 UTC window). No evidence supports a player-ID mapping defect — direct identity
lookup (`/api/v1/people/677594`, via `requests`, not curl — an earlier curl-based probe this
session gave a false-negative 406 from unquoted-URL shell splitting) confirms 677594 is genuinely
Julio Rodríguez.

## Capital quantification

- Total `size_usd` locked across the 22 open positions: **$194.24**.
- Reconciliation: `$1,000.00 initial + (-$121.85 realized P&L) - $194.24 (locked) = $683.91`,
  matching the reported `bankroll_usd` exactly. **Arithmetically self-consistent — this is not a
  bug.**
- **Economically, the figure is stale.** All 22 positions' games resolved between 2026-07-01 and
  2026-07-29; today is 2026-08-04. Treating $194.24 as "at risk" 6-34 days after the underlying
  games ended is not meaningful — it is dead capital sitting in a formula that has no terminal
  state for it. The reported $683.91 bankroll is arithmetically correct and economically
  misleading in the same breath.
- $194.24 is 19.4% of the $1,000 initial T1/MAIN book, and ~3.99% of all-time T1 staked capital
  ($4,678.96 across 463 closed positions) — small relative to lifetime volume, but large
  relative to the *current* live book, which is otherwise idle under ADR-0048's kelly=0.

## Recommendation

**Register GG-161: yes.** Reasoning: this is a governance-log-worthy finding distinct from what
`OPS_HEALTH_AND_DEPTH_STATUS_2026-08-04.md` already recorded — it identifies a second, previously
undocumented root-cause mechanism (cron-window-correlated API unreliability, Mechanism 2) that
the existing document's framing explicitly ruled out ("not an API-outage signal"), and it should
be tracked separately from that document's Task 1 finding so the correction is discoverable on
its own. Scope fence for this session is memos-only — GG-161 is registered as a finding, not
paired with a code fix.

**Terminal state: yes, needed, and this is the more important of the two recommendations.**
`aged_open` today is an indefinite limbo state, not a terminal one — capital never returns
regardless of how permanent Mechanism 1's data gap is. A defensible design (not committed to
code this session, per scope fence): after some ceiling past the existing 48h grace (e.g. 14-30
days — long enough that Mechanism 2's window-correlated failures should eventually clear on a
lucky run, short enough not to hold capital indefinitely), a position that has never resolved
via any of the three sources transitions to a genuinely terminal state — e.g. `unresolvable`,
credited back at $0 P&L or excluded from `bankroll_usd`'s open-cost sum entirely — rather than
remaining in `open_positions` forever. This would not have changed Julio's 3 recoverable
positions (still worth attempting resolution outside the cron's window before declaring them
terminal) but would resolve the ~9-player Mechanism-1 majority, which is not going to self-heal.

## T-422 update (2026-08-05/06): Mechanism 2 corrected and superseded; out-of-band repair executed; 5/22 resolved live

This session (T-422) set out to finish this diagnosis and build an out-of-band repair. Direct
testing found T-418's Mechanism 2 framing above — "cron-window-correlated API unreliability" —
was itself an incomplete diagnosis. The real mechanism, established through three rounds of
direct A/B testing against the live MLB Stats API from both the VPS and an unblocked network:

**2a. `_is_game_final()`'s query shape, not the primary stats call, was the actual blocker for
Julio Rodríguez's 3 recoverable dates.** `run_resolve_mlb.py:143-164` confirms game finality via
`GET /api/v1/schedule?gamePk={game_pk}`. This exact query shape 406s deterministically (5/5) from
the VPS's datacenter IP. The equivalent query `GET /api/v1/schedule?sportId=1&date={date}` (same
endpoint, different param shape) returns 200 and correctly reports `"Final"` for the same game —
confirmed against both the VPS and a local (non-VPS) network. `_is_game_final()` catches all
exceptions and returns `False` on any failure, so this 406 was silently indistinguishable from
"game not final yet" — the exact mechanism masking the bug. The primary `gameLog` stats call
itself (the thing T-418 flagged as failing ~68% of the time in a window-correlated pattern) was
in fact succeeding for Julio's dates when tested in isolation; it was the finality sub-call that
was actually blocking settlement.

**2b. Not time-of-day-correlated — request-volume-correlated, and this is GG-084, not a new
mechanism.** Running a full batch of 22 sequential resolution attempts from the VPS (even after
fixing 2a's query shape) degraded the *primary* `gameLog` call itself to 100% 406 partway through
the run — reproducing GG-084's already-documented "escalating Fastly-CDN block that worsens over
the course of a run" verbatim. This is the real explanation for T-418's ~68% cron-window failure
rate: the cron always runs as one batch of ~20+ sequential requests from the same datacenter IP,
so it always trips the same escalating block partway through, which *looks* time-of-day-correlated
(it only ever runs at 06:30 UTC) but is actually volume/session-correlated to any batch run from
that IP, regardless of when it runs. T-418's "run interactively outside the cron window" successes
were not evidence of a time-window effect — they were single, isolated requests, which never
accumulate enough volume in one session to trip GG-084's escalation.

**2c. Repair architecture: separate fetch (network-bound) from apply (pure local I/O).** Built
`scripts/repair_stuck_mlb_positions.py` (single-machine tool, valid if ever run from a network
not subject to GG-084, per its docstring) and a two-phase split actually used to produce the
result below: a fetch step run from an unblocked, non-VPS network (scratchpad-only
`fetch_hits_local.py`, not checked into the repo — see the caveat this creates in
`03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-161's amendment), producing a results JSON; and
`scripts/apply_resolved_hits.py`, run ON the VPS, which makes zero outbound HTTP calls and applies
results purely via `PaperTrader.settle_position()`.

**Result: 5 of 22 resolved and settled live** (all 4 Julio Rodríguez dates + 1 José Ramírez date,
`2026-07-29`, which also had a real split once the finality-check bug was routed around). Net P&L
booked: **+$15.84**. Portfolio backed up to
`paper_portfolio_mlb.pre_repair_20260806T000501Z.json` before the write. Post-repair state:
`bankroll_usd` $683.91 → $733.7471; `open_positions` 22 → 17 aged_open; `closed_positions` 463 →
468; `total_realized_pnl` -$121.85 → -$106.0099; `daily_net_pnl` +$15.84 (matches the 5
settlements exactly).

**The remaining 17 are now confirmed, not just presumed, permanently unresolvable (Mechanism 1)**
— re-fetched from the unblocked network specifically to rule out GG-084 as a confound for the
other 9 players' dates too, and all 17 returned `reason=no_split_for_date` across MLB-R, MLB-P,
and ESPN. T-418's original Mechanism 1 majority (~9 of 10 players) holds exactly as diagnosed;
this session adds the confirmation that it was tested clean of the IP-block confound. See ADR-0051
(DRAFT) for a proposed terminal state for this remaining set.
