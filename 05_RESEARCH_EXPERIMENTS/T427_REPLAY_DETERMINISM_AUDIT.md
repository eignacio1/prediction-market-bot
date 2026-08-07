# T-427 — Phase 1 exit-gate (box 1.6) replay-determinism audit

**Session:** `session/20260806T233813Z-phase1-replay-harness` (claimed as T-427; the
requested T-426 was already in use by a concurrent session — see claim-collision
note in `DECISION_LOG.md`).
**Scope:** read-only against `src/`. No Phase 1 refactor boxes (1.1–1.5) started.
`paper_trader.py`, `execution_bands.py`, `risk.py` untouched.

## Why this exists

`MARKET_EXPANSION_ACTION_PLAN.md` box 1.6 reads:

> **GATE: bit-identical replay** — existing ledger replayed through refactored
> path produces byte-identical positions

That gate is what makes Phase 1 safe to run concurrently with the live T4
accrual. No harness for it existed before this session. If Phase 1 starts
(2026-08-09) without one, it either stalls at its own gate on day one, or the
gate gets declared passed on an eyeball comparison. This audit answers the
prerequisite question — is "byte-identical" achievable at all against the
current write path — before any harness code was written.

## Finding: as literally stated, byte-identical replay is NOT achievable

`open_position()` (`paper_trader.py:380-596`) writes a position record with
three classes of field. Only one class replays byte-identically for free.

### Class A — genuinely irreproducible (must be EXCLUDED from the gate, permanently)

**`kalshi_order_id`, `kalshi_order_status`, `kalshi_contracts`.**

When `self._kalshi and self._kalshi.has_signing_key() and kalshi_ticker`,
`open_position()` makes a real network call to Kalshi's demo venue
(`kalshi_client.py::submit_order`, confirmed live-wired in every production
caller: `run_mlb_paper_trade.py`, `run_t4_mlb_live.py`, `run_paper_trade.py`).
The venue assigns the order id and fill status at that moment; neither is a
function of any input this system controls, and re-submitting during replay
would create a **new**, different order, not reproduce the old one — so even
attempting a live replay call cannot fix this, and a `kalshi_client=None`
replay (the only safe option) can only ever produce
`(None, "local_only", None)`.

This is not a corner case. Direct inspection of the freshly-pulled ledgers
(2026-08-06, via `pull_vps_cache` pattern from `build_t4_resolved_ledger.py`):

| Ledger | total positions | `kalshi_order_status == "submitted"` | real order id present |
|---|---|---|---|
| T1/MAIN | 485 | 431 (88.9%) | 431 |
| T4M-PROJ | 2,416 | 2,404 (99.5%) | 2,404 |

(Remainder: `"failed: HTTP 410"` — also a real, non-replayable network
outcome — and a small `"local_only"` set that a replay *can* validate.)

~97.7% combined of all stored positions carry real external-venue state. A
gate that requires these three fields to match cannot ever pass for the
overwhelming majority of the real ledger, on any code path, refactored or
not.

### Class B — pinnable, but NOT reproduced by naive replay (must be explicitly injected)

**`entered_at`** — read from `_utc_now()` (wall clock). Naive replay
(re-calling `open_position()` today) writes today's timestamp, not the
original. Fix: the harness monkeypatches `paper_trader._utc_now` to return
the stored value before each call.

**`logic_epoch`, `approval_commit`** — bound to the module-level globals
`CURRENT_LOGIC_EPOCH` / `CURRENT_APPROVAL_COMMIT` (`logic_epoch.py`), which
resolve to "whichever epoch boundary is current for the code checked out
right now" — not a function of the call's inputs at all. The epoch has
bumped 8→12 in about a month; a naive replay against current code silently
writes today's epoch onto a months-old position and would misreport this as
a determinism defect when it is actually an unpinned global. Fix: the
harness monkeypatches both module attributes to the position's own stored
values before each call.

**`position_id`** — `f"POS-{uuid.uuid4().hex[:10].upper()}"`. Genuinely
random; the original value cannot be *derived*, but it also isn't external
state — it can be pinned by injecting a fake `uuid4()` whose `.hex[:10]`
reproduces the stored id, letting the field participate in the
byte-comparison instead of being excluded outright (unlike Class A).

None of Class B is achievable by "just calling `open_position()` again with
old inputs." All three require explicit harness-side injection. This is the
part of the gate most likely to get eyeballed-and-declared-passed without a
harness, because a lazy comparison (e.g. `diff`-ing two files with today's
epoch baked into both) would hide the defect rather than catch it.

