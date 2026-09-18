# Runbook — First Real NFL T1 Settlement (2026-09-21)

**Written:** 2026-09-18, T-559/GG-291, following a full rehearsal against a disposable copy of the
real 42-position portfolio (see `DECISION_LOG.md` 2026-09-18 and `GOVERNANCE_GAP_LOG.md` GG-291,
GG-257, GG-266, GG-287 for full detail). This is the first time NFL T1 will ever settle a real
position — 18 of the 42 real open positions have `game_date=2026-09-20`, the earliest date in the
cohort. Nothing before this runbook has run a real settlement; everything below is informed by what
actually broke in rehearsal, not by assumption.

**Updated 2026-09-18, T-562/GG-291 Deliverable 4 (same day, later same session-claim lineage):**
GG-291's fix landed for real between the original rehearsal and this update — both halves, not just
one: `paper_trader.py`'s `open_position()` and both T1 game-market run scripts now stamp
`kalshi_threshold` at write time and refuse to write a settleable position with a null threshold
(Deliverable 2, commit `03acefe`); the real, live 42-position `nfl_moneyline` cohort on the VPS has
been backfilled to `kalshi_threshold=0.0` with a verified backup and a diff proving exactly 42 rows
changed, one field only (Deliverable 3, commit `b36429b`). A **second, independent rehearsal** was
then run this same day against a fresh disposable copy of the now-repaired real file, using synthetic
finals for all 9 games on 2026-09-20 (including a deliberate exact tie) — see "Deliverable-4
re-rehearsal results" below. Step 3 is now a **verification** step, not a pre-flight fix — the defect
is closed, but verify it hasn't regressed before trusting that going into the real run.

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

## 3. Verify the `kalshi_threshold=None` defect (GG-291) is still closed — MANDATORY, pre-flight

**Status as of 2026-09-18 (T-562/GG-291 Deliverables 2-3): CLOSED, both halves.** The original
rehearsal (T-559) found all 42 real open `nfl_moneyline` positions carrying `kalshi_threshold=None`,
which crashes `settle_position()` with `TypeError: '>=' not supported between instances of 'float'
and 'NoneType'` on the first settleable position. Both fixes have since landed for real, not just in
rehearsal:

- **Write path (Deliverable 2, commit `03acefe`):** `paper_trader.py`'s `open_position()` and both
  T1 game-market run scripts (`run_t1_nfl_game_market.py`, `nfl_exp027_adapter.py`) now derive and
  stamp `kalshi_threshold` at open time per market type, and refuse to write a settleable position
  with an undeterminable threshold rather than silently defaulting to `None`. Covered by tests
  (51 passed).
- **Backfill (Deliverable 3, commit `b36429b`):** the real, live 42-position `nfl_moneyline` cohort
  on the VPS was backfilled to `kalshi_threshold=0.0` (documented in `game_market_settlement.py`'s
  own docstring as correct — "a moneyline is a spread at zero"), with a verified backup and a
  before/after diff proving exactly 42 rows changed, exactly one substantive field
  (`kalshi_threshold`) plus provenance (`repaired_at`/`repair_ref`) — nothing else moved.

This step is now **verification that the fix has not regressed**, not a pre-flight repair:

1. Read the real portfolio file and confirm every open `nfl_moneyline` position still has a
   non-null `kalshi_threshold` (it should — the write path can no longer produce a null one, and the
   backfill is a one-time, already-applied correction). Check `GOVERNANCE_GAP_LOG.md` GG-291's
   status first in case something has changed between 2026-09-18 and the real run.
