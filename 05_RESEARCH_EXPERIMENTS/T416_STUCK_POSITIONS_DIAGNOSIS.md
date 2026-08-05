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
