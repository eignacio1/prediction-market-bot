# Runbook — First Real NFL T1 Settlement (2026-09-21)

**Written:** 2026-09-18, T-559/GG-291, following a full rehearsal against a disposable copy of the
real 42-position portfolio (see `DECISION_LOG.md` 2026-09-18 and `GOVERNANCE_GAP_LOG.md` GG-291,
GG-257, GG-266, GG-287 for full detail). This is the first time NFL T1 will ever settle a real
position — 18 of the 42 real open positions have `game_date=2026-09-20`, the earliest date in the
cohort. Nothing before this runbook has run a real settlement; everything below is informed by what
actually broke in rehearsal, not by assumption.

**Do not skip step 3.** It is the one rehearsal finding that will crash the real run if unaddressed.

---

## 0. Preconditions

- Confirm today's date is on or after 2026-09-21 and the 09-20 games have actually concluded
  (real final scores exist, not just kickoff having passed).
- Confirm no other session is claiming NFL T1 settlement work right now
  (`04_EXECUTION/SESSION_CLAIMS.md`, last ~24h) — settlement is a single-writer operation against
  the live portfolio file; do not run this concurrently with another session touching the same file.
- Claim your own session ID range before writing anything (Step 0 of `CLAUDE.md`).

## 1. Fetch finals — VPS, not local Mac (GG-266 caveat)

Per GG-266 (OPEN, LOW), the VPS is the documented-correct place to run ESPN fetches. **Rehearsal
caveat, not a resolution:** this session's Deliverable 2 dry run made real ESPN network calls from
this Mac with zero TLS/connection errors, which contradicts GG-266's stated symptom (see GG-266's
2026-09-18 amendment note). Do not treat that as license to run the real settlement from the Mac —
run it on the VPS as designed, and if the VPS run also fails on the exact TLS symptom GG-266
describes, that is new information worth feeding back into GG-266, not a reason to fall back to
running the real settlement locally.

```bash
ssh prediction-market-vps "cd /opt/prediction-market-bot && python3 -c \"
from prediction_market_bot.c1_signal_ingestion.nfl_espn_results import fetch_nfl_final_score
print(fetch_nfl_final_score('2026-09-20', 'KC', 'IND'))
\""
```

Confirm `status='STATUS_FINAL'` and both scores are non-null for every 09-20 game before proceeding.

## 2. Cross-check against a second source