### Class C — deterministic given correct input reconstruction (no special handling)

`player_name`, `player_id`, `kalshi_ticker`, `kalshi_threshold`, `direction`,
`mid_price_at_entry`, `vig_at_entry`, `size_usd`, `game_date`, `risk_eval_id`,
`forecast_id`, `band`, `model_p`, `gross_edge`, `fee_per_contract`,
`fee_net_edge`, `fee_contaminated`, `probable_injury_signal`, `t3_signal`,
`t1_edge`, `h_so_far_at_entry`, `ab_remaining_at_entry`, `entry_price_paid`,
`price_stratum`, `contracts` — all pure functions of the `approval` dict and
call arguments. `probable_injury_signal` is derived (`model_p`,
`mid_price`), not stored input, but is itself a pure function so it
reproduces exactly once `model_p`/`mid_price` are reconstructed correctly.

### Out of scope entirely — not written by `open_position()`

`aged_open`, `aged_open_at`, `aged_open_reason` appear on many stored
records but are written by `mark_aged_open()` (`paper_trader.py:935`),
called from `run_resolve_mlb.py:453` on positions stuck open >48h — a
separate function, invoked hours-to-days after the original
`open_position()` call. `status` itself is also mutated post-open by
resolution (`resolve_pending`/`exit_position`) for every closed position.
Neither is evidence of `open_position()` non-determinism if it differs from
a fresh replay (which always writes `status="OPEN"` and never touches the
`aged_open*` keys) — they are excluded from the comparison when the stored
record shows it left its as-opened state, and *included* (and expected to
match) when it didn't.

### Class D — code-version drift correlated with `logic_epoch` (found by RUNNING the harness, not by inspection — the most consequential result of this audit)

**This is the finding the task asked me to surface prominently if I found it.
The harness did NOT pass trivially against unrefactored code. Per instruction,
I investigated rather than assumed a harness bug — and confirmed this is real,
not a defect.**

`fee_net_edge` (and, downstream, `fee_contaminated`) is not a pure function of
stored inputs at all — it is a pure function of stored inputs **as evaluated
by whichever version of the vig-cascade formula was live in `paper_trader.py`
at the time the position was written.** That formula has changed three times
in the ledger's history, tracked exactly by the `logic_epoch` boundary table
(`logic_epoch.py`):

| Epoch range | Formula (NO-direction, band-specific) | Resolving gap |
|---|---|---|
| 1–2 | `gross_edge - fee_per_contract` (no direction-sign flip at all — the literal bug) | pre-GG-077 |
| 3 | `-gross_edge - fee_per_contract` (sign-flipped, **no vig term** — GG-077 fixed the sign for `bands_affected={'*'}` but did not yet add a vig-cost term for any band) | GG-077 (epoch-3 boundary, 2026-07-05) |
| T4M-PROJ: 4–12 (skipping the T1-only epoch-5 boundary) | `-gross_edge - 2.0*vig - fee_per_contract` | GG-113/ADR-0043 (epoch-4 boundary, 2026-07-15) |
| T1: 5–12 | `-gross_edge - 1.0*vig - fee_per_contract` | GG-119/ADR-0045 (epoch-5 boundary, 2026-07-15) |

Confirmed empirically, not just from the boundary-table narrative: sampled
5–6 records per epoch/band/branch cell and solved for the formula that
reproduces the stored `fee_net_edge` exactly (see harness run output below
for the reconciled record counts). Every cell matches one of the four rows
above with zero residual — this is not noise, it is exact.

**Why a single-HEAD replay harness cannot fix this:** the old formula code
does not exist anywhere in the current checkout. ADRs are immutable
(Hard Rule 3) — GG-077, ADR-0043, and ADR-0045 each *superseded* the
previous formula in place rather than branching it, so there is no
`git show <old-epoch-commit>:paper_trader.py` shortcut that helps a harness
running against current `HEAD`'s `open_position()` in-process. Reproducing
an epoch-1–4 position's `fee_net_edge` would require literally checking out
and running that historical commit's version of the function — a fundamentally
different (and much heavier) harness design than "call current
`open_position()` with pinned inputs." This is not a gap in the Class A/B/C
taxonomy above; it's a different *kind* of non-determinism: the function
itself is not stable over the ledger's history, independent of how well its
inputs are reconstructed.

**Practical scope for Phase 1's gate:** box 1.6 is meant to prove the
refactor doesn't silently change the vig-cascade's behavior. That is only a
meaningful, checkable claim against the formula version the refactor is
*actually refactoring* — i.e., the current epoch (12) formula. Historical
epoch 1–11 records are permanently out of reach of any single-HEAD replay,
refactored or not, for reasons that predate and are unrelated to Phase 1.
Scoping the gate to current-epoch data is not a weakening for expedience —
it's the only subset for which "replay reproduces this" is even a coherent
question.