2. If a null threshold is found anyway (e.g. from a position opened by an unpatched code path, or a
   new market type this fix didn't cover), stop and treat it as a **new** defect — register a fresh
   GG-NNN, do not silently re-run the GG-291 backfill script against a changed population without
   re-verifying its exact-count guard first (it aborts unless the match count equals its expected
   value, by design — do not raise that guard to "make it pass").
3. Do not hand-construct a new one-off threshold patch for the real file — if a regression is found,
   fix the write path first (per the GG-291 precedent), then repair data with the same
   backup-verify-diff discipline Deliverable 3 used.

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
| `kalshi_threshold=None` crashes `settle_position()` | Deliverable 3, first `--apply` attempt | Step 3 — verified CLOSED (write path fixed + real backfill applied, T-562/GG-291 Deliverables 2-3); re-verify, don't re-fix, unless a regression is found |
| Moneyline exact tie must be refused, not guessed | Deliverable 3, deliberate CIN/HOU synthetic tie; re-confirmed Deliverable 4, deliberate PHI/TEN synthetic tie against the repaired file | Step 5 — dry-run must show `SettlementAmbiguityError` on any real tie, matching GG-257 |
| Re-running settlement must not double-settle or corrupt state | Deliverable 3, two-run sha256 idempotency check; re-confirmed Deliverable 4 against the repaired file (byte-identical sha256, `Settled this run: 0` on rerun) | Step 8 — mandatory re-run and hash/count check before declaring done |
| GG-266's Mac/ESPN reachability claim did not reproduce in this session's real network calls | Deliverable 2, not-yet-final dry run | Step 1 — run on VPS as designed regardless; treat a real VPS-side reproduction (or non-reproduction) as new evidence for GG-266, not something this runbook resolves |
| A crashed run still writes a pre-attempt backup, and that backup is trustworthy | Deliverable 3, crash reproduction + `diff` check | Step 4 — still take an independent manual backup; don't rely solely on the automatic one on the first-ever real run |

## Deliverable-4 re-rehearsal results (2026-09-18, T-562/GG-291, same-day follow-on)

After Deliverables 2-3 landed for real (write-path fix + live 42-row backfill, both committed and
pushed), a **second, independent rehearsal** was run against a fresh disposable copy of the
now-repaired real portfolio snapshot, exercising the unmodified `apply_resolved_nfl_game_markets.py`
resolver end-to-end with synthetic finals (no network calls) via
`unittest.mock.patch.object(resolver, "fetch_nfl_final_score", ...)` — the same mocking pattern this
repo's own `tests/test_apply_resolved_nfl_game_markets.py` uses.

**Synthetic slate — all 9 games on 2026-09-20, including one deliberate exact tie (PHI @ TEN,
24-24):**

| Result | Count | Detail |
|---|---|---|
| Dry run (no `--apply`) | 0 settled, file hash unchanged | Confirms dry run makes no writes |
| `--apply`, first run | 16 settled, 2 refused, 24 unresolved | 14 LOSS at `pnl=-1.0000`, 2 WIN at `pnl=+1.2727` (CAR/ATL game) — every one of the 18 positions' outcome and P&L cross-checked line-by-line against an independent hand re-derivation of `settle_position()`'s formula computed *before* running the resolver; 0 mismatches |
| Tie refusal | 2/2 refused | Both `POS-1C334B5A21` (TEN, YES) and `POS-91144F65ED` (PHI, NO) raised `SettlementAmbiguityError` and remained `status: "OPEN"` — not settled, matching GG-257 |
| Later-dated positions (09-21/24/27/28) | 24/24 still OPEN | Fake `fetch_nfl_final_score` returns `None` for any date other than 2026-09-20, correctly leaving all not-yet-final positions untouched |
| `--apply`, second run (idempotency) | 0 settled | `Settled this run: 0`; both refused positions still refused/still OPEN; portfolio file sha256 byte-identical before and after the second run |

**Precondition asserted and confirmed before running any of the above:** all 42 positions in the
repaired snapshot have `kalshi_threshold == 0.0` (none `None`) — i.e. this rehearsal ran against the
*fixed* population, proving the write-path fix and the backfill work together end-to-end, not just
individually.

**Conclusion: no crash, no double-settlement, no silent tie-guessing, byte-identical idempotency.**
Deliverable 4's rehearsal script and its scratch working files are disposable session artifacts (same
status as T-559's `patch_threshold.py`/`hand_verify.py`) and are not committed to the repo.

Related IDs: GG-291, GG-287, GG-257, GG-266, GG-294, T-556, T-559, T-562.