Do not settle on a single source's word. Spot-check at least the highest-exposure positions'
final scores against a second, independently-sourced final score (a sportsbook results page, the
league's own box score, or any source independent of the ESPN endpoint this pipeline reads) before
running `--apply`. This step exists because GG-291's crash was caught in rehearsal precisely by
looking closely at what the resolver was about to do before trusting it blindly — apply the same
scrutiny to the data feeding it.

## 3. Fix the `kalshi_threshold=None` defect (GG-291) — MANDATORY, pre-flight

**This is the one finding from rehearsal that will crash the real run if skipped.** Rehearsal
(GG-291) confirmed all 42 real open `nfl_moneyline` positions carry `kalshi_threshold=None`, and
`settle_position()` crashes with `TypeError: '>=' not supported between instances of 'float' and
'NoneType'` on the first settleable position. Before running `--apply` against the real portfolio:

1. Verify the defect is still present: read the real portfolio file and confirm whether
   `kalshi_threshold` is still `null` on the open `nfl_moneyline` positions (it may have been fixed
   by another session between 2026-09-18 and the real run — check `GOVERNANCE_GAP_LOG.md` GG-291's
   status first).
2. If still present, this must be fixed for real, not patched around — either:
   - backfill `kalshi_threshold=0.0` directly on the real portfolio's 42 `nfl_moneyline` positions
     (the value `game_market_settlement.py`'s own docstring documents as correct for moneyline —
     "a moneyline is a spread at zero"), with a backup taken first and the backup verified via
     `diff` against pre-change state, or
   - fix the open-time write path (wherever `run_t1_nfl_game_market.py` constructs these position
     records) so future positions never write `kalshi_threshold=None` in the first place, or both.
3. **Do not use the rehearsal's copy-only workaround (`patch_threshold.py`) against the real file
   as-is without adapting it into a reviewed, backed-up, verified change** — it was written
   explicitly as a disposable rehearsal expedient, not a production migration script.
4. Re-verify: read the real portfolio again and confirm every open `nfl_moneyline` position has a
   non-null `kalshi_threshold` before proceeding to step 4.

## 4. Backup and verify the backup

`apply_resolved_nfl_game_markets.py`'s `_backup_portfolio()` runs automatically before any
settlement attempt in `--apply` mode (confirmed in rehearsal — it ran even on the crashing run).
Do not rely on this alone:

- Take an independent manual copy of the real portfolio file before running anything, with a
  timestamped name.
- After the automatic backup is written, `diff` it against your manual copy to confirm they match
  and no write happened before the backup was taken.

## 5. Dry-run against a fresh copy first

Do not run `--apply` against the real file on the first attempt of the day. Copy the real
(now `kalshi_threshold`-fixed) portfolio to a scratch location, and run the resolver against the
**copy** first, exactly as this rehearsal did, using the real (not synthetic) final scores fetched
in step 1. Confirm:
- The expected ~18 positions with `game_date=2026-09-20` are the ones attempted.
- No `TypeError` or other crash occurs.
- Any tied game (moneyline exact margin-of-victory == 0) is REFUSED with
  `SettlementAmbiguityError`, not silently settled (GG-257) — rehearsal proved this refusal path
  works correctly; it should behave identically against real data.
- The 24 positions dated 09-21 onward are correctly skipped as not-yet-final.

## 6. Hand-verify before trusting the dry-run output

For each settled position in the dry-run output, independently recompute the expected
outcome/P&L using `settle_position()`'s documented formula (`actual_stat >= threshold` for YES,
inverted for NO; payoff from the position's own `mid`/`vig`/`size`) and confirm it matches the
resolver's output exactly, the way `hand_verify.py` did in rehearsal. Do not skip this because the
dry run "looked clean" — rehearsal's dry run also looked clean right up until the crash on the
unpatched version.

## 7. Settle live, under lock

Only after steps 1-6 pass cleanly against the copy: run `apply_resolved_nfl_game_markets.py
--apply` against the **real** portfolio file. Confirm no other process is writing to the same file
concurrently (single-writer discipline — see Precondition 0). Capture full stdout/stderr to a
timestamped log file, not just the terminal.

## 8. Re-run for idempotency

Immediately after the real settlement run, re-run the exact same `--apply` command against the
now-partially-settled real file. Confirm:
- `Settled this run: 0` (settled positions were moved to `closed_positions` and are not re-attempted).
- Any refused tie positions are still refused, not settled, on the second run.
- The portfolio file's sha256 is identical before and after this second run (rehearsal confirmed
  this exact invariant holds: settled positions are removed from `open_positions`, so nothing new
  can be written on a repeat).

## 9. Report P&L

Report the real total realized P&L delta, the count settled/refused/unresolved, and the exact list
of any refused (ambiguous) positions with their reason, to the operator. Cross-reference against
`GOVERNANCE_GAP_LOG.md` for any new gap this real run surfaces that rehearsal didn't predict — a
real run against real, messier data (bye weeks, postponements, unusual final states) may hit
something synthetic data didn't exercise.

---

## Failure modes hit in rehearsal and how they were resolved here

| Failure mode | Where hit in rehearsal | Resolution in this runbook |
|---|---|---|
| `kalshi_threshold=None` crashes `settle_position()` | Deliverable 3, first `--apply` attempt | Step 3 — mandatory pre-flight fix, not a rehearsal-only patch |
| Moneyline exact tie must be refused, not guessed | Deliverable 3, deliberate CIN/HOU synthetic tie | Step 5 — dry-run must show `SettlementAmbiguityError` on any real tie, matching GG-257 |
| Re-running settlement must not double-settle or corrupt state | Deliverable 3, two-run sha256 idempotency check | Step 8 — mandatory re-run and hash/count check before declaring done |
| GG-266's Mac/ESPN reachability claim did not reproduce in this session's real network calls | Deliverable 2, not-yet-final dry run | Step 1 — run on VPS as designed regardless; treat a real VPS-side reproduction (or non-reproduction) as new evidence for GG-266, not something this runbook resolves |
| A crashed run still writes a pre-attempt backup, and that backup is trustworthy | Deliverable 3, crash reproduction + `diff` check | Step 4 — still take an independent manual backup; don't rely solely on the automatic one on the first-ever real run |

Related IDs: GG-291, GG-287, GG-257, GG-266, T-556, T-559.