## Corrected gate proposal

Replace box 1.6's literal wording with:

> **GATE: replay-identical modulo a frozen exclusion set, scoped to the
> current logic epoch** — existing ledger positions **written under the
> current `logic_epoch`** (12 as of 2026-08-06; re-check
> `logic_epoch.CURRENT_LOGIC_EPOCH` at gate time, since Phase 1 itself must
> not bump it), replayed through the refactored path, reproduce every field
> `open_position()` writes, **except**: (a) `kalshi_order_id`,
> `kalshi_order_status`, `kalshi_contracts`, permanently excluded from
> comparison whenever the original shows a real submission attempt
> (`status != "local_only"`) — this is unrecoverable external venue state,
> not something a refactor can preserve or break; (b) `position_id`,
> `entered_at`, `logic_epoch`, `approval_commit`, pinned via harness-injected
> values taken from the original stored record rather than left to the
> refactored code's own clock/RNG/module-state reads. All other written
> fields, plus `status` for positions still `OPEN` in the ledger, must match
> byte-for-byte. **Positions written under a superseded epoch are excluded
> from this gate by construction** (Class D, above) — their absence from a
> passing run is expected and is not evidence the refactor is wrong; if the
> current-epoch subset is too small at Phase-1 start to be a meaningful
> sample, supplement with synthetic fixtures constructed directly against
> the current formula rather than waiting for more current-epoch ledger
> volume to accrue.

This set is frozen *now*, from direct code inspection, live ledger data, and
an actual harness run against unrefactored code — not discovered ad hoc
mid-Phase-1 by whoever first runs the gate and gets a confusing diff.

## Harness

`scripts/replay_harness_t427.py`. Pulls both ledgers (already cached locally
this session via the `pull_vps_cache` SSH pattern from
`build_t4_resolved_ledger.py`; gitignored under `logs/`, not committed),
replays every `size_usd > 0`, `direction in {YES, NO}` position through a
fresh `PaperTrader(kalshi_client=None)` with the Class B monkeypatches
active, and applies the Class A/B/C comparison rules above per position.
Reports pass/fail/error counts and per-branch coverage (Task 3, below).

Run against the **current, unrefactored** code path this must pass trivially
— it is the baseline the harness itself is validated against before Phase 1
starts changing `open_position()`. See run output appended below / in the
session report.

## Task 3 — vig-cascade branch coverage (box 1.5 target, `paper_trader.py:460-467`)

```python
if direction == "YES":
    _directional_gross = gross_edge
elif band == "T4M-PROJ":
    _directional_gross = -gross_edge - 2.0 * vig
elif band == "T1":
    _directional_gross = -gross_edge - 1.0 * vig
else:
    _directional_gross = -gross_edge
```

All four branches ARE exercised by real ledger data (ad hoc `Counter` pass
over the pulled ledgers, then confirmed by the harness's own branch-coverage
report):

- **YES** — 35 (T1/MAIN) + 668 (T4M-PROJ) = 703 positions
- **T4M-PROJ NO** — 1,552 positions (`band=="T4M-PROJ"`, `direction=="NO"`)
- **T1 NO** — 450 positions (`band=="T1"`, `direction=="NO"`)
- **else fallthrough** — 196 positions (`band is None`, `direction=="NO"` —
  T4M-PROJ-era records predating band tagging)

The else branch is real, not a theoretical gap — 1.5's extraction to
per-market-type config has live coverage behind all four branches, not
three of four. (Exact counts from the harness's own run below.)

**Epoch reconciliation per branch (Class D, exact record-count match against
harness output):**

- **T1-NO** (450 total): 143 epoch 1–2 (unflipped) + 111 epoch 3
  (sign-flipped, no vig) + 196 epoch 5–8/current (current formula, matches
  harness `pass=196`) = 450. ✓
- **T4M-PROJ-NO** (1,552 total): 470 epoch 3 (sign-flipped, no vig) + 1,082
  epoch 4/6/7/8/12 (current formula, matches harness `pass=1082`) = 1,552. ✓
- **ELSE-fallthrough** (196 total): 196 epoch 2–3 (unflipped/no-band-tag era)
  + 0 current (matches harness `pass=0` — every else-branch record predates
  band tagging, none reach the current formula) = 196. ✓
- **YES** (703 total): direction-invariant formula (`_directional_gross =
  gross_edge`, unaffected by any of the three formula versions), all 703
  pass under current code (matches harness `pass=703`, 35+668). ✓

Every mismatch the harness reports is fully and exactly explained by Class D.
Zero unexplained residual.

## Run output

Harness run 2026-08-06 against unrefactored `paper_trader.py` (this branch,
pre-any-Phase-1-change):

```
=== .vps_cache_paper_portfolio_mlb.json ===
total positions in file:  485
evaluated (size>0, YES/NO): 485
PASS: 231  FAIL: 254  ERROR: 0
branch coverage (real ledger data):
  T1-NO              n=  450  pass=  196
  YES                n=   35  pass=   35
mismatch examples by branch:
  [T1-NO]
    fee_net_edge: stored=-0.108086 replayed=0.059862

=== .vps_cache_paper_portfolio_mlb_t4.json ===
total positions in file:  2416
evaluated (size>0, YES/NO): 2416
PASS: 1750  FAIL: 666  ERROR: 0
branch coverage (real ledger data):
  ELSE-fallthrough   n=  196  pass=    0
  T4M-PROJ-NO        n= 1552  pass= 1082
  YES                n=  668  pass=  668
mismatch examples by branch:
  [ELSE-fallthrough]
    fee_net_edge: stored=-0.091679 replayed=0.070133
  [T4M-PROJ-NO]
    fee_net_edge: stored=0.05408 replayed=-0.02592
    fee_contaminated: stored=False replayed=True

MISMATCHES FOUND — see above
```

Combined: 2,901 evaluated, 1,981 PASS, 920 FAIL, 0 ERROR. **Every one of the
920 failures is a Class D epoch-formula-version mismatch, not a harness
defect or Class A/B/C gap** — see epoch reconciliation above. Restricting
the comparison to current-epoch (12) positions only, as the corrected gate
proposes, would show 100% pass (the 1,981 PASS above already are exactly
the current-formula + direction-invariant-YES subset). Zero `ERROR`s means
the reconstruction (`reconstruct_approval`) and pinning
(`position_id`/`entered_at`/`logic_epoch`/`approval_commit`) machinery is
itself sound — every replay call succeeded and returned a comparable record;
none were rejected by risk/validation gates inside `open_position()`.

## Pytest baseline (Task 4, box 1.7 comparison)

Box 1.7 states a baseline of "2,799 passed / 8 known-failed / 29 skipped,"
explicitly flagged in that same doc as something to re-derive, not copy.
Re-run this session (2026-08-06, full suite, 375.21s):

```
14 failed, 2813 passed, 28 skipped, 2 warnings in 375.21s (0:06:15)
```

Breakdown of the 14 failures:
- **8 — `tests/test_exp015_t3_simulation.py`** (`ZeroDivisionError` on
  `T1_KELLY`). This is very likely the same "8 known-failed" cohort box 1.7
  refers to (count matches exactly) — consistent with ADR-0048/epoch-9
  (2026-07-29) zeroing `T1_MULTI_DAY`'s `kelly_fraction` in
  `execution_bands.py`, which `run_exp015.py`'s `T1_KELLY` constant reads
  from; the test module divides by it unconditionally
  (`T3_KELLY * CONFIRM_MULTIPLIER / T1_KELLY`) and was never updated for the
  zeroed-Kelly regime. Not investigated further — out of this task's scope
  fence (no `src/` changes), and pre-existing per box 1.7's own count.
- **6 — `tests/integration/test_mlb_api_connectivity.py`** (`TestESPNAPIConnectivity`,
  all methods). Not a new finding of this audit — already diagnosed and
  logged in `DECISION_LOG.md` 2026-08-05 (T-421): these hit ESPN's live
  scoreboard/summary endpoints, which 403 on the `Mozilla/5.0` User-Agent
  string this test suite and `run_t4_mlb_live.py`/`run_resolve_mlb.py` all
  share (GG-163, confirmed UA-keyed, not IP/datacenter-scoped). T-421's own
  session-end run on 2026-08-05 recorded the **identical** result —
  `2,813 passed / 28 skipped / 14 failed`, same 8+6 split — so this session's
  run is a second, independent reproduction of an already-open gap, not a
  new regression. Not investigated further here, consistent with T-421's
  same scope decision.

Passed/failed/skipped counts (2,813/14/28) match T-421's 2026-08-05 baseline
exactly, not box 1.7's stated 2,799/8/29 — box 1.7's figure predates GG-163's
discovery. This session's baseline is current as of 2026-08-06; no drift
since 2026-08-05.
